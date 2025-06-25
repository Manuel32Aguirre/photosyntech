from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QGridLayout, QHBoxLayout,
    QSizePolicy, QFrame
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.dates import DateFormatter
from PyQt6.QtCore import QTimer, Qt, QThread, pyqtSignal

from controller.GetWeather import GetWeather
from controller.WeatherWorker import WeatherWorker
from ui.modules.Module import Module
from collections import deque
import datetime
import time

BG_COLOR     = "#1B1731"
CARD_COLOR   = "#1A1D2E"
ACCENT_GREEN = "#1DB954"
TEXT_COLOR   = "white"
VENTANA_SEGUNDOS = 60

def parse_float(val):
    try:
        return float(val) if val != '--' else 0.0
    except ValueError:
        return 0.0

class SensorDataUpdater(QThread):
    data_ready = pyqtSignal(float, float, float, float, datetime.datetime)

    def __init__(self, signal_bio):
        super().__init__()
        self.signal_bio = signal_bio
        self.running = True

    def run(self):
        while self.running:
            temp_str, hum_str, light_str, soil_str = self.signal_bio.obtener_datos_sensores()
            temp  = parse_float(temp_str)
            hum   = parse_float(hum_str)
            light = parse_float(light_str)
            soil  = parse_float(soil_str)
            self.data_ready.emit(temp, hum, light, soil, datetime.datetime.now())
            time.sleep(3)

    def stop(self):
        self.running = False
        self.wait(1000)

class GraphsModule(Module):
    def __init__(self, signal_bio, main_module, weather: GetWeather):
        super().__init__()
        self.signal_bio = signal_bio
        self.main_module = main_module
        self.graph_data = {}
        self.buffer = {}
        self.data_updater = None
        self.__weather = weather
        self.__worker_thread = None
        self.__worker = None

    def draw(self):
        self.setStyleSheet(f"""
            QWidget  {{ background: {BG_COLOR}; color: {TEXT_COLOR}; font-family: Arial; }}
            QPushButton {{
                background: {ACCENT_GREEN}; color: white; padding: 6px 12px;
                border-radius: 6px; font-weight: 600;
            }}
            QFrame#Card {{ background: {CARD_COLOR}; border-radius: 12px; }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(24)

        title = QLabel("Visualización de sensores ambientales")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 26px; font-weight: 600;")
        root.addWidget(title)

        body = QHBoxLayout(spacing=24)
        root.addLayout(body)

        grid = QGridLayout(spacing=24)
        body.addLayout(grid, stretch=3)

        for name, label, color, pos in [
            ("Temperatura", "°C", "red", (0, 0)),
            ("Humedad Ambiente", "%", "cyan", (0, 1)),
            ("Iluminación", "Lux", "gold", (1, 0)),
            ("Humedad Suelo", "%", "green", (1, 1))  # NUEVO gráfico
        ]:
            graph = self.create_graph(name, label, color)
            grid.addWidget(graph, *pos)
            self.buffer[name] = {"x": deque(maxlen=VENTANA_SEGUNDOS), "y": deque(maxlen=VENTANA_SEGUNDOS)}

        card = QFrame(objectName="Card")
        card.setMinimumWidth(260)
        body.addWidget(card, stretch=1)

        v = QVBoxLayout(card)
        v.setContentsMargins(20, 20, 20, 20)
        v.setSpacing(12)

        lbl = QLabel("Clima en tu región")
        lbl.setStyleSheet("font-size: 18px; font-weight: 600;")
        v.addWidget(lbl)

        sub = QLabel("Utiliza estos datos como referencia")
        sub.setStyleSheet("opacity:.8;")
        v.addWidget(sub)

        self.lbl_info = QLabel(
            "CDMX\nCiudad de México\n\n"
            "🌡️  -- °C\n"
            "💦 Humedad Amb: --%\n"
            "🔆 Luz: -- lux\n"
            "🌱 Humedad Suelo: --%\n"
            "Esperando datos..."
        )
        self.lbl_info.setStyleSheet("font-size: 15px; line-height: 1.3em;")
        v.addWidget(self.lbl_info)

        btn = QPushButton("Actualizar ahora", clicked=self.__update_weather_data)
        v.addWidget(btn)
        v.addStretch()

        self.start_data_updater()

    def create_graph(self, title, ylabel, color):
        fig = Figure(facecolor=CARD_COLOR, figsize=(6, 4), dpi=100)
        canvas = FigureCanvas(fig)
        canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        canvas.setMinimumHeight(240)

        ax = fig.add_subplot(111)
        ax.set_facecolor("#0f0f1f")
        ax.grid(True, color="#3b3b5e", linestyle="--")
        ax.tick_params(axis='x', labelrotation=45, color=TEXT_COLOR, labelcolor=TEXT_COLOR)
        ax.tick_params(axis='y', color=TEXT_COLOR, labelcolor=TEXT_COLOR)
        for spine in ax.spines.values():
            spine.set_color(TEXT_COLOR)

        line, = ax.plot([], [], color=color, marker='o', ms=4, linestyle="-")
        ax.set_title(title, pad=12, color=TEXT_COLOR, fontsize=14)
        ax.set_ylabel(ylabel, color=TEXT_COLOR)
        ax.set_xlabel("Hora", color=TEXT_COLOR)
        ax.xaxis.set_major_formatter(DateFormatter('%H:%M:%S'))
        fig.tight_layout()

        self.graph_data[title] = {
            "ax": ax,
            "canvas": canvas,
            "line": line
        }

        return canvas

    def start_data_updater(self):
        if not self.data_updater:
            self.data_updater = SensorDataUpdater(self.signal_bio)
            self.data_updater.data_ready.connect(self.update_graphs)
            self.data_updater.start()

    def stop_data_updater(self):
        if self.data_updater and self.data_updater.isRunning():
            self.data_updater.stop()

    def force_update(self):
        temp_str, hum_str, light_str, soil_str = self.signal_bio.obtener_datos_sensores()
        temp  = parse_float(temp_str)
        hum   = parse_float(hum_str)
        light = parse_float(light_str)
        soil  = parse_float(soil_str)
        self.update_graphs(temp, hum, light, soil, datetime.datetime.now())

    def update_graphs(self, temp=0.0, hum=0.0, light=0.0, soil=0.0, timestamp=None):
        now = timestamp or datetime.datetime.now()

        # OVERRIDE: Usar la humedad fake del MainModule
        soil = float(self.main_module._MainModule__soil_fake_value)

        data_map = {
            "Temperatura": temp,
            "Humedad Ambiente": hum,
            "Iluminación": light,
            "Humedad Suelo": soil
        }

        for title, value in data_map.items():
            buf = self.buffer[title]
            g = self.graph_data[title]

            buf["x"].append(now)
            buf["y"].append(value)

            g["line"].set_data(buf["x"], buf["y"])
            g["ax"].relim()
            g["ax"].autoscale_view(scalex=False, scaley=True)
            g["ax"].set_xlim(now - datetime.timedelta(seconds=VENTANA_SEGUNDOS), now)
            g["canvas"].draw_idle()
        info = self.__weather.get_weather()
        self.lbl_info.setText(
            f"{info.city}\n{info.region}\n\n"
            f"🌡️  {info.temperature} °C\n"
            f"💦 {info.condition}\n"
            f"Actualizado: {info.last_updated}"
        )

    def __update_weather_data(self):
        info = self.__weather.get_weather()
        self.lbl_info.setText(
            f"{info.city}\n{info.region}\n\n"
            f"🌡️  {info.temperature} °C\n"
            f"💦 {info.condition}\n"
            f"Actualizado: {info.last_updated}"
        )

    def closeEvent(self, event):
        self.stop_data_updater()
        super().closeEvent(event)

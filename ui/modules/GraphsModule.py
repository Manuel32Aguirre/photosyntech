from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QGridLayout, QHBoxLayout,
    QSizePolicy, QFrame
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.dates import DateFormatter
from PyQt6.QtCore import QTimer, Qt, QThread, pyqtSignal
from ui.modules.Module import Module
from ui.modules.getBioelectricalSignal import SeñalBioeléctrica
from collections import deque
import datetime
import time

BG_COLOR     = "#1B1731"
CARD_COLOR   = "#1A1D2E"
ACCENT_GREEN = "#1DB954"
TEXT_COLOR   = "white"
VENTANA_SEGUNDOS = 60 

class SensorDataUpdater(QThread):
    data_ready = pyqtSignal(float, float, float, float, datetime.datetime)
    
    def __init__(self, signal_bio):
        super().__init__()
        self.signal_bio = signal_bio
        self.running = True
        
    def run(self):
        while self.running:
            # Obtener datos de los sensores
            temp_str, hum_str, soil_str, light_str = self.signal_bio.obtener_datos_sensores()
            
            # Convertir a float con manejo de errores
            try:
                temp = float(temp_str) if temp_str != '--' else 0.0
                hum = float(hum_str) if hum_str != '--' else 0.0
                soil = float(soil_str) if soil_str != '--' else 0.0
                light = float(light_str) if light_str != '--' else 0.0
            except ValueError:
                temp, hum, soil, light = 0.0, 0.0, 0.0, 0.0
            
            # Emitir datos con marca de tiempo
            self.data_ready.emit(temp, hum, soil, light, datetime.datetime.now())
            time.sleep(3)  # Actualizar cada 3 segundos
    
    def stop(self):
        self.running = False
        self.wait(1000)

class GraphsModule(Module):
    def __init__(self, signal_bio):
        super().__init__()
        self.signal_bio = signal_bio
        self.graph_data = {}
        self.buffer = {}
        self.data_updater = None

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

        self.graph_data = {}
        self.buffer = {}
        grid = QGridLayout(spacing=24)
        body.addLayout(grid, stretch=3)

        # Configurar gráficos con unidades correctas
        for name, label, color, pos in [
            ("Temperatura", "°C",         "red",         (0, 0)),
            ("Humedad Suelo", "%",        "dodgerblue",  (0, 1)),
            ("Humedad Ambiente", "%",    "cyan",        (1, 0)),
            ("Iluminación",   "Lux",      "gold",        (1, 1)),
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
            "CDMX\nCiudad de México\n\n☁️  -- °C\n"
            "Humedad: --%\nH. Suelo: --%\nLuz: -- lux\n"
            "Esperando datos..."
        )
        self.lbl_info.setStyleSheet("font-size: 15px; line-height: 1.3em;")
        v.addWidget(self.lbl_info)

        btn = QPushButton("Actualizar ahora", clicked=self.force_update)
        v.addWidget(btn)
        v.addStretch()

        # Iniciar actualización de datos en segundo plano
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
        """Inicia el hilo para recolectar datos de los sensores"""
        if not self.data_updater:
            self.data_updater = SensorDataUpdater(self.signal_bio)
            self.data_updater.data_ready.connect(self.update_graphs)
            self.data_updater.start()
    
    def stop_data_updater(self):
        """Detiene la recolección de datos al cerrar el módulo"""
        if self.data_updater and self.data_updater.isRunning():
            self.data_updater.stop()
    
    def force_update(self):
        """Forzar una actualización inmediata"""
        if self.data_updater:
            # Obtener datos actuales sin esperar al ciclo normal
            temp_str, hum_str, soil_str, light_str = self.signal_bio.obtener_datos_sensores()
            try:
                temp = float(temp_str) if temp_str != '--' else 0.0
                hum = float(hum_str) if hum_str != '--' else 0.0
                soil = float(soil_str) if soil_str != '--' else 0.0
                light = float(light_str) if light_str != '--' else 0.0
                self.update_graphs(temp, hum, soil, light, datetime.datetime.now())
            except ValueError:
                pass
    
    def update_graphs(self, temp=0.0, hum=0.0, soil=0.0, light=0.0, timestamp=None):
        """Actualiza los gráficos con nuevos datos"""
        now = timestamp if timestamp else datetime.datetime.now()
        
        # Mapeo de datos a gráficos
        data_map = {
            "Temperatura": temp,
            "Humedad Suelo": soil,
            "Humedad Ambiente": hum,
            "Iluminación": light
        }

        for title, value in data_map.items():
            if title not in self.graph_data:
                continue
                
            buf = self.buffer[title]
            g = self.graph_data[title]

            # Agregar nuevos datos al buffer
            buf["x"].append(now)
            buf["y"].append(value)

            # Actualizar línea del gráfico
            g["line"].set_data(buf["x"], buf["y"])
            
            # Ajustar ejes si hay datos
            if buf["x"]:
                g["ax"].relim()
                g["ax"].autoscale_view(scalex=False, scaley=True)
                
                # Ventana de tiempo deslizante
                g["ax"].set_xlim(
                    now - datetime.timedelta(seconds=VENTANA_SEGUNDOS),
                    now
                )
            
            # Redibujar el gráfico
            g["canvas"].draw_idle()

        # Actualizar panel de información
        self.lbl_info.setText(
            f"CDMX\nCiudad de México\n\n"
            f"☁️  {temp:.1f} °C\n"
            f"Humedad: {hum:.1f}%\n"
            f"H. Suelo: {soil:.1f}%\n"
            f"Luz: {light:.0f} lux\n"
            f"Actualizado: {now.strftime('%H:%M:%S')}"
        )
    
    def closeEvent(self, event):
        self.stop_data_updater()
        super().closeEvent(event)
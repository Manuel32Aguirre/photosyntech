from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QGridLayout, QHBoxLayout,
    QSizePolicy, QFrame
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.dates import DateFormatter
from PyQt6.QtCore import QTimer, Qt
from ui.modules.Module import Module
from collections import deque
import datetime


BG_COLOR     = "#1B1731"
CARD_COLOR   = "#1A1D2E"
ACCENT_GREEN = "#1DB954"
TEXT_COLOR   = "white"

VENTANA_SEGUNDOS = 60 

class GraphsModule(Module):
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

        for name, label, color, pos in [
            ("Temperatura", "Grados °C",  "red",         (0, 0)),
            ("Humedad Suelo", "%RH",      "dodgerblue",  (0, 1)),
            ("Humedad Ambiente", "%RH",   "cyan",        (1, 0)),
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
            "CDMX\nCiudad de México\n\n☁️  15 °C\nNublado\n"
            "Última actualización:\n2021-02-21 08:30"
        )
        self.lbl_info.setStyleSheet("font-size: 15px; line-height: 1.3em;")
        v.addWidget(self.lbl_info)

        btn = QPushButton("Actualizar ahora", clicked=self.update_graphs)
        v.addWidget(btn)
        v.addStretch()

        
        self.timer = QTimer(self, timeout=self.update_graphs)
        self.timer.start(1000) 

        self.update_graphs()


    def create_graph(self, title, ylabel, color):
        fig = Figure(facecolor=CARD_COLOR)
        canvas = FigureCanvas(fig)
        canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        canvas.setMinimumHeight(240)

        ax = fig.add_subplot(111)
        ax.set_facecolor("white")
        ax.grid(True)
        ax.tick_params(axis='x', labelrotation=45, color=TEXT_COLOR, labelcolor=TEXT_COLOR)
        ax.tick_params(axis='y', color=TEXT_COLOR, labelcolor=TEXT_COLOR)
        for spine in ax.spines.values():
            spine.set_color(TEXT_COLOR)

        line, = ax.plot([], [], color=color, marker='o', ms=5)

        ax.set_title(title, pad=12, color=TEXT_COLOR)
        ax.set_ylabel(ylabel)
        ax.set_xlabel("Hora")
        ax.xaxis.set_major_formatter(DateFormatter('%H:%M:%S'))
        fig.autofmt_xdate()

        annot = ax.annotate(
            "", xy=(0, 0), xytext=(0, -30), textcoords="offset points", ha="center",
            bbox=dict(boxstyle="round", fc="white", alpha=0.85, ec="black", lw=0.5),
            arrowprops=dict(arrowstyle="->", color="black")
        )
        annot.set_visible(False)

        def update_annot(ind):
            x_vals, y_vals = line.get_data()
            if len(ind["ind"]) > 0:  # ← Aquí el fix
                i = ind["ind"][0]
                annot.xy = (x_vals[i], y_vals[i])
                annot.set_text(f"{y_vals[i]:.2f}")

        def hover(event):
            if event.inaxes == ax:
                cont, ind = line.contains(event)
                if cont:
                    update_annot(ind)
                    annot.set_visible(True)
                    fig.canvas.draw_idle()
                elif annot.get_visible():
                    annot.set_visible(False)
                    fig.canvas.draw_idle()

        fig.canvas.mpl_connect("motion_notify_event", hover)

        self.graph_data[title] = {
            "ax": ax,
            "canvas": canvas,
            "line": line,
            "annot": annot
        }

        return canvas


    def update_graphs(self):
        from ui.modules.SensorReader import get_sensor_data
        now = datetime.datetime.now()
        data = get_sensor_data()

        for label, val in data.items():
            buf = self.buffer[label]
            g = self.graph_data[label]

            buf["x"].append(now)
            buf["y"].append(val)

            g["line"].set_data(buf["x"], buf["y"])
            g["ax"].relim()
            g["ax"].autoscale_view()

            g["ax"].set_xlim(
                now - datetime.timedelta(seconds=VENTANA_SEGUNDOS),
                now
            )

            g["canvas"].draw()

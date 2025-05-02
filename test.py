import sys
import time as timemod
import requests
import numpy as np
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame, QHBoxLayout, QVBoxLayout,
    QLabel, QComboBox, QToolButton, QGraphicsDropShadowEffect, QSizePolicy
)
from PyQt6.QtGui import QIcon, QCursor, QColor, QMovie
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QTimer
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

FIREBASE_PLANTA_URL = "https://photosyntech-10464-default-rtdb.firebaseio.com/planta.json"

class IconButton(QToolButton):
    def __init__(self, icon_path, text):
        super().__init__()
        self.setText(text)
        self.setIcon(QIcon(icon_path))
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        shadow = QGraphicsDropShadowEffect(blurRadius=15, xOffset=0, yOffset=0)
        shadow.setColor(QColor(0, 255, 200))
        self.setGraphicsEffect(shadow)
        self.anim = QPropertyAnimation(self, b"iconSize")
        self.anim.setDuration(300)
        self.anim.setEasingCurve(QEasingCurve.Type.OutBack)

    def enterEvent(self, event):
        self.anim.stop()
        start = self.iconSize()
        self.anim.setStartValue(start)
        self.anim.setEndValue(start * 1.3)
        self.anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.anim.stop()
        start = self.iconSize()
        self.anim.setStartValue(start)
        self.anim.setEndValue(start / 1.3)
        self.anim.start()
        super().leaveEvent(event)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PhotoSyntech v1.0")
        self.resize(1280, 720)
        self.times = []
        self.temps = []
        self.setup_ui()
        self.apply_styles()
        self.setup_animations()
        self.start_data_timer()

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left panel
        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(10)

        # Toolbar
        toolbar = QFrame()
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setSpacing(10)
        icons = [
            ("icons/upload.svg", ""), ("icons/sensor.svg", ""), ("icons/settings.svg", ""),
            ("icons/plant.svg", ""), ("icons/weather.svg", ""), ("icons/play.svg", ""),
            ("icons/key.svg", ""), ("icons/record.svg", "")
        ]
        for path, _ in icons:
            btn = IconButton(path, "")
            btn.setFixedSize(50, 50)
            btn.clicked.connect(lambda _, p=path: print(f"{p} clicked"))
            tb_layout.addWidget(btn)
        left_layout.addWidget(toolbar)

        # Figure & Canvas
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        left_layout.addWidget(self.canvas, 1)
        main_layout.addWidget(left_frame, 3)

        # Right panel
        right_frame = QFrame()
        right_frame.setObjectName("rightPanel")
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(15, 15, 15, 15)
        right_layout.setSpacing(10)

        # Info labels
        info = QHBoxLayout()
        self.climate_label = QLabel("🌡️ Temp: -- °C")
        self.soil_label = QLabel("💧 H.suelo: -- %")
        self.humid_label = QLabel("💦 H.rel: -- %")
        info.addWidget(self.climate_label)
        info.addWidget(self.soil_label)
        info.addWidget(self.humid_label)
        right_layout.addLayout(info)
        gif = QLabel(alignment=Qt.AlignmentFlag.AlignCenter)
        movie = QMovie("MTLnEyn6c.gif")
        movie.setSpeed(50)  # Reduce la velocidad (menos que 100 será más lento)
        gif.setMovie(movie)
        movie.start()
        right_layout.addWidget(gif, 3)


        # Controls
        ctr = QHBoxLayout()
        combo = QComboBox()
        combo.addItems(["C", "D", "E", "F", "G", "A", "B"])
        combo.currentTextChanged.connect(lambda t: print(f"Tonalidad: {t}"))
        rec = IconButton("icons/record.svg", "")
        rec.setFixedSize(50, 50)
        rec.clicked.connect(lambda: print("Record pressed"))
        ctr.addWidget(combo)
        ctr.addWidget(rec)
        right_layout.addLayout(ctr)

        main_layout.addWidget(right_frame, 1)

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow{background:#0a0a10;}
            #rightPanel{background:#0f0f1f;}
            QFrame{background:#1a1a2e;}
            QToolButton{border:none;}
            QLabel{color:#e0e0e0;}
            QComboBox{background:#1a1a2e;color:#e0e0e0;
                      border:1px solid #3b3b5e;border-radius:4px;}
        """)

    def setup_animations(self):
        tb = self.centralWidget().findChild(QFrame)
        anim = QPropertyAnimation(tb, b"geometry")
        anim.setDuration(800)
        start = QRect(tb.x(), -60, tb.width(), tb.height())
        end = tb.geometry()
        anim.setStartValue(start)
        anim.setEndValue(end)
        anim.setEasingCurve(QEasingCurve.Type.OutBounce)
        anim.start()

    def start_data_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.fetch_and_update)
        self.timer.start(5000)

    def fetch_and_update(self):
        try:
            r = requests.get(FIREBASE_PLANTA_URL, timeout=3)
            if r.status_code == 200:
                data = r.json() or {}
                t = data.get("temperatura")
                hs = data.get("humedad_suelo")
                hr = data.get("humedad")
                if t is not None and hs is not None and hr is not None:
                    self.climate_label.setText(f"🌡️ Temp: {t} °C")
                    self.soil_label.setText(f"💧 H.suelo: {hs} %")
                    self.humid_label.setText(f"💦 H.rel: {hr} %")
                    now = timemod.time()
                    self.times.append(now)
                    self.temps.append(t)

                    # Definir el rango del eje X para mantener el margen
                    if len(self.times) > 1:
                        # Asegurar que el margen no se agote
                        self.ax.set_xlim(self.times[0], self.times[-1] + 60)  # +60 segundos de margen
                    self.ax.clear()
                    self.ax.plot(self.times, self.temps)
                    self.ax.set_title("Temperatura vs Tiempo")
                    self.ax.set_xlabel("Tiempo")
                    self.ax.set_ylabel("°C")
                    self.canvas.draw()
        except Exception as e:
            print("Error fetching data:", e)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

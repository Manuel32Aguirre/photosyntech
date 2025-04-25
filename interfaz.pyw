import numpy as np
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QFrame, QHBoxLayout, QVBoxLayout,
    QLabel, QComboBox, QSizePolicy
)
from PyQt6.QtGui import QMovie
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from funciones import IconButton

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PhotoSyntech v1.0")
        self.resize(1280, 720)
        self.setup_ui()
        self.apply_styles()
        self.setup_animations()

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(0)

        # Left panel
        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(10,10,10,10)
        left_layout.setSpacing(10)

        # Toolbar
        toolbar = QFrame()
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setSpacing(10)
        icons = [
            ("icons/upload.svg",""), ("icons/sensor.svg",""), ("icons/settings.svg",""),
            ("icons/plant.svg",""), ("icons/weather.svg",""), ("icons/play.svg",""),
            ("icons/key.svg",""), ("icons/record.svg","")
        ]
        for path,_ in icons:
            btn = IconButton(path, "")
            btn.setFixedSize(50, 50)
            btn.clicked.connect(lambda _, p=path: print(f"{p} clicked"))
            tb_layout.addWidget(btn)
        left_layout.addWidget(toolbar)

        # Plot
        fig, ax = plt.subplots()
        x = np.linspace(0, 2*np.pi, 200)
        y = np.sin(x)
        ax.plot(x, y)
        ax.set_title("Señal obtenida")
        ax.set_xlabel("Tiempo")
        ax.set_ylabel("Amplitud")
        canvas = FigureCanvas(fig)
        canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        left_layout.addWidget(canvas, 1)

        main_layout.addWidget(left_frame, 3)

        # Right panel
        right_frame = QFrame()
        right_frame.setObjectName("rightPanel")
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(15,15,15,15)
        right_layout.setSpacing(10)

        info = QHBoxLayout()
        self.climate_label = QLabel("☀️ Clima: -- °C")
        self.state_label = QLabel("🌱 Estado: --")
        info.addWidget(self.climate_label)
        info.addWidget(self.state_label)
        right_layout.addLayout(info)

        gif = QLabel(alignment=Qt.AlignmentFlag.AlignCenter)
        movie = QMovie("mimosa.gif")
        gif.setMovie(movie)
        movie.start()
        right_layout.addWidget(gif, 3)

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
            QMainWindow { background: #0a0a10; }
            #rightPanel { background: #0f0f1f; }
            QFrame { background: #1a1a2e; }
            QToolButton { border: none; }
            QLabel { color: #e0e0e0; }
            QComboBox {
                background: #1a1a2e;
                color: #e0e0e0;
                border: 1px solid #3b3b5e;
                border-radius: 4px;
            }
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

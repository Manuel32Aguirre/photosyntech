from datetime import datetime, timedelta
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QHBoxLayout, QFrame, QVBoxLayout, QSizePolicy, QLabel, QComboBox
)
from PyQt6.QtGui import QMovie
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib import dates as mdates

from ui.IconButton import IconButton
from ui.fonts import fonts
from ui.modules.Module import Module
from ui.modules.getBioelectricalSignal import SeñalBioeléctrica
import os


class MainModule(Module):
    def __init__(self):
        super().__init__()
        self.__main_layout = QHBoxLayout()
        self.__left_frame = QFrame()
        self.__right_frame = QFrame()
        self.__right_frame.setObjectName("rightPanel")
        self.__left_layout = QVBoxLayout(self.__left_frame)
        self.__right_layout = QVBoxLayout(self.__right_frame)
        self.__fig, self.__ax = plt.subplots()
        self.__canvas = FigureCanvas(self.__fig)
        self.__climate_label = QLabel("🌡️ Temp: -- °C")
        self.__soil_label = QLabel("💧 H.suelo: -- %")
        self.__humid_label = QLabel("💦 H.rel: -- %")
        self.__combo = QComboBox()

        # Señal bioeléctrica
        self.__signal = SeñalBioeléctrica(frecuencia_hz=2)
        self.__timer = QTimer()
        self.__tiempos = []
        self.__voltajes = []

        # Ruta del gif
        d = os.path.dirname(__file__)
        self.__movie = QMovie(os.path.join(d, "../img/plant.gif"))

        self.setStyleSheet("""
            #rightPanel{background:#0f0f1f;}
            QFrame{background:#1a1a2e;}
            QToolButton{border:none;}
            QLabel{color:#e0e0e0;}
            QComboBox{background:#1a1a2e;color:#e0e0e0;
                      border:1px solid #3b3b5e;border-radius:4px;}
        """)

    def draw(self):
        self.__main_layout.setContentsMargins(0, 0, 0, 0)
        self.__main_layout.setSpacing(0)
        self.__left_layout.setContentsMargins(10, 10, 10, 10)
        self.__left_layout.setSpacing(10)

        # Toolbar
        toolbar = QFrame()
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setSpacing(10)
        #icons = [
          #  ("icons/upload.svg", ""), ("icons/sensor.svg", ""), ("icons/settings.svg", ""),
         #   ("icons/plant.svg", ""), ("icons/weather.svg", ""), ("icons/play.svg", ""),
        #    ("icons/key.svg", ""), ("icons/record.svg", "")
        #]
        #icons = []
        #for path, _ in icons:
         #   btn = IconButton(path, "")
         #   btn.setFixedSize(50, 50)
         #   btn.clicked.connect(lambda _, p=path: print(f"{p} clicked"))
         #   tb_layout.addWidget(btn)
        self.__left_layout.addWidget(toolbar)

        # Gráfica
        self.__canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.__left_layout.addWidget(self.__canvas, 1)
        self.__ax.set_title("Señal Bioeléctrica en tiempo real (2 Hz)")
        self.__ax.set_xlabel("Hora")
        self.__ax.set_ylabel("Voltaje (V)")
        self.__ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        self.__ax.xaxis.set_major_locator(mdates.AutoDateLocator())

        self.__main_layout.addWidget(self.__left_frame, 3)

        # Panel derecho
        self.__right_layout.setContentsMargins(15, 15, 15, 15)
        self.__right_layout.setSpacing(10)

        # INFO (H.temp / H.suelo / H.rel)
        info = QHBoxLayout()
        self.__climate_label.setFont(fonts.TITLE)
        self.__soil_label.setFont(fonts.TITLE)
        self.__humid_label.setFont(fonts.TITLE)
        info.addWidget(self.__climate_label)
        info.addWidget(self.__soil_label)
        info.addWidget(self.__humid_label)
        self.__right_layout.addLayout(info)

        # GIF planta
        gif = QLabel(alignment=Qt.AlignmentFlag.AlignCenter)
        gif.setMovie(self.__movie)
        self.__movie.setSpeed(50)
        self.__movie.start()
        self.__right_layout.addWidget(gif, 3)

        # Combo + botón grabar
        ctr = QHBoxLayout()
        self.__combo.addItems(["C", "D", "E", "F", "G", "A", "B"])
        self.__combo.currentTextChanged.connect(lambda t: print(f"Tonalidad: {t}"))
        rec = IconButton("img/record.webp", "")
        rec.setFixedSize(50, 50)
        rec.clicked.connect(lambda: print("Record pressed"))
        ctr.addWidget(self.__combo)
        ctr.addWidget(rec)
        self.__right_layout.addLayout(ctr)

        self.__main_layout.addWidget(self.__right_frame, 1)
        self.setLayout(self.__main_layout)

        # Inicia gráfica en tiempo real
        self.__iniciar_actualizacion()

    def __iniciar_actualizacion(self):
        self.__timer.timeout.connect(self.__actualizar_grafica)
        self.__timer.start(50)

    def __actualizar_grafica(self):
        tiempo, voltaje = self.__signal.siguiente_valor()
        self.__tiempos.append(tiempo)
        self.__voltajes.append(voltaje)

        ventana = timedelta(seconds=5)
        corte = tiempo - ventana
        while self.__tiempos and self.__tiempos[0] < corte:
            self.__tiempos.pop(0)
            self.__voltajes.pop(0)

        self.__ax.clear()
        self.__ax.plot(self.__tiempos, self.__voltajes, color="#6BA568")
        self.__ax.set_title("Señal Bioeléctrica en tiempo real (2 Hz)")
        self.__ax.set_xlabel("Hora")
        self.__ax.set_ylabel("Voltaje (V)")
        self.__ax.set_ylim(0, 3)
        self.__ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S.%f'))
        self.__ax.set_xlim(left=corte, right=tiempo)
        self.__fig.autofmt_xdate()
        self.__canvas.draw()

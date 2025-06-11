from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QHBoxLayout, QFrame, QVBoxLayout, QSizePolicy, QLabel, QComboBox
)
from PyQt6.QtGui import QMovie
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.lines import Line2D

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
        self.__climate_label = QLabel("\U0001F321️ Temp: -- °C")
        self.__soil_label = QLabel("💧 H.suelo: --")
        self.__humid_label = QLabel("💦 H.rel: --")
        self.__light_label = QLabel("🔆 Luz: -- lux")
        self.__combo = QComboBox()

        self.__signal = SeñalBioeléctrica()
        self.__timer = QTimer()
        self.__tiempos = []
        self.__voltajes = []

        self.__sensor_timer = QTimer()
        self.__sensor_timer.timeout.connect(self.__actualizar_labels_sensores)

        d = os.path.dirname(__file__)
        self.__movie = QMovie(os.path.join(d, "../img/plant.gif"))

        # Línea optimizada
        self.__linea, = self.__ax.plot([], [], color="#6BA568", linewidth=1)

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

        toolbar = QFrame()
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setSpacing(10)
        self.__left_layout.addWidget(toolbar)

        self.__canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.__left_layout.addWidget(self.__canvas, 1)

        self.__ax.set_title("Señal Bioeléctrica en tiempo real (200 Hz)")
        self.__ax.set_xlabel("Tiempo (s)")
        self.__ax.set_ylabel("Voltaje estimado (mV)")
        self.__ax.set_ylim(-500, 500)
        self.__ax.set_xlim(0, 10)

        self.__main_layout.addWidget(self.__left_frame, 3)

        self.__right_layout.setContentsMargins(15, 15, 15, 15)
        self.__right_layout.setSpacing(10)

        info = QVBoxLayout()
        for label in [self.__climate_label, self.__soil_label, self.__humid_label, self.__light_label]:
            label.setFont(fonts.TITLE)
            info.addWidget(label)
        self.__right_layout.addLayout(info)

        gif = QLabel(alignment=Qt.AlignmentFlag.AlignCenter)
        gif.setMovie(self.__movie)
        self.__movie.setSpeed(50)
        self.__movie.start()
        self.__right_layout.addWidget(gif, 3)

        ctr = QHBoxLayout()
        self.__combo.addItems(["C", "D", "E", "F", "G", "A", "B"])
        rec = IconButton("img/record.webp", "")
        rec.setFixedSize(50, 50)
        ctr.addWidget(self.__combo)
        ctr.addWidget(rec)
        self.__right_layout.addLayout(ctr)

        self.__main_layout.addWidget(self.__right_frame, 1)
        self.setLayout(self.__main_layout)

        self.__iniciar_actualizacion()

    def __iniciar_actualizacion(self):
        self.__timer.timeout.connect(self.__actualizar_grafica)
        self.__timer.start(5)  # ← ahora cada 5 ms (200 Hz)
        self.__sensor_timer.start(3000)

    def __actualizar_grafica(self):
        nuevos_tiempos = []
        nuevos_voltajes = []

        # Recolectar todos los nuevos datos disponibles
        while True:
            tiempo, voltaje = self.__signal.siguiente_valor()
            if tiempo is None:
                break
            nuevos_tiempos.append(tiempo)
            nuevos_voltajes.append(voltaje)

        # Si no hay nuevos datos, salir
        if not nuevos_tiempos:
            return

        self.__tiempos.extend(nuevos_tiempos)
        self.__voltajes.extend(nuevos_voltajes)

        # Ventana deslizante de 10 segundos
        ventana = 10.0
        corte = self.__tiempos[-1] - ventana
        while self.__tiempos and self.__tiempos[0] < corte:
            self.__tiempos.pop(0)
            self.__voltajes.pop(0)

        # Actualizar datos de la línea
        self.__linea.set_data(self.__tiempos, self.__voltajes)
        self.__ax.set_xlim(max(0, corte), self.__tiempos[-1])
        self.__canvas.draw_idle()  # ← más rápido que draw()

    def __actualizar_labels_sensores(self):
        temp, hum, soil, light = self.__signal.obtener_datos_sensores()
        print("DEBUG:", temp, hum, soil, light)

        self.__climate_label.setText(f"\U0001F321️ Temp: {temp} °C")
        self.__soil_label.setText(f"💧 H.suelo: {soil}")
        self.__humid_label.setText(f"💦 H.rel: {hum}")
        self.__light_label.setText(f"🔆 Luz: {light} lux")

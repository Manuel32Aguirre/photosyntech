from datetime import datetime
from typing import override
import requests
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QMovie
from PyQt6.QtWidgets import QHBoxLayout, QFrame, QVBoxLayout, QSizePolicy, QLabel, QComboBox
import matplotlib.pyplot as plt
from photosyntech.ui.IconButton import IconButton
from photosyntech.ui.fonts import fonts
from photosyntech.ui.modules.Module import Module
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.dates as mdates

FIREBASE_PLANTA_URL = "https://photosyntech-10464-default-rtdb.firebaseio.com/planta.json"


class MainModule(Module):

    def __init__(self):
        super().__init__()
        self.__timer = QTimer(self)
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
        self.__movie = QMovie("./ui/img/plant.gif")
        self.__combo = QComboBox()
        self.__times = []
        self.__temps = []
        self.setStyleSheet("""
            #rightPanel{background:#0f0f1f;}
            QFrame{background:#1a1a2e;}
            QToolButton{border:none;}
            QLabel{color:#e0e0e0;}
            QComboBox{background:#1a1a2e;color:#e0e0e0;
                      border:1px solid #3b3b5e;border-radius:4px;}
        """)

    def __load_saved_data(self):
        try:
            with open("temperatura_log.txt", "r") as f:
                for line in f:
                    parts = line.strip().split(", ")
                    # if len(parts) == 2:
                    timestamp = datetime.strptime(parts[0], "%Y-%m-%d %H:%M:%S")
                    temp = float(parts[1])
                    self.__times.append(timestamp)
                    self.__temps.append(temp)
        except FileNotFoundError:
            pass

    @override
    def draw(self):
        self.__load_saved_data()
        self.__start_data_timer()
        self.__main_layout.setContentsMargins(0, 0, 0, 0)
        self.__main_layout.setSpacing(0)
        self.__left_layout.setContentsMargins(10, 10, 10, 10)
        self.__left_layout.setSpacing(10)
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
        self.__left_layout.addWidget(toolbar)
        self.__canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.__left_layout.addWidget(self.__canvas, 1)
        if self.__times and self.__temps:
            self.__update_graph()

        self.__main_layout.addWidget(self.__left_frame, 3)

        self.__right_layout.setContentsMargins(15, 15, 15, 15)
        self.__right_layout.setSpacing(10)
        info = QHBoxLayout()
        self.__climate_label.setFont(fonts.TITLE)
        self.__soil_label.setFont(fonts.TITLE)
        self.__humid_label.setFont(fonts.TITLE)

        info.addWidget(self.__climate_label)
        info.addWidget(self.__soil_label)
        info.addWidget(self.__humid_label)
        self.__right_layout.addLayout(info)

        gif = QLabel(alignment=Qt.AlignmentFlag.AlignCenter)
        self.__movie.setSpeed(50)
        gif.setMovie(self.__movie)
        self.__movie.start()
        self.__right_layout.addWidget(gif, 3)
        ctr = QHBoxLayout()
        self.__combo.addItems(["C", "D", "E", "F", "G", "A", "B"])
        self.__combo.currentTextChanged.connect(lambda t: print(f"Tonalidad: {t}"))
        rec = IconButton("icons/record.svg", "")
        rec.setFixedSize(50, 50)
        rec.clicked.connect(lambda: print("Record pressed"))
        ctr.addWidget(self.__combo)
        ctr.addWidget(rec)
        self.__right_layout.addLayout(ctr)

        self.__main_layout.addWidget(self.__right_frame, 1)

        self.setLayout(self.__main_layout)

    def __update_graph(self):
        self.__ax.plot(self.__times, self.__temps, marker="o")
        self.__ax.set_title("Temperatura vs Hora del Día")
        self.__ax.set_xlabel("Hora")
        self.__ax.set_ylabel("°C")
        self.__ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        self.__ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        self.__fig.autofmt_xdate()
        self.__canvas.draw()

    def __start_data_timer(self):
        self.__timer.timeout.connect(self.__fetch_and_update)
        self.__timer.start(5000)

    def __fetch_and_update(self):
        try:
            r = requests.get(FIREBASE_PLANTA_URL, timeout=3)
            if r.status_code == 200:
                data = r.json() or {}
                t = data.get("temperatura")
                hs = data.get("humedad_suelo")
                hr = data.get("humedad")
                if t is not None and hs is not None and hr is not None:
                    self.__climate_label.setText(f"🌡️ Temp: {t} °C")
                    self.__soil_label.setText(f"💧 H.suelo: {hs} %")
                    self.__humid_label.setText(f"💦 H.rel: {hr} %")
                    now = datetime.now()
                    self.__times.append(now)
                    self.__temps.append(t)

                    with open("temperatura_log.txt", "a") as f:
                        f.write(f"{now.strftime('%Y-%m-%d %H:%M:%S')}, {t}\n")

                    self.__update_graph()
        except Exception as e:
            print("Error fetching data:", e)

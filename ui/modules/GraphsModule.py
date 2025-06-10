from typing import override

import matplotlib.pyplot as plt
from PyQt6.QtCore import Qt, QThread
from PyQt6.QtGui import QLinearGradient, QColor, QPainter
from PyQt6.QtWidgets import QGridLayout, QGroupBox, QVBoxLayout, QLabel, QPushButton, QFrame, QProgressBar
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from controller.GetWeather import GetWeather
from controller.SensorWorker import SensorWorker
from controller.WeatherWorker import WeatherWorker
from model.WeatherInfo import WeatherInfo
from ui.fonts.fonts import TITLE, NORMAL
from ui.modules.Module import Module


class GraphsModule(Module):

    def __init__(self, weather: GetWeather):
        super().__init__()
        self.__frame = QFrame()
        self.__frame.setObjectName('mainFrame')
        self.__grid_layout = QGridLayout(self.__frame)
        self.__main_layout = QVBoxLayout()
        self.__main_layout.setContentsMargins(0, 0, 0, 0)
        self.__main_layout.setSpacing(0)
        self.__main_layout.addWidget(self.__frame)

        # Nuevos atributos para manejo de hilos
        self.__sensor_worker = None
        self.__sensor_thread = None
        self.__graph_data = [[] for _ in range(4)]  # Datos para cada gráfica
        self.__lines = []  # Almacenar referencias a las líneas de las gráficas
        self.__backgrounds = []  # Fondos para blitting
        self.__max_points = 50  # Límite de puntos a mostrar
        self.__figs = []
        self.__ax = []
        self.__canvas = []

        self.__city_label = QLabel()
        self.__full_name = QLabel()
        self.__temp_label = QLabel()
        self.__status = QLabel()
        self.__last_update = QLabel()
        self.__update_btn = QPushButton('Actualizar ahora')

        self.__weather = weather
        self.__weather_card = QFrame()

        self.__worker_thread = None
        self.__worker = None

        self.__card = QFrame()
        self.__card.setObjectName('card')
        self.__progress_bar = QProgressBar()
        self.__progress_bar.setFixedWidth(665)
        self.__progress_bar.setRange(0, 0)
        self.__progress_bar.setVisible(True)

        self.setStyleSheet(
            """
            #mainFrame {
                background-color: #1a1a2e;
            }
            QGroupBox {
                border: none;
                margin-top: 1em;
                font: bold 18px 'Arial';
                color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
            }
            QLabel {
                color: white;
                font: bold 18px 'Arial';
            }
            QPushButton {
                border-radius: 15px;
                background-color: #006B40;
                color: white;
                font: bold 18px 'Arial';
            }
            QPushButton:hover {
                background-color: #006B80;
            }
            QPushButton:pressed {
                background-color: #006C20;
            }
            """
        )

    @override
    def draw(self):
        grid_indexes = ((0, 0), (0, 1), (1, 0), (1, 1))
        i = 0
        for title_group, ylabel in (
            ('Temperatura', 'ºC'), ('Humedad Suelo', '%RH'), ('Humedad Ambiente', '%RH'), ('Luminosidad', 'Lux')
        ):
            grap = self.__create_graph(title_group, 'Tiempo', ylabel)
            self.__grid_layout.addWidget(grap, grid_indexes[i][0], grid_indexes[i][1])
            line, = self.__ax[i].plot([], [], 'b-')
            self.__lines.append(line)
            # Preparar para blitting (solo una vez al inicio)
            self.__canvas[i].draw()
            self.__backgrounds.append(self.__canvas[i].copy_from_bbox(self.__ax[i].bbox))
            i += 1
        self.__create_weather_panel()
        self.setLayout(self.__main_layout)
        self.start_sensor_updates(interval=0.5)  # Actualizar cada 500 milisegundos

    def update_graphs(self, sensor_data):
        for i in range(4):
            # Mantener solo los últimos puntos
            if len(self.__graph_data[i]) >= self.__max_points:
                self.__graph_data[i] = self.__graph_data[i][1:]
            self.__graph_data[i].append(sensor_data[i])
            self.__update_line(i)

    def __update_line(self, index):
        self.__canvas[index].restore_region(self.__backgrounds[index])
        x_data = range(len(self.__graph_data[index]))
        self.__lines[index].set_data(x_data, self.__graph_data[index])
        if self.__graph_data[index]:
            min_val = min(self.__graph_data[index])
            max_val = max(self.__graph_data[index])
            margin = (max_val - min_val) * 0.1
            self.__ax[index].set_ylim(min_val - margin, max_val + margin)

        # Dibujar solo la línea nueva
        self.__ax[index].draw_artist(self.__lines[index])
        # Actualizar solo el área modificada
        self.__canvas[index].blit(self.__ax[index].bbox)
        # Forzar actualización en cola de eventos
        self.__canvas[index].flush_events()

    def start_sensor_updates(self, interval=5):
        self.stop_sensor_updates()
        self.__sensor_thread = QThread()
        self.__sensor_worker = SensorWorker(interval)
        self.__sensor_worker.moveToThread(self.__sensor_thread)
        self.__sensor_worker.data_ready.connect(self.update_graphs)
        self.__sensor_thread.started.connect(self.__sensor_worker.run)
        self.__sensor_thread.finished.connect(self.__sensor_thread.deleteLater)
        self.__graph_data = [[] for _ in range(4)]  # Inicializar datos
        self.__sensor_thread.start()

    def stop_sensor_updates(self):
        if self.__sensor_worker:
            self.__sensor_worker.stop()
        if self.__sensor_thread:
            self.__sensor_thread.quit()
            self.__sensor_thread.wait()
        self.__sensor_worker = None
        self.__sensor_thread = None

    def __create_graph(self, title_group, xlabel, ylabel):
        group = QGroupBox(title_group)
        group_layout = QVBoxLayout(group)
        fig, ax = plt.subplots()
        self.__figs.append(fig)
        self.__ax.append(ax)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_xlim(0, self.__max_points)
        ax.grid(True, linestyle='--', alpha=0.7)
        canvas = FigureCanvas(fig)
        self.__canvas.append(canvas)
        group_layout.addWidget(canvas)
        return group

    def __create_weather_panel(self):
        self.__update_weather()
        self.__grid_layout.addWidget(self.__progress_bar, 0, 2)
        self.__weather_card.setVisible(False)
        self.__weather_card.setObjectName('weatherCard')
        group_layout = QVBoxLayout(self.__weather_card)
        title = QLabel('Clima en tu región')
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(TITLE)
        subtitle = QLabel('Utiliza estos datos como referencia')
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        group_layout.addWidget(title)
        group_layout.addWidget(subtitle)
        self.__card.paintEvent = self.__paint_gradient
        grid_card = QGridLayout(self.__card)
        group_layout.addWidget(self.__card, stretch=2)
        self.__city_label.setFont(TITLE)
        self.__city_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid_card.addWidget(self.__city_label, 0, 0)
        self.__full_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid_card.addWidget(self.__full_name, 1, 0)
        self.__temp_label.setFont(NORMAL)
        self.__temp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid_card.addWidget(self.__temp_label, 2, 0)
        update_info = QLabel('El clima se actualizará en 01:00')
        update_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid_card.addWidget(update_info, 3, 0)
        self.__status.setFont(NORMAL)
        self.__status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid_card.addWidget(self.__status, 0, 1)
        self.__last_update.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid_card.addWidget(self.__last_update, 1, 1, 2, 1)
        self.__update_btn.setFixedHeight(40)
        self.__update_btn.clicked.connect(self.__update_weather)
        grid_card.addWidget(self.__update_btn, 3, 1)
        self.__grid_layout.addWidget(self.__weather_card, 0, 2)
        self.__worker_thread.start()

    def __paint_gradient(self, _):
        painter = QPainter(self.__card)
        painter.begin(self)
        gradient = QLinearGradient(0, 0, self.__card.width(), self.__card.height())
        gradient.setColorAt(0.0, QColor(12, 255, 150, 51))
        gradient.setColorAt(1.0, QColor(98, 148, 255, 51))
        painter.setBrush(gradient)
        painter.drawRoundedRect(self.__card.rect(), 25.0, 25.0)
        painter.end()

    def __complete_thread(self):
        self.__update_btn.setEnabled(True)
        self.__progress_bar.setVisible(False)
        self.__weather_card.setVisible(True)
        self.__worker_thread = None
        self.__worker = None

    def __update_wheater_labels(self, w: WeatherInfo):
        self.__city_label.setText(w.city)
        self.__full_name.setText(w.region)
        self.__temp_label.setText(f'{w.temperature}ºC')
        self.__status.setText(w.condition)
        self.__last_update.setText(f'Última actualización: {w.last_updated}')

    def __update_weather(self):
        self.__update_btn.setEnabled(False)
        self.__progress_bar.setVisible(True)
        self.__weather_card.setVisible(False)
        self.__worker_thread = QThread()
        self.__worker = WeatherWorker(weather=self.__weather)
        self.__worker.moveToThread(self.__worker_thread)
        self.__worker_thread.started.connect(self.__worker.run_task)
        self.__worker.finished.connect(self.__worker_thread.quit)
        self.__worker.finished.connect(self.__worker.deleteLater)
        self.__worker_thread.finished.connect(self.__worker_thread.deleteLater)
        self.__worker.result_ready.connect(self.__update_wheater_labels)
        self.__worker_thread.finished.connect(self.__complete_thread)
        self.__worker_thread.start()

    def __str__(self):
        return 'Datos de sensores'

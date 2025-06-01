from typing import override

import matplotlib.pyplot as plt
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QLinearGradient, QColor, QPainter
from PyQt6.QtWidgets import QGridLayout, QGroupBox, QVBoxLayout, QLabel, QPushButton, QWidget, QFrame
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from controller.GetWeather import GetWeather
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
        self.__figs = []
        self.__ax = []
        self.__canvas = []
        self.__weather = weather
        self.__card = QFrame()
        self.__card.setObjectName('card')
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
        grid_indexes = ((0, 0), (0, 1), (1, 0))
        i = 0
        for title_group, ylabel in (('Temperatura', 'ºC'), ('Humedad', 'pH'), ('Luminosidad', 'Lux')):
            grap = GraphsModule.__create_grahp(
                self.__figs, self.__ax, self.__canvas, title_group, 'Tiempo', ylabel
            )
            self.__grid_layout.addWidget(grap, grid_indexes[i][0], grid_indexes[i][1])
            i = i + 1
        self.__create_weather_panel()
        self.setLayout(self.__main_layout)

    @staticmethod
    def __create_grahp(lfig, lax, lcanvas, title_group, xlabel, ylabel) -> QWidget:
        group = QGroupBox(title_group)
        group_layout = QVBoxLayout(group)
        fig, ax = plt.subplots()
        lfig.append(fig)
        lax.append(ax)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        canvas = FigureCanvas(fig)
        lcanvas.append(canvas)
        group_layout.addWidget(canvas)
        return group

    def __create_weather_panel(self):
        self.__weather_card = QFrame()
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
        info = self.__weather.get_weather()
        city_label = QLabel(info.city)
        city_label.setFont(TITLE)
        city_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid_card.addWidget(city_label, 0, 0)
        full_name = QLabel(info.region)
        full_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid_card.addWidget(full_name, 1, 0)
        temp_label = QLabel(f'{info.temperature}ºC')
        temp_label.setFont(NORMAL)
        temp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid_card.addWidget(temp_label, 2, 0)
        update_info = QLabel('El clima se actualizará en 01:00')
        update_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid_card.addWidget(update_info, 3, 0)
        status = QLabel(info.condition)
        status.setFont(NORMAL)
        status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid_card.addWidget(status, 0, 1)
        last_update = QLabel(f'Última actualización: {info.last_updated}')
        last_update.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid_card.addWidget(last_update, 1, 1, 2, 1)
        update_btn = QPushButton('Actualizar ahora')
        update_btn.setFixedHeight(40)
        grid_card.addWidget(update_btn, 3, 1)
        self.__grid_layout.addWidget(self.__weather_card, 1, 1)

    def __paint_gradient(self, _):
        painter = QPainter(self.__card)
        painter.begin(self)
        gradient = QLinearGradient(0, 0, self.__card.width(), self.__card.height())
        gradient.setColorAt(0.0, QColor(12, 255, 150, 51))
        gradient.setColorAt(1.0, QColor(98, 148, 255, 51))
        painter.setBrush(gradient)
        painter.drawRoundedRect(self.__card.rect(), 25.0, 25.0)
        painter.end()

from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QGridLayout, QFrame
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import random

from ui.modules.Module import Module

class GraphsModule(Module):
    def draw(self):
        layout = QGridLayout()

        # Crear gráficos
        graph1 = self.create_graph("Temperatura", "Grados Centígrados °C", "red")
        graph2 = self.create_graph("Humedad", "%RH", "blue")
        graph3 = self.create_graph("Luminosidad", "Lux", "gold")

        # Crear clima
        clima_widget = self.create_climate_box()

        # Agregar en matriz
        layout.addWidget(graph1, 0, 0)
        layout.addWidget(graph2, 0, 1)
        layout.addWidget(graph3, 1, 0)
        layout.addWidget(clima_widget, 1, 1)

        self.setLayout(layout)

    def create_graph(self, title, ylabel, color):
        fig = Figure(figsize=(4, 3))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        x = list(range(10))
        y = [random.uniform(10, 30) for _ in range(10)]
        ax.plot(x, y, color=color)
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.set_xlabel("Tiempo")
        fig.tight_layout()
        return canvas

    def create_climate_box(self):
        climate_box = QVBoxLayout()
        label_title = QLabel("Clima en tu región")
        label_title.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        climate_box.addWidget(label_title)

        label_sub = QLabel("Utiliza estos datos como referencia")
        label_sub.setStyleSheet("color: white;")
        climate_box.addWidget(label_sub)

        label_info = QLabel("CDMX\nCiudad de México\n\n☁️  15°C\nNublado\nÚltima actualización:\n2021-02-21 08:30")
        label_info.setStyleSheet("color: white; font-size: 16px;")
        climate_box.addWidget(label_info)

        actualizar = QPushButton("Actualizar ahora")
        actualizar.setStyleSheet("background-color: #1db954; color: white; padding: 6px;")
        climate_box.addWidget(actualizar)

        frame = QFrame()
        frame.setStyleSheet("background-color: #1a1d2e; border-radius: 15px; padding: 15px;")
        frame.setLayout(climate_box)
        return frame

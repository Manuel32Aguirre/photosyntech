import sys

from PyQt6.QtWidgets import QApplication

from ui.MainWindow import MainWindow
from ui.fonts import fonts

if __name__ == "__main__":
    app = QApplication(sys.argv)
    #fonts.setup_fonts()
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

"""
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QSpinBox, QRadioButton, QButtonGroup, QCheckBox, QComboBox, QLineEdit,
    QPushButton, QLabel, QFileDialog
)
from PyQt6.QtCore import Qt

class ConfigWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Configuración del Sistema")
        self.setGeometry(100, 100, 700, 500)

        # Layout principal
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Primera fila: Sensores y Clima uno al lado del otro
        first_row = QHBoxLayout()

        # Sección de muestreo de sensores
        sensor_group = QGroupBox("Tomar una muestra de los sensores cada:")
        sensor_layout = QVBoxLayout()

        # Valor numérico
        value_layout = QHBoxLayout()
        value_layout.addWidget(QLabel("Valor:"))
        self.sensor_value = QSpinBox()
        self.sensor_value.setRange(1, 1000)
        value_layout.addWidget(self.sensor_value)
        sensor_layout.addLayout(value_layout)

        # Unidades (radio buttons)
        self.sensor_unit_group = QButtonGroup(self)
        self.sensor_seconds = QRadioButton("Segundos")
        self.sensor_minutes = QRadioButton("Minutos")
        self.sensor_hours = QRadioButton("Horas")

        self.sensor_unit_group.addButton(self.sensor_seconds)
        self.sensor_unit_group.addButton(self.sensor_minutes)
        self.sensor_unit_group.addButton(self.sensor_hours)

        sensor_layout.addWidget(self.sensor_seconds)
        sensor_layout.addWidget(self.sensor_minutes)
        sensor_layout.addWidget(self.sensor_hours)
        self.sensor_seconds.setChecked(True)  # Valor por defecto

        sensor_group.setLayout(sensor_layout)
        first_row.addWidget(sensor_group)

        # Sección de muestreo de clima
        weather_group = QGroupBox("Tomar una muestra del clima cada:")
        weather_layout = QVBoxLayout()

        # Valor numérico
        value_layout = QHBoxLayout()
        value_layout.addWidget(QLabel("Valor:"))
        self.weather_value = QSpinBox()
        self.weather_value.setRange(1, 1000)
        value_layout.addWidget(self.weather_value)
        weather_layout.addLayout(value_layout)

        # Unidades (radio buttons)
        self.weather_unit_group = QButtonGroup(self)
        self.weather_seconds = QRadioButton("Segundos")
        self.weather_minutes = QRadioButton("Minutos")
        self.weather_hours = QRadioButton("Horas")

        self.weather_unit_group.addButton(self.weather_seconds)
        self.weather_unit_group.addButton(self.weather_minutes)
        self.weather_unit_group.addButton(self.weather_hours)

        weather_layout.addWidget(self.weather_seconds)
        weather_layout.addWidget(self.weather_minutes)
        weather_layout.addWidget(self.weather_hours)
        self.weather_seconds.setChecked(True)  # Valor por defecto

        weather_group.setLayout(weather_layout)
        first_row.addWidget(weather_group)

        main_layout.addLayout(first_row)

        # Notificaciones de lecturas peligrosas (ocupa todo el ancho)
        self.danger_check = QCheckBox("Notificarme lecturas peligrosas")
        main_layout.addWidget(self.danger_check, alignment=Qt.AlignmentFlag.AlignLeft)

        # Tercera fila: Formatos y Ruta uno al lado del otro
        third_row = QHBoxLayout()

        # Formato de exportación
        format_group = QGroupBox("Exportar melodías generadas en formato:")
        format_layout = QVBoxLayout()

        self.format_combo = QComboBox()
        self.format_combo.addItems(["MP3", "OGG", "M4A"])
        format_layout.addWidget(self.format_combo)

        format_group.setLayout(format_layout)
        third_row.addWidget(format_group)

        # Ruta de almacenamiento
        path_group = QGroupBox("Ruta de almacenamiento de melodías:")
        path_layout = QVBoxLayout()

        self.path_edit = QLineEdit("C:/Users/ciego/photosyntech/melodias")
        path_layout.addWidget(self.path_edit)

        browse_btn = QPushButton("Seleccionar carpeta...")
        browse_btn.clicked.connect(self.browse_folder)
        path_layout.addWidget(browse_btn)

        path_group.setLayout(path_layout)
        third_row.addWidget(path_group)

        main_layout.addLayout(third_row)

        # Ajustar proporciones
        main_layout.setStretch(0, 1)  # Primera fila
        main_layout.setStretch(1, 0)  # Checkbox
        main_layout.setStretch(2, 1)  # Tercera fila

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar carpeta de almacenamiento",
            self.path_edit.text()
        )
        if folder:
            self.path_edit.setText(folder)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ConfigWindow()
    window.show()
    sys.exit(app.exec())
"""
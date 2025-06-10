from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QGroupBox,
    QSpinBox, QRadioButton, QButtonGroup, QCheckBox, QComboBox, QLineEdit,
    QPushButton, QLabel, QFileDialog
)

from ui.modules.Module import Module


class SettingsModule(Module):

    def __init__(self):
        super().__init__()
        self.__path_edit = QLineEdit("C:/photosyntech/melodias")
        self.__format_combo = QComboBox()
        self.__danger_check = QCheckBox("Notificarme lecturas peligrosas")
        self.__weather_hours = QRadioButton("Horas")
        self.__weather_minutes = QRadioButton("Minutos")
        self.__weather_seconds = QRadioButton("Segundos")
        self.__weather_unit_group = QButtonGroup(self)
        self.__weather_value = QSpinBox()
        self.__sensor_hours = QRadioButton("Horas")
        self.__sensor_minutes = QRadioButton("Minutos")
        self.__sensor_seconds = QRadioButton("Segundos")
        self.__sensor_unit_group = QButtonGroup(self)
        self.__sensor_value = QSpinBox()

    def draw(self):
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        # Primera fila: Sensores y Clima uno al lado del otro
        first_row = QHBoxLayout()

        # Sección de muestreo de sensores
        sensor_group = QGroupBox("Tomar una muestra de los sensores cada:")
        sensor_layout = QVBoxLayout()

        # Valor numérico
        value_layout = QHBoxLayout()
        value_layout.addWidget(QLabel("Valor:"))
        self.__sensor_value.setRange(1, 1000)
        value_layout.addWidget(self.__sensor_value)
        sensor_layout.addLayout(value_layout)

        self.__sensor_unit_group.addButton(self.__sensor_seconds)
        self.__sensor_unit_group.addButton(self.__sensor_minutes)
        self.__sensor_unit_group.addButton(self.__sensor_hours)

        sensor_layout.addWidget(self.__sensor_seconds)
        sensor_layout.addWidget(self.__sensor_minutes)
        sensor_layout.addWidget(self.__sensor_hours)
        self.__sensor_seconds.setChecked(True)
        sensor_group.setLayout(sensor_layout)
        first_row.addWidget(sensor_group)
        weather_group = QGroupBox("Tomar una muestra del clima cada:")
        weather_layout = QVBoxLayout()
        value_layout = QHBoxLayout()
        value_layout.addWidget(QLabel("Valor:"))
        self.__weather_value.setRange(1, 1000)
        value_layout.addWidget(self.__weather_value)
        weather_layout.addLayout(value_layout)
        self.__weather_unit_group.addButton(self.__weather_seconds)
        self.__weather_unit_group.addButton(self.__weather_minutes)
        self.__weather_unit_group.addButton(self.__weather_hours)
        weather_layout.addWidget(self.__weather_seconds)
        weather_layout.addWidget(self.__weather_minutes)
        weather_layout.addWidget(self.__weather_hours)
        self.__weather_seconds.setChecked(True)
        weather_group.setLayout(weather_layout)
        first_row.addWidget(weather_group)
        main_layout.addLayout(first_row)
        main_layout.addWidget(self.__danger_check, alignment=Qt.AlignmentFlag.AlignLeft)
        third_row = QHBoxLayout()
        format_group = QGroupBox("Exportar melodías generadas en formato:")
        format_layout = QVBoxLayout()
        self.__format_combo.addItems(["MP3", "OGG", "M4A"])
        format_layout.addWidget(self.__format_combo)
        format_group.setLayout(format_layout)
        third_row.addWidget(format_group)
        path_group = QGroupBox("Ruta de almacenamiento de melodías:")
        path_layout = QVBoxLayout()
        path_layout.addWidget(self.__path_edit)
        browse_btn = QPushButton("Seleccionar carpeta...")
        browse_btn.clicked.connect(self.__browse_folder)
        path_layout.addWidget(browse_btn)
        path_group.setLayout(path_layout)
        third_row.addWidget(path_group)
        main_layout.addLayout(third_row)
        main_layout.setStretch(0, 1)  # Primera fila
        main_layout.setStretch(1, 0)  # Checkbox
        main_layout.setStretch(2, 1)  # Tercera fila

        self.setLayout(main_layout)

    def __browse_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar carpeta de almacenamiento",
            self.__path_edit.text()
        )
        if folder:
            self.__path_edit.setText(folder)

    def __str__(self):
        return 'Configuración'

from PyQt6.QtWidgets import (
    QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QRadioButton,
    QCheckBox, QComboBox, QPushButton, QFileDialog,
    QButtonGroup
)
from PyQt6.QtCore import Qt
from ui.modules.Module import Module
from ui.modules.MainModule import MainModule
from ui.modules.GraphsModule import GraphsModule
from ui.modules.ReportModules import ReportModule


# ------------ Módulo 3: Configuración ------------
class ConfigModule(Module):
    def draw(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Muestreo sensores
        layout.addLayout(self.create_sample_section("Tomar una muestra de los sensores cada:"))

        # Muestreo clima
        layout.addLayout(self.create_sample_section("Tomar una muestra del clima:"))

        # Checkbox + tooltip
        notif_layout = QHBoxLayout()
        checkbox = QCheckBox("Notificarme lecturas peligrosas")
        checkbox.setChecked(True)

        tooltip_icon = QLabel("🔍")
        tooltip_icon.setToolTip("Una lectura riesgosa se considera arriba de 25°C")
        notif_layout.addWidget(checkbox)
        notif_layout.addWidget(tooltip_icon)
        layout.addLayout(notif_layout)

        # Exportar melodías
        format_layout = QVBoxLayout()
        format_layout.addWidget(QLabel("Exportar melodías generadas en formato:"))
        combo = QComboBox()
        combo.addItems(["MP3", "OGG", "M4A"])
        format_layout.addWidget(combo)
        layout.addLayout(format_layout)

        # Ruta de almacenamiento
        path_layout = QVBoxLayout()
        path_layout.addWidget(QLabel("Ruta de almacenamiento de melodías:"))

        path_box = QHBoxLayout()
        folder_icon = QLabel("📁")
        path_display = QLineEdit("C:/Users/diego/photosyntech/melodias")
        path_display.setReadOnly(True)
        browse_btn = QPushButton("Examinar")

        def open_folder():
            folder = QFileDialog.getExistingDirectory()
            if folder:
                path_display.setText(folder)

        browse_btn.clicked.connect(open_folder)

        path_box.addWidget(folder_icon)
        path_box.addWidget(path_display)
        path_box.addWidget(browse_btn)

        path_layout.addLayout(path_box)
        layout.addLayout(path_layout)

        self.setLayout(layout)

    def create_sample_section(self, label_text):
        section_layout = QVBoxLayout()
        section_layout.addWidget(QLabel(label_text))
        row = QHBoxLayout()
        value_input = QLineEdit()
        value_input.setFixedWidth(60)
        row.addWidget(QLabel("Valor"))
        row.addWidget(value_input)

        radios = QVBoxLayout()
        units = ["Segundos", "Minutos", "Horas"]
        group = QButtonGroup(self)
        for unit in units:
            btn = QRadioButton(unit)
            if unit == "Segundos":
                btn.setChecked(True)
            group.addButton(btn)
            radios.addWidget(btn)
        row.addLayout(radios)
        section_layout.addLayout(row)
        return section_layout


# ------------ Módulo 5: Señales de planta ------------
class PlantSignalModule(Module):
    def draw(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Contenido de Señales de planta"))
        self.setLayout(layout)

# ------------ Lista de módulos ------------
def get_all_modules() -> list[Module]:
    return [
        MainModule(),
        GraphsModule(),
        ConfigModule(),
        ReportModule(),    
        PlantSignalModule()
    ]
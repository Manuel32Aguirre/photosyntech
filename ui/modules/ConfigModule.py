from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QRadioButton,
    QCheckBox, QComboBox, QPushButton, QFileDialog, QFrame, QButtonGroup, QToolTip, QGridLayout
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from ui.modules.Module import Module


class ConfigModule(Module):
    def draw(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #1B1731;
                color: white;
                font-family: Arial;
            }
            QRadioButton, QCheckBox {
                color: #00C97C;
            }
            QLineEdit {
                border: 1px solid #00C97C;
                background-color: #1B1731;
                color: white;
                padding: 6px;
            }
            QComboBox {
                background-color: #e6f2ee;
                color: black;
                padding: 6px;
            }
        """)

        main_layout = QVBoxLayout()
        grid = QGridLayout()
        grid.setHorizontalSpacing(60)
        grid.setVerticalSpacing(30)

        # FILA 1: Dos secciones de muestras
        grid.addLayout(self.create_sample_section("Tomar una muestra de los sensores cada:"), 0, 0)
        grid.addLayout(self.create_sample_section("Tomar una muestra del clima:"), 0, 1)

        # FILA 2: Checkbox e info
        notif_layout = QHBoxLayout()
        checkbox = QCheckBox("Notificarme lecturas peligrosas")
        checkbox.setChecked(True)
        tooltip_icon = QLabel("🛈")
        tooltip_icon.setToolTip("Una lectura riesgosa se considera arriba de 25°C")
        tooltip_icon.setStyleSheet("color: white; font-size: 18px; margin-left: 5px;")
        notif_layout.addWidget(checkbox)
        notif_layout.addWidget(tooltip_icon)
        notif_layout.addStretch()
        grid.addLayout(notif_layout, 1, 0)

        # FILA 3: Formato
        format_layout = QVBoxLayout()
        format_label = QLabel("Exportar melodías\ngeneradas en formato:")
        format_label.setFont(QFont("Arial", 12))
        format_layout.addWidget(format_label)
        combo = QComboBox()
        combo.addItems(["MP3", "OGG", "M4A"])
        combo.setFixedWidth(280)
        format_layout.addWidget(combo)
        grid.addLayout(format_layout, 2, 0)

        # FILA 3: Ruta y botón
        path_container = QVBoxLayout()
        path_container.addWidget(QLabel("Ruta de almacenamiento de melodías:"))

        path_row = QHBoxLayout()
        folder_icon = QLabel("📁")
        folder_icon.setStyleSheet("font-size: 24px; color: yellow; margin-right: 6px;")
        path_display = QLineEdit("C:/Users/diego/photosyntech/melodias")
        path_display.setReadOnly(True)
        path_display.setStyleSheet("background-color: #79a88e; color: white; padding: 6px;")

        path_row.addWidget(folder_icon)
        path_row.addWidget(path_display)
        path_container.addLayout(path_row)

        browse_btn = QPushButton("Examinar")
        browse_btn.setStyleSheet("background-color: #00804B; color: white; padding: 10px; font-weight: bold;")
        browse_btn.setFixedWidth(180)

        def open_folder():
            folder = QFileDialog.getExistingDirectory()
            if folder:
                path_display.setText(folder)

        browse_btn.clicked.connect(open_folder)
        path_container.addWidget(browse_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        grid.addLayout(path_container, 2, 1)

        main_layout.addLayout(grid)
        self.setLayout(main_layout)

    def create_sample_section(self, label_text):
        section = QVBoxLayout()
        label = QLabel(label_text)
        label.setFont(QFont("Arial", 12))
        section.addWidget(label)

        row = QHBoxLayout()
        value_label = QLabel("Valor")
        value_label.setFont(QFont("Arial", 11))
        value_input = QLineEdit()
        value_input.setFixedWidth(80)
        row.addWidget(value_label)
        row.addWidget(value_input)

        radios = QVBoxLayout()
        group = QButtonGroup(self)
        for unit in ["Segundos", "Minutos", "Horas"]:
            btn = QRadioButton(unit)
            if unit == "Segundos":
                btn.setChecked(True)
            group.addButton(btn)
            radios.addWidget(btn)

        row.addLayout(radios)
        section.addLayout(row)
        return section

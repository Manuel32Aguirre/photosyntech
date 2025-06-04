from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from ui.modules.Module import Module

class ReportModule(Module):
    def draw(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        # Título
        title = QLabel('Visualizar reportes de la planta “Nombre de la planta”:')
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        layout.addWidget(title)

        # Subtítulo
        subtitle = QLabel("Seleccione el período del reporte que desea consultar:")
        subtitle.setStyleSheet("font-size: 14px; color: white;")
        layout.addWidget(subtitle)

        # ComboBox
        combo = QComboBox()
        combo.addItems(["Mes 1", "Mes 2", "Mes 3", "Mes n"])
        combo.setFixedWidth(220)
        combo.setStyleSheet("background-color: #cdd5cf; color: black;")
        layout.addWidget(combo)

        # Imagen del reporte 
        image = QLabel()
        pixmap = QPixmap("ui/img/report_icon.png")
        if pixmap.isNull():
            image.setText("🧾")
            image.setStyleSheet("font-size: 100px; margin-top: 20px;")
        else:
            image.setPixmap(pixmap.scaledToWidth(200))
        image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(image)

        # Botones de acción
        btn_layout = QHBoxLayout()
        share_btn = QPushButton("🔗")
        share_btn.setStyleSheet("background-color: #2ecc71; font-size: 20px; padding: 8px;")
        share_btn.setFixedSize(50, 50)

        download_btn = QPushButton("⬇️")
        download_btn.setStyleSheet("background-color: #2ecc71; font-size: 20px; padding: 8px;")
        download_btn.setFixedSize(50, 50)

        btn_layout.addWidget(share_btn)
        btn_layout.addWidget(download_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

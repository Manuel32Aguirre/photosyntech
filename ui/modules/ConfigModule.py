from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QRadioButton,
    QCheckBox, QComboBox, QPushButton, QFileDialog, QButtonGroup,
    QMessageBox, QSizePolicy, QGroupBox
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
            QGroupBox {
                border: 2px solid #00C97C;
                border-radius: 5px;
                margin-top: 10px;
            }
            QGroupBox:title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 10px;
                color: #00C97C;
                font-weight: bold;
            }
            QLineEdit {
                background-color: #262143;
                border: 1px solid #00C97C;
                padding: 6px;
                color: white;
            }
            QComboBox {
                background-color: #e6f2ee;
                color: black;
                padding: 6px;
            }
            QPushButton {
                padding: 10px;
                font-weight: bold;
            }
        """)

        self.setMinimumHeight(800)
        main_layout = QHBoxLayout()

        # === PANEL IZQUIERDO ===
        panel_izquierdo = QVBoxLayout()

        # Perfil
        perfil_group = QGroupBox("Perfil")
        perfil_layout = QVBoxLayout()
        self.perfil_label = QLabel("Perfil cargado: Ninguno")
        self.perfil_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        perfil_layout.addWidget(self.perfil_label)

        cargar_btn = QPushButton("📂 Cargar perfil de planta")
        cargar_btn.setStyleSheet("background-color: #663399; color: white;")
        cargar_btn.setFixedWidth(250)
        perfil_layout.addWidget(cargar_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        perfil_group.setLayout(perfil_layout)
        panel_izquierdo.addWidget(perfil_group)

        # Muestreo
        muestreo_group = QGroupBox("Muestreo")
        muestreo_layout = QVBoxLayout()
        muestreo_layout.addLayout(self.create_sample_section("Sensores internos"))
        muestreo_layout.addLayout(self.create_sample_section("Clima ambiental"))
        muestreo_group.setLayout(muestreo_layout)
        panel_izquierdo.addWidget(muestreo_group)

        # Alertas
        alertas_group = QGroupBox("Alertas")
        alertas_layout = QHBoxLayout()
        alerta_checkbox = QCheckBox("Activar notificaciones")
        alerta_checkbox.setChecked(True)
        iconito = QLabel("⚠️")
        iconito.setToolTip("Lecturas peligrosas mayores a 25°C")
        alertas_layout.addWidget(alerta_checkbox)
        alertas_layout.addWidget(iconito)
        alertas_group.setLayout(alertas_layout)
        panel_izquierdo.addWidget(alertas_group)

        panel_izquierdo.addStretch()

        # === PANEL DERECHO ===
        panel_derecho = QVBoxLayout()

        # Exportación
        export_group = QGroupBox("Exportar melodías")
        export_layout = QVBoxLayout()
        format_label = QLabel("Formato de archivo:")
        combo = QComboBox()
        combo.addItems(["MP3", "OGG", "M4A"])
        combo.setFixedWidth(200)
        export_layout.addWidget(format_label)
        export_layout.addWidget(combo)
        export_group.setLayout(export_layout)
        panel_derecho.addWidget(export_group)

        # Ruta
        ruta_group = QGroupBox("Ruta de almacenamiento")
        ruta_layout = QVBoxLayout()
        ruta_layout.addWidget(QLabel("Carpeta destino:"))
        path_row = QHBoxLayout()
        folder_icon = QLabel("📁")
        folder_icon.setStyleSheet("font-size: 24px; margin-right: 6px;")
        self.path_display = QLineEdit("C:/Users/diego/photosyntech/melodias")
        self.path_display.setReadOnly(True)
        self.path_display.setStyleSheet("background-color: #79a88e; color: white;")
        path_row.addWidget(folder_icon)
        path_row.addWidget(self.path_display)
        ruta_layout.addLayout(path_row)

        browse_btn = QPushButton("Seleccionar carpeta")
        browse_btn.setStyleSheet("background-color: #00804B; color: white;")
        browse_btn.setFixedWidth(180)
        ruta_layout.addWidget(browse_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        ruta_group.setLayout(ruta_layout)
        panel_derecho.addWidget(ruta_group)

        panel_derecho.addStretch()

        # === Eventos ===
        def cargar_perfil():
            perfil_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo de perfil", "", "Text Files (*.txt)")
            if perfil_path:
                try:
                    with open(perfil_path, "r", encoding="utf-8") as f:
                        lineas = [line.strip() for line in f if line.strip() and not line.startswith("#")]

                    datos = {}
                    for linea in lineas:
                        if "=" in linea:
                            clave, valor = linea.split("=", 1)
                            datos[clave.strip()] = valor.strip()

                    # Validar claves necesarias
                    claves_necesarias = [
                        "nombre", "nombre_cientifico", "descripcion",
                        "humedad_suelo_min", "humedad_suelo_max",
                        "humedad_relativa_min", "humedad_relativa_max",
                        "iluminacion_min", "iluminacion_max",
                        "voltaje_min", "voltaje_max"
                    ]
                    faltantes = [clave for clave in claves_necesarias if clave not in datos]
                    if faltantes:
                        raise ValueError("Faltan claves requeridas: " + ", ".join(faltantes))

                    # Validar que los valores numéricos sean válidos
                    for clave in claves_necesarias:
                        if clave.endswith("_min") or clave.endswith("_max"):
                            float(datos[clave])  # lanza excepción si no es numérico

                    # Guardar como Perfil.txt tal como está
                    with open(perfil_path, "r", encoding="utf-8") as f_in, open("Perfil.txt", "w", encoding="utf-8") as f_out:
                        f_out.write(f_in.read())

                    self.perfil_label.setText(f"Perfil cargado: {perfil_path.split('/')[-1]}")
                    QMessageBox.information(self, "Éxito", "✅ Perfil válido cargado y guardado.")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"❌ Error al validar el perfil:\n{e}")


        def open_folder():
            folder = QFileDialog.getExistingDirectory()
            if folder:
                self.path_display.setText(folder)

        cargar_btn.clicked.connect(cargar_perfil)
        browse_btn.clicked.connect(open_folder)

        # === Ensamble final ===
        main_layout.addLayout(panel_izquierdo, 1)
        main_layout.addLayout(panel_derecho, 1)
        self.setLayout(main_layout)

    def create_sample_section(self, label_text):
        section = QVBoxLayout()
        label = QLabel(label_text)
        label.setFont(QFont("Arial", 12))
        section.addWidget(label)

        row = QHBoxLayout()
        value_input = QLineEdit()
        value_input.setFixedWidth(80)
        row.addWidget(QLabel("Valor"))
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

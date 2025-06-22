from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox,
    QPushButton, QFileDialog, QGroupBox, QGridLayout, QMessageBox, QCheckBox
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from ui.modules.Module import Module
import sounddevice as sd
import os

class ConfigModule(Module):
    def __init__(self):
        super().__init__()
        self.opciones_frecuencia = {
            "1 min": 60,
            "10 min": 600,
            "30 min": 1800,
            "60 min": 3600
        }
        self.frecuencias = {
            "temperatura": 60,
            "humedad_relativa": 600,
            "iluminacion": 1800,
            "humedad_suelo": 3600
        }

    def draw(self):
        self.setStyleSheet("""
            QWidget { background-color: #1B1731; color: white; font-family: Arial; }
            QGroupBox { border: 2px solid #00C97C; border-radius: 5px; margin-top: 10px; }
            QGroupBox:title { subcontrol-origin: margin; subcontrol-position: top center; padding: 0 10px; color: #00C97C; font-weight: bold; }
            QLineEdit { background-color: #262143; border: 1px solid #00C97C; padding: 6px; color: white; }
            QComboBox { background-color: #e6f2ee; color: black; padding: 6px; }
            QPushButton { padding: 10px; font-weight: bold; }
        """)

        self.setMinimumHeight(800)
        lytPrincipal = QHBoxLayout()

        # PANEL IZQUIERDO
        lytPanelIzquierdo = QVBoxLayout()

        grpPerfil = QGroupBox("Perfil")
        lytPerfil = QVBoxLayout()
        self.lblPerfil = QLabel("Perfil cargado: Ninguno")
        self.lblPerfil.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btnCargarPerfil = QPushButton("📂 Cargar perfil de planta")
        btnCargarPerfil.setStyleSheet("background-color: #663399; color: white;")
        btnCargarPerfil.setFixedWidth(250)
        lytPerfil.addWidget(self.lblPerfil)
        lytPerfil.addWidget(btnCargarPerfil, alignment=Qt.AlignmentFlag.AlignCenter)
        grpPerfil.setLayout(lytPerfil)
        lytPanelIzquierdo.addWidget(grpPerfil)

        grpFrecuencias = QGroupBox("Frecuencia de Almacenamiento")
        lytFrecuencias = QGridLayout()
        lytFrecuencias.setColumnStretch(0, 2)
        lytFrecuencias.setColumnStretch(1, 3)
        self.controles_frecuencias = {}
        sensores = [
            ("Temperatura", "temperatura"),
            ("Humedad Relativa", "humedad_relativa"),
            ("Iluminación", "iluminacion"),
            ("Humedad de Suelo", "humedad_suelo")
        ]
        for i, (nombre, clave) in enumerate(sensores):
            lbl = QLabel(nombre)
            lbl.setFont(QFont("Arial", 10))
            cmbFrecuencia = QComboBox()
            for opcion in self.opciones_frecuencia.keys():
                cmbFrecuencia.addItem(opcion)
            cmbFrecuencia.setObjectName(f"cmb_{clave}")
            cmbFrecuencia.currentIndexChanged.connect(
                lambda _, c=clave, cmb=cmbFrecuencia: self.__actualizar_frecuencia(c, cmb)
            )
            self.controles_frecuencias[clave] = cmbFrecuencia
            lytFrecuencias.addWidget(lbl, i, 0)
            lytFrecuencias.addWidget(cmbFrecuencia, i, 1)
        grpFrecuencias.setLayout(lytFrecuencias)
        lytPanelIzquierdo.addWidget(grpFrecuencias)

        grpDispositivo = QGroupBox("Dispositivo de Grabación")
        lytDispositivo = QVBoxLayout()
        lblDispositivo = QLabel("Seleccionar dispositivo de entrada:")
        self.cmbDispositivos = QComboBox()
        self.cmbDispositivos.setFixedWidth(300)
        self.cmbDispositivos.setStyleSheet("background-color: #e6f2ee; color: black;")
        self.actualizar_lista_dispositivos()
        self.cmbDispositivos.currentIndexChanged.connect(self.__actualizar_dispositivo_config)
        lytDispositivo.addWidget(lblDispositivo)
        lytDispositivo.addWidget(self.cmbDispositivos)
        grpDispositivo.setLayout(lytDispositivo)
        lytPanelIzquierdo.addWidget(grpDispositivo)

        grpAlertas = QGroupBox("Alertas")
        lytAlertas = QHBoxLayout()
        chkAlertas = QCheckBox("Activar notificaciones")
        chkAlertas.setChecked(True)
        lblIconoAlerta = QLabel("⚠️")
        lblIconoAlerta.setToolTip("Lecturas peligrosas mayores a 25°C")
        lytAlertas.addWidget(chkAlertas)
        lytAlertas.addWidget(lblIconoAlerta)
        grpAlertas.setLayout(lytAlertas)
        lytPanelIzquierdo.addWidget(grpAlertas)
        lytPanelIzquierdo.addStretch()

        # PANEL DERECHO
        lytPanelDerecho = QVBoxLayout()
        grpRuta = QGroupBox("Ruta de almacenamiento")
        lytRuta = QVBoxLayout()
        lblCarpeta = QLabel("Carpeta destino:")
        lytRuta.addWidget(lblCarpeta)

        lytFilaRuta = QHBoxLayout()
        lblIconoCarpeta = QLabel("📁")
        lblIconoCarpeta.setStyleSheet("font-size: 24px; margin-right: 6px;")
        self.txtRuta = QLineEdit("")
        self.txtRuta.setReadOnly(True)
        self.txtRuta.setStyleSheet("background-color: #79a88e; color: white;")
        lytFilaRuta.addWidget(lblIconoCarpeta)
        lytFilaRuta.addWidget(self.txtRuta)
        lytRuta.addLayout(lytFilaRuta)

        btnSeleccionarCarpeta = QPushButton("Seleccionar carpeta")
        btnSeleccionarCarpeta.setStyleSheet("background-color: #00804B; color: white;")
        btnSeleccionarCarpeta.setFixedWidth(180)
        btnSeleccionarCarpeta.clicked.connect(self.__seleccionar_carpeta)
        lytRuta.addWidget(btnSeleccionarCarpeta, alignment=Qt.AlignmentFlag.AlignCenter)
        grpRuta.setLayout(lytRuta)
        lytPanelDerecho.addWidget(grpRuta)
        lytPanelDerecho.addStretch()

        btnCargarPerfil.clicked.connect(self.__cargar_perfil)
        self.cargar_configuraciones()

        lytPrincipal.addLayout(lytPanelIzquierdo, 1)
        lytPrincipal.addLayout(lytPanelDerecho, 1)
        self.setLayout(lytPrincipal)

    def __cargar_perfil(self):
        rutaPerfil, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo de perfil", "", "Text Files (*.txt)")
        if rutaPerfil:
            try:
                with open(rutaPerfil, "r", encoding="utf-8") as f_in, open("Perfil.txt", "w", encoding="utf-8") as f_out:
                    f_out.write(f_in.read())
                self.lblPerfil.setText(f"Perfil cargado: {rutaPerfil.split('/')[-1]}")
                QMessageBox.information(self, "Éxito", "✅ Perfil válido cargado y guardado.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"❌ Error al validar el perfil:\n{e}")

    def __seleccionar_carpeta(self):
        carpeta = QFileDialog.getExistingDirectory()
        if carpeta:
            self.txtRuta.setText(carpeta)
            self.guardar_configuraciones()

    def cargar_configuraciones(self):
        try:
            config = {}
            if os.path.exists("configuracion.txt"):
                with open("configuracion.txt", "r", encoding="utf-8") as f:
                    for linea in f:
                        linea = linea.strip()
                        if linea and "=" in linea:
                            clave, valor = linea.split("=", 1)
                            config[clave.strip().lower()] = valor.strip()

            for clave in self.frecuencias.keys():
                config_key = f"frecuencia{clave}".lower()
                if config_key in config:
                    try:
                        segundos = int(config[config_key])
                        self.frecuencias[clave] = segundos
                        cmb = self.controles_frecuencias[clave]
                        texto_opcion = None
                        for opcion, valor_seg in self.opciones_frecuencia.items():
                            if valor_seg == segundos:
                                texto_opcion = opcion
                                break
                        if texto_opcion:
                            index = cmb.findText(texto_opcion, Qt.MatchFlag.MatchExactly)
                            if index >= 0:
                                cmb.setCurrentIndex(index)
                    except ValueError:
                        pass

            if "dispositivo" in config:
                try:
                    dispositivo_id = int(config["dispositivo"])
                    for i in range(self.cmbDispositivos.count()):
                        if self.cmbDispositivos.itemData(i) == dispositivo_id:
                            self.cmbDispositivos.setCurrentIndex(i)
                            break
                except ValueError:
                    pass

            if "rutaalmacenamiento" in config:
                self.txtRuta.setText(config["rutaalmacenamiento"])

        except Exception as e:
            print(f"Error al cargar configuraciones: {e}")

    def guardar_configuraciones(self):
        try:
            config = {}
            if os.path.exists("configuracion.txt"):
                with open("configuracion.txt", "r", encoding="utf-8") as f:
                    for linea in f:
                        linea = linea.strip()
                        if linea and "=" in linea:
                            clave, valor = linea.split("=", 1)
                            config[clave.strip().lower()] = valor.strip()

            if self.cmbDispositivos.currentIndex() >= 0:
                dispositivo_id = self.cmbDispositivos.currentData()
                config["dispositivo"] = str(dispositivo_id)

            for clave, segundos in self.frecuencias.items():
                config_key = f"frecuencia{clave}".lower()
                config[config_key] = str(segundos)

            config["rutaalmacenamiento"] = self.txtRuta.text()

            with open("configuracion.txt", "w", encoding="utf-8") as f:
                for clave, valor in config.items():
                    f.write(f"{clave}={valor}\n")

            print("✅ Configuraciones guardadas")

        except Exception as e:
            print(f"Error al guardar configuraciones: {e}")
            QMessageBox.critical(self, "Error", f"No se pudo guardar la configuración:\n{str(e)}")

    def __actualizar_frecuencia(self, sensor, combo):
        texto_seleccionado = combo.currentText()
        if texto_seleccionado in self.opciones_frecuencia:
            segundos = self.opciones_frecuencia[texto_seleccionado]
            self.frecuencias[sensor] = segundos
            self.guardar_configuraciones()

    def actualizar_lista_dispositivos(self):
        try:
            dispositivos = sd.query_devices()
            self.cmbDispositivos.clear()
            for i, dispositivo in enumerate(dispositivos):
                if dispositivo['max_input_channels'] > 0:
                    nombre = dispositivo['name']
                    self.cmbDispositivos.addItem(f"{i}: {nombre}", userData=i)
        except Exception as e:
            print(f"Error al obtener dispositivos: {e}")
            QMessageBox.warning(self, "Error", f"No se pudieron obtener los dispositivos de audio: {str(e)}")

    def __actualizar_dispositivo_config(self, index):
        if index >= 0:
            self.guardar_configuraciones()

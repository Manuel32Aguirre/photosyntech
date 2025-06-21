from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QRadioButton,
    QCheckBox, QComboBox, QPushButton, QFileDialog, QButtonGroup,
    QMessageBox, QGroupBox, QGridLayout
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from ui.modules.Module import Module
import sounddevice as sd
import os

class ConfigModule(Module):
    def __init__(self):
        super().__init__()
        # Definir opciones de frecuencia y valores en segundos
        self.opciones_frecuencia = {
            "1 min": 60,
            "10 min": 600,
            "30 min": 1800,
            "60 min": 3600
        }
        
        self.frecuencias = {
            "temperatura": 60,   # 1 min
            "humedad_relativa": 600,  # 10 min
            "iluminacion": 1800,  # 30 min
            "humedad_suelo": 3600  # 60 min
        }

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
        lytPrincipal = QHBoxLayout()

        # === PANEL IZQUIERDO ===
        lytPanelIzquierdo = QVBoxLayout()

        grpPerfil = QGroupBox("Perfil")
        lytPerfil = QVBoxLayout()
        self.lblPerfil = QLabel("Perfil cargado: Ninguno")
        self.lblPerfil.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lytPerfil.addWidget(self.lblPerfil)

        btnCargarPerfil = QPushButton("📂 Cargar perfil de planta")
        btnCargarPerfil.setStyleSheet("background-color: #663399; color: white;")
        btnCargarPerfil.setFixedWidth(250)
        lytPerfil.addWidget(btnCargarPerfil, alignment=Qt.AlignmentFlag.AlignCenter)
        grpPerfil.setLayout(lytPerfil)
        lytPanelIzquierdo.addWidget(grpPerfil)

        # === GRUPO PARA FRECUENCIAS DE MUESTREO ===
        grpFrecuencias = QGroupBox("Frecuencia de Almacenamiento")
        lytFrecuencias = QGridLayout()
        lytFrecuencias.setColumnStretch(0, 2)
        lytFrecuencias.setColumnStretch(1, 3)
        
        # Crear controles para cada sensor
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
            # Agregar opciones predefinidas
            for opcion in self.opciones_frecuencia.keys():
                cmbFrecuencia.addItem(opcion)
            
            cmbFrecuencia.setObjectName(f"cmb_{clave}")
            
            # Conectar señal
            cmbFrecuencia.currentIndexChanged.connect(
                lambda _, c=clave, cmb=cmbFrecuencia: self.__actualizar_frecuencia(c, cmb)
            )
            
            self.controles_frecuencias[clave] = cmbFrecuencia
            
            lytFrecuencias.addWidget(lbl, i, 0)
            lytFrecuencias.addWidget(cmbFrecuencia, i, 1)
        
        grpFrecuencias.setLayout(lytFrecuencias)
        lytPanelIzquierdo.addWidget(grpFrecuencias)
        
        # === GRUPO PARA DISPOSITIVOS DE AUDIO ===
        grpDispositivo = QGroupBox("Dispositivo de Grabación")
        lytDispositivo = QVBoxLayout()
        
        lblDispositivo = QLabel("Seleccionar dispositivo de entrada:")
        lytDispositivo.addWidget(lblDispositivo)
        
        self.cmbDispositivos = QComboBox()
        self.cmbDispositivos.setFixedWidth(300)
        self.cmbDispositivos.setStyleSheet("background-color: #e6f2ee; color: black;")
        
        self.actualizar_lista_dispositivos()
        self.cmbDispositivos.currentIndexChanged.connect(self.__actualizar_dispositivo_config)
        
        lytDispositivo.addWidget(self.cmbDispositivos)
        grpDispositivo.setLayout(lytDispositivo)
        lytPanelIzquierdo.addWidget(grpDispositivo)
        
        # === GRUPO ALERTAS ===
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

        # === PANEL DERECHO ===
        lytPanelDerecho = QVBoxLayout()

        grpExportar = QGroupBox("Exportar melodías")
        lytExportar = QVBoxLayout()
        lblFormato = QLabel("Formato de archivo:")
        cmbFormato = QComboBox()
        cmbFormato.addItems(["MP3", "OGG", "M4A"])
        cmbFormato.setFixedWidth(200)
        lytExportar.addWidget(lblFormato)
        lytExportar.addWidget(cmbFormato)
        grpExportar.setLayout(lytExportar)
        lytPanelDerecho.addWidget(grpExportar)

        grpRuta = QGroupBox("Ruta de almacenamiento")
        lytRuta = QVBoxLayout()
        lblCarpeta = QLabel("Carpeta destino:")
        lytRuta.addWidget(lblCarpeta)

        lytFilaRuta = QHBoxLayout()
        lblIconoCarpeta = QLabel("📁")
        lblIconoCarpeta.setStyleSheet("font-size: 24px; margin-right: 6px;")
        self.txtRuta = QLineEdit("C:/Users/diego/photosyntech/melodias")
        self.txtRuta.setReadOnly(True)
        self.txtRuta.setStyleSheet("background-color: #79a88e; color: white;")
        lytFilaRuta.addWidget(lblIconoCarpeta)
        lytFilaRuta.addWidget(self.txtRuta)
        lytRuta.addLayout(lytFilaRuta)

        btnSeleccionarCarpeta = QPushButton("Seleccionar carpeta")
        btnSeleccionarCarpeta.setStyleSheet("background-color: #00804B; color: white;")
        btnSeleccionarCarpeta.setFixedWidth(180)
        lytRuta.addWidget(btnSeleccionarCarpeta, alignment=Qt.AlignmentFlag.AlignCenter)

        grpRuta.setLayout(lytRuta)
        lytPanelDerecho.addWidget(grpRuta)

        lytPanelDerecho.addStretch()

        # === FUNCIONES ===
        def cargarPerfil():
            rutaPerfil, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo de perfil", "", "Text Files (*.txt)")
            if rutaPerfil:
                try:
                    with open(rutaPerfil, "r", encoding="utf-8") as f:
                        lineas = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
                    datos = {
                        clave.strip(): valor.strip()
                        for linea in lineas if "=" in linea
                        for clave, valor in [linea.split("=", 1)]
                    }

                    claves = [
                        "nombre", "nombre_cientifico", "descripcion",
                        "temperatura_min", "temperatura_max",
                        "humedad_relativa_min", "humedad_relativa_max",
                        "iluminacion_min", "iluminacion_max",
                        "voltaje_min", "voltaje_max"
                    ]
                    faltantes = [c for c in claves if c not in datos]
                    if faltantes:
                        raise ValueError(f"Faltan claves requeridas: {', '.join(faltantes)}")

                    for clave in claves:
                        if clave.endswith("_min") or clave.endswith("_max"):
                            float(datos[clave])

                    with open(rutaPerfil, "r", encoding="utf-8") as f_in, open("Perfil.txt", "w", encoding="utf-8") as f_out:
                        f_out.write(f_in.read())

                    self.lblPerfil.setText(f"Perfil cargado: {rutaPerfil.split('/')[-1]}")
                    QMessageBox.information(self, "Éxito", "✅ Perfil válido cargado y guardado.")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"❌ Error al validar el perfil:\n{e}")

        def seleccionarCarpeta():
            carpeta = QFileDialog.getExistingDirectory()
            if carpeta:
                self.txtRuta.setText(carpeta)

        btnCargarPerfil.clicked.connect(cargarPerfil)
        btnSeleccionarCarpeta.clicked.connect(seleccionarCarpeta)

        # Cargar configuraciones iniciales
        self.cargar_configuraciones()
        
        # Ensamblaje final
        lytPrincipal.addLayout(lytPanelIzquierdo, 1)
        lytPrincipal.addLayout(lytPanelDerecho, 1)
        self.setLayout(lytPrincipal)

    def cargar_configuraciones(self):
        """Carga las configuraciones desde el archivo con formato clave=valor"""
        try:
            config = {}
            if os.path.exists("configuracion.txt"):
                with open("configuracion.txt", "r", encoding="utf-8") as f:
                    for linea in f:
                        linea = linea.strip()
                        if linea and "=" in linea:
                            clave, valor = linea.split("=", 1)
                            # Normalizar clave a minúsculas
                            config[clave.strip().lower()] = valor.strip()
            
            # Cargar frecuencias
            for clave in self.frecuencias.keys():
                # Crear clave en el formato "frecuenciatemperatura"
                config_key = f"frecuencia{clave}".lower()
                
                if config_key in config:
                    try:
                        segundos = int(config[config_key])
                        self.frecuencias[clave] = segundos
                        
                        # Buscar opción correspondiente en el ComboBox
                        cmb = self.controles_frecuencias[clave]
                        
                        # Buscar la opción que coincida con los segundos
                        texto_opcion = None
                        for opcion, valor_seg in self.opciones_frecuencia.items():
                            if valor_seg == segundos:
                                texto_opcion = opcion
                                break
                        
                        # Si no se encuentra, usar valor por defecto (primer elemento)
                        if texto_opcion is None:
                            texto_opcion = list(self.opciones_frecuencia.keys())[0]
                            self.frecuencias[clave] = list(self.opciones_frecuencia.values())[0]
                        
                        # Establecer la opción en el ComboBox
                        index = cmb.findText(texto_opcion, Qt.MatchFlag.MatchExactly)
                        if index >= 0:
                            cmb.setCurrentIndex(index)
                    except ValueError:
                        pass
            
            # Cargar dispositivo
            if "dispositivo" in config:
                try:
                    dispositivo_id = int(config["dispositivo"])
                    for i in range(self.cmbDispositivos.count()):
                        if self.cmbDispositivos.itemData(i) == dispositivo_id:
                            self.cmbDispositivos.setCurrentIndex(i)
                            break
                except ValueError:
                    pass
            
        except Exception as e:
            print(f"Error al cargar configuraciones: {e}")

    def guardar_configuraciones(self):
        """Guarda todas las configuraciones en el archivo con formato clave=valor"""
        try:
            config = {}
            # Si ya existe un archivo, cargamos su contenido para no perder otras configuraciones
            if os.path.exists("configuracion.txt"):
                with open("configuracion.txt", "r", encoding="utf-8") as f:
                    for linea in f:
                        linea = linea.strip()
                        if linea and "=" in linea:
                            clave, valor = linea.split("=", 1)
                            # Conservar todas las configuraciones existentes
                            config[clave.strip().lower()] = valor.strip()
            
            # Actualizamos las configuraciones que manejamos en este módulo
            # Dispositivo
            if self.cmbDispositivos.currentIndex() >= 0:
                dispositivo_id = self.cmbDispositivos.currentData()
                config["dispositivo"] = str(dispositivo_id)
            
            # Frecuencias
            for clave, segundos in self.frecuencias.items():
                config_key = f"frecuencia{clave}".lower()
                config[config_key] = str(segundos)
            
            # Escribimos todo el diccionario de configuraciones al archivo
            with open("configuracion.txt", "w", encoding="utf-8") as f:
                for clave, valor in config.items():
                    f.write(f"{clave}={valor}\n")
                
            print("✅ Configuraciones guardadas")
            
        except Exception as e:
            print(f"Error al guardar configuraciones: {e}")
            QMessageBox.critical(self, "Error", f"No se pudo guardar la configuración:\n{str(e)}")

    def __actualizar_frecuencia(self, sensor, combo):
        """Actualiza la configuración de frecuencia para un sensor"""
        texto_seleccionado = combo.currentText()
        
        if texto_seleccionado in self.opciones_frecuencia:
            segundos = self.opciones_frecuencia[texto_seleccionado]
            self.frecuencias[sensor] = segundos
            self.guardar_configuraciones()
        else:
            # Opción por defecto si no se encuentra
            self.frecuencias[sensor] = list(self.opciones_frecuencia.values())[0]
            combo.setCurrentText(list(self.opciones_frecuencia.keys())[0])

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
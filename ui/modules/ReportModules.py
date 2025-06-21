import datetime
import os
import tempfile

import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QFrame, QSizePolicy, QFileDialog, QMessageBox, QInputDialog, QWidget, QScrollArea
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Image, Paragraph, Spacer

from ui.modules.Module import Module


class ReportModule(Module):
    def __init__(self):
        super().__init__()
        self.directorio_historial = "historialLecturas"
        self.sensores = ["temperatura", "humedad_relativa", "iluminacion", "humedad_suelo"]
        self.nombres_sensores = {
            "temperatura": "Temperatura (°C)",
            "humedad_relativa": "Humedad Relativa (%)",
            "iluminacion": "Iluminación (lux)",
            "humedad_suelo": "Humedad de Suelo (%)"
        }
        self.periodos = {
            "Últimos 7 días": 7,
            "Últimos 15 días": 15,
            "Último mes": 30,
            "Últimos 3 meses": 90,
            "Último año": 365,
            "Todo el historial": 0
        }
        self.planta_nombre = "Nombre de la planta"
        self.figura = None
        self.canvas = None

    def draw(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        layout.setSpacing(15)

        # Título
        title = QLabel(f'Visualizar reportes de la planta "{self.planta_nombre}":')
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        layout.addWidget(title)

        # Controles de selección
        ctr_layout = QHBoxLayout()

        # Selector de sensor
        sensor_layout = QVBoxLayout()
        sensor_label = QLabel("Seleccionar sensor:")
        sensor_label.setStyleSheet("color: white;")
        self.sensor_combo = QComboBox()
        self.sensor_combo.addItems(["Todos los sensores"] + list(self.nombres_sensores.values()))
        self.sensor_combo.setFixedWidth(220)
        self.sensor_combo.setStyleSheet("background-color: #cdd5cf; color: black;")
        sensor_layout.addWidget(sensor_label)
        sensor_layout.addWidget(self.sensor_combo)
        ctr_layout.addLayout(sensor_layout)

        # Selector de período
        periodo_layout = QVBoxLayout()
        periodo_label = QLabel("Seleccionar período:")
        periodo_label.setStyleSheet("color: white;")
        self.periodo_combo = QComboBox()
        self.periodo_combo.addItems(self.periodos.keys())
        self.periodo_combo.setFixedWidth(220)
        self.periodo_combo.setStyleSheet("background-color: #cdd5cf; color: black;")
        periodo_layout.addWidget(periodo_label)
        periodo_layout.addWidget(self.periodo_combo)
        ctr_layout.addLayout(periodo_layout)

        # Botón de generar
        self.btn_generar = QPushButton("Generar Reporte")
        self.btn_generar.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.btn_generar.setFixedWidth(150)
        self.btn_generar.clicked.connect(self.generar_reporte)
        ctr_layout.addWidget(self.btn_generar, alignment=Qt.AlignmentFlag.AlignBottom)

        layout.addLayout(ctr_layout)

        # Área de gráficos
        """
        self.grafico_frame = QFrame()
        self.grafico_frame.setStyleSheet("background-color: white; border-radius: 8px;")
        self.grafico_frame.setMinimumSize(600, 400)
        self.grafico_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        grafico_layout = QVBoxLayout(self.grafico_frame)
        self.figura = Figure(figsize=(6, 4), dpi=100)
        self.canvas = FigureCanvas(self.figura)
        grafico_layout.addWidget(self.canvas)
        
        layout.addWidget(self.grafico_frame)
        """
        self.scroll_area = QScrollArea()  # Guardar como atributo
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("background-color: white; border-radius: 8px;")

        # Contenedor para el área de gráficos
        self.grafico_container = QWidget()
        self.grafico_container_layout = QVBoxLayout(self.grafico_container)
        self.grafico_container_layout.setContentsMargins(0, 0, 0, 0)

        self.grafico_frame = QFrame()
        self.grafico_frame.setMinimumSize(600, 400)
        self.grafico_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        grafico_layout = QVBoxLayout(self.grafico_frame)
        self.figura = Figure(figsize=(6, 4), dpi=100)
        self.canvas = FigureCanvas(self.figura)
        grafico_layout.addWidget(self.canvas)

        # Añadir el gráfico al contenedor
        self.grafico_container_layout.addWidget(self.grafico_frame)

        # Configurar el widget contenedor en el scroll
        self.scroll_area.setWidget(self.grafico_container)

        # Añadir el scroll al layout principal (en lugar del gráfico frame directamente)
        layout.addWidget(self.scroll_area)

        # Botones de acción
        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.share_btn = QPushButton("Compartir Reporte")
        self.share_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
                margin-right: 10px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.share_btn.setFixedWidth(180)
        self.share_btn.clicked.connect(self.compartir_reporte)

        self.download_btn = QPushButton("Descargar Reporte")
        self.download_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.download_btn.setFixedWidth(180)
        self.download_btn.clicked.connect(self.descargar_reporte)

        btn_layout.addWidget(self.share_btn)
        btn_layout.addWidget(self.download_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

        # Cargar nombre de la planta desde el perfil
        self.cargar_nombre_planta()

    def cargar_nombre_planta(self):
        """Carga el nombre de la planta desde el archivo Perfil.txt"""
        try:
            if os.path.exists("Perfil.txt"):
                with open("Perfil.txt", "r", encoding="utf-8") as f:
                    for linea in f:
                        if linea.startswith("nombre="):
                            self.planta_nombre = linea.split("=", 1)[1].strip()
                            break
        except Exception as e:
            print(f"Error al cargar perfil: {e}")

    def cargar_datos_sensor(self, sensor, dias=0):
        """Carga datos de un sensor específico desde el archivo TXT"""
        archivo = os.path.join(self.directorio_historial, f"{sensor}.txt")
        datos = []

        if not os.path.exists(archivo):
            print(f"Archivo no encontrado: {archivo}")
            return datos

        try:
            with open(archivo, "r", encoding="utf-8") as f:
                for linea in f:
                    partes = linea.strip().split(",")
                    if len(partes) >= 2:
                        try:
                            timestamp = datetime.datetime.strptime(partes[0], "%Y-%m-%d %H:%M:%S")
                            valor = float(partes[1])

                            # Filtrar por fecha si es necesario
                            if dias > 0:
                                limite = datetime.datetime.now() - datetime.timedelta(days=dias)
                                if timestamp >= limite:
                                    datos.append((timestamp, valor))
                            else:
                                datos.append((timestamp, valor))
                        except ValueError:
                            continue
        except Exception as e:
            print(f"Error al leer archivo {archivo}: {e}")

        return datos

    def generar_reporte(self):
        """Genera el reporte gráfico según las selecciones"""
        sensor_seleccionado = self.sensor_combo.currentText()
        periodo_seleccionado = self.periodo_combo.currentText()
        dias = self.periodos.get(periodo_seleccionado, 30)

        # Limpiar figura anterior
        self.figura.clear()

        if sensor_seleccionado == "Todos los sensores":
            ax = self.figura.subplots(2, 2)
            self.figura.set_size_inches(10, 8)
            self.figura.subplots_adjust(hspace=0.4, wspace=0.3)

            for i, sensor in enumerate(self.sensores):
                datos = self.cargar_datos_sensor(sensor, dias)
                if not datos:
                    continue

                fechas = [d[0] for d in datos]
                valores = [d[1] for d in datos]

                row = i // 2
                col = i % 2

                # Calcular estadísticas
                media = np.mean(valores)
                maximo = np.max(valores)
                minimo = np.min(valores)

                ax[row, col].plot(fechas, valores, 'o-', markersize=3)
                ax[row, col].set_title(self.nombres_sensores[sensor])
                ax[row, col].set_ylabel("Valor")
                ax[row, col].grid(True, linestyle='--', alpha=0.7)
                ax[row, col].tick_params(axis='x', rotation=45)

                # Añadir estadísticas
                ax[row, col].axhline(media, color='r', linestyle='--', label=f'Media: {media:.2f}')
                ax[row, col].axhline(maximo, color='g', linestyle=':', label=f'Máx: {maximo:.2f}')
                ax[row, col].axhline(minimo, color='b', linestyle=':', label=f'Mín: {minimo:.2f}')
                ax[row, col].legend()

            self.figura.suptitle(f"Reporte de Sensores - {self.planta_nombre}\nPeríodo: {periodo_seleccionado}", fontsize=16)
        else:
            # Buscar el sensor correspondiente al nombre seleccionado
            sensor_key = None
            for key, value in self.nombres_sensores.items():
                if value == sensor_seleccionado:
                    sensor_key = key
                    break

            if sensor_key:
                datos = self.cargar_datos_sensor(sensor_key, dias)
                if not datos:
                    QMessageBox.warning(self, "Sin datos", f"No se encontraron datos para {sensor_seleccionado} en el período seleccionado.")
                    return

                fechas = [d[0] for d in datos]
                valores = [d[1] for d in datos]

                # Calcular estadísticas
                media = np.mean(valores)
                maximo = np.max(valores)
                minimo = np.min(valores)
                desviacion = np.std(valores)

                ax = self.figura.subplots()
                self.figura.set_size_inches(10, 6)

                # Gráfico principal
                ax.plot(fechas, valores, 'o-', markersize=3, label="Valores")
                ax.axhline(media, color='r', linestyle='--', label=f'Media: {media:.2f}')
                ax.axhline(maximo, color='g', linestyle=':', label=f'Máx: {maximo:.2f}')
                ax.axhline(minimo, color='b', linestyle=':', label=f'Mín: {minimo:.2f}')

                # Área de desviación estándar
                ax.fill_between(fechas,
                               [media - desviacion] * len(valores),
                               [media + desviacion] * len(valores),
                               color='gray', alpha=0.2, label='Desviación estándar')

                ax.set_title(f"{sensor_seleccionado} - {self.planta_nombre}\nPeríodo: {periodo_seleccionado}")
                ax.set_ylabel("Valor")
                ax.grid(True, linestyle='--', alpha=0.7)
                ax.legend()
                ax.tick_params(axis='x', rotation=45)

                # Estadísticas en texto
                stats_text = (
                    f"Estadísticas:\n"
                    f"Media: {media:.2f}\n"
                    f"Máximo: {maximo:.2f}\n"
                    f"Mínimo: {minimo:.2f}\n"
                    f"Desviación estándar: {desviacion:.2f}\n"
                    f"Número de muestras: {len(valores)}"
                )
                ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
                        verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        self.canvas.draw()
        # 1. Actualizar geometría del canvas
        self.canvas.updateGeometry()

        # 2. Ajustar tamaño del contenedor
        self.grafico_container.adjustSize()

        # 3. Forzar actualización del área de scroll
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setWidgetResizable(True)

        # 4. Opcional: mover scroll a la parte superior
        self.scroll_area.verticalScrollBar().setValue(0)

    def exportar_imagen(self, ruta):
        """Exporta la figura actual como imagen"""
        try:
            self.figura.savefig(ruta, dpi=300, bbox_inches='tight')
            return True
        except Exception as e:
            print(f"Error al exportar imagen: {e}")
            return False

    def generar_pdf(self, ruta):
        """Genera un reporte PDF completo"""
        try:
            doc = SimpleDocTemplate(ruta, pagesize=letter)
            styles = getSampleStyleSheet()
            elementos = []

            # Título
            titulo = Paragraph(f"<b>Reporte de Monitoreo - {self.planta_nombre}</b>", styles['Title'])
            elementos.append(titulo)

            # Información del reporte
            periodo = self.periodo_combo.currentText()
            sensor = self.sensor_combo.currentText()
            fecha_generacion = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            info_text = f"""
            <b>Detalles del reporte:</b><br/>
            Sensor: {sensor}<br/>
            Período: {periodo}<br/>
            Fecha de generación: {fecha_generacion}<br/>
            """
            info = Paragraph(info_text, styles['Normal'])
            elementos.append(info)
            elementos.append(Spacer(1, 12))

            # Guardar gráfico temporalmente
            temp_img = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            self.exportar_imagen(temp_img.name)
            temp_img.close()

            # Añadir gráfico al PDF
            img = Image(temp_img.name, width=450, height=300)
            elementos.append(img)
            elementos.append(Spacer(1, 12))

            # Estadísticas detalladas (solo para un sensor)
            if sensor != "Todos los sensores":
                sensor_key = None
                for key, value in self.nombres_sensores.items():
                    if value == sensor:
                        sensor_key = key
                        break

                if sensor_key:
                    datos = self.cargar_datos_sensor(
                        sensor_key,
                        self.periodos.get(self.periodo_combo.currentText(), 30)
                    )

                    if datos:
                        valores = [d[1] for d in datos]
                        media = np.mean(valores)
                        maximo = np.max(valores)
                        minimo = np.min(valores)
                        desviacion = np.std(valores)

                        stats_text = f"""
                        <b>Estadísticas detalladas:</b><br/>
                        Media: {media:.2f}<br/>
                        Valor máximo: {maximo:.2f}<br/>
                        Valor mínimo: {minimo:.2f}<br/>
                        Desviación estándar: {desviacion:.2f}<br/>
                        Número de muestras: {len(valores)}<br/>
                        """
                        stats = Paragraph(stats_text, styles['Normal'])
                        elementos.append(stats)

            # Generar PDF
            doc.build(elementos)
            os.unlink(temp_img.name)  # Eliminar archivo temporal
            return True
        except Exception as e:
            print(f"Error al generar PDF: {e}")
            return False

    def compartir_reporte(self):
        """Simula el compartir el reporte (en una implementación real podría ser por email, etc.)"""
        QMessageBox.information(self, "Compartir", "Funcionalidad de compartir aún no implementada.")

    def descargar_reporte(self):
        """Permite descargar el reporte como imagen o PDF"""
        if not self.figura or not self.canvas:
            QMessageBox.warning(self, "Error", "Primero debe generar un reporte.")
            return

        opciones = ["Imagen PNG", "Reporte PDF"]
        opcion, ok = QInputDialog.getItem(
            self,
            "Formato de descarga",
            "Seleccione el formato:",
            opciones,
            0,
            False
        )

        if not ok:
            return

        if opcion == "Imagen PNG":
            filtro = "Imágenes PNG (*.png)"
            ruta, _ = QFileDialog.getSaveFileName(
                self,
                "Guardar Imagen",
                f"reporte_{self.planta_nombre}.png",
                filtro
            )
            if ruta:
                if not ruta.lower().endswith('.png'):
                    ruta += '.png'
                if self.exportar_imagen(ruta):
                    QMessageBox.information(self, "Éxito", f"Imagen guardada en:\n{ruta}")
                else:
                    QMessageBox.critical(self, "Error", "No se pudo guardar la imagen.")

        elif opcion == "Reporte PDF":
            filtro = "Documentos PDF (*.pdf)"
            ruta, _ = QFileDialog.getSaveFileName(
                self,
                "Guardar Reporte PDF",
                f"reporte_completo_{self.planta_nombre}.pdf",
                filtro
            )
            if ruta:
                if not ruta.lower().endswith('.pdf'):
                    ruta += '.pdf'
                if self.generar_pdf(ruta):
                    QMessageBox.information(self, "Éxito", f"Reporte PDF guardado en:\n{ruta}")
                else:
                    QMessageBox.critical(self, "Error", "No se pudo generar el reporte PDF.")
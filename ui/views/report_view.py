"""
Vista de reportes optimizada usando nueva arquitectura
"""
import datetime
import os
import tempfile
from pathlib import Path

import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QFrame, QSizePolicy, QFileDialog, QMessageBox, QInputDialog, 
    QWidget, QScrollArea
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Image, Paragraph, Spacer

from config.settings import Settings
from services.profile_service import ProfileService
from core.data_storage import DataStorage


class ReportView(QWidget):
    """Vista de generación de reportes"""
    
    def __init__(self):
        super().__init__()
        self.profileService = ProfileService()
        self.dataStorage = DataStorage()
        
        self.sensores = ["temperatura", "humedad_relativa", "iluminacion", "humedad_suelo"]
        self.nombresSensores = {
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
        
        self.figura = None
        self.canvas = None
        self._setupUI()
    
    def _setupUI(self):
        """Configura la interfaz de usuario"""
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        layout.setSpacing(15)
        
        # Título
        plantaNombre = self.profileService.getPlantName()
        title = QLabel(f'Reportes de "{plantaNombre}"')
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        layout.addWidget(title)
        
        # Controles de selección
        controlsLayout = QHBoxLayout()
        
        # Selector de sensor
        sensorLayout = QVBoxLayout()
        sensorLabel = QLabel("Sensor:")
        sensorLabel.setStyleSheet("color: white;")
        self.sensorCombo = QComboBox()
        self.sensorCombo.addItems(["Todos"] + list(self.nombresSensores.values()))
        self.sensorCombo.setFixedWidth(220)
        self.sensorCombo.setStyleSheet("background-color: #cdd5cf; color: black;")
        sensorLayout.addWidget(sensorLabel)
        sensorLayout.addWidget(self.sensorCombo)
        controlsLayout.addLayout(sensorLayout)
        
        # Selector de período
        periodoLayout = QVBoxLayout()
        periodoLabel = QLabel("Período:")
        periodoLabel.setStyleSheet("color: white;")
        self.periodoCombo = QComboBox()
        self.periodoCombo.addItems(self.periodos.keys())
        self.periodoCombo.setFixedWidth(220)
        self.periodoCombo.setStyleSheet("background-color: #cdd5cf; color: black;")
        periodoLayout.addWidget(periodoLabel)
        periodoLayout.addWidget(self.periodoCombo)
        controlsLayout.addLayout(periodoLayout)
        
        # Botón generar
        self.btnGenerar = QPushButton("Generar Reporte")
        self.btnGenerar.setStyleSheet("""
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
        self.btnGenerar.setFixedWidth(150)
        self.btnGenerar.clicked.connect(self.generarReporte)
        controlsLayout.addWidget(self.btnGenerar, alignment=Qt.AlignmentFlag.AlignBottom)
        
        layout.addLayout(controlsLayout)
        
        # Área de gráficos con scroll
        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setStyleSheet("background-color: white; border-radius: 8px;")
        
        self.graficoContainer = QWidget()
        graficoLayout = QVBoxLayout(self.graficoContainer)
        
        self.figura = Figure(figsize=(10, 6), dpi=100)
        self.canvas = FigureCanvas(self.figura)
        graficoLayout.addWidget(self.canvas)
        
        self.scrollArea.setWidget(self.graficoContainer)
        layout.addWidget(self.scrollArea)
        
        # Botón de descarga
        btnLayout = QHBoxLayout()
        btnLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.btnDescargar = QPushButton("📥 Descargar Reporte")
        self.btnDescargar.setStyleSheet("""
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
        self.btnDescargar.setFixedWidth(180)
        self.btnDescargar.clicked.connect(self.descargarReporte)
        btnLayout.addWidget(self.btnDescargar)
        
        layout.addLayout(btnLayout)
        self.setLayout(layout)
    
    def cargarDatosSensor(self, sensor: str, dias: int = 0) -> list:
        """Carga datos históricos de un sensor"""
        archivo = Path(Settings.HISTORY_DIR) / f"{sensor}.txt"
        datos = []
        
        if not archivo.exists():
            print(f"⚠️ No hay datos históricos para {sensor}")
            return datos
        
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                for linea in f:
                    partes = linea.strip().split(",")
                    if len(partes) >= 2:
                        try:
                            timestamp = datetime.datetime.strptime(partes[0], "%Y-%m-%d %H:%M:%S")
                            valor = float(partes[1])
                            
                            if dias > 0:
                                limite = datetime.datetime.now() - datetime.timedelta(days=dias)
                                if timestamp >= limite:
                                    datos.append((timestamp, valor))
                            else:
                                datos.append((timestamp, valor))
                        except ValueError:
                            continue
        except Exception as e:
            print(f"❌ Error leyendo {archivo}: {e}")
        
        return datos
    
    def generarReporte(self):
        """Genera el reporte gráfico"""
        sensorSeleccionado = self.sensorCombo.currentText()
        periodoSeleccionado = self.periodoCombo.currentText()
        dias = self.periodos.get(periodoSeleccionado, 30)
        
        self.figura.clear()
        
        if sensorSeleccionado == "Todos":
            self._generarReporteTodos(dias, periodoSeleccionado)
        else:
            self._generarReporteUno(sensorSeleccionado, dias, periodoSeleccionado)
        
        self.canvas.draw()
        self.canvas.updateGeometry()
        self.scrollArea.verticalScrollBar().setValue(0)
    
    def _generarReporteTodos(self, dias: int, periodo: str):
        """Genera reporte de todos los sensores"""
        axes = self.figura.subplots(2, 2)
        self.figura.set_size_inches(12, 9)
        self.figura.subplots_adjust(hspace=0.4, wspace=0.3)
        
        for i, sensor in enumerate(self.sensores):
            datos = self.cargarDatosSensor(sensor, dias)
            if not datos:
                continue
            
            fechas, valores = zip(*datos)
            row, col = i // 2, i % 2
            ax = axes[row, col]
            
            media = np.mean(valores)
            maximo = np.max(valores)
            minimo = np.min(valores)
            
            ax.plot(fechas, valores, 'o-', markersize=2, linewidth=1)
            ax.axhline(media, color='r', linestyle='--', alpha=0.7, label=f'Media: {media:.1f}')
            ax.set_title(self.nombresSensores[sensor])
            ax.set_ylabel("Valor")
            ax.grid(True, linestyle='--', alpha=0.3)
            ax.tick_params(axis='x', rotation=45)
            ax.legend()
        
        plantaNombre = self.profileService.getPlantName()
        self.figura.suptitle(f"Reporte Completo - {plantaNombre}\n{periodo}", fontsize=14, fontweight='bold')
    
    def _generarReporteUno(self, sensorNombre: str, dias: int, periodo: str):
        """Genera reporte de un solo sensor"""
        sensorKey = None
        for key, value in self.nombresSensores.items():
            if value == sensorNombre:
                sensorKey = key
                break
        
        if not sensorKey:
            return
        
        datos = self.cargarDatosSensor(sensorKey, dias)
        if not datos:
            QMessageBox.warning(self, "Sin datos", 
                f"No hay datos para {sensorNombre} en el período seleccionado.")
            return
        
        fechas, valores = zip(*datos)
        
        media = np.mean(valores)
        maximo = np.max(valores)
        minimo = np.min(valores)
        desviacion = np.std(valores)
        
        ax = self.figura.subplots()
        self.figura.set_size_inches(12, 7)
        
        ax.plot(fechas, valores, 'o-', markersize=3, linewidth=1.5, label="Valores")
        ax.axhline(media, color='r', linestyle='--', label=f'Media: {media:.2f}')
        ax.axhline(maximo, color='g', linestyle=':', label=f'Máx: {maximo:.2f}')
        ax.axhline(minimo, color='b', linestyle=':', label=f'Mín: {minimo:.2f}')
        
        ax.fill_between(fechas,
                       [media - desviacion] * len(valores),
                       [media + desviacion] * len(valores),
                       color='gray', alpha=0.2, label='σ (desviación)')
        
        plantaNombre = self.profileService.getPlantName()
        ax.set_title(f"{sensorNombre} - {plantaNombre}\n{periodo}", fontsize=14, fontweight='bold')
        ax.set_ylabel("Valor")
        ax.grid(True, linestyle='--', alpha=0.3)
        ax.legend()
        ax.tick_params(axis='x', rotation=45)
        
        # Estadísticas
        statsText = (
            f"Media: {media:.2f}\n"
            f"Máx: {maximo:.2f}\n"
            f"Mín: {minimo:.2f}\n"
            f"σ: {desviacion:.2f}\n"
            f"n={len(valores)}"
        )
        ax.text(0.02, 0.98, statsText, transform=ax.transAxes,
                verticalalignment='top', fontsize=10,
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    def descargarReporte(self):
        """Descarga el reporte como PNG o PDF"""
        if not self.figura or not self.canvas:
            QMessageBox.warning(self, "Error", "Primero genere un reporte.")
            return
        
        opciones = ["Imagen PNG", "Reporte PDF"]
        opcion, ok = QInputDialog.getItem(self, "Formato", "Seleccione formato:", opciones, 0, False)
        
        if not ok:
            return
        
        plantaNombre = self.profileService.getPlantName()
        
        if opcion == "Imagen PNG":
            ruta, _ = QFileDialog.getSaveFileName(
                self, "Guardar Imagen", f"reporte_{plantaNombre}.png", "PNG (*.png)"
            )
            if ruta:
                if not ruta.endswith('.png'):
                    ruta += '.png'
                try:
                    self.figura.savefig(ruta, dpi=300, bbox_inches='tight')
                    QMessageBox.information(self, "✅ Éxito", f"Imagen guardada:\n{ruta}")
                except Exception as e:
                    QMessageBox.critical(self, "❌ Error", f"No se pudo guardar: {e}")
        
        elif opcion == "Reporte PDF":
            ruta, _ = QFileDialog.getSaveFileName(
                self, "Guardar PDF", f"reporte_{plantaNombre}.pdf", "PDF (*.pdf)"
            )
            if ruta:
                if not ruta.endswith('.pdf'):
                    ruta += '.pdf'
                if self._generarPDF(ruta):
                    QMessageBox.information(self, "✅ Éxito", f"PDF guardado:\n{ruta}")
                else:
                    QMessageBox.critical(self, "❌ Error", "No se pudo generar el PDF.")
    
    def _generarPDF(self, ruta: str) -> bool:
        """Genera PDF del reporte"""
        try:
            doc = SimpleDocTemplate(ruta, pagesize=letter)
            styles = getSampleStyleSheet()
            elementos = []
            
            # Título
            plantaNombre = self.profileService.getPlantName()
            titulo = Paragraph(f"<b>Reporte de Monitoreo - {plantaNombre}</b>", styles['Title'])
            elementos.append(titulo)
            elementos.append(Spacer(1, 12))
            
            # Info
            info = Paragraph(f"""
                <b>Sensor:</b> {self.sensorCombo.currentText()}<br/>
                <b>Período:</b> {self.periodoCombo.currentText()}<br/>
                <b>Generado:</b> {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            """, styles['Normal'])
            elementos.append(info)
            elementos.append(Spacer(1, 20))
            
            # Gráfico temporal
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp:
                self.figura.savefig(temp.name, dpi=200, bbox_inches='tight')
                img = Image(temp.name, width=500, height=350)
                elementos.append(img)
                temp_path = temp.name
            
            # Construir PDF
            doc.build(elementos)
            
            # Eliminar temporal
            os.unlink(temp_path)
            return True
            
        except Exception as e:
            print(f"❌ Error generando PDF: {e}")
            return False

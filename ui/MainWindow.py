from PyQt6.QtWidgets import QMainWindow, QTabWidget
from ui.modules.Module import Module
from ui.modules.modules_provider import get_all_modules

class MainWindow(QMainWindow):
    def __init__(self, señalBio):
        super().__init__()
        self.setWindowTitle("PhotoSyntech v1.0")
        self.resize(1280, 720)

        self.__widgetCentral = QTabWidget()
        self.__modulos = get_all_modules(señalBio)

        self.__configurarInterfaz()
        self.setCentralWidget(self.__widgetCentral)

        self.setStyleSheet("""
            QTabWidget::pane { border: none; }
            QTabBar::tab {
                background: #8DB986;
                color: black;
                font-weight: bold;
                padding: 10px;
                border: 1px solid #7AA774;
            }
            QTabBar::tab:selected {
                background: #6BA568;
                color: white;
            }
        """)

    def __configurarInterfaz(self):
        nombresDePestanas = [
            "Ventana principal",
            "Datos de sensores",
            "Configuración",
            "Análisis y reportes",
        ]

        for indice, modulo in enumerate(self.__modulos):
            modulo.draw()
            nombre = nombresDePestanas[indice] if indice < len(nombresDePestanas) else f"Pestaña {indice}"
            self.__widgetCentral.addTab(modulo, nombre)

from PyQt6.QtWidgets import QMainWindow, QTabWidget
from ui.modules.Module import Module
from ui.modules.modules_provider import get_all_modules

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PhotoSyntech v1.0")
        self.resize(1280, 720)
        self.__central = QTabWidget()
        self.__tabs: list[Module] = get_all_modules()
        self.__setup_ui()
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

    def __setup_ui(self):
        tab_names = [
            "Ventana principal",
            "Datos de sensores",
            "Configuración",
            "Análisis y reportes",
            "Señales de planta"
        ]

        for i, m in enumerate(self.__tabs):
            m.draw()
            name = tab_names[i] if i < len(tab_names) else f"Tab {i}"
            self.__central.addTab(m, name)

        self.setCentralWidget(self.__central)

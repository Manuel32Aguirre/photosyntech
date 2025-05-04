from PyQt6.QtCore import QPropertyAnimation, QRect, QEasingCurve
from PyQt6.QtWidgets import (
    QMainWindow, QFrame, QTabWidget
)

from ui.modules.Module import Module
from ui.modules.modules_provider import get_all_modules

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PhotoSyntech v1.0")
        self.resize(1280, 720)
        self.__central = QTabWidget()
        self.__tabs: list[Module] = get_all_modules()
        self.times = []
        self.temps = []
        self.__setup_ui()
        self.__setup_animations()

        self.setStyleSheet(
            """
            QTabWidget::pane{border: none;}
            
            """
        )

    def __setup_ui(self):
        for i, m in enumerate(self.__tabs):
            m.draw()
            self.__central.addTab(m, f"Tab {i}")
        self.setCentralWidget(self.__central)

    def __setup_animations(self):
        tb = self.centralWidget().findChild(QFrame)
        anim = QPropertyAnimation(tb, b"geometry")
        anim.setDuration(800)
        start = QRect(tb.x(), -60, tb.width(), tb.height())
        end = tb.geometry()
        anim.setStartValue(start)
        anim.setEndValue(end)
        anim.setEasingCurve(QEasingCurve.Type.OutBounce)
        anim.start()

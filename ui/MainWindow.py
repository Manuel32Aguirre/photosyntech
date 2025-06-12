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
        self.showFullScreen()
        self.resizable = False
        self.__central = QTabWidget()
        self.__tabs: list[Module] = get_all_modules()
        self.times = []
        self.temps = []
        self.__setup_ui()
        self.__setup_animations()

        self.setStyleSheet(
            """
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
            """
        )

    def __setup_ui(self):
        for m in self.__tabs:
            m.draw()
            self.__central.addTab(m, str(m))
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

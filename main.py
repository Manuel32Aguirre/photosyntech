import sys

from PyQt6.QtWidgets import QApplication

from ui.MainWindow import MainWindow
from ui.fonts import fonts

if __name__ == "__main__":
    app = QApplication(sys.argv)
    fonts.setup_fonts()
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

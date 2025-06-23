import sys
from PyQt6.QtWidgets import QApplication
from ui.MainWindow import MainWindow
from ui.modules.getBioelectricalSignal import SeñalBioeléctrica

def main():
    app = QApplication(sys.argv)
    señal = SeñalBioeléctrica()
    window = MainWindow(señal)
    window.showMaximized()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

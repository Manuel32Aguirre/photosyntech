import sys
from PyQt6.QtWidgets import QApplication

from ui.MainWindow import MainWindow
from ui.modules.getBioelectricalSignal import SeñalBioeléctrica  # ← IMPORTANTE

if __name__ == "__main__":
    app = QApplication(sys.argv)

    señal = SeñalBioeléctrica()       # ← Crear solo una vez
    window = MainWindow(señal)        # ← Pasarla al MainWindow
    window.show()

    sys.exit(app.exec())

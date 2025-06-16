from PyQt6.QtWidgets import (
    QLabel, QVBoxLayout
)
from ui.modules.Module import Module
from ui.modules.MainModule import MainModule
from ui.modules.GraphsModule import GraphsModule
from ui.modules.ReportModules import ReportModule
from ui.modules.ConfigModule import ConfigModule  # ✅ Importar el bueno
from ui.modules.MainModule import MainModule
from ui.modules.GraphsModule import GraphsModule


# ------------ Módulo 5: Señales de planta ------------
class PlantSignalModule(Module):
    def draw(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Contenido de Señales de planta"))
        self.setLayout(layout)


# ------------ Lista de módulos ------------
def get_all_modules(señal_bio) -> list[Module]:
    return [
        MainModule(señal_bio),
        GraphsModule(señal_bio),
        ConfigModule(),
        ReportModule(),
        PlantSignalModule()
    ]


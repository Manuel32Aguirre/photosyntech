from PyQt6.QtWidgets import (
    QLabel, QVBoxLayout
)
from controller.GetWeatherApi import GetWeatherApi
from ui.modules.GraphsModule import GraphsModule
from ui.modules.MainModule import MainModule
from ui.modules.Module import Module
from ui.modules.MainModule import MainModule
from ui.modules.GraphsModule import GraphsModule
from ui.modules.ReportModules import ReportModule
from ui.modules.ConfigModule import ConfigModule  # ✅ Importar el bueno

from ui.modules.SettingsModule import SettingsModule


# ------------ Módulo 5: Señales de planta ------------
class PlantSignalModule(Module):
    def draw(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Contenido de Señales de planta"))
        self.setLayout(layout)


# ------------ Lista de módulos ------------
def get_all_modules() -> list[Module]:
    """
    This functions provides a list of all available modules in the system.
    There could be need that we need to add dependency injection for each module.

    We can add any DI tool before returning the list of modules.
    """
    w = GetWeatherApi()
    return [
        MainModule(),
        GraphsModule(w),
        SettingsModule()
    ]
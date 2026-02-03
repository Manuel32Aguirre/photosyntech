from PyQt6.QtWidgets import (
    QLabel, QVBoxLayout
)

from controller.weather_api import WeatherApi
from ui.modules.Module import Module
from ui.modules.MainModule import MainModule
from ui.modules.GraphsModule import GraphsModule
from ui.modules.ReportModules import ReportModule
from ui.modules.ConfigModule import ConfigModule

def get_all_modules(señal_bio) -> list[Module]:
    main_module = MainModule(señal_bio)
    w = WeatherApi()
    return [
        main_module,
        GraphsModule(señal_bio, main_module, w),
        ConfigModule(),
        ReportModule(),
    ]

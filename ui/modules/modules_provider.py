from datetime import datetime

from controller.GetWeather import GetWeather
from model.WeatherInfo import WeatherInfo
from ui.modules.GraphsModule import GraphsModule
from ui.modules.MainModule import MainModule
from ui.modules.Module import Module


def get_all_modules() -> list[Module]:
    """
    This functions provides a list of all available modules in the system.
    There could be need that we need to add dependency injection for each module.

    We can add any DI tool before returning the list of modules.
    """
    w = type('', (GetWeather,), {
        'get_weather': lambda self: WeatherInfo(
            city='CDMX',
            region='Azcapotzalco',
            last_updated=datetime.now(),
            condition='Cloudy',
            temperature=28.5,
        )
    })()
    return [
        MainModule(),
        GraphsModule(w)
    ]

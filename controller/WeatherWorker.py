from PyQt6.QtCore import pyqtSignal, QObject

from controller.GetWeather import GetWeather
from model.WeatherInfo import WeatherInfo


class WeatherWorker(QObject):
    finished = pyqtSignal()
    result_ready = pyqtSignal(WeatherInfo)

    def __init__(self, weather: GetWeather):
        super().__init__()
        self.__weather = weather

    def run_task(self):
        result = self.__weather.get_weather()
        self.result_ready.emit(result)
        self.finished.emit()
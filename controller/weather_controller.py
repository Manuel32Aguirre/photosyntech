from abc import ABC, abstractmethod

from model.weather_info import WeatherInfo


class WeatherController(ABC):

    @abstractmethod
    def get_weather(self) -> WeatherInfo:
        pass
from abc import ABC, abstractmethod

from model.WeatherInfo import WeatherInfo


class GetWeather(ABC):

    @abstractmethod
    def get_weather(self) -> WeatherInfo:
        pass

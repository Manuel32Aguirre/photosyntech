from datetime import datetime

import requests

from controller.GetWeather import GetWeather
from model.WeatherInfo import WeatherInfo


class GetWeatherApi(GetWeather):

    __API_KEY_WEATHER = '1d174da619c9478ba7922729250906'
    __ENDPOINT_IP = 'https://ipinfo.io/json'
    __ENDPOINT_WEATHER = 'http://api.weatherapi.com/v1/current.json'

    def get_weather(self) -> WeatherInfo:
        ip = requests.get(GetWeatherApi.__ENDPOINT_IP).json()['ip']
        params = {
            'key': GetWeatherApi.__API_KEY_WEATHER,
            'q': ip,
            'lang': 'es'
        }
        response = requests.get(GetWeatherApi.__ENDPOINT_WEATHER, params=params).json()
        return WeatherInfo(
            city=response["location"]["name"],
            region=response["location"]["region"],
            last_updated=datetime.strptime(response["current"]["last_updated"], "%Y-%m-%d %H:%M"),
            temperature=response["current"]["temp_c"],
            condition=response["current"]["condition"]["text"]
        )

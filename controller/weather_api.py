from datetime import datetime
import os
from dotenv import load_dotenv
import requests

from controller.weather_controller import WeatherController
from model.weather_info import WeatherInfo

load_dotenv()


class WeatherApi(WeatherController):
    
    def __init__(self):
        self.api_key = os.getenv('OPENWEATHERMAP_API_KEY', '')
        self.city = os.getenv('CITY', 'Gustavo A. Madero,mx')
        self.endpoint = 'http://api.openweathermap.org/data/2.5/forecast'
        
        if not self.api_key or self.api_key == 'TU_API_KEY_AQUI':
            print("API key de OpenWeatherMap no configurada en .env")

    def get_weather(self) -> WeatherInfo:
        try:
            params = {
                'q': self.city,
                'units': 'metric',
                'appid': self.api_key,
                'lang': 'es'
            }
            
            response = requests.get(self.endpoint, params=params, timeout=5).json()
            
            if 'cod' in response and response['cod'] != '200':
                print(f"Error API del clima: {response.get('message', 'Unknown')}")
                return self._get_default_weather()
            
            current = response['list'][0]
            city_info = response['city']
            
            return WeatherInfo(
                city=city_info['name'],
                region=city_info['country'],
                last_updated=datetime.fromtimestamp(current['dt']),
                temperature=current['main']['temp'],
                condition=current['weather'][0]['description']
            )
        except Exception as e:
            print(f"No se pudo obtener datos del clima: {e}")
            return self._get_default_weather()
    
    def _get_default_weather(self) -> WeatherInfo:
        return WeatherInfo(
            city="Ciudad Desconocida",
            region="Región Desconocida",
            last_updated=datetime.now(),
            temperature=25.0,
            condition="No disponible"
        )
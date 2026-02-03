from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class WeatherInfo:
    city: str
    region: str
    last_updated: datetime
    temperature: float
    condition: str
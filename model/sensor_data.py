"""
Modelo de datos para lecturas de sensores
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class SensorReading:
    """Lectura individual de un sensor"""
    timestamp: datetime
    value: float
    sensor_type: str
    
    def __str__(self) -> str:
        return f"{self.sensor_type}: {self.value} @ {self.timestamp}"


@dataclass
class SensorSnapshot:
    """Snapshot de todos los sensores en un momento dado"""
    timestamp: datetime
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    light: Optional[float] = None
    soil_moisture: Optional[float] = None
    
    def is_complete(self) -> bool:
        """Verifica si todos los sensores tienen datos"""
        return all([
            self.temperature is not None,
            self.humidity is not None,
            self.light is not None,
            self.soil_moisture is not None
        ])

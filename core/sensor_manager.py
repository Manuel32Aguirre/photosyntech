"""
Gestor centralizado de datos de sensores
Maneja el estado actual y gestiona actualizaciones
"""
import time
import random
from typing import Dict, Tuple, Optional
from dataclasses import dataclass, field


@dataclass
class SensorData:
    value: str = "--"
    last_updated: float = field(default_factory=time.time)
    
    def is_valid(self) -> bool:
        return self.value != "--"
    
    def get_float(self, default: float = 0.0) -> float:
        try:
            return float(self.value) if self.is_valid() else default
        except ValueError:
            return default


class SensorManager:
    
    def __init__(self):
        self._sensors: Dict[str, SensorData] = {
            "temperatura": SensorData(),
            "humedad_relativa": SensorData(),
            "iluminacion": SensorData(),
            "humedad_suelo": SensorData()
        }
        
        self._soilFakeEnabled = True
        self._soilFakeValue = round(random.uniform(50, 60), 1)
        self._soilFakeLastUpdate = time.time()
        self._soilFakeInterval = 60  # segundos
    
    def updateSensor(self, sensorName: str, value: str):
        if sensorName in self._sensors:
            self._sensors[sensorName].value = value
            self._sensors[sensorName].lastUpdated = time.time()
    
    def getSensorValue(self, sensorName: str) -> str:
        if sensorName == "humedad_suelo" and self._soilFakeEnabled:
            self._updateFakeSoilIfNeeded()
            return str(self._soilFakeValue)
        
        if sensorName in self._sensors:
            return self._sensors[sensorName].value
        return "--"
    
    def getSensorData(self, sensorName: str) -> Optional[SensorData]:
        return self._sensors.get(sensorName)
    
    def getAllSensors(self) -> Tuple[str, str, str, str]:
        return (
            self.getSensorValue("temperatura"),
            self.getSensorValue("humedad_relativa"),
            self.getSensorValue("iluminacion"),
            self.getSensorValue("humedad_suelo")
        )
    
    def updateAllSensors(self, temp: str, humidity: str, light: str, soil: str):
        self.updateSensor("temperatura", temp)
        self.updateSensor("humedad_relativa", humidity)
        self.updateSensor("iluminacion", light)
        if not self._soilFakeEnabled:
            self.updateSensor("humedad_suelo", soil)
    
    def _updateFakeSoilIfNeeded(self):
        currentTime = time.time()
        if currentTime - self._soilFakeLastUpdate >= self._soilFakeInterval:
            self._soilFakeValue = round(random.uniform(50, 60), 1)
            self._soilFakeLastUpdate = currentTime
    
    def enableFakeSoil(self, enabled: bool = True):
        self._soilFakeEnabled = enabled
    
    def getSoilFakeValue(self) -> float:
        self._updateFakeSoilIfNeeded()
        return self._soilFakeValue
    
    def parseFloat(self, value: str, default: float = 0.0) -> float:
        try:
            return float(value) if value != '--' else default
        except ValueError:
            return default

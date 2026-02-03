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
    """Datos de un sensor individual"""
    value: str = "--"
    last_updated: float = field(default_factory=time.time)
    
    def is_valid(self) -> bool:
        """Verifica si el dato es válido"""
        return self.value != "--"
    
    def get_float(self, default: float = 0.0) -> float:
        """Obtiene el valor como float"""
        try:
            return float(self.value) if self.is_valid() else default
        except ValueError:
            return default


class SensorManager:
    """Gestor centralizado de todos los sensores"""
    
    def __init__(self):
        self._sensors: Dict[str, SensorData] = {
            "temperatura": SensorData(),
            "humedad_relativa": SensorData(),
            "iluminacion": SensorData(),
            "humedad_suelo": SensorData()
        }
        
        # Para humedad de suelo fake
        self._soilFakeEnabled = True
        self._soilFakeValue = round(random.uniform(50, 60), 1)
        self._soilFakeLastUpdate = time.time()
        self._soilFakeInterval = 60  # segundos
    
    def updateSensor(self, sensorName: str, value: str):
        """
        Actualiza el valor de un sensor
        
        Args:
            sensorName: Nombre del sensor
            value: Nuevo valor
        """
        if sensorName in self._sensors:
            self._sensors[sensorName].value = value
            self._sensors[sensorName].lastUpdated = time.time()
    
    def getSensorValue(self, sensorName: str) -> str:
        """
        Obtiene el valor actual de un sensor
        
        Args:
            sensorName: Nombre del sensor
            
        Returns:
            Valor del sensor como string
        """
        if sensorName == "humedad_suelo" and self._soilFakeEnabled:
            self._updateFakeSoilIfNeeded()
            return str(self._soilFakeValue)
        
        if sensorName in self._sensors:
            return self._sensors[sensorName].value
        return "--"
    
    def getSensorData(self, sensorName: str) -> Optional[SensorData]:
        """Obtiene el objeto SensorData completo"""
        return self._sensors.get(sensorName)
    
    def getAllSensors(self) -> Tuple[str, str, str, str]:
        """
        Obtiene todos los valores de sensores
        
        Returns:
            Tupla (temperatura, humedad_relativa, iluminacion, humedad_suelo)
        """
        return (
            self.getSensorValue("temperatura"),
            self.getSensorValue("humedad_relativa"),
            self.getSensorValue("iluminacion"),
            self.getSensorValue("humedad_suelo")
        )
    
    def updateAllSensors(self, temp: str, humidity: str, light: str, soil: str):
        """
        Actualiza todos los sensores de una vez
        
        Args:
            temp: Temperatura
            humidity: Humedad relativa
            light: Iluminación
            soil: Humedad de suelo
        """
        self.updateSensor("temperatura", temp)
        self.updateSensor("humedad_relativa", humidity)
        self.updateSensor("iluminacion", light)
        if not self._soilFakeEnabled:
            self.updateSensor("humedad_suelo", soil)
    
    def _updateFakeSoilIfNeeded(self):
        """Actualiza el valor fake de humedad de suelo si es necesario"""
        currentTime = time.time()
        if currentTime - self._soilFakeLastUpdate >= self._soilFakeInterval:
            self._soilFakeValue = round(random.uniform(50, 60), 1)
            self._soilFakeLastUpdate = currentTime
    
    def enableFakeSoil(self, enabled: bool = True):
        """Habilita/deshabilita el valor fake de humedad de suelo"""
        self._soilFakeEnabled = enabled
    
    def getSoilFakeValue(self) -> float:
        """Obtiene el valor fake de humedad de suelo"""
        self._updateFakeSoilIfNeeded()
        return self._soilFakeValue
    
    def parseFloat(self, value: str, default: float = 0.0) -> float:
        """
        Parsea un valor de sensor a float de forma segura
        
        Args:
            value: Valor como string
            default: Valor por defecto si falla el parseo
            
        Returns:
            Valor como float
        """
        try:
            return float(value) if value != '--' else default
        except ValueError:
            return default

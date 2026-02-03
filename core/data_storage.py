"""
Gestor de almacenamiento de datos
Maneja la persistencia de lecturas de sensores
"""
import os
import datetime
import time
from typing import Dict
from config.settings import Settings
from config.config_manager import ConfigManager


class DataStorage:
    
    def __init__(self):
        self.historyDir = Settings.HISTORY_DIR
        self.configManager = ConfigManager()
        self.lastSave: Dict[str, float] = {}
        
        os.makedirs(self.historyDir, exist_ok=True)
        
        for sensor in Settings.DEFAULT_SENSOR_FREQUENCIES.keys():
            self.lastSave[sensor] = 0
    
    def saveSensorReading(self, sensorName: str, value: str, force: bool = False):
        
        if value == "--" or value == "":
            return
        
        if not force:
            frequency = self.configManager.get_sensor_frequency(sensorName)
            currentTime = time.time()
            
            if currentTime - self.lastSave.get(sensorName, 0) < frequency:
                return
        
        try:
            filepath = os.path.join(self.historyDir, f"{sensorName}.txt")
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            with open(filepath, "a", encoding="utf-8") as f:
                f.write(f"{timestamp},{value}\n")
            
            self.lastSave[sensorName] = time.time()
            
        except Exception as e:
            print(f"Error guardando sensor {sensorName}: {e}")
    
    def saveMultipleSensors(self, sensorData: Dict[str, str]):
        for sensorName, value in sensorData.items():
            self.saveSensorReading(sensorName, value)
    
    def loadSensorHistory(self, sensorName: str, days: int = 0) -> list:
        filepath = os.path.join(self.history_dir, f"{sensor_name}.txt")
        data = []
        
        if not os.path.exists(filepath):
            return data
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split(",")
                    if len(parts) >= 2:
                        try:
                            timestamp = datetime.datetime.strptime(parts[0], "%Y-%m-%d %H:%M:%S")
                            value = float(parts[1])
                            
                            if days > 0:
                                limit = datetime.datetime.now() - datetime.timedelta(days=days)
                                if timestamp >= limit:
                                    data.append((timestamp, value))
                            else:
                                data.append((timestamp, value))
                                
                        except ValueError:
                            continue
        except Exception as e:
            print(f"Error cargando historial de {sensorName}: {e}")
        
        return data
    
    def getSensorStats(self, sensorName: str, days: int = 0) -> dict:
        data = self.loadSensorHistory(sensorName, days)
        
        if not data:
            return {}
        
        values = [v for _, v in data]
        
        import numpy as np
        return {
            "count": len(values),
            "mean": np.mean(values),
            "min": np.min(values),
            "max": np.max(values),
            "std": np.std(values)
        }
    
    def clearSensorHistory(self, sensorName: str):
        filepath = os.path.join(self.historyDir, f"{sensorName}.txt")
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            print(f"Error eliminando historial de {sensorName}: {e}")

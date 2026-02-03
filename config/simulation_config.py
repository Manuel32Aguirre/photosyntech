"""
Gestor de configuración de simulación
Lee los rangos desde simulacion.txt
"""
import os
import random
import time
import math
from typing import Dict
from config.settings import Settings


class SimulationConfig:
    """Gestor de configuración de simulación"""
    
    def __init__(self):
        self.configFile = Settings.SIMULATION_FILE
        self.usarDatosReales = Settings.USE_REAL_DATA
        self.config = self._loadConfig()
        
        # Estado de simulación
        self.lastSensorUpdate = 0
        self.bioSignalPhase = 0
    
    def _loadConfig(self) -> Dict:
        """Carga la configuración de simulación"""
        defaultConfig = {
            'usarDatosReales': 'true',
            'temperaturaMin': 18.0,
            'temperaturaMax': 32.0,
            'humedadRelativaMin': 40.0,
            'humedadRelativaMax': 80.0,
            'iluminacionMin': 15000.0,
            'iluminacionMax': 60000.0,
            'humedadSueloMin': 45.0,
            'humedadSueloMax': 75.0,
            'voltajeBioMin': -15.0,
            'voltajeBioMax': 15.0,
            'voltajeBioVariacion': 5.0,
            'frecuenciaActualizacionSensores': 3.0
        }
        
        if not os.path.exists(self.configFile):
            return defaultConfig
        
        config = defaultConfig.copy()
        
        try:
            with open(self.configFile, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        if key == 'usarDatosReales':
                            config[key] = value.lower()
                            # Actualizar flag global
                            self.usarDatosReales = (value.lower() == 'true')
                        elif key in config:
                            try:
                                config[key] = float(value)
                            except ValueError:
                                pass
        except Exception as e:
            print(f"Error cargando configuración de simulación: {e}")
        
        return config
    
    def debeUsarDatosReales(self) -> bool:
        """Verifica si debe usar datos reales o simulados"""
        return self.usarDatosReales
    
    def generarTemperatura(self) -> float:
        """Genera temperatura simulada"""
        return random.uniform(
            self.config['temperaturaMin'],
            self.config['temperaturaMax']
        )
    
    def generarHumedadRelativa(self) -> float:
        """Genera humedad relativa simulada"""
        return random.uniform(
            self.config['humedadRelativaMin'],
            self.config['humedadRelativaMax']
        )
    
    def generarIluminacion(self) -> float:
        """Genera iluminación simulada"""
        return random.uniform(
            self.config['iluminacionMin'],
            self.config['iluminacionMax']
        )
    
    def generarHumedadSuelo(self) -> float:
        """Genera humedad de suelo simulada"""
        return random.uniform(
            self.config['humedadSueloMin'],
            self.config['humedadSueloMax']
        )
    
    def generarVoltajeBioelectrico(self) -> float:
        """
        Genera voltaje bioeléctrico simulado con patrón más realista
        Usa una combinación de ondas para simular señal biológica
        """
        # Incrementar fase para simular señal continua
        self.bioSignalPhase += 0.1
        
        # Combinar múltiples frecuencias para señal más realista
        baseSignal = math.sin(self.bioSignalPhase)
        noise = random.uniform(-0.3, 0.3)
        
        # Calcular voltaje
        minVoltage = self.config['voltajeBioMin']
        maxVoltage = self.config['voltajeBioMax']
        variation = self.config['voltajeBioVariacion']
        
        # Señal centrada en 0 con variación
        voltage = (baseSignal * variation) + noise
        
        # Limitar al rango
        return max(minVoltage, min(maxVoltage, voltage))
    
    def deberiActualizarSensores(self) -> bool:
        """Verifica si deben actualizarse los sensores simulados"""
        currentTime = time.time()
        frequency = self.config['frecuenciaActualizacionSensores']
        
        if currentTime - self.lastSensorUpdate >= frequency:
            self.lastSensorUpdate = currentTime
            return True
        
        return False
    
    def generarDatosSensores(self) -> tuple:
        """
        Genera todos los datos de sensores
        
        Returns:
            Tupla (temperatura, humedad, luz, suelo) como strings
        """
        temp = f"{self.generarTemperatura():.1f}"
        hum = f"{self.generarHumedadRelativa():.1f}"
        light = f"{self.generarIluminacion():.0f}"
        soil = f"{self.generarHumedadSuelo():.1f}"
        
        return temp, hum, light, soil

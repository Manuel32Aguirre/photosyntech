# getBioelectricalSignal.py
# Adaptador para compatibilidad con código legacy
# Usa la nueva arquitectura internamente

import threading
import time
import numpy as np
from collections import deque

# Importar nueva arquitectura
from hardware.serial_reader import SerialReader
from core.signal_processor import SignalProcessor
from core.sensor_manager import SensorManager

class SeñalBioeléctrica:
    """
    Wrapper de compatibilidad que usa la nueva arquitectura internamente.
    Mantiene la interfaz original para no romper el código legacy.
    """
    def __init__(self, puerto='COM7', baudrate=115200, offset=1.695, ganancia=5.97):
        # Usar nueva arquitectura
        self.serialReader = SerialReader()
        self.signalProcessor = SignalProcessor()
        self.sensorManager = self.serialReader.sensorManager
        
        # Mantener compatibilidad con propiedades legacy
        self.offset = offset
        self.ganancia = ganancia
        self.fs = 200
        
        # Iniciar lectura
        self.serialReader.start()
        
        print(f"✅ Iniciado en modo: {self.serialReader.getModoOperacion()}")
        
        # Compatibilidad con código antiguo
        self.serial = self.serialReader.serialConnection
        self.tiempoInicio = time.time()

        print(f"✅ Iniciado en modo: {self.serialReader.getModoOperacion()}")
        
        # Compatibilidad con código antiguo
        self.serial = self.serialReader.serialConnection
        self.tiempoInicio = time.time()

    def siguiente_valor(self):
        """Obtiene el siguiente valor del buffer (compatibilidad legacy)"""
        tiempo, voltaje = self.serialReader.getNextBioValue()
        return (tiempo, voltaje) if tiempo is not None else (None, None)

    def obtener_datos_sensores(self):
        """Obtiene datos de sensores (compatibilidad legacy)"""
        # getAllSensors() retorna tupla (temp, hum, light, soil)
        return self.sensorManager.getAllSensors()
    
    def aplicar_filtros(self, señal):
        """Aplica filtros a la señal (usa nueva arquitectura)"""
        return self.signalProcessor.applyFilters(np.array(señal))

    def calcular_features(self):
        """Calcula features de la señal (usa nueva arquitectura)"""
        buffer = self.serialReader.getBufferCopy()
        
        if len(buffer) < 100:
            return None
        
        tiempos, voltajes = zip(*buffer)
        voltajes_np = np.array(voltajes)
        
        return self.signalProcessor.calculateFeatures(voltajes_np)
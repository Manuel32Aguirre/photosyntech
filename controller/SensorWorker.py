from time import sleep

from PyQt6.QtCore import QObject, pyqtSignal

class SensorWorker(QObject):
    data_ready = pyqtSignal(list)  # Señal para emitir los nuevos datos

    def __init__(self, interval=5):
        super().__init__()
        self.running = True
        self.interval = interval  # Segundos entre actualizaciones

    def run(self):
        while self.running:
            try:
                sensor_data = self.read_sensors()
                self.data_ready.emit(sensor_data)
            except Exception as e:
                print(f"Error reading sensors: {e}")

            sleep(self.interval)

    def read_sensors(self):
        """Simulación de lectura de sensores (reemplaza con tu implementación real)"""
        import random
        return [
            random.uniform(20, 30),     # Temperatura
            random.uniform(40, 80),     # Humedad suelo
            random.uniform(30, 70),     # Humedad ambiente
            random.uniform(100, 1000)   # Luminosidad
        ]

    def stop(self):
        self.running = False

import math
import time
from datetime import datetime

class SeñalBioeléctrica:
    def __init__(self, frecuencia_hz=60, amplitud=0.5):
        self.frecuencia = frecuencia_hz
        self.amplitud = amplitud
        self._start_time = time.time()

    def siguiente_valor(self):
        tiempo_actual = time.time() - self._start_time
        voltaje = self.amplitud * math.sin(2 * math.pi * self.frecuencia * tiempo_actual) + 1
        return datetime.now(), voltaje

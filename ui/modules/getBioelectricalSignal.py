import math
import time
from datetime import datetime

class SeñalBioeléctrica:
    def __init__(self, frecuencia_hz=60, amplitud=1.0):
        self.frecuencia = frecuencia_hz
        self.amplitud = amplitud
        self._start_time = time.time()

    def siguiente_valor(self):
        tiempo_actual = time.time() - self._start_time
        voltaje = self.amplitud * math.sin(2 * math.pi * self.frecuencia * tiempo_actual)
        return datetime.now(), voltaje

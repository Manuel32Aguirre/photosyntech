import serial
import threading
import time
import re
from collections import deque

class SeñalBioeléctrica:
    def __init__(self, puerto='COM7', baudrate=115200, offset=1.7, ganancia=5.94):
        self.offset = offset
        self.ganancia = ganancia
        self.buffer = deque(maxlen=1000)
        self.lock = threading.Lock()
        self.sensor_lock = threading.Lock()
        self.t0 = time.time()

        self.temp = "--"
        self.hum = "--"
        self.soil = "--"
        self.light = "--"

        try:
            self.ser = serial.Serial(puerto, baudrate, timeout=1)
            self.hilo_lectura = threading.Thread(target=self.__leer_datos, daemon=True)
            self.hilo_lectura.start()
            print("Puerto serial abierto correctamente.")
        except serial.SerialException as e:
            print(f"[ERROR] No se pudo abrir el puerto serial: {e}")
            self.ser = None

    def __leer_datos(self):
        time.sleep(2)  # Evita basura inicial

        # Adaptado para reconocer números con o sin sufijos
        patron = re.compile(
            r'DATA:BIO:([0-9.]+),TEMP:([0-9\-]+),HUM:([0-9\-]+),SOIL:([0-9\-]+),LIGHT:([0-9\-]+)'
        )

        while True:
            try:
                linea = self.ser.readline().decode('utf-8', errors='ignore').strip()

                match = patron.match(linea)
                if not match:
                    continue

                bio, temp, hum, soil, light = match.groups()

                voltaje_crudo = float(bio)
                voltaje_mv = ((voltaje_crudo - self.offset) / self.ganancia) * 1000
                tiempo_relativo = time.time() - self.t0

                with self.lock:
                    self.buffer.append((tiempo_relativo, voltaje_mv))

                with self.sensor_lock:
                    self.temp = temp
                    self.hum = hum
                    self.soil = soil
                    self.light = light

            except Exception as e:
                print(f"[ERROR] al procesar línea: {e}")

    def siguiente_valor(self):
        with self.lock:
            if self.buffer:
                return self.buffer.popleft()
            else:
                return None, None

    def obtener_datos_sensores(self):
        with self.sensor_lock:
            return self.temp, self.hum, self.soil, self.light

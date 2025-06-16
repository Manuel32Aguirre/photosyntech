import serial
import threading
import time
import re
from collections import deque

class SeñalBioeléctrica:
    def __init__(self, puerto='COM7', baudrate=115200, offset=1.695, ganancia=5.985):
        self.offset = offset
        self.ganancia = ganancia

        self.buffer = deque(maxlen=5000)
        self.lock = threading.Lock()
        self.sensor_lock = threading.Lock()
        self.t0 = time.time()

        self.temp = "--"
        self.hum = "--"
        self.soil = "--"
        self.light = "--"

        try:
            self.ser = serial.Serial(puerto, baudrate, timeout=2)
            self.hilo_lectura = threading.Thread(target=self.__leer_datos, daemon=True)
            self.hilo_lectura.start()
            print("Puerto serial abierto correctamente.")
        except serial.SerialException as e:
            print(f"[ERROR] No se pudo abrir el puerto serial: {e}")
            self.ser = None

    def __leer_datos(self):
        time.sleep(2)
        patron = re.compile(
            r'DATA:BIO:(-?[\d.]+),TEMP:([^,]+),HUM:([^,]+),SOIL:([^,]+),LIGHT:([^,]+)'
        )

        while True:
            try:
                linea = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if not linea:
                    continue

                match = patron.match(linea)
                if match:
                    volt_sin_calibrar, temp, hum, soil, light = match.groups()
                    volt_sin_calibrar = float(volt_sin_calibrar)

                    # Calibrar con offset exacto y ganancia exacta
                    volt_calibrado = (volt_sin_calibrar - self.offset) / self.ganancia
                    voltaje_mv = volt_calibrado * 1000  # en milivoltios

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

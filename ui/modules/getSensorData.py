import threading

import serial


class SensorReader:
    def __init__(self, puerto='COM9', baudrate=115200):
        try:
            self.serial = serial.Serial(puerto, baudrate, timeout=1)
            print("Puerto serial abierto correctamente.")
        except Exception as e:
            print(f"[ERROR] No se pudo abrir el puerto {puerto}: {e}")
            raise

        self.temp = '--'
        self.hum = '--'
        self.soil = '--'
        self.light = '--'
        self.lock = threading.Lock()
        self.hilo = threading.Thread(target=self.__leer, daemon=True)
        self.hilo.start()

    def __leer(self):
        while True:
            try:
                linea = self.serial.readline().decode('utf-8').strip()
                if linea.startswith("TEMP:"):
                    with self.lock: self.temp = linea.split(":")[1].strip()
                elif linea.startswith("HUM:"):
                    with self.lock: self.hum = linea.split(":")[1].strip()
                elif linea.startswith("SOIL:"):
                    with self.lock: self.soil = linea.split(":")[1].strip()
                elif linea.startswith("LIGHT:"):
                    with self.lock: self.light = linea.split(":")[1].strip()
                # Si no empieza con ninguna etiqueta, ignoramos la línea silenciosamente
            except Exception:
                # Si ocurre un error de decodificación, simplemente se ignora
                continue

    def obtener_datos(self):
        with self.lock:
            return self.temp, self.hum, self.soil, self.light

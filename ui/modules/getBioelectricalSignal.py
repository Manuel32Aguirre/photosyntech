import serial
import threading
import time
import re
from collections import deque

class SeñalBioeléctrica:
    def __init__(self, puerto='COM7', baudrate=115200, offset=1.695, ganancia=5.97):
        self.offset = offset
        self.ganancia = ganancia

        self.bufferDatos = deque(maxlen=5000)
        self.bloqueoBuffer = threading.Lock()
        self.bloqueoSensores = threading.Lock()
        self.tiempoInicio = time.time()

        self.temperaturaActual = "--"
        self.humedadActual = "--"
        self.luzActual = "--"
        self.humedadSueloActual = "--"  # NUEVO

        try:
            self.serial = serial.Serial(puerto, baudrate, timeout=2)
            self.hiloLectura = threading.Thread(target=self.__leerDatos, daemon=True)
            self.hiloLectura.start()
            print("Puerto serial abierto correctamente.")
        except serial.SerialException as error:
            print(f"[ERROR] No se pudo abrir el puerto serial: {error}")
            self.serial = None

    def __leerDatos(self):
        time.sleep(2)

        patron_bio = re.compile(r'B:([-+]?\d*\.\d+|\d+)')
        patron_sensores = re.compile(r'T:([^,]+),H:([^,]+),L:([^,]+),S:([^,]+)')  # actualizado

        while True:
            try:
                linea = self.serial.readline().decode('utf-8', errors='ignore').strip()
                if not linea:
                    continue

                # Señal bioeléctrica
                match_bio = patron_bio.match(linea)
                if match_bio:
                    voltaje_bruto = float(match_bio.group(1))  # en voltios recibido

                    # Recuperar la señal original:
                    voltaje_real = (voltaje_bruto - self.offset) / self.ganancia

                    # Convertir a milivoltios:
                    voltaje_mv = voltaje_real * 1000

                    tiempoRelativo = time.time() - self.tiempoInicio

                    with self.bloqueoBuffer:
                        self.bufferDatos.append((tiempoRelativo, voltaje_mv))
                    continue

                # Sensores
                match_sens = patron_sensores.search(linea)
                if match_sens:
                    temp, hum, light, soil = match_sens.groups()

                    with self.bloqueoSensores:
                        self.temperaturaActual = temp
                        self.humedadActual = hum
                        self.luzActual = light
                        self.humedadSueloActual = soil  # NUEVO
                    continue

            except Exception as error:
                print(f"[ERROR] al procesar línea: {error}")

    def siguiente_valor(self):
        with self.bloqueoBuffer:
            return self.bufferDatos.popleft() if self.bufferDatos else (None, None)

    def obtener_datos_sensores(self):
        with self.bloqueoSensores:
            return (
                self.temperaturaActual,
                self.humedadActual,
                self.luzActual,
                self.humedadSueloActual 
            )

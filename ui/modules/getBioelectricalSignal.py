# getBioelectricalSignal.py
import serial
import threading
import time
import re
import numpy as np
from collections import deque
from scipy.signal import iirnotch, butter, filtfilt

class SeñalBioeléctrica:
    def __init__(self, puerto='COM7', baudrate=115200, offset=1.695, ganancia=5.97):
        self.offset = offset
        self.ganancia = ganancia
        self.fs = 200  # Frecuencia de muestreo
        
        # Configuración de filtros
        f_notch = 60
        bw = 1
        self.b_notch, self.a_notch = iirnotch(f_notch, Q=f_notch/bw, fs=self.fs)
        
        fc_lowpass = 10
        orden_lowpass = 4
        self.b_lowpass, self.a_lowpass = butter(orden_lowpass, fc_lowpass/(0.5*self.fs), btype='low')
        
        # Buffers de datos
        self.bufferDatos = deque(maxlen=5000)  # Almacena (tiempo, voltaje)
        self.bloqueoBuffer = threading.Lock()
        self.bloqueoSensores = threading.Lock()
        self.tiempoInicio = time.time()
        
        # Sensores
        self.temperaturaActual = "--"
        self.humedadActual = "--"
        self.luzActual = "--"
        self.humedadSueloActual = "--"
        
        # Inicializar comunicación serial
        try:
            self.serial = serial.Serial(puerto, baudrate, timeout=2)
            self.hiloLectura = threading.Thread(target=self.__leerDatos, daemon=True)
            self.hiloLectura.start()
            print("✅ Puerto serial abierto correctamente.")
        except serial.SerialException as error:
            print(f"[ERROR] No se pudo abrir el puerto serial: {error}")
            self.serial = None

    def __leerDatos(self):
        time.sleep(2)
        
        patron_bio = re.compile(r'B:([-+]?\d*\.\d+|\d+)')
        patron_sensores = re.compile(r'T:([^,]+),H:([^,]+),L:([^,]+),S:([^,]+)')
        
        while True:
            try:
                if self.serial is None:
                    time.sleep(1)
                    continue
                    
                linea = self.serial.readline().decode('utf-8', errors='ignore').strip()
                if not linea:
                    continue

                match_bio = patron_bio.match(linea)
                if match_bio:
                    voltaje_bruto = float(match_bio.group(1))
                    
                    voltaje_real = (voltaje_bruto - self.offset) / self.ganancia
                    voltaje_mv = voltaje_real * 1000
                    tiempoRelativo = time.time() - self.tiempoInicio

                    with self.bloqueoBuffer:
                        self.bufferDatos.append((tiempoRelativo, voltaje_mv))
                    continue

                match_sens = patron_sensores.search(linea)
                if match_sens:
                    temp, hum, light, soil = match_sens.groups()

                    with self.bloqueoSensores:
                        self.temperaturaActual = temp
                        self.humedadActual = hum
                        self.luzActual = light
                        self.humedadSueloActual = soil
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
    
    def aplicar_filtros(self, señal):
        if len(señal) > 15:
            señal = filtfilt(self.b_notch, self.a_notch, señal)
            señal = filtfilt(self.b_lowpass, self.a_lowpass, señal)
        return señal

    def calcular_features(self):
        """ Calcula features: RMS, media, centroide, energía por bandas """
        with self.bloqueoBuffer:
            if len(self.bufferDatos) < 100:
                return None  # No hay suficientes datos todavía

            tiempos, voltajes = zip(*self.bufferDatos)
            voltajes_np = np.array(voltajes)
            voltajes_filtrado = self.aplicar_filtros(voltajes_np)

            # RMS, Media, STD
            diferencias = np.diff(voltajes_filtrado)
            rms = np.sqrt(np.mean(np.square(diferencias)))
            media = np.mean(diferencias)
            std = np.std(diferencias)

            # FFT
            fft_result = np.fft.rfft(voltajes_filtrado)
            fft_freq = np.fft.rfftfreq(len(voltajes_filtrado), d=1/self.fs)
            fft_magnitude = np.abs(fft_result)

            centroide = np.sum(fft_freq * fft_magnitude) / np.sum(fft_magnitude)

            bandas = [(0,5), (5,10), (10,20), (20,50), (50,100)]
            energia_bandas = {}

            for fmin, fmax in bandas:
                idx = np.where((fft_freq >= fmin) & (fft_freq < fmax))
                energia = np.sum(fft_magnitude[idx])
                energia_bandas[f"{fmin}-{fmax}Hz"] = energia

            features = {
                "rms": rms,
                "media": media,
                "std": std,
                "centroide_freq": centroide,
                "energia": energia_bandas
            }

            return features

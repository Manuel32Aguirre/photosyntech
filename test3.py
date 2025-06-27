import matplotlib.pyplot as plt
from scipy.signal import iirnotch, filtfilt, butter
import numpy as np
import time
import threading

# === Configuración ===
fs = 200  # frecuencia de muestreo
duracion = 30  # segundos
total_muestras = fs * duracion

# === Simulador limpio (sin ruido)
def obtener_valor_bioelectrico():
    return -100  # valor constante en mV

# === Guardar eventos cuando presionas ENTER ===
eventos_segundos = []
inicio_tiempo = None

def registrar_evento():
    global eventos_segundos
    print("Presiona Enter cuando toques o quites el dedo.")
    while True:
        input()
        t_actual = time.time() - inicio_tiempo
        eventos_segundos.append(round(t_actual, 2))
        print(f"🕐 Evento registrado en segundo: {round(t_actual, 2)}")

# === Filtros ===
def aplicar_filtros(senal, fs):
    # Notch 60 Hz
    b60, a60 = iirnotch(60, Q=30, fs=fs)
    senal = filtfilt(b60, a60, senal)
    
    # Notch 80 Hz
    b80, a80 = iirnotch(80, Q=30, fs=fs)
    senal = filtfilt(b80, a80, senal)
    
    # Pasa bajas 5 Hz
    b_lp, a_lp = butter(4, 5, btype='low', fs=fs)
    senal = filtfilt(b_lp, a_lp, senal)
    
    return senal

# === Captura ===
print("Iniciando captura de datos...")

bio_signal = []
inicio_tiempo = time.time()

# Hilo para registrar eventos
hilo_eventos = threading.Thread(target=registrar_evento, daemon=True)
hilo_eventos.start()

while len(bio_signal) < total_muestras:
    valor = obtener_valor_bioelectrico()
    bio_signal.append(valor)
    time.sleep(1/fs)

print("✅ Captura finalizada.")

# === Procesamiento ===
tiempos = np.linspace(0, duracion, len(bio_signal))
senal_filtrada = aplicar_filtros(bio_signal, fs)

# === FFT ===
fft = np.abs(np.fft.rfft(senal_filtrada))
frecuencias = np.fft.rfftfreq(len(senal_filtrada), d=1/fs)

# === Gráfica ===
plt.figure(figsize=(12, 6))

plt.subplot(2, 1, 1)
plt.plot(tiempos, senal_filtrada, color='green')
plt.title("Señal Bioeléctrica Filtrada + Eventos")
plt.xlabel("Tiempo (s)")
plt.ylabel("Voltaje (mV)")
for evento in eventos_segundos:
    plt.axvline(x=evento, color='red', linestyle='--', label='Evento' if evento == eventos_segundos[0] else "")
if eventos_segundos:
    plt.legend()

plt.subplot(2, 1, 2)
plt.plot(frecuencias, fft, color='purple')
plt.title("FFT después de Filtros")
plt.xlabel("Frecuencia (Hz)")
plt.ylabel("Magnitud")

plt.tight_layout()
plt.show()

# === Imprimir todos los eventos marcados ===
print("\n📍 Eventos registrados en los segundos:")
for e in eventos_segundos:
    print(f"→ {e} s")

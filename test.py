import matplotlib
matplotlib.use("TkAgg")  # Fix para Windows

import serial
import threading
import time
import matplotlib.pyplot as plt
from collections import deque
import re
import numpy as np
from scipy.signal import iirnotch, butter, filtfilt

# Configuración
puerto_serial = 'COM7'
baudrate = 115200
offset = 1.695
ganancia = 5.97
frecuencia_muestreo = 200  # Hz
duracion_minutos = 5
ventana_muestras = 400

# Buffers
bufferDatos = deque(maxlen=5000)
tiempos_graf = deque([i * (1 / frecuencia_muestreo) for i in range(ventana_muestras)], maxlen=ventana_muestras)
voltajes_graf = deque([0.0] * ventana_muestras, maxlen=ventana_muestras)

bloqueoBuffer = threading.Lock()
tiempoInicio = time.time()

# Filtro notch
f_notch = 60  # Hz
bw = 1       # Ancho de banda en Hz
b_notch, a_notch = iirnotch(f_notch, Q=f_notch / bw, fs=frecuencia_muestreo)

# Filtro pasabajo digital
fc_lowpass = 10  # Hz
orden_lowpass = 4
b_lowpass, a_lowpass = butter(orden_lowpass, fc_lowpass / (0.5 * frecuencia_muestreo), btype='low')

# Hilo lectura serial
def leer_serial():
    try:
        ser = serial.Serial(puerto_serial, baudrate, timeout=2)
        print("✅ Puerto serial abierto correctamente.")
    except serial.SerialException as error:
        print(f"[ERROR] No se pudo abrir el puerto serial: {error}")
        return

    patron_bio = re.compile(r'B:([-+]?\d*\.\d+|\d+)')

    while True:
        try:
            linea = ser.readline().decode('utf-8', errors='ignore').strip()
            if not linea:
                continue

            match_bio = patron_bio.match(linea)
            if match_bio:
                voltaje_bruto = float(match_bio.group(1))
                voltaje_real = (voltaje_bruto - offset) / ganancia
                voltaje_mv = voltaje_real * 1000
                t_rel = time.time() - tiempoInicio

                with bloqueoBuffer:
                    bufferDatos.append((t_rel, voltaje_mv))
        except Exception as e:
            print(f"[ERROR] al procesar línea: {e}")

# Iniciar hilo serial
hilo_serial = threading.Thread(target=leer_serial, daemon=True)
hilo_serial.start()

# --- Gráfica en tiempo real ---
plt.ion()
fig, ax = plt.subplots(figsize=(10, 4))
linea, = ax.plot(tiempos_graf, voltajes_graf, label='Señal reconstruida (mV)')
ax.set_xlabel('Tiempo (s)')
ax.set_ylabel('Voltaje estimado (mV)')
ax.set_title('Señal bioeléctrica en tiempo real (reconstruida)')
ax.grid(True)
ax.legend()

# Captura durante X min
print(f"⏳ Capturando señal por {duracion_minutos:.1f} min...")
duracion_seg = duracion_minutos * 60
t_captura_ini = time.time()

while (time.time() - t_captura_ini) < duracion_seg:
    with bloqueoBuffer:
        if bufferDatos:
            ultimos = list(bufferDatos)[-ventana_muestras:]
            t_vals = [t for t, _ in ultimos]
            v_vals = [v for _, v in ultimos]

            if len(v_vals) > 15:
                v_filtrado = filtfilt(b_lowpass, a_lowpass, v_vals)
            else:
                v_filtrado = v_vals

            tiempos_graf.clear()
            voltajes_graf.clear()
            tiempos_graf.extend(t_vals)
            voltajes_graf.extend(v_filtrado)

    # Actualizar gráfica
    linea.set_xdata(tiempos_graf)
    linea.set_ydata(voltajes_graf)
    if tiempos_graf:
        ax.set_xlim(tiempos_graf[0], tiempos_graf[-1])
        # --- CENTRADO AUTOMÁTICO ---
        media_actual = np.mean(voltajes_graf)
        margen = 10  # mV (más relajado)
        ax.set_ylim(media_actual - margen, media_actual + margen)

    fig.canvas.draw()
    fig.canvas.flush_events()

    time.sleep(1 / frecuencia_muestreo)



# Guardar dataset
nombre_archivo = "dataset_prueba.txt"
with open(nombre_archivo, "w", encoding="utf-8") as f:
    f.write("tiempo,voltaje\n")
    with bloqueoBuffer:
        for t, v in bufferDatos:
            f.write(f"{t:.3f},{v:.3f}\n")

print(f"\n✅ Dataset guardado: {nombre_archivo} ({len(bufferDatos)} muestras)")

# Análisis
diferencias = []
with bloqueoBuffer:
    for i in range(1, len(bufferDatos)):
        delta = bufferDatos[i][1] - bufferDatos[i-1][1]
        diferencias.append(delta)

diferencias_np = np.array(diferencias)
rms = np.sqrt(np.mean(np.square(diferencias_np)))
media_dif = np.mean(diferencias_np)
std_dif = np.std(diferencias_np)

print("\n📊 Análisis del dataset:")
print(f" - RMS de las diferencias: {rms:.3f} mV")
print(f" - Media de las diferencias: {media_dif:.3f} mV")
print(f" - STD de las diferencias: {std_dif:.3f} mV")

# FFT (con filtro notch)
voltajes_np = np.array([v for _, v in bufferDatos])
voltajes_np_notch = filtfilt(b_notch, a_notch, voltajes_np)

fft_result = np.fft.rfft(voltajes_np_notch)
fft_freq = np.fft.rfftfreq(len(voltajes_np_notch), d=1/frecuencia_muestreo)
fft_magnitude = np.abs(fft_result)

freq_pico = fft_freq[np.argmax(fft_magnitude)]
centroide_freq = np.sum(fft_freq * fft_magnitude) / np.sum(fft_magnitude)

bandas = [(0, 5), (5, 10), (10, 20), (20, 50), (50, 100)]
energia_bandas = {}
for (fmin, fmax) in bandas:
    idx = np.where((fft_freq >= fmin) & (fft_freq < fmax))
    energia = np.sum(fft_magnitude[idx])
    energia_bandas[f"{fmin}-{fmax} Hz"] = energia

print("\n⚡ Análisis en frecuencia (FFT) (con filtro notch 60 Hz):")
print(f" - Frecuencia pico dominante: {freq_pico:.2f} Hz")
print(f" - Centroide de frecuencia: {centroide_freq:.2f} Hz")
print(" - Energía por bandas:")
for banda, energia in energia_bandas.items():
    print(f"   > {banda}: {energia:.1f}")

# Histograma
plt.figure(figsize=(8,4))
plt.hist(diferencias_np, bins=100, color='green', alpha=0.7)
plt.title("Histograma de las diferencias entre muestras consecutivas")
plt.xlabel("Δ Voltaje (mV)")
plt.ylabel("Frecuencia")
plt.grid(True)
plt.show()

# Espectro FFT
plt.figure(figsize=(10,5))
plt.plot(fft_freq, fft_magnitude, color='purple')
plt.title("Espectro de frecuencias (FFT)")
plt.xlabel("Frecuencia (Hz)")
plt.ylabel("Magnitud")
plt.grid(True)
plt.xlim(0, 50)
plt.show()

print("\n✅ Fin del análisis.")

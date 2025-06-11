import serial
import matplotlib.pyplot as plt
import time
import threading
from collections import deque

# Configuración
puerto_serial = 'COM7'
baudrate = 115200
frecuencia_muestreo = 200
intervalo = 1 / frecuencia_muestreo
ventana_muestras = 400

offset = 1.7        # en volts
ganancia = 5.94

voltajes = deque([0.0] * ventana_muestras, maxlen=ventana_muestras)
tiempos = deque([i * intervalo for i in range(ventana_muestras)], maxlen=ventana_muestras)
start_time = time.time()

# Hilo para lectura serial
def leer_serial():
    try:
        ser = serial.Serial(puerto_serial, baudrate, timeout=1)
    except serial.SerialException as e:
        print(f"Error al abrir el puerto: {e}")
        return

    while True:
        try:
            linea = ser.readline().decode('utf-8', errors='ignore').strip()
            if linea:
                voltaje_crudo = float(linea)
                voltajes.append(voltaje_crudo)
                tiempos.append(time.time() - start_time)
        except Exception:
            continue

# Hilo de lectura
hilo_serial = threading.Thread(target=leer_serial, daemon=True)
hilo_serial.start()

# Configurar gráfica
plt.ion()
fig, ax = plt.subplots(figsize=(10, 4))
linea, = ax.plot(list(tiempos), list(voltajes), label='Señal reconstruida (mV)')
ax.set_ylim(-500, 500)
ax.set_xlabel('Tiempo (s)')
ax.set_ylabel('Voltaje estimado (mV)')
ax.set_title('Señal bioeléctrica en tiempo real (reconstruida)')
ax.grid(True)
ax.legend()

# Bucle de actualización
try:
    while True:
        voltajes_mv = [((v - offset) / ganancia) * 1000 for v in voltajes]
        linea.set_ydata(voltajes_mv)
        linea.set_xdata(list(tiempos))
        ax.set_xlim(tiempos[0], tiempos[-1])
        if voltajes_mv:
            print(f"Vreal = {voltajes_mv[-1]:.2f} mV")
        fig.canvas.draw()
        fig.canvas.flush_events()
        time.sleep(intervalo)
except KeyboardInterrupt:
    print("Interrumpido.")

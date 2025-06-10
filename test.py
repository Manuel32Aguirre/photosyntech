import serial
import matplotlib.pyplot as plt
import time

# ⚠️ Cambia esto por el puerto COM correcto
puerto_serial = 'COM7'      # ← por ejemplo: COM4, COM5, etc.
baudrate = 115200

# Configuración de lectura
frecuencia_muestreo = 60
intervalo = 1 / frecuencia_muestreo
ventana_muestras = 120

# Intentar abrir el puerto serial
try:
    ser = serial.Serial(puerto_serial, baudrate, timeout=1)
except serial.SerialException as e:
    raise RuntimeError(f"No se pudo abrir el puerto serial {puerto_serial}: {e}")

# Inicializar buffers
tiempo = [i * intervalo for i in range(ventana_muestras)]
voltajes = [0.0] * ventana_muestras

# Gráfica interactiva
plt.ion()
fig, ax = plt.subplots(figsize=(10, 4))
line, = ax.plot(tiempo, voltajes, label='Señal ADC GPIO32 (ESP32)')
ax.set_ylim(0, 3.3)
ax.set_xlabel('Tiempo (s)')
ax.set_ylabel('Voltaje (V)')
ax.set_title('Lectura de señal en tiempo real desde ESP32')
ax.grid(True)
ax.legend()

start_time = time.time()

# Bucle de lectura y graficación
try:
    while True:
        linea = ser.readline().decode('utf-8').strip()
        if linea:
            try:
                voltaje = float(linea)
                voltajes.pop(0)
                voltajes.append(voltaje)

                t = time.time() - start_time
                tiempo = [t - (ventana_muestras - i) * intervalo for i in range(ventana_muestras)]

                line.set_ydata(voltajes)
                line.set_xdata(tiempo)
                ax.set_xlim(tiempo[0], tiempo[-1])
                fig.canvas.draw()
                fig.canvas.flush_events()
                time.sleep(intervalo)
            except ValueError:
                continue
except KeyboardInterrupt:
    print("Interrumpido por el usuario.")
finally:
    ser.close()

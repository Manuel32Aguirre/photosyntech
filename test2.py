import serial

puerto = 'COM7'  # Cambia esto si tu ESP32 usa otro puerto
baudrate = 115200

try:
    ser = serial.Serial(puerto, baudrate, timeout=1)
    print("[OK] Conectado a", puerto)
except serial.SerialException as e:
    print(f"[ERROR] No se pudo abrir el puerto {puerto}: {e}")
    exit()

while True:
    try:
        linea = ser.readline().decode('utf-8', errors='ignore').strip()
        if not linea:
            continue

        # Si es una lectura de sensor, esperar confirmación del usuario
        if "TEMP:" in linea:
            print("🌡️ Temperatura:", linea.split(":")[1], "°C")
            input("Presiona ENTER para continuar...")

        elif "HUM:" in linea:
            print("💧 Humedad relativa:", linea.split(":")[1], "%")
            input("Presiona ENTER para continuar...")

        elif "SOIL:" in linea:
            print("🌱 Humedad del suelo (ADC):", linea.split(":")[1])
            input("Presiona ENTER para continuar...")

        elif "LIGHT:" in linea:
            print("🔆 Luz ambiente (ADC):", linea.split(":")[1])
            input("Presiona ENTER para continuar...")

        else:
            # Intentar interpretar como señal bioeléctrica
            try:
                voltaje = float(linea)
                print("📈 Señal bioeléctrica:", round(voltaje * 1000, 2), "mV")
            except ValueError:
                pass  # Línea ignorada

    except Exception as e:
        print("[ERROR]", e)

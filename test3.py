import sounddevice as sd
import soundfile as sf
import numpy as np
import keyboard
import threading
import queue
import datetime
import time

# CONFIG
DEVICE_ID = 13  # <-- Tu dispositivo que sí graba el sistema
SAMPLERATE = 44100
CHANNELS = 2

# Globals
grabando = False
evento_detener = threading.Event()
cola_audio = queue.Queue()
hilo_grabacion = None

def callback(indata, frames, time_info, status):
    if status:
        print(f"[⚠️] Grabación: {status}")
    if grabando:
        cola_audio.put(indata.copy())

def grabar_audio():
    global evento_detener
    evento_detener.clear()

    print(f"[🎙️] Abriendo stream en dispositivo {DEVICE_ID}...")
    
    try:
        with sd.InputStream(
            device=DEVICE_ID,
            samplerate=SAMPLERATE,
            channels=CHANNELS,
            dtype='float32',
            callback=callback
        ):
            print("[INFO] Stream iniciado")
            
            while grabando:
                sd.sleep(100)
            
            print("[🛑] Stream detenido")
    
    except Exception as e:
        print(f"[❌] Error grabación: {str(e)}")

def guardar_audio():
    if cola_audio.empty():
        print("[⚠️] No se grabó ningún audio.")
        return

    frames = []
    while not cola_audio.empty():
        frames.append(cola_audio.get())

    audio_final = np.concatenate(frames, axis=0)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"grabacion_{timestamp}.wav"
    
    sf.write(filename, audio_final, SAMPLERATE)
    print(f"[✅] Grabado: {filename}")

def main():
    global grabando, hilo_grabacion
    
    print("Presiona ESPACIO para iniciar la grabación.")
    print("Vuelve a presionar ESPACIO para detener, guardar y salir.")
    
    # Esperar primer espacio
    while True:
        if keyboard.is_pressed('space'):
            print("[🎙️] ¡Grabando!")
            grabando = True
            hilo_grabacion = threading.Thread(target=grabar_audio, daemon=True)
            hilo_grabacion.start()
            
            while keyboard.is_pressed('space'):  # Debounce
                time.sleep(0.1)
            
            break
        time.sleep(0.1)
    
    # Ahora está grabando...
    while True:
        if keyboard.is_pressed('space'):
            print("[🛑] Parando y saliendo...")
            grabando = False
            if hilo_grabacion and hilo_grabacion.is_alive():
                hilo_grabacion.join()
            guardar_audio()
            break  # 🚀 salir del programa
        
        time.sleep(0.1)

if __name__ == "__main__":
    main()

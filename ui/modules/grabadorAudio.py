import sounddevice as sd
import soundfile as sf
import threading
import queue
import time

class GrabadorAudio:
    def __init__(self, filename, device_id=None):
        self.filename = filename
        self.device_id = device_id
        self._evento_detener = threading.Event()
        self._cola_audio = queue.Queue()
        self._audio_stream = None
        self._hilo_escritura = None
        self._frames_total = 0

    def iniciar_grabacion(self):
        samplerate = 44100
        self._evento_detener.clear()
        self._frames_total = 0

        dispositivo_valido = False

        if self.device_id is not None:
            try:
                dev_info = sd.query_devices(self.device_id)
                if dev_info['max_input_channels'] > 0:
                    dispositivo_valido = True
                    print(f"Usando dispositivo: {self.device_id} - {dev_info['name']}")
            except Exception as e:
                print(f"Dispositivo guardado inválido: {e}")

        if not dispositivo_valido:
            print("[INFO] Buscando dispositivo válido...")
            for i, dev in enumerate(sd.query_devices()):
                try:
                    if dev['max_input_channels'] > 0:
                        self.device_id = i
                        dispositivo_valido = True
                        print(f"Fallback: usando dispositivo {i}: {dev['name']}")
                        break
                except:
                    continue

        if not dispositivo_valido:
            print("[❌] No se encontró dispositivo de entrada válido")
            return

        def callback(indata, frames, time_info, status):
            if status:
                print(f"Grabación: {status}")
            if not self._evento_detener.is_set():
                self._cola_audio.put(indata.copy())

        try:
            self._audio_stream = sd.InputStream(
                samplerate=samplerate,
                channels=2,
                dtype='float32',
                device=self.device_id,
                callback=callback
            )

            print(f"Abriendo WAV: {self.filename}")

            # Iniciar la escritura
            self._hilo_escritura = threading.Thread(target=self._escribir_audio, daemon=True)
            self._hilo_escritura.start()

            # 👉 Arrancar el stream aquí (NO en otro hilo)
            self._audio_stream.start()
            print("[INFO] Stream iniciado")
            print(f"Grabando en: {self.filename}")

        except Exception as e:
            print(f"[❌] Error iniciando grabación: {str(e)}")

    def detener_grabacion(self):
        print(f"Deteniendo grabación...")
        self._evento_detener.set()

        try:
            if self._audio_stream:
                self._audio_stream.stop()
                self._audio_stream.close()
                self._audio_stream = None
                print("[INFO] Stream detenido y cerrado")
        except Exception as e:
            print(f"[❌] Error deteniendo stream: {e}")

        if self._hilo_escritura and self._hilo_escritura.is_alive():
            self._hilo_escritura.join(timeout=3.0)

        print(f"Grabación finalizada: {self.filename}")
        print(f"Total frames grabados: {self._frames_total}")
        duracion_seg = self._frames_total / 44100
        print(f"Duración estimada: {duracion_seg:.2f} segundos")

    def _escribir_audio(self):
        samplerate = 44100
        try:
            with sf.SoundFile(
                self.filename, mode='w', samplerate=samplerate,
                channels=2, subtype='PCM_16'
            ) as f:
                print(f"[INFO] WAV abierto: escribiendo audio...")
                while not self._evento_detener.is_set() or not self._cola_audio.empty():
                    try:
                        data = self._cola_audio.get(timeout=0.5)
                        data_int16 = (data * 32767).clip(-32768, 32767).astype('int16')
                        f.write(data_int16)
                        self._frames_total += len(data_int16)
                    except queue.Empty:
                        continue
            print(f"WAV guardado correctamente: {self.filename}")
        except Exception as e:
            print(f"[❌] Error escribiendo WAV: {e}")

from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtWidgets import (
    QHBoxLayout, QFrame, QVBoxLayout, QSizePolicy, QLabel, QComboBox, QPushButton
)
from PyQt6.QtGui import QMovie, QIcon
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from ui.fonts import fonts
from ui.modules.Module import Module
import os
from ui.modules import sintesisMusical
import threading
import queue
import sounddevice as sd
import soundfile as sf
import datetime
import numpy as np
import time

UMBRAL_MIN = 10

class MainModule(Module):
    def __init__(self, señal_bio):
        super().__init__()
        self.__signal = señal_bio
        self.__grabando = False
        self.__grabacion_thread = None
        self.__audio_stream = None
        self.__grab_label = QLabel("⏺️ 00:00")
        self.__grab_timer = QTimer()
        self.__mute = False
        self.__main_layout = QHBoxLayout()
        self.__left_frame = QFrame()
        self.__right_frame = QFrame()
        self.__right_frame.setObjectName("rightPanel")
        self.__left_layout = QVBoxLayout(self.__left_frame)
        self.__right_layout = QVBoxLayout(self.__right_frame)

        self.__fig, self.__ax = plt.subplots()
        self.__canvas = FigureCanvas(self.__fig)
        self.__climate_label = QLabel("🌡️ Temp: -- °C")
        self.__humid_label = QLabel("💦 H.rel: --")
        self.__light_label = QLabel("🔆 Luz: -- lux")
        self.__soil_label = QLabel("🌱 Hum.suelo: --")
        self.__estado_label = QLabel("😐 Estado: --")

        self.__combo = QComboBox()
        self.__timer = QTimer()
        self.__tiempos = []
        self.__voltajes = []

        self.__sensor_timer = QTimer()
        self.__sensor_timer.timeout.connect(self.__actualizar_labels_sensores)

        d = os.path.dirname(__file__)
        self.__movie = QMovie(os.path.join(d, "../img/plant.gif"))
        self.__linea, = self.__ax.plot([], [], color="#6BA568", linewidth=1)

        self.__cola_musica = queue.Queue(maxsize=10)
        self.__estado_musical_actual = None
        self.__hilo_musica = threading.Thread(target=self.__hilo_musical_persistente, daemon=True)
        self.__hilo_musica.start()

        self.__archivo_sonido = None
        self.__cola_audio = queue.Queue()
        self.__evento_detener = threading.Event()

        # Configuración de almacenamiento de sensores
        self.frecuencias_sensores = {
            "temperatura": 30,
            "humedad_relativa": 30,
            "iluminacion": 30,
            "humedad_suelo": 30
        }
        self.ultimo_guardado = {
            "temperatura": 0,
            "humedad_relativa": 0,
            "iluminacion": 0,
            "humedad_suelo": 0
        }
        
        # Crear directorio para historial de lecturas si no existe
        self.directorio_historial = "historialLecturas"
        if not os.path.exists(self.directorio_historial):
            os.makedirs(self.directorio_historial)
        
        self.cargar_frecuencias_sensores()
        
        self.setStyleSheet("""
            #rightPanel{background:#0f0f1f;}
            QFrame{background:#1a1a2e;}
            QLabel{color:#e0e0e0;}
            QComboBox{background:#1a1a2e;color:#e0e0e0;
                      border:1px solid #3b3b5e;border-radius:4px;}
        """)
        
        self.__grab_timer.timeout.connect(self.__actualizar_tiempo_grabacion)

    def draw(self):
        self.__main_layout.setContentsMargins(0, 0, 0, 0)
        self.__main_layout.setSpacing(0)
        self.__left_layout.setContentsMargins(10, 10, 10, 10)
        self.__left_layout.setSpacing(10)
        
        toolbar = QFrame()
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setSpacing(10)
        self.__left_layout.addWidget(toolbar)

        self.__canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.__left_layout.addWidget(self.__canvas, 1)

        self.__ax.set_title("Señal Bioeléctrica en tiempo real (200 Hz)")
        self.__ax.set_xlabel("Tiempo (s)")
        self.__ax.set_ylabel("Voltaje estimado (mV)")
        self.__ax.set_ylim(-500, 500)
        self.__ax.set_xlim(0, 10)

        self.__main_layout.addWidget(self.__left_frame, 3)

        self.__right_layout.setContentsMargins(15, 15, 15, 15)
        self.__right_layout.setSpacing(10)

        info = QVBoxLayout()
        for label in [self.__climate_label, self.__humid_label, self.__light_label, self.__soil_label]:
            label.setFont(fonts.TITLE)
            info.addWidget(label)

        info.addWidget(self.__estado_label)
        self.__right_layout.addLayout(info)

        gif = QLabel(alignment=Qt.AlignmentFlag.AlignCenter)
        gif.setMovie(self.__movie)
        self.__movie.setSpeed(50)
        self.__movie.start()
        self.__right_layout.addWidget(gif, 3)

        ctr = QHBoxLayout()
        tonalidades = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        self.__combo.addItems(tonalidades)
        self.__combo.currentTextChanged.connect(self.__actualizar_configuracion_txt)

        tonalidad_inicial = self.__leer_tonalidad_config()
        if tonalidad_inicial in tonalidades:
            self.__combo.setCurrentText(tonalidad_inicial)
        else:
            print(f"[⚠️] Tonalidad desconocida en configuracion.txt → '{tonalidad_inicial}'")

        d = os.path.dirname(__file__)

        self.__btn_grabar = QPushButton()
        self.__btn_grabar.setCheckable(True)
        self.__btn_grabar.setChecked(False)
        self.__btn_grabar.setIcon(QIcon(os.path.join(d, "../img/record.png")))
        self.__btn_grabar.setIconSize(QSize(50, 50))
        self.__btn_grabar.setFixedSize(50, 50)
        self.__btn_grabar.setStyleSheet("""
            QPushButton {
                border-radius: 25px;
                border: 2px solid #3b3b5e;
                background-color: #1a1a2e;
            }
            QPushButton:checked {
                background-color: red;
            }
        """)
        self.__btn_grabar.clicked.connect(self.__toggle_grabacion)

        self.__btn_toggle = QPushButton()
        self.__btn_toggle.setCheckable(True)
        self.__btn_toggle.setChecked(True)
        self.__btn_toggle.setIcon(QIcon(os.path.join(d, "../img/stopMusic.png")))
        self.__btn_toggle.setIconSize(QSize(50, 50))
        self.__btn_toggle.setFixedSize(50, 50)
        self.__btn_toggle.setStyleSheet("""
            QPushButton {
                border-radius: 25px;
                border: 2px solid #3b3b5e;
                background-color: #1a1a2e;
            }
            QPushButton:checked {
                background-color: #3b5e3b;
            }
        """)
        self.__btn_toggle.clicked.connect(self.__toggle_musica)
        
        self.__grab_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.__grab_label.setStyleSheet("font-size: 16px; color: red;")
        self.__grab_label.hide()
        self.__right_layout.addWidget(self.__grab_label)

        ctr.addWidget(self.__combo)
        ctr.addWidget(self.__btn_grabar)
        ctr.addWidget(self.__btn_toggle)
        self.__right_layout.addLayout(ctr)

        self.__main_layout.addWidget(self.__right_frame, 1)
        self.setLayout(self.__main_layout)

        self.__iniciar_actualizacion()

    def __iniciar_actualizacion(self):
        self.__timer.timeout.connect(self.__actualizar_grafica)
        self.__timer.start(5)
        self.__sensor_timer.start(3000)

    def __actualizar_grafica(self):
        nuevos_tiempos, nuevos_voltajes = [], []
        while True:
            tiempo, voltaje = self.__signal.siguiente_valor()
            if tiempo is None:
                break
            nuevos_tiempos.append(tiempo)
            nuevos_voltajes.append(voltaje)

        if not nuevos_tiempos:
            return

        self.__tiempos.extend(nuevos_tiempos)
        self.__voltajes.extend(nuevos_voltajes)

        ventana = 2
        corte = self.__tiempos[-1] - ventana
        while self.__tiempos and self.__tiempos[0] < corte:
            self.__tiempos.pop(0)
            self.__voltajes.pop(0)

        for punto in self.__ax.lines[1:]:
            punto.remove()

        self.__linea.set_data(self.__tiempos, self.__voltajes)
        self.__ax.set_xlim(max(0, corte), self.__tiempos[-1])
        self.__canvas.draw_idle()

        if self.__voltajes:
            voltaje_actual = self.__voltajes[-1]
            voltaje_abs = abs(voltaje_actual)

        if voltaje_abs >= UMBRAL_MIN and not self.__mute:
            if not self.__cola_musica.full():
                tipo = "mayor"
                self.__cola_musica.put(tipo)
                print(f"[🎵 ACTIVIDAD DETECTADA] Voltaje={voltaje_abs:.1f} mV (umbral mínimo {UMBRAL_MIN})")

    def cargar_frecuencias_sensores(self):
        """Carga las frecuencias de almacenamiento desde el archivo de configuración"""
        try:
            if os.path.exists("configuracion.txt"):
                with open("configuracion.txt", "r", encoding="utf-8") as f:
                    for linea in f:
                        linea = linea.strip()
                        if "=" in linea:
                            clave, valor = linea.split("=", 1)
                            clave = clave.strip().lower()
                            
                            # Buscar claves de frecuencia
                            if clave.startswith("frecuencia"):
                                sensor = clave[10:]  # Extrae el nombre del sensor
                                if sensor in self.frecuencias_sensores:
                                    try:
                                        segundos = int(valor.strip())
                                        if segundos < 3:
                                            segundos = 3  # Mínimo 3 segundos
                                        self.frecuencias_sensores[sensor] = segundos
                                        print(f"Frecuencia configurada para {sensor}: {segundos} segundos")
                                    except ValueError:
                                        print(f"Valor inválido para frecuencia{sensor}: {valor}")
        except Exception as e:
            print(f"Error al cargar frecuencias de sensores: {e}")

    def guardar_dato_sensor(self, sensor, valor):
        """Guarda un dato de sensor en su archivo correspondiente, con marca de tiempo"""
        try:
            # Si el valor es "--", no guardar
            if valor == "--":
                return
                
            # Obtener el tiempo actual en segundos
            tiempo_actual = time.time()
            
            # Verificar si ha pasado el tiempo suficiente desde el último guardado
            tiempo_transcurrido = tiempo_actual - self.ultimo_guardado[sensor]
            if tiempo_transcurrido >= self.frecuencias_sensores[sensor]:
                # Crear nombre de archivo en el directorio historialLecturas
                archivo = os.path.join(self.directorio_historial, f"{sensor}.txt")
                
                # Obtener fecha y hora formateada
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Guardar el dato
                with open(archivo, "a", encoding="utf-8") as f:
                    f.write(f"{timestamp},{valor}\n")
                
                # Actualizar el tiempo del último guardado
                self.ultimo_guardado[sensor] = tiempo_actual
                
                print(f"[💾] Dato de {sensor} guardado: {valor} (cada {self.frecuencias_sensores[sensor]}s)")
        except Exception as e:
            print(f"Error al guardar dato de {sensor}: {e}")

    def __leer_tonalidad_config(self):
        """Lee la tonalidad del archivo de configuración con formato clave=valor"""
        try:
            if os.path.exists("configuracion.txt"):
                with open("configuracion.txt", "r", encoding="utf-8") as f:
                    for linea in f:
                        linea = linea.strip()
                        # Buscar con diferentes capitalizaciones
                        if linea.lower().startswith("tonalidad="):
                            return linea.split("=", 1)[1].strip()
        except Exception as e:
            print("[ERROR] No se pudo leer configuracion.txt:", e)
        return "C"

    def __leer_dispositivo_config(self):
        """Lee el ID del dispositivo del archivo de configuración con formato clave=valor"""
        try:
            if os.path.exists("configuracion.txt"):
                with open("configuracion.txt", "r", encoding="utf-8") as f:
                    for linea in f:
                        linea = linea.strip()
                        # Buscar con diferentes capitalizaciones
                        if linea.lower().startswith("dispositivo="):
                            return int(linea.split("=", 1)[1].strip())
        except Exception as e:
            print("[ERROR] No se pudo leer dispositivo de configuracion.txt:", e)
        return None

    def __hilo_musical_persistente(self):
        while True:
            try:
                tipo = self.__cola_musica.get(timeout=1)
                if not self.__estado_musical_actual:
                    print(f"[🎵] Iniciando música en escala {tipo.upper()}")
                    self.__estado_musical_actual = tipo
                    tonalidad = self.__combo.currentText()
                    sintesisMusical.tocar_progresion(tipo_escala=tipo)
            except queue.Empty:
                continue

    def __toggle_musica(self):
        if self.__btn_toggle.isChecked():
            print("[🎵] Música activada manualmente")
            self.__mute = False
            self.__btn_toggle.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "../img/stopMusic.png")))
        else:
            print("[🛑] Música silenciada manualmente")
            sintesisMusical.detener_musica()
            self.__estado_musical_actual = None
            self.__mute = True
            while not self.__cola_musica.empty():
                self.__cola_musica.get()
            self.__btn_toggle.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "../img/startMusic.ico")))

    def __actualizar_configuracion_txt(self, nueva_nota):
        """Actualiza la configuración usando el nuevo formato clave=valor"""
        try:
            config = {}
            # Leer configuración existente si existe
            if os.path.exists("configuracion.txt"):
                with open("configuracion.txt", "r", encoding="utf-8") as f:
                    for linea in f:
                        linea = linea.strip()
                        if linea and "=" in linea:
                            clave, valor = linea.split("=", 1)
                            # Normalizar clave a minúsculas
                            config[clave.strip().lower()] = valor.strip()
            
            # Actualizar tonalidad
            config["tonalidad"] = nueva_nota
            
            # Escribir configuración actualizada
            with open("configuracion.txt", "w", encoding="utf-8") as f:
                for clave, valor in config.items():
                    f.write(f"{clave}={valor}\n")
                
            print(f"[✔] Tonalidad actualizada a '{nueva_nota}' en configuracion.txt")
        except Exception as e:
            print("[ERROR] No se pudo actualizar configuracion.txt:", e)

    def __toggle_grabacion(self):
        if self.__btn_grabar.isChecked():
            print("[🎙️] Comenzando grabación...")
            self.__grabando = True
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            self.__filename = f"grabacion_{timestamp}.wav"
            self.__grab_start_time = datetime.datetime.now()

            self.__grab_label.setText("⏺️ 00:00")
            self.__grab_label.show()
            self.__grab_timer.start(1000)

            dispositivo_id = self.__leer_dispositivo_config()
            
            dispositivo_valido = False
            dispositivo_info = None
            
            if dispositivo_id is not None:
                try:
                    dispositivo_info = sd.query_devices(dispositivo_id)
                    if dispositivo_info['max_input_channels'] > 0:
                        dispositivo_valido = True
                        print(f"Usando dispositivo configurado: {dispositivo_id} - {dispositivo_info['name']}")
                    else:
                        print(f"⚠️ Dispositivo configurado {dispositivo_id} no tiene canales de entrada")
                except Exception as e:
                    print(f"❌ Error con dispositivo configurado {dispositivo_id}: {e}")
            
            if not dispositivo_valido:
                print("Buscando dispositivo de grabación adecuado...")
                dispositivos = sd.query_devices()
                for i, dev in enumerate(dispositivos):
                    try:
                        if dev['max_input_channels'] > 0 and "input" in dev['name'].lower():
                            dispositivo_id = i
                            dispositivo_info = dev
                            dispositivo_valido = True
                            print(f"Seleccionando dispositivo automáticamente: {i} - {dev['name']}")
                            break
                    except:
                        continue
            
            if not dispositivo_valido:
                try:
                    dispositivo_id = sd.default.device[0]
                    dispositivo_info = sd.query_devices(dispositivo_id)
                    if dispositivo_info['max_input_channels'] > 0:
                        dispositivo_valido = True
                        print(f"Usando dispositivo por defecto: {dispositivo_id} - {dispositivo_info['name']}")
                    else:
                        print(f"⚠️ Dispositivo por defecto {dispositivo_id} no tiene canales de entrada")
                except Exception as e:
                    print(f"❌ Error con dispositivo por defecto: {e}")
            
            if not dispositivo_valido:
                print("Buscando cualquier dispositivo de entrada disponible...")
                dispositivos = sd.query_devices()
                for i, dev in enumerate(dispositivos):
                    try:
                        if dev['max_input_channels'] > 0:
                            dispositivo_id = i
                            dispositivo_info = dev
                            dispositivo_valido = True
                            print(f"Usando dispositivo de emergencia: {i} - {dev['name']}")
                            break
                    except:
                        continue
            
            if not dispositivo_valido:
                print("❌ No se encontró ningún dispositivo de entrada válido")
                self.__btn_grabar.setChecked(False)
                self.__grab_label.hide()
                self.__grabando = False
                return

            self.__evento_detener.clear()
            self.__cola_audio = queue.Queue()
            
            self.__grabacion_thread = threading.Thread(
                target=self.__grabar_audio_con_callback,
                args=(self.__filename, dispositivo_id),
                daemon=True
            )
            self.__grabacion_thread.start()

        else:
            print("[🛑] Deteniendo grabación...")
            self.__grabando = False
            self.__grab_timer.stop()
            self.__grab_label.hide()

            self.__evento_detener.set()

            if self.__grabacion_thread and self.__grabacion_thread.is_alive():
                self.__grabacion_thread.join(timeout=3.0)
                print("[✔️] Grabación finalizada")

    def __callback_grabacion(self, indata, frames, time, status):
        if status:
            print(f"Error en grabación: {status}")
        if self.__grabando:
            self.__cola_audio.put(indata.copy())

    def __escribir_audio(self, filename):
        samplerate = 44100
        try:
            print(f"[🔊] Iniciando grabación en {filename}...")
            
            with sf.SoundFile(
                filename, 
                mode='w', 
                samplerate=samplerate, 
                channels=2,
                subtype='PCM_16'
            ) as self.__archivo_sonido:
                
                while not self.__evento_detener.is_set() or not self.__cola_audio.empty():
                    try:
                        data = self.__cola_audio.get(timeout=0.5)
                        self.__archivo_sonido.write(data)
                    except queue.Empty:
                        continue
            
            print(f"[💾] Grabación guardada: {filename}")
            
        except Exception as e:
            print(f"[❌] Error en grabación: {str(e)}")
        finally:
            self.__archivo_sonido = None

    def __grabar_audio_con_callback(self, filename, device_id):
        samplerate = 44100
        self.__evento_detener.clear()
        
        try:
            self.__audio_stream = sd.InputStream(
                samplerate=samplerate,
                channels=2,
                dtype='float32',
                device=device_id,
                callback=self.__callback_grabacion
            )
            
            hilo_escritura = threading.Thread(
                target=self.__escribir_audio,
                args=(filename,),
                daemon=True
            )
            hilo_escritura.start()
            
            self.__audio_stream.start()
            print(f"Stream de audio iniciado en el dispositivo {device_id}")
            
            while self.__grabando:
                sd.sleep(100)
            
            self.__audio_stream.stop()
            self.__audio_stream.close()
            print("Stream de audio detenido")
            
        except Exception as e:
            print(f"[❌] Error en grabación: {str(e)}")
        finally:
            self.__evento_detener.set()
            
            if self.__audio_stream:
                try:
                    self.__audio_stream.stop()
                    self.__audio_stream.close()
                except:
                    pass
                self.__audio_stream = None
            
            if 'hilo_escritura' in locals() and hilo_escritura.is_alive():
                hilo_escritura.join(timeout=2.0)
                print("Hilo de escritura terminado")

    def __actualizar_tiempo_grabacion(self):
        if self.__grabando:
            elapsed = datetime.datetime.now() - self.__grab_start_time
            minutes, seconds = divmod(elapsed.seconds, 60)
            self.__grab_label.setText(f"⏺️ {minutes:02d}:{seconds:02d}")

    def __actualizar_labels_sensores(self):
        temp, hum, light, soil = self.__signal.obtener_datos_sensores()
        self.__climate_label.setText(f"🌡️ Temp: {temp} °C")
        self.__humid_label.setText(f"💦 H.rel: {hum}")
        self.__light_label.setText(f"🔆 Luz: {light} lux")
        self.__soil_label.setText(f"🌱 Hum.suelo: {soil} %")

        try:
            # Guardar datos según frecuencias configuradas
            # Nota: La función guardar_dato_sensor verifica la frecuencia y si el dato es válido (no "--")
            self.guardar_dato_sensor("temperatura", temp)
            self.guardar_dato_sensor("humedad_relativa", hum)
            self.guardar_dato_sensor("iluminacion", light)
            self.guardar_dato_sensor("humedad_suelo", soil)

            # Calcular estado de la planta
            t = float(temp)
            h = float(hum)
            l = float(light)
            s = float(soil)

            porcentaje = min(100.0, (t/35.0*100 + h + l/1000.0*100 + s) / 4)

            if porcentaje < 80:
                self.__estado_label.setText(f"😢 Triste ({porcentaje:.0f}%)")
            else:
                self.__estado_label.setText(f"😊 Feliz ({porcentaje:.0f}%)")

            print(f"[SENSORES] Temp={t}°C, Hum={h}%, Luz={l} lux, Suelo={s}% → Estado={porcentaje:.1f}%")
        except:
            self.__estado_label.setText("😐 Estado: --")
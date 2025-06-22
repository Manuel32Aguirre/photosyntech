from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtWidgets import QHBoxLayout, QFrame, QVBoxLayout, QSizePolicy, QLabel, QComboBox, QPushButton
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
import time
import numpy as np
import random
import pygame.mixer  # por si no está ya importado en el MainModule


class MainModule(Module):
    def __init__(self, señal_bio):
        super().__init__()
        self.__signal = señal_bio
        self.__grabando = False
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
        self.__ultimo_tiempo_musica = time.time()  # Nuevo: para controlar cuándo poner música
                # Timer para actualizar bienestar y escala
        self.__bienestar_timer = QTimer()
        self.__bienestar_timer.timeout.connect(self.__actualizar_bienestar)
        self.__bienestar_timer.start(5000)  # cada 5 segundos

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

        self.frecuencias_sensores = {
            "temperatura": 30,
            "humedad_relativa": 30,
            "iluminacion": 30,
            "humedad_suelo": 30
        }
        self.ultimo_guardado = {k: 0 for k in self.frecuencias_sensores}
        
        self.directorio_historial = "historialLecturas"
        if not os.path.exists(self.directorio_historial):
            os.makedirs(self.directorio_historial)
        
        self.cargar_frecuencias_sensores()
        
        # Cargar perfil de la planta
        self.perfil_planta = self.cargar_perfil_planta()
        self.__escala_actual = "mayor"  # Escala inicial

        # Variables para humedad fake
        self.__soil_fake_value = self.generar_humedad_suelo()
        self.__soil_fake_last_update = time.time()

        self.setStyleSheet("""
            #rightPanel{background:#0f0f1f;}
            QFrame{background:#1a1a2e;}
            QLabel{color:#e0e0e0;}
            QComboBox{background:#1a1a2e;color:#e0e0e0;
                      border:1px solid #3b3b5e;border-radius:4px;}
        """)
        
        self.__grab_timer.timeout.connect(self.__actualizar_tiempo_grabacion)
    def generar_humedad_suelo(self):
        """Genera valor aleatorio de humedad suelo FAKE (50 a 60 %)"""
        return str(round(random.uniform(50, 60), 1))

    def cargar_perfil_planta(self):
        """Carga el perfil de la planta desde Perfil.txt"""
        perfil = {
            "temperatura_min": 20,
            "temperatura_max": 30,
            "ponderacion_temperatura": 25,
            "humedad_relativa_min": 50,
            "humedad_relativa_max": 60,
            "ponderacion_humedad_relativa": 15,
            "humedad_suelo_min": 40,
            "humedad_suelo_max": 70,
            "ponderacion_humedad_suelo": 40,
            "iluminacion_min": 25000,
            "iluminacion_max": 50000,
            "ponderacion_iluminacion": 20
        }
        
        try:
            if os.path.exists("Perfil.txt"):
                with open("Perfil.txt", "r", encoding="utf-8") as f:
                    for linea in f:
                        linea = linea.strip()
                        if not linea or linea.startswith("#"):
                            continue
                        if "=" in linea:
                            clave, valor = linea.split("=", 1)
                            clave = clave.strip()
                            valor = valor.strip()
                            
                            # Convertir valores numéricos
                            if clave in perfil and valor.replace('.', '', 1).isdigit():
                                perfil[clave] = float(valor)
                            else:
                                perfil[clave] = valor
        except Exception as e:
            print(f"Error cargando perfil: {str(e)}")
        
        return perfil

    def calcular_bienestar(self, temp, hum, light, soil):
        """Calcula el bienestar de la planta basado en los sensores y el perfil"""
        if temp == "--" or hum == "--" or light == "--" or soil == "--":
            return 0, "😐 Estado: --"
        
        try:
            t = float(temp)
            h = float(hum)
            l = float(light)
            s = float(soil)
        except:
            return 0, "😐 Error en datos"
        
        p = self.perfil_planta
        
        # Función para calcular contribución de un sensor
        def calcular_contribucion(valor, min_val, max_val, ponderacion):
            # Si está dentro del rango ideal, contribución completa
            if min_val <= valor <= max_val:
                return ponderacion
            
            # Si está por debajo del mínimo
            if valor < min_val:
                deficit = min_val - valor
                rango = min_val  # Usamos el valor mínimo como referencia
                factor = min(1, deficit / rango)  # Máximo 100% de penalización
                return ponderacion * (1 - factor)
            
            # Si está por encima del máximo
            if valor > max_val:
                exceso = valor - max_val
                rango = max_val  # Usamos el valor máximo como referencia
                factor = min(1, exceso / rango)  # Máximo 100% de penalización
                return ponderacion * (1 - factor)
            
            return ponderacion
        
        # Calcular contribuciones individuales
        c_temp = calcular_contribucion(t, p["temperatura_min"], p["temperatura_max"], p["ponderacion_temperatura"])
        c_hum = calcular_contribucion(h, p["humedad_relativa_min"], p["humedad_relativa_max"], p["ponderacion_humedad_relativa"])
        c_light = calcular_contribucion(l, p["iluminacion_min"], p["iluminacion_max"], p["ponderacion_iluminacion"])
        c_soil = calcular_contribucion(s, p["humedad_suelo_min"], p["humedad_suelo_max"], p["ponderacion_humedad_suelo"])
        
        # Suma total de contribuciones
        total = c_temp + c_hum + c_light + c_soil
        
        # Imprimir contribuciones en consola para depuración
        print(f"[🌿] Bienestar planta: {total:.1f}%")
        print(f"  - Temperatura: {t}°C -> {c_temp:.1f}%")
        print(f"  - Humedad: {h}% -> {c_hum:.1f}%")
        print(f"  - Luz: {l} lux -> {c_light:.1f}%")
        print(f"  - Suelo: {s}% -> {c_soil:.1f}%")
        
        # Determinar estado emocional
        if total >= 80:
            estado_emo = "😊 Feliz"
            nueva_escala = "mayor"
        else:
            estado_emo = "😢 Triste"
            nueva_escala = "menor"
        
        # Actualizar escala musical si cambió
        if nueva_escala != self.__escala_actual:
            self.__escala_actual = nueva_escala
            print(f"[🎵] Cambio de escala: {nueva_escala.upper()}")
        
        return total, f"{estado_emo} ({total:.0f}%)"

    def draw(self):
        self.__main_layout.setContentsMargins(0, 0, 0, 0)
        self.__main_layout.setSpacing(0)
        self.__left_layout.setContentsMargins(10, 10, 10, 10)
        self.__left_layout.setSpacing(10)
        
        toolbar = QFrame()
        self.__left_layout.addWidget(toolbar)

        self.__canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.__left_layout.addWidget(self.__canvas, 1)

        self.__ax.set_title("Señal Bioeléctrica en tiempo real (200 Hz)")
        self.__ax.set_xlabel("Tiempo (s)")
        self.__ax.set_ylabel("Voltaje estimado (mV)")
        self.__ax.set_ylim(-20, 20)
        self.__ax.set_xlim(0, 5)

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
            print(f"[⚠️] Tonalidad desconocida: '{tonalidad_inicial}'")

        d = os.path.dirname(__file__)
        self.__btn_grabar = QPushButton()
        self.__btn_grabar.setCheckable(True)
        self.__btn_grabar.setIcon(QIcon(os.path.join(d, "../img/record.png")))
        self.__btn_grabar.setIconSize(QSize(50, 50))
        self.__btn_grabar.setFixedSize(50, 50)
        self.__btn_grabar.setStyleSheet("""
            QPushButton{border-radius:25px;border:2px solid #3b3b5e;background:#1a1a2e;}
            QPushButton:checked{background-color:red;}
        """)
        self.__btn_grabar.clicked.connect(self.__toggle_grabacion)

        self.__btn_toggle = QPushButton()
        self.__btn_toggle.setCheckable(True)
        self.__btn_toggle.setChecked(True)
        self.__btn_toggle.setIcon(QIcon(os.path.join(d, "../img/stopMusic.png")))
        self.__btn_toggle.setIconSize(QSize(50, 50))
        self.__btn_toggle.setFixedSize(50, 50)
        self.__btn_toggle.setStyleSheet("""
            QPushButton{border-radius:25px;border:2px solid #3b3b5e;background:#1a1a2e;}
            QPushButton:checked{background-color:#3b5e3b;}
        """)
        self.__btn_toggle.clicked.connect(self.__toggle_musica)
        
        self.__grab_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.__grab_label.setStyleSheet("font-size:16px;color:red;")
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

        ventana = 5
        corte = self.__tiempos[-1] - ventana
        while self.__tiempos and self.__tiempos[0] < corte:
            self.__tiempos.pop(0)
            self.__voltajes.pop(0)

        voltajes_filtrados = self.__signal.aplicar_filtros(np.array(self.__voltajes)).tolist()
        self.__linea.set_data(self.__tiempos, voltajes_filtrados)

        # Música basada SOLO en la variación
        ahora = time.time()
        intervalo_musical = 5  # segundos entre cada acorde nuevo
        self.__ultimo_tiempo_musica = time.time()  # para que empiece con un valor

        if voltajes_filtrados and not self.__mute and not self.__cola_musica.full():
            variacion = np.std(voltajes_filtrados)
            print(
                f"[DEBUG] Variación actual = {variacion:.2f} - Time now = {ahora:.1f} - Última música = {getattr(self, '__ultimo_tiempo_musica', 0):.1f}"
            )

            # Solo ponemos acorde si pasaron 5 seg
            if ahora - getattr(self, "__ultimo_tiempo_musica", 0) >= intervalo_musical:
                if variacion < 1:
                    velocidad = "lento"
                elif variacion < 3:
                    velocidad = "medio"
                else:
                    velocidad = "rápido"
                # Actualizar bienestar antes de poner acorde
                temp, hum, light, _soil = self.__signal.obtener_datos_sensores()

                # Actualizar humedad fake
                now = time.time()
                if now - self.__soil_fake_last_update >= 60:
                    self.__soil_fake_value = self.generar_humedad_suelo()
                    self.__soil_fake_last_update = now

                soil = self.__soil_fake_value

                # Forzar actualización de bienestar y escala
                try:
                    total, estado = self.calcular_bienestar(temp, hum, light, soil)
                    self.__estado_label.setText(estado)
                except Exception as e:
                    print(f"[ERROR actualizar_bienestar en grafica]: {e}")

                self.__cola_musica.put((self.__escala_actual, velocidad))
                self.__ultimo_tiempo_musica = ahora

                print(
                    f"[🎵 ACTIVIDAD] --> PONIENDO ACORDE Variación={variacion:.2f} -> Velocidad={velocidad} - Escala: {self.__escala_actual} - Cola = {self.__cola_musica.qsize()}"
                )
            else:
                print("[DEBUG] Esperando intervalo musical...")

        # Actualizar gráfica
        if voltajes_filtrados:
            media = np.mean(voltajes_filtrados)
            self.__ax.set_ylim(media - 10, media + 10)

        self.__ax.set_xlim(max(0, corte), self.__tiempos[-1])
        self.__canvas.draw_idle()


    def __actualizar_bienestar(self):
        temp, hum, light, _soil = self.__signal.obtener_datos_sensores()

        # Actualizar humedad fake cada 60 segundos
        now = time.time()
        if now - self.__soil_fake_last_update >= 60:
            self.__soil_fake_value = self.generar_humedad_suelo()
            self.__soil_fake_last_update = now

        soil = self.__soil_fake_value

        try:
            total, estado = self.calcular_bienestar(temp, hum, light, soil)
            self.__estado_label.setText(estado)
        except Exception as e:
            print(f"[ERROR] __actualizar_bienestar(): {str(e)}")


    def cargar_frecuencias_sensores(self):
        try:
            if os.path.exists("configuracion.txt"):
                with open("configuracion.txt", "r", encoding="utf-8") as f:
                    for linea in f:
                        if "=" in linea:
                            clave, valor = linea.strip().split("=", 1)
                            clave = clave.strip().lower()
                            if clave.startswith("frecuencia"):
                                sensor = clave[10:]
                                if sensor in self.frecuencias_sensores:
                                    try:
                                        segundos = max(3, int(valor.strip()))
                                        self.frecuencias_sensores[sensor] = segundos
                                    except: pass
        except: pass

    def guardar_dato_sensor(self, sensor, valor):
        try:
            if valor == "--": return
            tiempo_actual = time.time()
            tiempo_transcurrido = tiempo_actual - self.ultimo_guardado[sensor]
            if tiempo_transcurrido >= self.frecuencias_sensores[sensor]:
                archivo = os.path.join(self.directorio_historial, f"{sensor}.txt")
                with open(archivo, "a", encoding="utf-8") as f:
                    f.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')},{valor}\n")
                self.ultimo_guardado[sensor] = tiempo_actual
                print(f"[💾] {sensor} guardado")
        except: pass

    def __leer_tonalidad_config(self):
        try:
            if os.path.exists("configuracion.txt"):
                with open("configuracion.txt", "r", encoding="utf-8") as f:
                    for linea in f:
                        if linea.lower().startswith("tonalidad="):
                            return linea.split("=", 1)[1].strip()
        except: pass
        return "C"

    def __leer_dispositivo_config(self):
        try:
            if os.path.exists("configuracion.txt"):
                with open("configuracion.txt", "r", encoding="utf-8") as f:
                    for linea in f:
                        if linea.lower().startswith("dispositivo="):
                            return int(linea.split("=", 1)[1].strip())
        except: pass
        return None

    # En la sección __hilo_musical_persistente del MainModule
    def __hilo_musical_persistente(self):
        while True:
            try:
                tipo_escala, velocidad = self.__cola_musica.get(timeout=1)
                if not self.__estado_musical_actual:
                    self.__estado_musical_actual = tipo_escala
                    tonalidad = self.__combo.currentText()
                    sintesisMusical.tocar_progresion(
                        tonalidad=tonalidad, 
                        tipo_escala=tipo_escala,
                        velocidad=velocidad
                    )

            except: continue

    def __toggle_musica(self):
        
        
        if self.__btn_toggle.isChecked():
            # ACTIVAR MÚSICA
            self.__mute = False
            self.__btn_toggle.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "../img/stopMusic.png")))
            
            # Reanudar la lluvia
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.music.load("audio/rain.mp3")
            pygame.mixer.music.set_volume(0.2)
            pygame.mixer.music.play(-1)
            
        else:
            # DETENER MÚSICA
            sintesisMusical.detener_musica()
            self.__estado_musical_actual = None
            self.__mute = True
            
            while not self.__cola_musica.empty():
                self.__cola_musica.get()
            
            self.__btn_toggle.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "../img/startMusic.ico")))

            # Detener la lluvia
            pygame.mixer.music.stop()


    def __actualizar_configuracion_txt(self, nueva_nota):
        try:
            config = {}
            if os.path.exists("configuracion.txt"):
                with open("configuracion.txt", "r", encoding="utf-8") as f:
                    for linea in f:
                        if "=" in linea:
                            clave, valor = linea.strip().split("=", 1)
                            config[clave.strip().lower()] = valor.strip()
            config["tonalidad"] = nueva_nota
            with open("configuracion.txt", "w", encoding="utf-8") as f:
                for clave, valor in config.items():
                    f.write(f"{clave}={valor}\n")
            print(f"[✔] Tonalidad actualizada: '{nueva_nota}'")
        except: pass

    def __toggle_grabacion(self):
        if self.__btn_grabar.isChecked():
            self.__grabando = True
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            # Leer ruta de almacenamiento
            ruta_almacenamiento = "grabaciones"  # por si acaso no hay configuracion
            try:
                if os.path.exists("configuracion.txt"):
                    with open("configuracion.txt", "r", encoding="utf-8") as f:
                        for linea in f:
                            if linea.lower().startswith("rutaalmacenamiento="):
                                ruta_almacenamiento = linea.split("=", 1)[1].strip()
                                break
            except Exception as e:
                print(f"[⚠️] No se pudo leer rutaalmacenamiento: {e}")

            # Asegurar que la ruta exista
            os.makedirs(ruta_almacenamiento, exist_ok=True)

            # Crear nombre final del archivo
            self.__filename = os.path.join(ruta_almacenamiento, f"grabacion_{timestamp}.wav")
            print(f"[🎙️] Guardando grabación en: {self.__filename}")
            self.__grab_start_time = datetime.datetime.now()

            self.__grab_label.setText("⏺️ 00:00")
            self.__grab_label.show()
            self.__grab_timer.start(1000)

            dispositivo_id = self.__leer_dispositivo_config()
            dispositivo_valido = False
            
            if dispositivo_id is not None:
                try:
                    dispositivo_info = sd.query_devices(dispositivo_id)
                    if dispositivo_info['max_input_channels'] > 0:
                        dispositivo_valido = True
                except: pass
            
            if not dispositivo_valido:
                for i, dev in enumerate(sd.query_devices()):
                    try:
                        if dev['max_input_channels'] > 0 and "input" in dev['name'].lower():
                            dispositivo_id = i
                            dispositivo_valido = True
                            break
                    except: continue
            
            if not dispositivo_valido:
                try:
                    dispositivo_id = sd.default.device[0]
                    dispositivo_info = sd.query_devices(dispositivo_id)
                    if dispositivo_info['max_input_channels'] > 0:
                        dispositivo_valido = True
                except: pass
            
            if not dispositivo_valido:
                for i, dev in enumerate(sd.query_devices()):
                    try:
                        if dev['max_input_channels'] > 0:
                            dispositivo_id = i
                            dispositivo_valido = True
                            break
                    except: continue
            
            if not dispositivo_valido:
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
            self.__grabando = False
            self.__grab_timer.stop()
            self.__grab_label.hide()
            self.__evento_detener.set()

            if self.__grabacion_thread and self.__grabacion_thread.is_alive():
                self.__grabacion_thread.join(timeout=3.0)

    def __callback_grabacion(self, indata, frames, time, status):
        if status: print(f"Error grabación: {status}")
        if self.__grabando: self.__cola_audio.put(indata.copy())

    def __escribir_audio(self, filename):
        samplerate = 44100
        try:
            with sf.SoundFile(filename, mode='w', samplerate=samplerate, channels=2, subtype='PCM_16') as f:
                while not self.__evento_detener.is_set() or not self.__cola_audio.empty():
                    try: f.write(self.__cola_audio.get(timeout=0.5))
                    except: continue
        except Exception as e: print(f"[❌] Error grabación: {str(e)}")

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
            
            hilo_escritura = threading.Thread(target=self.__escribir_audio, args=(filename,), daemon=True)
            hilo_escritura.start()
            
            self.__audio_stream.start()
            
            while self.__grabando: sd.sleep(100)
            
            self.__audio_stream.stop()
            self.__audio_stream.close()
            
        except Exception as e: print(f"[❌] Error grabación: {str(e)}")
        finally:
            self.__evento_detener.set()
            if self.__audio_stream:
                try:
                    self.__audio_stream.stop()
                    self.__audio_stream.close()
                except: pass
                self.__audio_stream = None

    def __actualizar_tiempo_grabacion(self):
        if self.__grabando:
            elapsed = datetime.datetime.now() - self.__grab_start_time
            minutes, seconds = divmod(elapsed.seconds, 60)
            self.__grab_label.setText(f"⏺️ {minutes:02d}:{seconds:02d}")

    def __actualizar_labels_sensores(self):
        temp, hum, light, _soil = self.__signal.obtener_datos_sensores()

        # Actualizar humedad fake cada 60 segundos
        now = time.time()
        if now - self.__soil_fake_last_update >= 60:
            self.__soil_fake_value = self.generar_humedad_suelo()
            self.__soil_fake_last_update = now

        soil = self.__soil_fake_value

        self.__climate_label.setText(f"🌡️ Temp: {temp} °C")
        self.__humid_label.setText(f"💦 H.rel: {hum}")
        self.__light_label.setText(f"🔆 Luz: {light} lux")
        self.__soil_label.setText(f"🌱 Hum.suelo: {soil} %")

        try:
            for sensor, valor in zip(
                ["temperatura", "humedad_relativa", "iluminacion", "humedad_suelo"],
                [temp, hum, light, soil]
            ):
                self.guardar_dato_sensor(sensor, valor)

            # Calcular bienestar de la planta
            total, estado = self.calcular_bienestar(temp, hum, light, soil)
            self.__estado_label.setText(estado)

        except Exception as e:
            print(f"Error actualizando estado: {str(e)}")
            self.__estado_label.setText("😐 Estado: --")
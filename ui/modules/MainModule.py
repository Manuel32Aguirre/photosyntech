from PyQt6.QtCore import Qt, QTimer, QSize, QThread, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QFrame, QVBoxLayout, QSizePolicy, QLabel, QComboBox, QPushButton
from PyQt6.QtGui import QMovie, QIcon
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from ui.styles.fonts import fonts
from ui.modules.Module import Module
import os
from ui.modules import sintesisMusical
import threading
import sounddevice as sd
import soundfile as sf
import datetime
import time
import numpy as np
import random
import pygame.mixer
import queue
from collections import deque

class AudioRecorderThread(QThread):
    grabacion_terminada = pyqtSignal(str)
    error_grabacion = pyqtSignal(str)
    
    def __init__(self, filename, dispositivo_id=None, samplerate=44100):
        super().__init__()
        self.filename = filename
        self.dispositivo_id = dispositivo_id
        self.samplerate = samplerate
        self.grabando = False
        self.frames = []
        
    def run(self):
        try:
            def callback(indata, frames, time_info, status):
                if status:
                    print(f"Grabación: {status}")
                if self.grabando:
                    self.frames.append(indata.copy())
            
            with sd.InputStream(
                device=self.dispositivo_id,
                samplerate=self.samplerate,
                channels=2,
                dtype='float32',
                callback=callback
            ):
                self.grabando = True
                while self.grabando:
                    self.msleep(100)
                    
            if self.frames:
                audio_final = np.concatenate(self.frames, axis=0)
                sf.write(self.filename, audio_final, self.samplerate)
                self.grabacion_terminada.emit(self.filename)
            else:
                self.error_grabacion.emit("No se grabó audio")
                
        except Exception as e:
            self.error_grabacion.emit(str(e))
    
    def detener_grabacion(self):
        self.grabando = False

class MusicThread(QThread):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.activo = True
        
    def run(self):
        while self.activo:
            if self.parent._MainModule__mute or not self.parent._MainModule__musica_activa:
                self.msleep(1000)
                continue
            
            try:
                tonalidad = self.parent.obtener_tonalidad_actual()
                tipo_escala = self.parent._MainModule__escala_actual
                
                if len(self.parent._MainModule__voltajes_buffer) >= 1500:
                    voltajes_array = np.array(list(self.parent._MainModule__voltajes_buffer))
                    variacion = np.std(voltajes_array[-50:])
                else:
                    variacion = 0
                    
                sintesisMusical.tocar_un_acorde(
                    tonalidad=tonalidad, 
                    tipo_escala=tipo_escala, 
                    variacion=variacion
                )
            except Exception as e:
                print(f"Error en música: {e}")
                
            self.msleep(500)
    
    def detener(self):
        self.activo = False

class MainModule(Module):
    def __init__(self, señal_bio):
        super().__init__()
        
        self.__config_cache = {}
        self.__config_last_read = 0
        
        self.__signal = señal_bio
        self.__grabando = False
        self.__grab_label = QLabel("⏺️ 00:00")
        self.__grab_timer = QTimer()
        self.__grab_timer.timeout.connect(self.__actualizar_tiempo_grabacion)
        self.__mute = False
        
        self.__tiempos_buffer = deque(maxlen=5000)
        self.__voltajes_buffer = deque(maxlen=5000)
        
        plt.ioff()
        self.__fig, self.__ax = plt.subplots(figsize=(8, 4), dpi=80)
        self.__fig.patch.set_facecolor('#1a1a2e')
        self.__ax.set_facecolor('#1a1a2e')
        self.__canvas = FigureCanvas(self.__fig)
        self.__canvas.setMinimumSize(400, 200)
        
        self.__linea, = self.__ax.plot([], [], color="#6BA568", linewidth=1.5, alpha=0.8)
        self.__ax.grid(True, alpha=0.3)
        
        self.__sensor_timer = QTimer()
        self.__sensor_timer.timeout.connect(self.__actualizar_labels_sensores)
        
        self.__climate_label = QLabel("🌡️ Temp: -- °C")
        self.__humid_label = QLabel("💦 H.rel: --")
        self.__light_label = QLabel("🔆 Luz: -- lux")
        self.__soil_label = QLabel("🌱 Hum.suelo: --")
        self.__estado_label = QLabel("😐 Estado: --")
        
        self.__soil_fake_value = str(round(random.uniform(50, 60), 1))
        self.__soil_fake_last_update = time.time()

        self.__ultimo_tiempo_musica = time.time()
        self.__escala_actual = None
        self.__bienestar_timer = QTimer()
        self.__bienestar_timer.timeout.connect(self.__actualizar_bienestar)
        self.__bienestar_timer.start(10000)
        self.__musica_activa = True
        self.__bienestar_inicializado = False
        self.__music_thread = None
        self.__ultima_tonalidad_usada = self.obtener_tonalidad_actual()
        
        self.__audio_recorder = None

        self.__main_layout = QHBoxLayout()
        self.__left_frame = QFrame()
        self.__right_frame = QFrame()
        self.__right_frame.setObjectName("rightPanel")
        self.__left_layout = QVBoxLayout(self.__left_frame)
        self.__right_layout = QVBoxLayout(self.__right_frame)

        d = os.path.dirname(__file__)
        self.__movie = QMovie(os.path.join(d, "../img/plant.gif"))
        self.__movie.setScaledSize(QSize(200, 200))

        self.__setup_controles_musica()
        self.__setup_controles_grabacion()
        self.__setup_ui()

        self.frecuencias_sensores = {
            "temperatura": 30, "humedad_relativa": 30,
            "iluminacion": 30, "humedad_suelo": 30
        }
        self.ultimo_guardado = {k: 0 for k in self.frecuencias_sensores}
        self.directorio_historial = "historialLecturas"
        os.makedirs(self.directorio_historial, exist_ok=True)
        
        self.cargar_frecuencias_sensores()
        self.perfil_planta = self.cargar_perfil_planta()

        self.setStyleSheet("""
            #rightPanel{background:#0f0f1f;}
            QFrame{background:#1a1a2e;}
            QLabel{color:#e0e0e0; font-family: Arial;}
            QComboBox{background:#1a1a2e;color:#e0e0e0;
                      border:1px solid #3b3b5e;border-radius:4px;
                      padding: 4px;}
            QPushButton{border-radius:25px;border:2px solid #3b3b5e;
                       background:#1a1a2e;}
            QPushButton:checked{background-color:#3b5e3b;}
        """)

        self.__update_counter = 0

    def __setup_ui(self):
        self.__main_layout.setContentsMargins(0, 0, 0, 0)
        self.__main_layout.setSpacing(0)

        self.__left_layout.setContentsMargins(10, 10, 10, 10)
        self.__left_layout.setSpacing(10)
        
        self.__canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.__left_layout.addWidget(self.__canvas, 1)
        
        self.__ax.set_title("Señal Bioeléctrica en tiempo real", color='white', fontsize=12)
        self.__ax.set_xlabel("Tiempo (s)", color='white')
        self.__ax.set_ylabel("Voltaje estimado (mV)", color='white')
        self.__ax.tick_params(colors='white', labelsize=8)
        self.__ax.set_ylim(-20, 20)
        self.__ax.set_xlim(0, 5)
        
        self.__main_layout.addWidget(self.__left_frame, 3)

        self.__right_layout.setContentsMargins(15, 15, 15, 15)
        self.__right_layout.setSpacing(10)
        
        info = QVBoxLayout()
        labels = [self.__climate_label, self.__humid_label, self.__light_label, self.__soil_label]
        for label in labels:
            label.setFont(fonts.TITLE)
            label.setWordWrap(False)
            info.addWidget(label)
        
        info.addWidget(self.__estado_label)
        self.__estado_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.__estado_label.setStyleSheet("font-size: 20px; color: #e0e0e0; font-weight: bold;")
        self.__right_layout.addLayout(info)

        gif_label = QLabel(alignment=Qt.AlignmentFlag.AlignCenter)
        gif_label.setMovie(self.__movie)
        gif_label.setMaximumSize(200, 200)
        self.__movie.setSpeed(30)
        self.__movie.start()
        self.__right_layout.addWidget(gif_label, 2)

        self.__grab_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.__grab_label.setStyleSheet("font-size:16px;color:red;font-weight:bold;")
        self.__grab_label.hide()
        self.__right_layout.addWidget(self.__grab_label)

        ctr = QHBoxLayout()
        ctr.addWidget(self.__combo)
        ctr.addWidget(self.__btn_grabar)
        ctr.addWidget(self.__btn_toggle)
        self.__right_layout.addLayout(ctr)

        self.__main_layout.addWidget(self.__right_frame, 1)
        self.setLayout(self.__main_layout)

        self.__timer = QTimer()
        self.__timer.timeout.connect(self.__actualizar_grafica)
        self.__timer.start(50)
        self.__sensor_timer.start(5000)

    def __setup_controles_musica(self):
        self.__combo = QComboBox()
        self.__combo.setMaximumWidth(80)
        tonalidades = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        self.__combo.addItems(tonalidades)
        self.__combo.currentTextChanged.connect(self.__actualizar_configuracion_txt)
        
        tonalidad_inicial = self.__leer_tonalidad_config()
        if tonalidad_inicial in tonalidades:
            self.__combo.setCurrentText(tonalidad_inicial)
            
        d = os.path.dirname(__file__)
        self.__btn_toggle = QPushButton()
        self.__btn_toggle.setCheckable(True)
        self.__btn_toggle.setChecked(False)
        self.__btn_toggle.setIcon(QIcon(os.path.join(d, "../img/stopMusic.png")))
        self.__btn_toggle.setIconSize(QSize(40, 40))
        self.__btn_toggle.setFixedSize(50, 50)
        self.__btn_toggle.clicked.connect(self.__toggle_musica)

    def __setup_controles_grabacion(self):
        d = os.path.dirname(__file__)
        self.__btn_grabar = QPushButton()
        self.__btn_grabar.setCheckable(True)
        self.__btn_grabar.setIcon(QIcon(os.path.join(d, "../img/record.png")))
        self.__btn_grabar.setIconSize(QSize(40, 40))
        self.__btn_grabar.setFixedSize(50, 50)
        self.__btn_grabar.clicked.connect(self.__toggle_grabacion)

    def cargar_perfil_planta(self):
        perfil = {
            "temperatura_min": 20, "temperatura_max": 30, "ponderacion_temperatura": 25,
            "humedad_relativa_min": 50, "humedad_relativa_max": 60, "ponderacion_humedad_relativa": 15,
            "humedad_suelo_min": 40, "humedad_suelo_max": 70, "ponderacion_humedad_suelo": 40,
            "iluminacion_min": 25000, "iluminacion_max": 50000, "ponderacion_iluminacion": 20
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
                            if clave in perfil and valor.replace('.', '', 1).replace('-', '', 1).isdigit():
                                perfil[clave] = float(valor)
        except Exception as e:
            print(f"Error cargando perfil: {e}")
        
        return perfil

    def calcular_bienestar(self, temp, hum, light, soil):
        if any(val == "--" for val in [temp, hum, light, soil]):
            return 0, "😐 Estado: --"
        
        try: 
            t, h, l, s = float(temp), float(hum), float(light), float(soil)
        except: 
            return 0, "😐 Error en datos"
        
        p = self.perfil_planta
        
        def calcular_contribucion(valor, min_val, max_val, ponderacion):
            if min_val <= valor <= max_val: 
                return ponderacion
            if valor < min_val: 
                return ponderacion * max(0, 1 - (min_val - valor) / min_val)
            return ponderacion * max(0, 1 - (valor - max_val) / max_val)
        
        contribuciones = [
            calcular_contribucion(t, p["temperatura_min"], p["temperatura_max"], p["ponderacion_temperatura"]),
            calcular_contribucion(h, p["humedad_relativa_min"], p["humedad_relativa_max"], p["ponderacion_humedad_relativa"]),
            calcular_contribucion(l, p["iluminacion_min"], p["iluminacion_max"], p["ponderacion_iluminacion"]),
            calcular_contribucion(s, p["humedad_suelo_min"], p["humedad_suelo_max"], p["ponderacion_humedad_suelo"])
        ]
        
        total = sum(contribuciones)
        estado_emo, nueva_escala = ("😊 Feliz", "mayor") if total >= 80 else ("😢 Triste", "menor")
        
        if self.__escala_actual != nueva_escala:
            self.__escala_actual = nueva_escala
            
        if not self.__bienestar_inicializado:
            self.__bienestar_inicializado = True
            self.__iniciar_musica()
        
        return total, f"{estado_emo} ({total:.0f}%)"

    def __actualizar_grafica(self):
        self.__update_counter += 1
        
        nuevos_datos = []
        while True:
            tiempo, voltaje = self.__signal.siguiente_valor()
            if tiempo is None: 
                break
            nuevos_datos.append((tiempo, voltaje))
        
        if not nuevos_datos:
            return
        
        for tiempo, voltaje in nuevos_datos:
            self.__tiempos_buffer.append(tiempo)
            self.__voltajes_buffer.append(voltaje)
        
        if self.__update_counter % 3 != 0:
            return
        
        if not self.__tiempos_buffer:
            return
        
        tiempos_array = np.array(list(self.__tiempos_buffer))
        voltajes_array = np.array(list(self.__voltajes_buffer))
        
        if len(voltajes_array) > 0:
            voltajes_filtrados = self.__signal.aplicar_filtros(voltajes_array)
        else:
            return
        
        self.__linea.set_data(tiempos_array, voltajes_filtrados)
        
        ahora = time.time()
        if (voltajes_filtrados.size > 0 and not self.__mute and 
            ahora - self.__ultimo_tiempo_musica >= 10):
            
            self.__ultimo_tiempo_musica = ahora
            
            if ahora - self.__soil_fake_last_update >= 60:
                self.__soil_fake_value = str(round(random.uniform(50, 60), 1))
                self.__soil_fake_last_update = ahora
            
            try:
                temp, hum, light, _ = self.__signal.obtener_datos_sensores()
                self.actualizar_perfil_y_bienestar(temp, hum, light, self.__soil_fake_value)
            except Exception as e:
                print(f"Error actualizando bienestar: {e}")
        
        if len(voltajes_filtrados) > 0:
            media = np.mean(voltajes_filtrados[-100:])
            self.__ax.set_ylim(media - 10, media + 10)
        
        if len(tiempos_array) > 0:
            tiempo_actual = tiempos_array[-1]
            self.__ax.set_xlim(max(0, tiempo_actual - 5), tiempo_actual)
        
        try:
            self.__canvas.draw_idle()
        except Exception as e:
            print(f"Error dibujando canvas: {e}")

    def actualizar_perfil_y_bienestar(self, temp, hum, light, soil):
        current_time = time.time()
        if current_time - getattr(self, '_last_profile_update', 0) > 30:
            self.perfil_planta = self.cargar_perfil_planta()
            self._last_profile_update = current_time
        
        total, estado = self.calcular_bienestar(temp, hum, light, soil)
        self.__estado_label.setText(estado)
        
        if not self.__bienestar_inicializado:
            self.__bienestar_inicializado = True
            self.__iniciar_musica()
        
        return total

    def __iniciar_musica(self):
        try:
            if not pygame.mixer.get_init(): 
                pygame.mixer.init(buffer=512)
            
            sintesisMusical.iniciar_lluvia()
            self.__mute = False
            self.__btn_toggle.setChecked(True)
            
            d = os.path.dirname(__file__)
            self.__btn_toggle.setIcon(QIcon(os.path.join(d, "../img/stopMusic.png")))
            
            if self.__music_thread is None or not self.__music_thread.isRunning():
                self.__music_thread = MusicThread(self)
                self.__music_thread.start()
                
        except Exception as e:
            print(f"Error iniciando música: {e}")

    def obtener_tonalidad_actual(self):
        return self.__leer_tonalidad_config()

    def __actualizar_bienestar(self):
        try:
            temp, hum, light, _ = self.__signal.obtener_datos_sensores()
            
            now = time.time()
            if now - self.__soil_fake_last_update >= 60:
                self.__soil_fake_value = str(round(random.uniform(50, 60), 1))
                self.__soil_fake_last_update = now
            
            self.actualizar_perfil_y_bienestar(temp, hum, light, self.__soil_fake_value)
        except Exception as e:
            print(f"Error en actualizar_bienestar: {e}")

    def cargar_frecuencias_sensores(self):
        try:
            current_time = time.time()
            if current_time - self.__config_last_read < 30:
                return
            
            self.__config_last_read = current_time
            
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
                                        self.frecuencias_sensores[sensor] = max(3, int(valor.strip()))
                                    except: 
                                        pass
        except Exception as e:
            print(f"Error cargando frecuencias: {e}")

    def guardar_dato_sensor(self, sensor, valor):
        if valor == "--": 
            return
        
        tiempo_actual = time.time()
        if tiempo_actual - self.ultimo_guardado[sensor] >= self.frecuencias_sensores[sensor]:
            try:
                filepath = os.path.join(self.directorio_historial, f"{sensor}.txt")
                with open(filepath, "a", encoding="utf-8") as f:
                    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    f.write(f"{timestamp},{valor}\n")
                self.ultimo_guardado[sensor] = tiempo_actual
            except Exception as e:
                print(f"Error guardando sensor {sensor}: {e}")

    def __leer_tonalidad_config(self):
        try:
            current_time = time.time()
            if ('tonalidad' in self.__config_cache and 
                current_time - self.__config_cache.get('tonalidad_time', 0) < 10):
                return self.__config_cache['tonalidad']
            
            if os.path.exists("configuracion.txt"):
                with open("configuracion.txt", "r", encoding="utf-8") as f:
                    for linea in f:
                        if linea.lower().startswith("tonalidad="):
                            tonalidad = linea.split("=", 1)[1].strip()
                            self.__config_cache['tonalidad'] = tonalidad
                            self.__config_cache['tonalidad_time'] = current_time
                            return tonalidad
        except Exception as e:
            print(f"Error leyendo tonalidad: {e}")
        
        return "C"

    def __leer_dispositivo_config(self):
        try:
            current_time = time.time()
            if ('dispositivo' in self.__config_cache and 
                current_time - self.__config_cache.get('dispositivo_time', 0) < 30):
                return self.__config_cache['dispositivo']
            
            if os.path.exists("configuracion.txt"):
                with open("configuracion.txt", "r", encoding="utf-8") as f:
                    for linea in f:
                        if linea.lower().startswith("dispositivo="):
                            dispositivo = int(linea.split("=", 1)[1].strip())
                            self.__config_cache['dispositivo'] = dispositivo
                            self.__config_cache['dispositivo_time'] = current_time
                            return dispositivo
        except Exception as e:
            print(f"Error leyendo dispositivo: {e}")
        
        return None

    def __toggle_musica(self):
        try:
            if self.__btn_toggle.isChecked():
                self.__mute = False
                d = os.path.dirname(__file__)
                self.__btn_toggle.setIcon(QIcon(os.path.join(d, "../img/stopMusic.png")))
                sintesisMusical.iniciar_lluvia()
                
                if self.__music_thread is None or not self.__music_thread.isRunning():
                    self.__music_thread = MusicThread(self)
                    self.__music_thread.start()
            else:
                sintesisMusical.detener_musica()
                self.__mute = True
                
                if self.__music_thread and self.__music_thread.isRunning():
                    self.__music_thread.detener()
                    
                pygame.mixer.music.stop()
                d = os.path.dirname(__file__)
                self.__btn_toggle.setIcon(QIcon(os.path.join(d, "../img/startMusic.ico")))
        except Exception as e:
            print(f"Error toggle música: {e}")

    def __actualizar_configuracion_txt(self, nueva_nota):
        try:
            self.__config_cache['tonalidad'] = nueva_nota
            self.__config_cache['tonalidad_time'] = time.time()
            
            if os.path.exists("configuracion.txt"):
                nuevas_lineas = []
                tonalidad_actualizada = False
                
                with open("configuracion.txt", "r", encoding="utf-8") as f:
                    for linea in f:
                        if linea.strip().lower().startswith("tonalidad="):
                            nuevas_lineas.append(f"tonalidad={nueva_nota}\n")
                            tonalidad_actualizada = True
                        else: 
                            nuevas_lineas.append(linea)
                
                if not tonalidad_actualizada: 
                    nuevas_lineas.append(f"tonalidad={nueva_nota}\n")
                
                with open("configuracion.txt", "w", encoding="utf-8") as f:
                    f.writelines(nuevas_lineas)
        except Exception as e:
            print(f"Error actualizando configuración: {e}")

    def __toggle_grabacion(self):
        if self.__btn_grabar.isChecked():
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            ruta_almacenamiento = "grabaciones"
            
            try:
                if os.path.exists("configuracion.txt"):
                    with open("configuracion.txt", "r", encoding="utf-8") as f:
                        for linea in f:
                            if linea.lower().startswith("rutaalmacenamiento="):
                                ruta_almacenamiento = linea.split("=", 1)[1].strip()
                                break
            except: 
                pass

            os.makedirs(ruta_almacenamiento, exist_ok=True)
            filename = os.path.join(ruta_almacenamiento, f"grabacion_{timestamp}.wav")
            
            print(f"Iniciando grabación: {filename}")
            

            self.__grabando = True
            self.__grab_start_time = datetime.datetime.now()
            self.__grab_label.setText("⏺️ 00:00")
            self.__grab_label.show()
            self.__grab_timer.start(1000)
            
            dispositivo_id = self.__leer_dispositivo_config()
            self.__audio_recorder = AudioRecorderThread(filename, dispositivo_id)
            self.__audio_recorder.grabacion_terminada.connect(self.__on_grabacion_terminada)
            self.__audio_recorder.error_grabacion.connect(self.__on_error_grabacion)
            self.__audio_recorder.start()
            
        else:
            print("Deteniendo grabación...")
            self.__grabando = False
            self.__grab_timer.stop()
            self.__grab_label.hide()
            
            if self.__audio_recorder and self.__audio_recorder.isRunning():
                self.__audio_recorder.detener_grabacion()
                self.__audio_recorder.wait(3000)

    def __on_grabacion_terminada(self, filename):
        print(f"Grabación guardada: {filename}")

    def __on_error_grabacion(self, error):
        print(f"Error en grabación: {error}")
        self.__grabando = False
        self.__grab_timer.stop()
        self.__grab_label.hide()
        self.__btn_grabar.setChecked(False)

    def __actualizar_tiempo_grabacion(self):
        if not self.__grabando:
            return
            
        try:
            elapsed = datetime.datetime.now() - self.__grab_start_time
            minutes, seconds = divmod(elapsed.seconds, 60)
            self.__grab_label.setText(f"⏺️ {minutes:02d}:{seconds:02d}")
        except Exception as e:
            print(f"Error actualizando tiempo grabación: {e}")

    def __actualizar_labels_sensores(self):
        """Optimizado para reducir overhead"""
        try:
            temp, hum, light, _ = self.__signal.obtener_datos_sensores()
            
            # Actualizar dato fake de suelo
            now = time.time()
            if now - self.__soil_fake_last_update >= 60:
                self.__soil_fake_value = str(round(random.uniform(50, 60), 1))
                self.__soil_fake_last_update = now
            
            soil = self.__soil_fake_value
            
            # Actualizar labels (optimizado)
            self.__climate_label.setText(f"🌡️ Temp: {temp} °C")
            self.__humid_label.setText(f"💦 H.rel: {hum}")
            self.__light_label.setText(f"🔆 Luz: {light} lux")
            self.__soil_label.setText(f"🌱 Hum.suelo: {soil} %")
            
            # Guardar datos y actualizar bienestar
            sensores_data = [
                ("temperatura", temp),
                ("humedad_relativa", hum),
                ("iluminacion", light),
                ("humedad_suelo", soil)
            ]
            
            for sensor, valor in sensores_data:
                self.guardar_dato_sensor(sensor, valor)
            
            self.actualizar_perfil_y_bienestar(temp, hum, light, soil)
            
        except Exception as e:
            print(f"Error actualizando sensores: {e}")

    def closeEvent(self, event):
        """Cleanup al cerrar la aplicación"""
        try:
            # Detener threads
            if self.__music_thread and self.__music_thread.isRunning():
                self.__music_thread.detener()
                self.__music_thread.wait(2000)
            
            if self.__audio_recorder and self.__audio_recorder.isRunning():
                self.__audio_recorder.detener_grabacion()
                self.__audio_recorder.wait(2000)
            
            # Detener timers
            self.__timer.stop()
            self.__sensor_timer.stop()
            self.__bienestar_timer.stop()
            self.__grab_timer.stop()
            
            # Limpiar pygame
            try:
                pygame.mixer.quit()
            except:
                pass
            
            super().closeEvent(event)
            
        except Exception as e:
            print(f"Error al cerrar: {e}")
            event.accept()
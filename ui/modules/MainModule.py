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
import sounddevice as sd
import soundfile as sf
import datetime
import time
import numpy as np
import random
import pygame.mixer
import queue

class MainModule(Module):
    def __init__(self, señal_bio):
        super().__init__()
        self.__signal = señal_bio
        self.__grabando = False
        self.__grab_label = QLabel("⏺️ 00:00")
        self.__grab_timer = QTimer()
        self.__grab_timer.timeout.connect(self.__actualizar_tiempo_grabacion)
        self.__mute = False
        
        self.__fig, self.__ax = plt.subplots()
        self.__canvas = FigureCanvas(self.__fig)
        self.__linea, = self.__ax.plot([], [], color="#6BA568", linewidth=1)
        self.__tiempos = []
        self.__voltajes = []

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
        self.__bienestar_timer.start(5000)
        self.__musica_activa = True
        self.__bienestar_inicializado = False
        self.__hilo_musica = None
        self.__ultima_tonalidad_usada = self.obtener_tonalidad_actual()

        # Layouts y frames
        self.__main_layout = QHBoxLayout()
        self.__left_frame = QFrame()
        self.__right_frame = QFrame()
        self.__right_frame.setObjectName("rightPanel")
        self.__left_layout = QVBoxLayout(self.__left_frame)
        self.__right_layout = QVBoxLayout(self.__right_frame)

        # GIF
        d = os.path.dirname(__file__)
        self.__movie = QMovie(os.path.join(d, "../img/plant.gif"))

        # Botones
        self.__setup_controles_musica(QHBoxLayout())  # crea self.__combo y self.__btn_toggle
        self.__setup_controles_grabacion(QHBoxLayout())  # crea self.__btn_grabar

        # Ahora sí, configuro UI
        self.__setup_ui()

        # Sensores
        self.frecuencias_sensores = {
            "temperatura": 30, "humedad_relativa": 30,
            "iluminacion": 30, "humedad_suelo": 30
        }
        self.ultimo_guardado = {k: 0 for k in self.frecuencias_sensores}
        self.directorio_historial = "historialLecturas"
        os.makedirs(self.directorio_historial, exist_ok=True)
        self.cargar_frecuencias_sensores()
        self.perfil_planta = self.cargar_perfil_planta()

        # Estilo
        self.setStyleSheet("""
            #rightPanel{background:#0f0f1f;}
            QFrame{background:#1a1a2e;}
            QLabel{color:#e0e0e0;}
            QComboBox{background:#1a1a2e;color:#e0e0e0;
                      border:1px solid #3b3b5e;border-radius:4px;}
        """)

    def __setup_ui(self):
        self.__main_layout.setContentsMargins(0, 0, 0, 0)
        self.__main_layout.setSpacing(0)

        # LEFT PANEL (gráfica)
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

        # RIGHT PANEL (labels + gif + botones)
        self.__right_layout.setContentsMargins(15, 15, 15, 15)
        self.__right_layout.setSpacing(10)
        info = QVBoxLayout()
        for label in [self.__climate_label, self.__humid_label, self.__light_label, self.__soil_label]:
            label.setFont(fonts.TITLE)
            info.addWidget(label)
        info.addWidget(self.__estado_label)
        self.__estado_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.__estado_label.setStyleSheet("font-size: 24px; color: #e0e0e0;")
        self.__right_layout.addLayout(info)

        gif = QLabel(alignment=Qt.AlignmentFlag.AlignCenter)
        gif.setMovie(self.__movie)
        self.__movie.setSpeed(50)
        self.__movie.start()
        self.__right_layout.addWidget(gif, 3)

        self.__grab_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.__grab_label.setStyleSheet("font-size:16px;color:red;")
        self.__grab_label.hide()
        self.__right_layout.addWidget(self.__grab_label)

        # Controles (combo tonalidad + grabar + toggle)
        ctr = QHBoxLayout()
        ctr.addWidget(self.__combo)
        ctr.addWidget(self.__btn_grabar)
        ctr.addWidget(self.__btn_toggle)
        self.__right_layout.addLayout(ctr)

        self.__main_layout.addWidget(self.__right_frame, 1)
        self.setLayout(self.__main_layout)

        # Timers
        self.__timer = QTimer()
        self.__timer.timeout.connect(self.__actualizar_grafica)
        self.__timer.start(5)
        self.__sensor_timer.start(3000)

    def __setup_controles_musica(self, ctr):
        self.__combo = QComboBox()
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
        self.__btn_toggle.setIconSize(QSize(50, 50))
        self.__btn_toggle.setFixedSize(50, 50)
        self.__btn_toggle.setStyleSheet(
            "QPushButton{border-radius:25px;border:2px solid #3b3b5e;background:#1a1a2e;} "
            "QPushButton:checked{background-color:#3b5e3b;}"
        )
        self.__btn_toggle.clicked.connect(self.__toggle_musica)

    def __setup_controles_grabacion(self, ctr):
        d = os.path.dirname(__file__)
        self.__btn_grabar = QPushButton()
        self.__btn_grabar.setCheckable(True)
        self.__btn_grabar.setIcon(QIcon(os.path.join(d, "../img/record.png")))
        self.__btn_grabar.setIconSize(QSize(50, 50))
        self.__btn_grabar.setFixedSize(50, 50)
        self.__btn_grabar.setStyleSheet(
            "QPushButton{border-radius:25px;border:2px solid #3b3b5e;background:#1a1a2e;} "
            "QPushButton:checked{background-color:red;}"
        )
        self.__btn_grabar.clicked.connect(self.__toggle_grabacion)


    def __hilo_musical_en_tiempo_real(self):
        while True:
            if self.__mute or not self.__musica_activa:
                time.sleep(1)
                continue
            tonalidad = self.obtener_tonalidad_actual()
            tipo_escala = self.__escala_actual
            try:
                variacion = np.std(np.array(self.__voltajes[-100:])) if len(self.__voltajes) >= 100 else 0
                sintesisMusical.tocar_un_acorde(tonalidad=tonalidad, tipo_escala=tipo_escala, variacion=variacion)
            except: pass
            time.sleep(0.5)

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
                        if not linea or linea.startswith("#"): continue
                        if "=" in linea:
                            clave, valor = linea.split("=", 1)
                            clave = clave.strip()
                            valor = valor.strip()
                            if clave in perfil and valor.replace('.', '', 1).isdigit():
                                perfil[clave] = float(valor)
        except: pass
        return perfil

    def calcular_bienestar(self, temp, hum, light, soil):
        if temp == "--" or hum == "--" or light == "--" or soil == "--":
            return 0, "😐 Estado: --"
        try: t, h, l, s = float(temp), float(hum), float(light), float(soil)
        except: return 0, "😐 Error en datos"
        p = self.perfil_planta
        def calcular_contribucion(valor, min_val, max_val, ponderacion):
            if min_val <= valor <= max_val: return ponderacion
            if valor < min_val: return ponderacion * (1 - min(1, (min_val - valor) / min_val))
            return ponderacion * (1 - min(1, (valor - max_val) / max_val))
        c_temp = calcular_contribucion(t, p["temperatura_min"], p["temperatura_max"], p["ponderacion_temperatura"])
        c_hum = calcular_contribucion(h, p["humedad_relativa_min"], p["humedad_relativa_max"], p["ponderacion_humedad_relativa"])
        c_light = calcular_contribucion(l, p["iluminacion_min"], p["iluminacion_max"], p["ponderacion_iluminacion"])
        c_soil = calcular_contribucion(s, p["humedad_suelo_min"], p["humedad_suelo_max"], p["ponderacion_humedad_suelo"])
        total = c_temp + c_hum + c_light + c_soil
        estado_emo, nueva_escala = ("😊 Feliz", "mayor") if total >= 80 else ("😢 Triste", "menor")
        if self.__escala_actual is None:
            self.__escala_actual = nueva_escala
            if not self.__bienestar_inicializado: 
                self.__bienestar_inicializado = True
                self.__iniciar_musica()
        elif nueva_escala != self.__escala_actual: 
            self.__escala_actual = nueva_escala
        return total, f"{estado_emo} ({total:.0f}%)"

    def __actualizar_grafica(self):
        nuevos_voltajes = []
        while True:
            tiempo, voltaje = self.__signal.siguiente_valor()
            if tiempo is None: break
            self.__tiempos.append(tiempo)
            nuevos_voltajes.append(voltaje)
        if not nuevos_voltajes: return
        self.__voltajes.extend(nuevos_voltajes)
        ventana = 5
        corte = self.__tiempos[-1] - ventana
        while self.__tiempos and self.__tiempos[0] < corte:
            self.__tiempos.pop(0)
            self.__voltajes.pop(0)
        voltajes_filtrados = self.__signal.aplicar_filtros(np.array(self.__voltajes))
        self.__linea.set_data(self.__tiempos, voltajes_filtrados)
        ahora = time.time()
        if voltajes_filtrados.size and not self.__mute and ahora - self.__ultimo_tiempo_musica >= 5:
            variacion = np.std(voltajes_filtrados)
            now = time.time()
            if now - self.__soil_fake_last_update >= 60:
                self.__soil_fake_value = str(round(random.uniform(50, 60), 1))
                self.__soil_fake_last_update = now
            temp, hum, light, _soil = self.__signal.obtener_datos_sensores()
            soil = self.__soil_fake_value
            try: self.actualizar_perfil_y_bienestar(temp, hum, light, soil)
            except: pass
            self.__ultimo_tiempo_musica = ahora
            ton_actual = self.obtener_tonalidad_actual()
            if ton_actual != self.__ultima_tonalidad_usada:
                self.__ultima_tonalidad_usada = ton_actual
        if voltajes_filtrados.size:
            media = np.mean(voltajes_filtrados)
            self.__ax.set_ylim(media - 10, media + 10)
        self.__ax.set_xlim(max(0, corte), self.__tiempos[-1])
        self.__canvas.draw_idle()

    def actualizar_perfil_y_bienestar(self, temp, hum, light, soil):
        self.perfil_planta = self.cargar_perfil_planta()
        total, estado = self.calcular_bienestar(temp, hum, light, soil)
        self.__estado_label.setText(estado)
        if not self.__bienestar_inicializado:
            self.__bienestar_inicializado = True
            self.__iniciar_musica()
        return total

    def __iniciar_musica(self):
        if not pygame.mixer.get_init(): pygame.mixer.init()
        sintesisMusical.iniciar_lluvia()
        self.__mute = False
        self.__btn_toggle.setChecked(True)
        self.__btn_toggle.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "../img/stopMusic.png")))
        if self.__hilo_musica is None or not self.__hilo_musica.is_alive():
            self.__hilo_musica = threading.Thread(target=self.__hilo_musical_en_tiempo_real, daemon=True)
            self.__hilo_musica.start()

    def obtener_tonalidad_actual(self):
        return self.__leer_tonalidad_config()

    def __actualizar_bienestar(self):
        temp, hum, light, _soil = self.__signal.obtener_datos_sensores()
        now = time.time()
        if now - self.__soil_fake_last_update >= 60:
            self.__soil_fake_value = str(round(random.uniform(50, 60), 1))
            self.__soil_fake_last_update = now
        soil = self.__soil_fake_value
        try: self.actualizar_perfil_y_bienestar(temp, hum, light, soil)
        except: pass

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
                                    try: self.frecuencias_sensores[sensor] = max(3, int(valor.strip()))
                                    except: pass
        except: pass

    def guardar_dato_sensor(self, sensor, valor):
        if valor == "--": return
        tiempo_actual = time.time()
        if tiempo_actual - self.ultimo_guardado[sensor] >= self.frecuencias_sensores[sensor]:
            try:
                with open(os.path.join(self.directorio_historial, f"{sensor}.txt"), "a", encoding="utf-8") as f:
                    f.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')},{valor}\n")
                self.ultimo_guardado[sensor] = tiempo_actual
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

    def __toggle_musica(self):
        if self.__btn_toggle.isChecked():
            self.__mute = False
            self.__btn_toggle.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "../img/stopMusic.png")))
            sintesisMusical.iniciar_lluvia()
        else:
            sintesisMusical.detener_musica()
            self.__mute = True
            pygame.mixer.music.stop()
            self.__btn_toggle.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "../img/startMusic.ico")))

    def __actualizar_configuracion_txt(self, nueva_nota):
        try:
            if os.path.exists("configuracion.txt"):
                nuevas_lineas = []
                tonalidad_actualizada = False
                with open("configuracion.txt", "r", encoding="utf-8") as f:
                    for linea in f:
                        if linea.strip().lower().startswith("tonalidad="):
                            nuevas_lineas.append(f"tonalidad={nueva_nota}\n")
                            tonalidad_actualizada = True
                        else: nuevas_lineas.append(linea)
                if not tonalidad_actualizada: nuevas_lineas.append(f"tonalidad={nueva_nota}\n")
                with open("configuracion.txt", "w", encoding="utf-8") as f:
                    f.writelines(nuevas_lineas)
        except: pass

    def __toggle_grabacion(self):
        if self.__btn_grabar.isChecked():
            # EMPEZAR A GRABAR
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            ruta_almacenamiento = "grabaciones"
            try:
                if os.path.exists("configuracion.txt"):
                    with open("configuracion.txt", "r", encoding="utf-8") as f:
                        for linea in f:
                            if linea.lower().startswith("rutaalmacenamiento="):
                                ruta_almacenamiento = linea.split("=", 1)[1].strip()
                                break
            except: pass

            os.makedirs(ruta_almacenamiento, exist_ok=True)
            self.__filename = os.path.join(ruta_almacenamiento, f"grabacion_{timestamp}.wav")
            print(f"[🎙️] Grabando en: {self.__filename}")

            self.__grabando = True
            self.__grab_start_time = datetime.datetime.now()
            self.__grab_label.setText("⏺️ 00:00")
            self.__grab_label.show()
            self.__grab_timer.start(1000)

            dispositivo_id = self.__leer_dispositivo_config()

            self.__cola_audio = queue.Queue()
            self.__evento_detener = threading.Event()

            def callback(indata, frames, time_info, status):
                if status:
                    print(f"[⚠️] Grabación: {status}")
                if self.__grabando:
                    self.__cola_audio.put(indata.copy())

            self.__grabacion_thread = threading.Thread(
                target=self.__grabar_audio_con_callback,
                args=(self.__filename, dispositivo_id, callback),
                daemon=True
            )
            self.__grabacion_thread.start()

        else:
            # PARAR GRABACIÓN
            print("[🛑] Parando grabación...")
            self.__grabando = False
            self.__grab_timer.stop()
            self.__grab_label.hide()
            self.__evento_detener.set()

            if self.__grabacion_thread and self.__grabacion_thread.is_alive():
                self.__grabacion_thread.join()

            self.__guardar_audio(self.__filename)
    def __guardar_audio(self, filename):
        if self.__cola_audio.empty():
            print("[⚠️] No se grabó ningún audio.")
            return

        frames = []
        while not self.__cola_audio.empty():
            frames.append(self.__cola_audio.get())

        audio_final = np.concatenate(frames, axis=0)
        samplerate = 44100

        sf.write(filename, audio_final, samplerate)
        print(f"[✅] Grabación guardada: {filename}")
        


    def __grabar_audio_con_callback(self, filename, dispositivo_id, callback):
        samplerate = 44100
        try:
            with sd.InputStream(
                device=dispositivo_id,
                samplerate=samplerate,
                channels=2,
                dtype='float32',
                callback=callback
            ):
                print("[INFO] Stream iniciado")
                while self.__grabando:
                    sd.sleep(100)
                print("[🛑] Stream detenido")
        except Exception as e:
            print(f"[❌] Error en grabación: {str(e)}")

    def __actualizar_tiempo_grabacion(self):
        elapsed = datetime.datetime.now() - self.__grab_start_time
        minutes, seconds = divmod(elapsed.seconds, 60)
        self.__grab_label.setText(f"⏺️ {minutes:02d}:{seconds:02d}")

    def __actualizar_labels_sensores(self):
        temp, hum, light, _soil = self.__signal.obtener_datos_sensores()
        now = time.time()
        if now - self.__soil_fake_last_update >= 60:
            self.__soil_fake_value = str(round(random.uniform(50, 60), 1))
            self.__soil_fake_last_update = now
        soil = self.__soil_fake_value
        self.__climate_label.setText(f"🌡️ Temp: {temp} °C")
        self.__humid_label.setText(f"💦 H.rel: {hum}")
        self.__light_label.setText(f"🔆 Luz: {light} lux")
        self.__soil_label.setText(f"🌱 Hum.suelo: {soil} %")
        try:
            for sensor, valor in zip(["temperatura", "humedad_relativa", "iluminacion", "humedad_suelo"], [temp, hum, light, soil]):
                self.guardar_dato_sensor(sensor, valor)
            self.actualizar_perfil_y_bienestar(temp, hum, light, soil)
        except: pass

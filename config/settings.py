"""
Constantes y configuraciones por defecto del sistema
"""
class Settings:
    """Configuración centralizada de la aplicación"""
    
    # Aplicación
    APP_NAME = "PhotoSyntech"
    APP_VERSION = "1.0"
    WINDOW_WIDTH = 1280
    WINDOW_HEIGHT = 720
    
    # Simulación
    SIMULATION_CONFIG_FILE = "simulacion.txt"
    USE_REAL_DATA = True  # Cambiar a False para usar datos simulados
    
    # Serial
    DEFAULT_PORT = 'COM7'
    DEFAULT_BAUDRATE = 115200
    SERIAL_TIMEOUT = 2
    
    # Señal Bioeléctrica
    SIGNAL_OFFSET = 1.695
    SIGNAL_GAIN = 5.97
    SAMPLING_FREQUENCY = 200  # Hz
    BUFFER_MAX_SIZE = 5000
    
    # Filtros
    NOTCH_FREQUENCY = 60  # Hz
    NOTCH_BANDWIDTH = 1
    LOWPASS_CUTOFF = 10  # Hz
    LOWPASS_ORDER = 4
    
    # Archivos
    CONFIG_FILE = "configuracion.txt"
    PROFILE_FILE = "Perfil.txt"
    SIMULATION_FILE = "simulacion.txt"
    HISTORY_DIR = "historialLecturas"
    RECORDINGS_DIR = "grabaciones"
    AUDIO_DIR = "audio"
    RAIN_AUDIO = "audio/rain.mp3"
    
    # Sensores - Frecuencias por defecto (segundos)
    DEFAULT_SENSOR_FREQUENCIES = {
        "temperatura": 60,
        "humedad_relativa": 600,
        "iluminacion": 1800,
        "humedad_suelo": 3600
    }
    
    # Música
    DEFAULT_TONALITY = "C"
    MUSIC_VOLUME = 0.2
    MIDI_INSTRUMENT = 92
    TONALITIES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    
    # Perfil de planta por defecto
    DEFAULT_PLANT_PROFILE = {
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
    
    # UI
    UPDATE_INTERVAL_MS = 50  # Milisegundos para actualización de gráfica
    SENSOR_UPDATE_INTERVAL_MS = 5000  # Actualización de sensores
    WELLBEING_UPDATE_INTERVAL_MS = 10000  # Actualización de bienestar
    
    # Gráficas
    GRAPH_DPI = 80
    GRAPH_FIGURE_SIZE = (8, 4)
    GRAPH_TIME_WINDOW = 5  # segundos
    
    # Colors (Tema)
    COLOR_BG_DARK = "#1a1a2e"
    COLOR_BG_PANEL = "#1B1731"
    COLOR_ACCENT_GREEN = "#6BA568"
    COLOR_TEXT = "#e0e0e0"

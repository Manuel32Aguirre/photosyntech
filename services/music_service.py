"""
Servicio de síntesis musical
Encapsula toda la lógica de generación y reproducción de música
"""
import pygame.midi
import pygame.mixer
import random
import time
from PyQt6.QtCore import QThread
from config.settings import Settings
from config.config_manager import ConfigManager


class MusicThread(QThread):
    """Thread separado para música sin bloquear UI"""
    def __init__(self, musicService):
        super().__init__()
        self.musicService = musicService
        self.active = True
    
    def run(self):
        """Ejecuta el loop de música"""
        while self.active:
            if self.musicService.isMuted() or not self.musicService.isMusicActive():
                self.msleep(1000)
                continue
            
            try:
                self.musicService.playSingleChord()
            except Exception as e:
                print(f"Error en música: {e}")
            
            self.msleep(500)
    
    def stop(self):
        """Detiene el thread"""
        self.active = False


class MusicService:
    """Servicio para manejar síntesis musical adaptativa"""
    
    # Escalas por tonalidad
    SCALES = {
        "C":  ([60, 62, 64, 65, 67, 69, 71, 72], [60, 62, 63, 65, 67, 68, 70, 72]),
        "C#": ([61, 63, 65, 66, 68, 70, 72, 73], [61, 63, 64, 66, 68, 69, 71, 73]),
        "D":  ([62, 64, 66, 67, 69, 71, 73, 74], [62, 64, 65, 67, 69, 70, 72, 74]),
        "D#": ([63, 65, 67, 68, 70, 72, 74, 75], [63, 65, 66, 68, 70, 71, 73, 75]),
        "E":  ([64, 66, 68, 69, 71, 73, 75, 76], [64, 66, 67, 69, 71, 72, 74, 76]),
        "F":  ([65, 67, 69, 70, 72, 74, 76, 77], [65, 67, 68, 70, 72, 73, 75, 77]),
        "F#": ([66, 68, 70, 71, 73, 75, 77, 78], [66, 68, 69, 71, 73, 74, 76, 78]),
        "G":  ([67, 69, 71, 72, 74, 76, 78, 79], [67, 69, 70, 72, 74, 75, 77, 79]),
        "G#": ([68, 70, 72, 73, 75, 77, 79, 80], [68, 70, 71, 73, 75, 76, 78, 80]),
        "A":  ([69, 71, 73, 74, 76, 78, 80, 81], [69, 71, 72, 74, 76, 77, 79, 81]),
        "A#": ([70, 72, 74, 75, 77, 79, 81, 82], [70, 72, 73, 75, 77, 78, 80, 82]),
        "B":  ([71, 73, 75, 76, 78, 80, 82, 83], [71, 73, 74, 76, 78, 79, 81, 83]),
    }
    
    # Calidades de acordes por tipo de escala
    CHORD_QUALITIES = {
        "mayor": ["mayor", "menor", "menor", "mayor", "mayor", "menor", "disminuido"],
        "menor": ["menor", "disminuido", "mayor", "menor", "menor", "mayor", "mayor"]
    }
    
    # Intervalos de acordes
    CHORD_INTERVALS = {
        "mayor": [0, 4, 7],
        "menor": [0, 3, 7],
        "disminuido": [0, 3, 6]
    }
    
    RANGE_MIN = 48
    RANGE_MAX = 60
    
    def __init__(self):
        self.configManager = ConfigManager()
        self.player = None
        self.muted = False
        self.musicActive = False
        self.currentScaleType = None
        self.musicThread = None
        
        # Inicializar MIDI
        self._initMidi()
    
    def _initMidi(self):
        """Inicializa el sistema MIDI"""
        try:
            pygame.midi.init()
            self.player = pygame.midi.Output(0)
            self.player.set_instrument(Settings.MIDI_INSTRUMENT, channel=0)
        except Exception as e:
            print(f"Error inicializando MIDI: {e}")
    
    def startRainAmbient(self):
        """Inicia el sonido ambiental de lluvia"""
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(buffer=512)
            
            pygame.mixer.music.load(Settings.RAIN_AUDIO)
            pygame.mixer.music.set_volume(Settings.MUSIC_VOLUME)
            pygame.mixer.music.play(-1)
            print("Lluvia iniciada")
        except Exception as e:
            print(f"Error iniciando lluvia: {e}")
    
    def stopRainAmbient(self):
        """Detiene el sonido ambiental"""
        try:
            pygame.mixer.music.stop()
        except Exception as e:
            print(f"Error deteniendo lluvia: {e}")
    
    def startMusic(self, scaleType: str = "mayor"):
        """
        Inicia la música adaptativa
        
        Args:
            scaleType: Tipo de escala ("mayor" o "menor")
        """
        if self.musicActive:
            return
        
        self.currentScaleType = scaleType
        self.musicActive = True
        self.muted = False
        
        self.startRainAmbient()
        
        # Iniciar thread de música
        if self.musicThread is None or not self.musicThread.isRunning():
            self.musicThread = MusicThread(self)
            self.musicThread.start()
    
    def stopMusic(self):
        """Detiene la música"""
        self.musicActive = False
        self.muted = True
        
        self.stopRainAmbient()
        
        if self.musicThread and self.musicThread.isRunning():
            self.musicThread.stop()
            self.musicThread.wait(2000)
        
        self._turnOffAllNotes()
    
    def toggleMute(self):
        """Alterna el estado de silencio"""
        self.muted = not self.muted
        
        if self.muted:
            self.stopRainAmbient()
            self._turnOffAllNotes()
        else:
            self.startRainAmbient()
    
    def setScaleType(self, scaleType: str):
        """Establece el tipo de escala (mayor/menor)"""
        if scaleType in ["mayor", "menor"]:
            self.currentScaleType = scaleType
    
    def isMuted(self) -> bool:
        """Verifica si está silenciado"""
        return self.muted
    
    def isMusicActive(self) -> bool:
        """Verifica si la música está activa"""
        return self.musicActive
    
    def playSingleChord(self, variation: float = 0):
        """
        Toca un acorde basado en el estado actual
        
        Args:
            variation: Variación de la señal para adaptar el sonido
        """
        if not self.player or self.muted:
            return
        
        tonality = self.configManager.get_tonality()
        scaleType = self.currentScaleType or "mayor"
        
        # Generar acorde
        tones = self.SCALES.get(tonality, self.SCALES["C"])
        scale = tones[0] if scaleType == "mayor" else tones[1]
        
        # Seleccionar grado aleatorio
        degree = random.randint(0, 6)
        baseNote = scale[degree]
        
        # Calidad del acorde
        qualities = self.CHORD_QUALITIES[scaleType]
        quality = qualities[degree % 7]
        
        # Generar notas del acorde
        chord = self._generateChord(baseNote, quality)
        
        # Tocar acorde
        for note in chord:
            self.player.note_on(note, 80, 0)
    
    def _generateChord(self, base: int, quality: str) -> list:
        """Genera un acorde con las notas apropiadas"""
        if quality not in self.CHORD_INTERVALS:
            quality = "mayor"
        
        chord = [base + interval for interval in self.CHORD_INTERVALS[quality]]
        return self._adjustRange(chord)
    
    def _adjustRange(self, chord: list) -> list:
        """Ajusta el rango de notas del acorde"""
        while max(chord) > self.RANGE_MAX:
            chord = [n - 12 for n in chord]
        while min(chord) < self.RANGE_MIN:
            chord = [n + 12 for n in chord]
        return chord
    
    def _turnOffAllNotes(self):
        """Apaga todas las notas MIDI"""
        if not self.player:
            return
        
        try:
            for note in range(128):
                self.player.note_off(note, 0, 0)
        except Exception as e:
            print(f"Error apagando notas: {e}")
    
    def cleanup(self):
        """Limpia recursos"""
        self.stopMusic()
        
        try:
            if self.player:
                pygame.midi.quit()
            pygame.mixer.quit()
        except:
            pass

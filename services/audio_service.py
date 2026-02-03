"""
Servicio de grabación de audio
Encapsula toda la lógica de grabación
"""
import os
import datetime
import sounddevice as sd
import soundfile as sf
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal
from config.config_manager import ConfigManager
from config.settings import Settings


class AudioRecorderThread(QThread):
    """Thread separado para grabación de audio sin bloquear UI"""
    recordingFinished = pyqtSignal(str)
    recordingError = pyqtSignal(str)
    
    def __init__(self, filename: str, deviceId: int = None, samplerate: int = 44100):
        super().__init__()
        self.filename = filename
        self.deviceId = deviceId
        self.samplerate = samplerate
        self.isRecording = False
        self.frames = []
    
    def run(self):
        """Ejecuta la grabación"""
        try:
            def callback(indata, frames, timeInfo, status):
                if status:
                    print(f"[⚠️] Grabación: {status}")
                if self.isRecording:
                    self.frames.append(indata.copy())
            
            with sd.InputStream(
                device=self.deviceId,
                samplerate=self.samplerate,
                channels=2,
                dtype='float32',
                callback=callback
            ):
                self.isRecording = True
                while self.isRecording:
                    self.msleep(100)
            
            # Guardar audio
            if self.frames:
                audioFinal = np.concatenate(self.frames, axis=0)
                sf.write(self.filename, audioFinal, self.samplerate)
                self.recordingFinished.emit(self.filename)
            else:
                self.recordingError.emit("No se grabó audio")
                
        except Exception as e:
            self.recording_error.emit(str(e))
    
    def stopRecording(self):
        """Detiene la grabación"""
        self.isRecording = False


class AudioService:
    """Servicio para manejar grabación de audio"""
    
    def __init__(self):
        self.configManager = ConfigManager()
        self.recorderThread = None
        self.isRecording = False
        self.recordingStartTime = None
    
    def startRecording(self) -> tuple[AudioRecorderThread, str]:
        """
        Inicia una grabación de audio
        
        Returns:
            Tuple (thread, filename)
        """
        if self.isRecording:
            raise RuntimeError("Ya hay una grabación en progreso")
        
        # Generar nombre de archivo
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        storagePath = self.configManager.get_storage_path()
        
        # Crear directorio si no existe
        os.makedirs(storagePath, exist_ok=True)
        
        filename = os.path.join(storagePath, f"grabacion_{timestamp}.wav")
        
        # Obtener dispositivo configurado
        deviceId = self.configManager.get_device_id()
        
        # Crear y empezar thread
        self.recorderThread = AudioRecorderThread(filename, deviceId)
        self.isRecording = True
        self.recordingStartTime = datetime.datetime.now()
        
        print(f"[🎙️] Iniciando grabación: {filename}")
        
        return self.recorderThread, filename
    
    def stopRecording(self):
        """Detiene la grabación actual"""
        if not self.isRecording or not self.recorderThread:
            return
        
        print("[🛑] Deteniendo grabación...")
        
        self.recorderThread.stopRecording()
        self.recorderThread.wait(3000)
        
        self.isRecording = False
        self.recordingStartTime = None
    
    def getRecordingDuration(self) -> float:
        """
        Obtiene la duración de la grabación actual en segundos
        
        Returns:
            Duración en segundos
        """
        if not self.recordingStartTime:
            return 0.0
        
        elapsed = datetime.datetime.now() - self.recordingStartTime
        return elapsed.total_seconds()
    
    def isRecordingActive(self) -> bool:
        """Verifica si hay una grabación activa"""
        return self.isRecording
    
    @staticmethod
    def getAvailableDevices() -> list:
        """
        Obtiene la lista de dispositivos de audio disponibles
        
        Returns:
            Lista de tuplas (id, nombre) de dispositivos con entrada
        """
        try:
            devices = sd.query_devices()
            available = []
            
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    available.append((i, device['name']))
            
            return available
        except Exception as e:
            print(f"Error obteniendo dispositivos: {e}")
            return []

"""
Procesador de señales bioeléctricas
Encapsula toda la lógica de filtrado y procesamiento
"""
import numpy as np
from scipy.signal import iirnotch, butter, filtfilt
from config.settings import Settings


class SignalProcessor:
    """Procesador de señales bioeléctricas con filtros configurables"""
    
    def __init__(self):
        self.fs = Settings.SAMPLING_FREQUENCY
        self._setupFilters()
    
    def _setupFilters(self):
        """Configura los filtros de señal"""
        # Filtro notch (elimina ruido de línea eléctrica)
        fNotch = Settings.NOTCH_FREQUENCY
        bw = Settings.NOTCH_BANDWIDTH
        self.bNotch, self.aNotch = iirnotch(
            fNotch, 
            Q=fNotch/bw, 
            fs=self.fs
        )
        
        # Filtro pasa-bajos
        fc = Settings.LOWPASS_CUTOFF
        order = Settings.LOWPASS_ORDER
        self.bLowpass, self.aLowpass = butter(
            order, 
            fc/(0.5*self.fs), 
            btype='low'
        )
    
    def convertRawToMv(self, rawVoltage: float, offset: float = None, gain: float = None) -> float:
        """
        Convierte voltaje bruto a milivoltios
        
        Args:
            raw_voltage: Voltaje bruto del sensor
            offset: Offset de calibración
            gain: Ganancia del amplificador
            
        Returns:
            Voltaje en milivoltios
        """
        offset = offset or Settings.SIGNAL_OFFSET
        gain = gain or Settings.SIGNAL_GAIN
        
        voltageReal = (rawVoltage - offset) / gain
        return voltageReal * 1000
    
    def applyFilters(self, signal: np.ndarray) -> np.ndarray:
        """
        Aplica filtros a la señal
        
        Args:
            signal: Array de señal a filtrar
            
        Returns:
            Señal filtrada
        """
        if len(signal) < 15:
            return signal
        
        try:
            # Aplicar filtro notch
            signalFiltered = filtfilt(self.bNotch, self.aNotch, signal)
            # Aplicar filtro pasa-bajos
            signalFiltered = filtfilt(self.bLowpass, self.aLowpass, signalFiltered)
            return signalFiltered
        except Exception as e:
            print(f"Error aplicando filtros: {e}")
            return signal
    
    def calculateFeatures(self, signal: np.ndarray) -> dict:
        """
        Calcula características de la señal para análisis
        
        Args:
            signal: Array de señal
            
        Returns:
            Diccionario con características calculadas
        """
        if len(signal) < 100:
            return None
        
        try:
            # Aplicar filtros primero
            signalFiltered = self.applyFilters(signal)
            
            # Calcular diferencias
            differences = np.diff(signalFiltered)
            
            # Métricas temporales
            rms = np.sqrt(np.mean(np.square(differences)))
            mean = np.mean(differences)
            std = np.std(differences)
            
            # FFT para análisis frecuencial
            fftResult = np.fft.rfft(signalFiltered)
            fftFreq = np.fft.rfftfreq(len(signalFiltered), d=1/self.fs)
            fftMagnitude = np.abs(fftResult)
            
            # Centroide espectral
            centroid = np.sum(fftFreq * fftMagnitude) / np.sum(fftMagnitude)
            
            # Energía por bandas de frecuencia
            bands = [(0, 5), (5, 10), (10, 20), (20, 50), (50, 100)]
            bandEnergy = {}
            
            for fmin, fmax in bands:
                idx = np.where((fftFreq >= fmin) & (fftFreq < fmax))
                energy = np.sum(fftMagnitude[idx])
                bandEnergy[f"{fmin}-{fmax}Hz"] = energy
            
            return {
                "rms": rms,
                "mean": mean,
                "std": std,
                "spectral_centroid": centroid,
                "band_energy": bandEnergy
            }
        except Exception as e:
            print(f"Error calculando features: {e}")
            return None

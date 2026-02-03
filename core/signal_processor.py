import numpy as np
from scipy.signal import iirnotch, butter, filtfilt
from config.settings import Settings


class SignalProcessor:
    
    def __init__(self):
        self.fs = Settings.SAMPLING_FREQUENCY
        self._setupFilters()
    
    def _setupFilters(self):
        fNotch = Settings.NOTCH_FREQUENCY
        bw = Settings.NOTCH_BANDWIDTH
        self.bNotch, self.aNotch = iirnotch(
            fNotch, 
            Q=fNotch/bw, 
            fs=self.fs
        )
        
        fc = Settings.LOWPASS_CUTOFF
        order = Settings.LOWPASS_ORDER
        self.bLowpass, self.aLowpass = butter(
            order, 
            fc/(0.5*self.fs), 
            btype='low'
        )
    
    def convertRawToMv(self, rawVoltage: float, offset: float = None, gain: float = None) -> float:
        offset = offset or Settings.SIGNAL_OFFSET
        gain = gain or Settings.SIGNAL_GAIN
        
        voltageReal = (rawVoltage - offset) / gain
        return voltageReal * 1000
    
    def applyFilters(self, signal: np.ndarray) -> np.ndarray:
        if len(signal) < 15:
            return signal
        
        try:
            signalFiltered = filtfilt(self.bNotch, self.aNotch, signal)
            signalFiltered = filtfilt(self.bLowpass, self.aLowpass, signalFiltered)
            return signalFiltered
        except Exception as e:
            print(f"Error aplicando filtros: {e}")
            return signal
    
    def calculateFeatures(self, signal: np.ndarray) -> dict:
        if len(signal) < 100:
            return None
        
        try:
            signalFiltered = self.applyFilters(signal)
            differences = np.diff(signalFiltered)
            
            rms = np.sqrt(np.mean(np.square(differences)))
            mean = np.mean(differences)
            std = np.std(differences)
            
            fftResult = np.fft.rfft(signalFiltered)
            fftFreq = np.fft.rfftfreq(len(signalFiltered), d=1/self.fs)
            fftMagnitude = np.abs(fftResult)
            
            centroid = np.sum(fftFreq * fftMagnitude) / np.sum(fftMagnitude)
            
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

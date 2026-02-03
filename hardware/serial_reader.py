"""
Lector de puerto serial para comunicación con ESP32
Maneja la adquisición de datos del hardware o simulación
"""
import serial
import threading
import time
import re
from collections import deque
from config.settings import Settings
from config.simulation_config import SimulationConfig
from core.signal_processor import SignalProcessor
from core.sensor_manager import SensorManager


class SerialReader:
    """Lector de datos desde puerto serial (ESP32) o simulador"""
    
    def __init__(
        self,
        port: str = None,
        baudrate: int = None,
        sensorManager: SensorManager = None
    ):
        self.port = port or Settings.DEFAULT_PORT
        self.baudrate = baudrate or Settings.DEFAULT_BAUDRATE
        self.sensorManager = sensorManager or SensorManager()
        self.signalProcessor = SignalProcessor()
        self.simulationConfig = SimulationConfig()
        self.usarDatosReales = self.simulationConfig.debeUsarDatosReales()
        
        # Buffer de datos bioélectricos
        self.bioBuffer = deque(maxlen=Settings.BUFFER_MAX_SIZE)
        self.bufferLock = threading.Lock()
        
        # Estado
        self.serialConnection = None
        self.readerThread = None
        self.isRunning = False
        self.startTime = time.time()
        
        # Patrones de regex para parsing
        self.bioPattern = re.compile(r'B:([-+]?\d*\.\d+|\d+)')
        self.sensorPattern = re.compile(r'T:([^,]+),H:([^,]+),L:([^,]+),S:([^,]+)')
        
        # Iniciar conexión o simulación
        self._connect()
    
    def _connect(self):
        """Establece conexión serial o modo simulación"""
        if not self.usarDatosReales:
            # Modo simulación
            print("🎮 Modo SIMULACIÓN activado - Generando datos aleatorios")
            print(f"   Revisa {Settings.SIMULATION_FILE} para configurar rangos")
            self.serialConnection = None
            self.isRunning = True
            self.readerThread = threading.Thread(target=self._simulationLoop, daemon=True)
            self.readerThread.start()
            return
        
        # Modo real - intentar conectar
        try:
            self.serialConnection = serial.Serial(
                self.port,
                self.baudrate,
                timeout=Settings.SERIAL_TIMEOUT
            )
            print(f"✅ Puerto serial {self.port} abierto correctamente")
            self.isRunning = True
            self.readerThread = threading.Thread(target=self._serialLoop, daemon=True)
            self.readerThread.start()
        except serial.SerialException as e:
            print(f"[ERROR] No se pudo abrir el puerto serial: {e}")
            print("   Revisa configuracion.txt o activa modo simulación en simulacion.txt")
            self.serialConnection = None
    
    def _serialLoop(self):
        """Loop principal de lectura de datos REALES"""
        time.sleep(2)  # Esperar inicialización
        
        while self.isRunning:
            try:
                if self.serialConnection is None:
                    time.sleep(1)
                    continue
                
                # Leer línea
                line = self.serialConnection.readline().decode('utf-8', errors='ignore').strip()
                
                if not line:
                    continue
                
                # Intentar parsear como señal bioeléctrica
                bioMatch = self.bioPattern.match(line)
                if bioMatch:
                    self._processBioSignal(float(bioMatch.group(1)), isSimulated=False)
                    continue
                
                # Intentar parsear como datos de sensores
                sensorMatch = self.sensorPattern.search(line)
                if sensorMatch:
                    temp, hum, light, soil = sensorMatch.groups()
                    self.sensorManager.updateAllSensors(temp, hum, light, soil)
                    continue
                    
            except Exception as e:
                print(f"[ERROR] al procesar línea serial: {e}")
    
    def _simulationLoop(self):
        """Loop de simulación de datos"""
        print("🔄 Loop de simulación iniciado...")
        
        while self.isRunning:
            try:
                # Generar señal bioeléctrica (alta frecuencia - 200Hz)
                voltajeMv = self.simulationConfig.generarVoltajeBioelectrico()
                self._processBioSignal(voltajeMv, isSimulated=True)
                
                # Generar datos de sensores (baja frecuencia)
                if self.simulationConfig.deberiActualizarSensores():
                    temp, hum, light, soil = self.simulationConfig.generarDatosSensores()
                    self.sensorManager.updateAllSensors(temp, hum, light, soil)
                
                # Dormir para mantener frecuencia de 200Hz
                time.sleep(1.0 / 200.0)
                
            except Exception as e:
                print(f"[ERROR] en simulación: {e}")
                time.sleep(0.1)
    
    def _processBioSignal(self, rawVoltage: float, isSimulated: bool = False):
        """Procesa una lectura de señal bioeléctrica"""
        # Convertir a mV (si es real, si es simulado ya está en mV)
        if isSimulated:
            voltageMv = rawVoltage
        else:
            voltageMv = self.signalProcessor.convertRawToMv(rawVoltage)
        
        # Calcular tiempo relativo
        relativeTime = time.time() - self.startTime
        
        # Guardar en buffer
        with self.bufferLock:
            self.bioBuffer.append((relativeTime, voltageMv))
    
    def start(self):
        """Inicia la lectura (compatibilidad - ya se inicia en __init__)"""
        if not self.isRunning and self.readerThread is None:
            self._connect()
    
    def getNextBioValue(self) -> tuple:
        """
        Obtiene el siguiente valor del buffer
        
        Returns:
            Tupla (tiempo, voltaje) o (None, None) si no hay datos
        """
        with self.bufferLock:
            if self.bioBuffer:
                return self.bioBuffer.popleft()
        return (None, None)
    
    def getBufferCopy(self) -> list:
        """Obtiene una copia del buffer completo"""
        with self.bufferLock:
            return list(self.bioBuffer)
    
    def isConnected(self) -> bool:
        """Verifica si está conectado o en modo simulación"""
        if not self.usarDatosReales:
            return True  # Simulación siempre está "conectada"
        return self.serialConnection is not None and self.serialConnection.is_open
    
    def getModoOperacion(self) -> str:
        """Obtiene el modo de operación actual"""
        return "SIMULACIÓN" if not self.usarDatosReales else "HARDWARE REAL"
    
    def disconnect(self):
        """Cierra la conexión serial o detiene simulación"""
        self.isRunning = False
        
        if self.readerThread:
            self.readerThread.join(timeout=2)
        
        if self.serialConnection and self.serialConnection.is_open:
            try:
                self.serialConnection.close()
                print("Puerto serial cerrado")
            except Exception as e:
                print(f"Error cerrando puerto serial: {e}")
        else:
            print("Simulación detenida")
    
    def __del__(self):
        """Destructor para asegurar limpieza"""
        self.disconnect()

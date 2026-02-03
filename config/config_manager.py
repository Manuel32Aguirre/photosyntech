"""
Gestor centralizado de configuración
Maneja lectura/escritura del archivo de configuración con cache
"""
import os
import time
from typing import Dict, Any, Optional
from config.settings import Settings


class ConfigManager:
    """Gestor singleton de configuración"""
    
    _instance = None
    _cache: Dict[str, Any] = {}
    _cache_timestamps: Dict[str, float] = {}
    _cache_ttl = 30  # segundos
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._config_file = Settings.CONFIG_FILE
        self._initialized = True
    
    def _is_cache_valid(self, key: str) -> bool:
        """Verifica si el cache es válido para una clave"""
        if key not in self._cache:
            return False
        timestamp = self._cache_timestamps.get(key, 0)
        return (time.time() - timestamp) < self._cache_ttl
    
    def _set_cache(self, key: str, value: Any):
        """Guarda un valor en cache"""
        self._cache[key] = value
        self._cache_timestamps[key] = time.time()
    
    def _read_config_file(self) -> Dict[str, str]:
        """Lee el archivo de configuración completo"""
        config = {}
        if os.path.exists(self._config_file):
            try:
                with open(self._config_file, "r", encoding="utf-8") as f:
                    for linea in f:
                        linea = linea.strip()
                        if linea and "=" in linea and not linea.startswith("#"):
                            clave, valor = linea.split("=", 1)
                            config[clave.strip().lower()] = valor.strip()
            except Exception as e:
                print(f"Error leyendo configuración: {e}")
        return config
    
    def _write_config_file(self, config: Dict[str, str]):
        """Escribe el archivo de configuración completo"""
        try:
            with open(self._config_file, "w", encoding="utf-8") as f:
                for clave, valor in config.items():
                    f.write(f"{clave}={valor}\n")
        except Exception as e:
            print(f"Error escribiendo configuración: {e}")
    
    def get(self, key: str, default: Any = None, use_cache: bool = True) -> Any:
        """
        Obtiene un valor de configuración
        
        Args:
            key: Clave de configuración
            default: Valor por defecto si no existe
            use_cache: Si debe usar el cache
        """
        key_lower = key.lower()
        
        # Verificar cache
        if use_cache and self._is_cache_valid(key_lower):
            return self._cache[key_lower]
        
        # Leer desde archivo
        config = self._read_config_file()
        value = config.get(key_lower, default)
        
        # Guardar en cache
        if use_cache:
            self._set_cache(key_lower, value)
        
        return value
    
    def set(self, key: str, value: Any):
        """
        Establece un valor de configuración
        
        Args:
            key: Clave de configuración
            value: Valor a guardar
        """
        key_lower = key.lower()
        
        # Actualizar cache inmediatamente
        self._set_cache(key_lower, value)
        
        # Leer configuración actual
        config = self._read_config_file()
        
        # Actualizar valor
        config[key_lower] = str(value)
        
        # Escribir archivo
        self._write_config_file(config)
    
    def get_tonality(self) -> str:
        """Obtiene la tonalidad musical configurada"""
        return self.get("tonalidad", Settings.DEFAULT_TONALITY)
    
    def set_tonality(self, tonality: str):
        """Establece la tonalidad musical"""
        self.set("tonalidad", tonality)
    
    def get_device_id(self) -> Optional[int]:
        """Obtiene el ID del dispositivo de audio"""
        try:
            device_str = self.get("dispositivo")
            return int(device_str) if device_str else None
        except (ValueError, TypeError):
            return None
    
    def set_device_id(self, device_id: int):
        """Establece el ID del dispositivo de audio"""
        self.set("dispositivo", device_id)
    
    def get_storage_path(self) -> str:
        """Obtiene la ruta de almacenamiento"""
        return self.get("rutaalmacenamiento", Settings.RECORDINGS_DIR)
    
    def set_storage_path(self, path: str):
        """Establece la ruta de almacenamiento"""
        self.set("rutaalmacenamiento", path)
    
    def get_sensor_frequency(self, sensor: str) -> int:
        """Obtiene la frecuencia de guardado para un sensor (en segundos)"""
        key = f"frecuencia{sensor}".lower()
        default = Settings.DEFAULT_SENSOR_FREQUENCIES.get(sensor, 60)
        try:
            freq_str = self.get(key, str(default))
            return max(3, int(freq_str))
        except (ValueError, TypeError):
            return default
    
    def set_sensor_frequency(self, sensor: str, seconds: int):
        """Establece la frecuencia de guardado para un sensor"""
        key = f"frecuencia{sensor}".lower()
        self.set(key, seconds)
    
    def clear_cache(self):
        """Limpia el cache de configuración"""
        self._cache.clear()
        self._cache_timestamps.clear()
    
    def ensure_config_exists(self):
        """Asegura que existe el archivo de configuración con valores por defecto"""
        if not os.path.exists(self._config_file):
            default_config = {
                "tonalidad": Settings.DEFAULT_TONALITY,
                "dispositivo": "0",
                "rutaalmacenamiento": Settings.RECORDINGS_DIR,
            }
            # Agregar frecuencias de sensores
            for sensor, freq in Settings.DEFAULT_SENSOR_FREQUENCIES.items():
                default_config[f"frecuencia{sensor}"] = str(freq)
            
            self._write_config_file(default_config)

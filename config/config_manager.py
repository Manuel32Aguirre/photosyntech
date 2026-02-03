import os
import time
from typing import Dict, Any, Optional
from config.settings import Settings


class ConfigManager:
    
    _instance = None
    _cache: Dict[str, Any] = {}
    _cache_timestamps: Dict[str, float] = {}
    _cache_ttl = 30 
    
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
        if key not in self._cache:
            return False
        timestamp = self._cache_timestamps.get(key, 0)
        return (time.time() - timestamp) < self._cache_ttl
    
    def _set_cache(self, key: str, value: Any):
        self._cache[key] = value
        self._cache_timestamps[key] = time.time()
    
    def _read_config_file(self) -> Dict[str, str]:
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
        try:
            with open(self._config_file, "w", encoding="utf-8") as f:
                for clave, valor in config.items():
                    f.write(f"{clave}={valor}\n")
        except Exception as e:
            print(f"Error escribiendo configuración: {e}")
    
    def get(self, key: str, default: Any = None, use_cache: bool = True) -> Any:
        key_lower = key.lower()
        
        if use_cache and self._is_cache_valid(key_lower):
            return self._cache[key_lower]
        
        config = self._read_config_file()
        value = config.get(key_lower, default)
        
        if use_cache:
            self._set_cache(key_lower, value)
        
        return value
    
    def set(self, key: str, value: Any):
        key_lower = key.lower()
        
        self._set_cache(key_lower, value)
        config = self._read_config_file()
        config[key_lower] = str(value)
        self._write_config_file(config)
    
    def get_tonality(self) -> str:
        return self.get("tonalidad", Settings.DEFAULT_TONALITY)
    
    def set_tonality(self, tonality: str):
        self.set("tonalidad", tonality)
    
    def get_device_id(self) -> Optional[int]:
        try:
            device_str = self.get("dispositivo")
            return int(device_str) if device_str else None
        except (ValueError, TypeError):
            return None
    
    def set_device_id(self, device_id: int):
        self.set("dispositivo", device_id)
    
    def get_storage_path(self) -> str:
        return self.get("rutaalmacenamiento", Settings.RECORDINGS_DIR)
    
    def set_storage_path(self, path: str):
        self.set("rutaalmacenamiento", path)
    
    def get_sensor_frequency(self, sensor: str) -> int:
        key = f"frecuencia{sensor}".lower()
        default = Settings.DEFAULT_SENSOR_FREQUENCIES.get(sensor, 60)
        try:
            freq_str = self.get(key, str(default))
            return max(3, int(freq_str))
        except (ValueError, TypeError):
            return default
    
    def set_sensor_frequency(self, sensor: str, seconds: int):
        key = f"frecuencia{sensor}".lower()
        self.set(key, seconds)
    
    def clear_cache(self):
        self._cache.clear()
        self._cache_timestamps.clear()
    
    def ensure_config_exists(self):
        if not os.path.exists(self._config_file):
            default_config = {
                "tonalidad": Settings.DEFAULT_TONALITY,
                "dispositivo": "0",
                "rutaalmacenamiento": Settings.RECORDINGS_DIR,
            }
            for sensor, freq in Settings.DEFAULT_SENSOR_FREQUENCIES.items():
                default_config[f"frecuencia{sensor}"] = str(freq)
            
            self._write_config_file(default_config)

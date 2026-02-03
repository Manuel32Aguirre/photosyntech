"""
Servicio de gestión de perfiles de plantas
Maneja la carga y cálculo de bienestar
"""
import os
from typing import Dict, Tuple
from config.settings import Settings


class ProfileService:
    """Servicio para manejar perfiles de plantas y cálculos de bienestar"""
    
    def __init__(self):
        self.profile_file = Settings.PROFILE_FILE
        self.current_profile = self._load_default_profile()
    
    def _load_default_profile(self) -> Dict:
        """Carga el perfil por defecto"""
        return Settings.DEFAULT_PLANT_PROFILE.copy()
    
    def load_profile_from_file(self, filepath: str = None) -> bool:
        """
        Carga un perfil de planta desde archivo
        
        Args:
            filepath: Ruta del archivo (None para usar el por defecto)
            
        Returns:
            True si se cargó correctamente
        """
        filepath = filepath or self.profile_file
        
        if not os.path.exists(filepath):
            return False
        
        try:
            profile = self._load_default_profile()
            
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    
                    if "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip()
                        
                        if key in profile:
                            try:
                                profile[key] = float(value)
                            except ValueError:
                                continue
            
            self.current_profile = profile
            return True
            
        except Exception as e:
            print(f"Error cargando perfil: {e}")
            return False
    
    def save_profile_to_file(self, filepath: str = None) -> bool:
        """
        Guarda el perfil actual a archivo
        
        Args:
            filepath: Ruta del archivo (None para usar el por defecto)
            
        Returns:
            True si se guardó correctamente
        """
        filepath = filepath or self.profile_file
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("# Perfil de planta\n")
                for key, value in self.current_profile.items():
                    f.write(f"{key}={value}\n")
            return True
        except Exception as e:
            print(f"Error guardando perfil: {e}")
            return False
    
    def get_plant_name(self) -> str:
        """Obtiene el nombre de la planta desde el perfil"""
        try:
            if os.path.exists(self.profile_file):
                with open(self.profile_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("nombre="):
                            return line.split("=", 1)[1].strip()
        except Exception as e:
            print(f"Error leyendo nombre: {e}")
        
        return "Nombre de la planta"
    
    def calculate_wellbeing(
        self, 
        temperature: str, 
        humidity: str, 
        light: str, 
        soil: str
    ) -> Tuple[float, str, str]:
        """
        Calcula el bienestar de la planta basado en los sensores
        
        Args:
            temperature: Temperatura
            humidity: Humedad relativa
            light: Iluminación
            soil: Humedad de suelo
            
        Returns:
            Tupla (score, status_message, scale_type)
        """
        # Validar valores
        if any(val == "--" for val in [temperature, humidity, light, soil]):
            return 0, "😐 Estado: --", "mayor"
        
        try:
            t = float(temperature)
            h = float(humidity)
            l = float(light)
            s = float(soil)
        except (ValueError, TypeError):
            return 0, "😐 Error en datos", "mayor"
        
        # Obtener perfil
        p = self.current_profile
        
        # Calcular contribuciones
        contributions = [
            self._calculate_contribution(
                t, p["temperatura_min"], p["temperatura_max"], p["ponderacion_temperatura"]
            ),
            self._calculate_contribution(
                h, p["humedad_relativa_min"], p["humedad_relativa_max"], p["ponderacion_humedad_relativa"]
            ),
            self._calculate_contribution(
                l, p["iluminacion_min"], p["iluminacion_max"], p["ponderacion_iluminacion"]
            ),
            self._calculate_contribution(
                s, p["humedad_suelo_min"], p["humedad_suelo_max"], p["ponderacion_humedad_suelo"]
            )
        ]
        
        total_score = sum(contributions)
        
        # Determinar estado y escala musical
        if total_score >= 80:
            status = f"😊 Feliz ({total_score:.0f}%)"
            scale_type = "mayor"
        else:
            status = f"😢 Triste ({total_score:.0f}%)"
            scale_type = "menor"
        
        return total_score, status, scale_type
    
    def _calculate_contribution(
        self, 
        value: float, 
        min_val: float, 
        max_val: float, 
        weight: float
    ) -> float:
        """Calcula la contribución de un sensor al bienestar"""
        if min_val <= value <= max_val:
            return weight
        
        if value < min_val:
            return weight * max(0, 1 - (min_val - value) / min_val)
        
        return weight * max(0, 1 - (value - max_val) / max_val)
    
    def get_profile(self) -> Dict:
        """Obtiene el perfil actual"""
        return self.current_profile.copy()
    
    def update_profile(self, updates: Dict):
        """Actualiza valores del perfil"""
        for key, value in updates.items():
            if key in self.current_profile:
                self.current_profile[key] = value

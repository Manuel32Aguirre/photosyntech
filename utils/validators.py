"""
Utilidades de validación
"""
from typing import Optional, Any


def validate_float(value: Any, default: float = 0.0, min_val: float = None, max_val: float = None) -> float:
    """
    Valida y convierte un valor a float de forma segura
    
    Args:
        value: Valor a convertir
        default: Valor por defecto si falla
        min_val: Valor mínimo permitido
        max_val: Valor máximo permitido
        
    Returns:
        Valor como float validado
    """
    try:
        if value == "--" or value == "" or value is None:
            return default
        
        result = float(value)
        
        if min_val is not None and result < min_val:
            return default
        
        if max_val is not None and result > max_val:
            return default
        
        return result
        
    except (ValueError, TypeError):
        return default


def validate_sensor_value(value: str) -> bool:
    """
    Valida si un valor de sensor es válido
    
    Args:
        value: Valor a validar
        
    Returns:
        True si es válido
    """
    if not value or value == "--" or value == "":
        return False
    
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False


def clamp(value: float, min_val: float, max_val: float) -> float:
    """
    Restringe un valor a un rango
    
    Args:
        value: Valor a restringir
        min_val: Valor mínimo
        max_val: Valor máximo
        
    Returns:
        Valor restringido al rango
    """
    return max(min_val, min(max_val, value))

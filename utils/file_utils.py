"""
Utilidades para manejo de archivos
"""
import os
from typing import Optional


def ensure_dir(directory: str) -> bool:
    """
    Asegura que un directorio existe, creándolo si es necesario
    
    Args:
        directory: Ruta del directorio
        
    Returns:
        True si el directorio existe o fue creado
    """
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creando directorio {directory}: {e}")
        return False


def safe_file_read(filepath: str, encoding: str = 'utf-8') -> Optional[str]:
    """
    Lee un archivo de forma segura
    
    Args:
        filepath: Ruta del archivo
        encoding: Codificación del archivo
        
    Returns:
        Contenido del archivo o None si hay error
    """
    try:
        with open(filepath, 'r', encoding=encoding) as f:
            return f.read()
    except Exception as e:
        print(f"Error leyendo archivo {filepath}: {e}")
        return None


def safe_file_write(filepath: str, content: str, encoding: str = 'utf-8') -> bool:
    """
    Escribe un archivo de forma segura
    
    Args:
        filepath: Ruta del archivo
        content: Contenido a escribir
        encoding: Codificación del archivo
        
    Returns:
        True si se escribió correctamente
    """
    try:
        # Asegurar que existe el directorio
        directory = os.path.dirname(filepath)
        if directory:
            ensure_dir(directory)
        
        with open(filepath, 'w', encoding=encoding) as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error escribiendo archivo {filepath}: {e}")
        return False

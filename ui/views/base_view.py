"""
Clase base para todas las vistas de la aplicación
"""
from PyQt6.QtWidgets import QWidget
from abc import abstractmethod


class BaseView(QWidget):
    """Vista base abstracta"""
    
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def setup_ui(self):
        """Configura la interfaz de usuario"""
        pass
    
    def cleanup(self):
        """Limpia recursos al cerrar la vista"""
        pass

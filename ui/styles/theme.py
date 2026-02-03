"""
Tema centralizado de la aplicación
Define colores y estilos reutilizables
"""
from config.settings import Settings


class Theme:
    """Tema visual de la aplicación"""
    
    # Colores principales
    BG_DARK = Settings.COLOR_BG_DARK
    BG_PANEL = Settings.COLOR_BG_PANEL
    ACCENT_GREEN = Settings.COLOR_ACCENT_GREEN
    TEXT = Settings.COLOR_TEXT
    
    # Colores adicionales
    CARD_COLOR = "#1A1D2E"
    BUTTON_GREEN = "#4CAF50"
    BUTTON_GREEN_HOVER = "#45a049"
    BUTTON_RED = "#e74c3c"
    BUTTON_RED_HOVER = "#c0392b"
    PURPLE = "#663399"
    GRID_LINE = "#3b3b5e"
    
    # Estilos de widgets comunes
    @staticmethod
    def get_main_window_style() -> str:
        """Estilo para la ventana principal"""
        return """
            QTabWidget::pane { border: none; }
            QTabBar::tab {
                background: #8DB986;
                color: black;
                font-weight: bold;
                padding: 10px;
                border: 1px solid #7AA774;
            }
            QTabBar::tab:selected {
                background: #6BA568;
                color: white;
            }
        """
    
    @staticmethod
    def get_panel_style() -> str:
        """Estilo para paneles"""
        return f"""
            QWidget {{ 
                background-color: {Theme.BG_PANEL}; 
                color: {Theme.TEXT}; 
                font-family: Arial; 
            }}
            QFrame {{ background: {Theme.BG_DARK}; }}
            QLabel {{ color: {Theme.TEXT}; font-family: Arial; }}
        """
    
    @staticmethod
    def get_button_style(color: str = None, hover_color: str = None) -> str:
        """Estilo para botones"""
        color = color or Theme.BUTTON_GREEN
        hover_color = hover_color or Theme.BUTTON_GREEN_HOVER
        
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
        """
    
    @staticmethod
    def get_combo_style() -> str:
        """Estilo para ComboBox"""
        return f"""
            QComboBox {{
                background-color: {Theme.BG_DARK};
                color: {Theme.TEXT};
                border: 1px solid {Theme.GRID_LINE};
                border-radius: 4px;
                padding: 4px;
            }}
        """
    
    @staticmethod
    def get_input_style() -> str:
        """Estilo para LineEdit"""
        return f"""
            QLineEdit {{
                background-color: {Theme.BG_DARK};
                border: 1px solid {Theme.ACCENT_GREEN};
                padding: 6px;
                color: {Theme.TEXT};
            }}
        """

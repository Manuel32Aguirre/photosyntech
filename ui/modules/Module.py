from PyQt6.QtWidgets import QWidget
from abc import abstractmethod

class Module(QWidget):

    def __init__(self):
        super().__init__()

    @abstractmethod
    def draw(self):
        pass
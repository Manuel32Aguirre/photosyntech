from typing import override

from PyQt6.QtWidgets import QVBoxLayout, QListWidget

from photosyntech.ui.modules.Module import Module


class GraphsModule(Module):

    def __init__(self):
        super().__init__()
        self.__main_layout = QVBoxLayout()

    @override
    def draw(self):
        pass
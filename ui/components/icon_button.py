from PyQt6.QtGui import QIcon, QCursor, QColor
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt6.QtWidgets import QToolButton, QGraphicsDropShadowEffect


class IconButton(QToolButton):
    def __init__(self, icon_path, text):
        super().__init__()
        self.setText(text)
        self.setIcon(QIcon(icon_path))
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        shadow = QGraphicsDropShadowEffect(blurRadius=15, xOffset=0, yOffset=0)
        shadow.setColor(QColor(0, 255, 200))
        self.setGraphicsEffect(shadow)
        self.anim = QPropertyAnimation(self, b"iconSize")
        self.anim.setDuration(300)
        self.anim.setEasingCurve(QEasingCurve.Type.OutBack)

    def enterEvent(self, event):
        self.anim.stop()
        start = self.iconSize()
        self.anim.setStartValue(start)
        self.anim.setEndValue(start * 1.3)
        self.anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.anim.stop()
        start = self.iconSize()
        self.anim.setStartValue(start)
        self.anim.setEndValue(start / 1.3)
        self.anim.start()
        super().leaveEvent(event)

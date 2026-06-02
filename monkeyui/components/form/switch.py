import os
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, Property, Signal, QRect, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QPainter, QColor, QPainterPath

class MkSwitch(QWidget):
    """
    开关组件 (Switch)
    类似 Element Plus 的按钮开关
    """
    toggled = Signal(bool)

    def __init__(self, checked=False, active_color="#409eff", inactive_color="#dcdfe6", width=40, height=20, parent=None):
        super().__init__(parent)
        self._checked = checked
        self._active_color = QColor(active_color)
        self._inactive_color = QColor(inactive_color)
        self._switch_width = width
        self._switch_height = height
        self._handle_radius = self._switch_height - 4
        
        # Used for animation
        self._handle_pos = 2 if not self._checked else self._switch_width - self._handle_radius - 2
        
        self.setFixedSize(self._switch_width, self._switch_height)
        self.setCursor(Qt.PointingHandCursor)
        
        # Animation
        self._anim = QPropertyAnimation(self, b"handle_pos")
        self._anim.setEasingCurve(QEasingCurve.InOutQuad)
        self._anim.setDuration(200)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw background
        bg_color = self._active_color if self._checked else self._inactive_color
        
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), self.height() / 2, self.height() / 2)
        painter.fillPath(path, bg_color)

        # Draw handle (the circle)
        painter.setBrush(QColor("white"))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(int(self._handle_pos), 2, self._handle_radius, self._handle_radius)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setChecked(not self._checked)
        super().mouseReleaseEvent(event)

    def setChecked(self, checked):
        if self._checked != checked:
            self._checked = checked
            self.toggled.emit(self._checked)
            self._start_animation()

    def _start_animation(self):
        self._anim.stop()
        start_val = self._handle_pos
        end_val = self._switch_width - self._handle_radius - 2 if self._checked else 2
        self._anim.setStartValue(start_val)
        self._anim.setEndValue(end_val)
        self._anim.start()

    @Property(float)
    def handle_pos(self):
        return self._handle_pos

    @handle_pos.setter
    def handle_pos(self, pos):
        self._handle_pos = pos
        self.update()

    @Property(bool)
    def checked(self):
        return self._checked

    @checked.setter
    def checked(self, value):
        self.setChecked(value)

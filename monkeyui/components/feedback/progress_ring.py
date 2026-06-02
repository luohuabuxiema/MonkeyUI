import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import Qt, Property, Signal, QRectF
from PySide6.QtGui import QColor, QPainter, QPen

from ...core.theme import ThemeManager

class MkProgressRing(QWidget):
    """
    进度环 (Progress Ring) 组件
    支持不同的状态、线宽。
    状态: normal, success, warning, exception
    """
    def __init__(self, percentage=0, status="normal", stroke_width=6, width=120, show_text=True, parent=None):
        super().__init__(parent)
        self._percentage = max(0, min(100, percentage))
        self._status = status
        self._stroke_width = stroke_width
        self._ring_width = width
        self._show_text = show_text

        self._setup_ui()

    def _setup_ui(self):
        self.setFixedSize(self._ring_width, self._ring_width)
        
        # Inner text label centered
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setAlignment(Qt.AlignCenter)

        self.text_label = QLabel(f"{self._percentage}%")
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setVisible(self._show_text)
        self.layout.addWidget(self.text_label)

        self._update_style()

    def _get_color(self):
        colors = {
            "normal": "#409eff",
            "success": "#67c23a",
            "warning": "#e6a23c",
            "exception": "#f56c6c"
        }
        return colors.get(self._status, colors["normal"])

    def _update_style(self):
        self.text_label.setStyleSheet(f"""
            QLabel {{
                color: #606266;
                font-size: {max(12, int(self._ring_width * 0.15))}px;
            }}
        """)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = QRectF(
            self._stroke_width / 2.0, 
            self._stroke_width / 2.0,
            self.width() - self._stroke_width, 
            self.height() - self._stroke_width
        )

        # Draw background track
        pen_bg = QPen(QColor("#ebeef5"))
        pen_bg.setWidth(self._stroke_width)
        pen_bg.setCapStyle(Qt.RoundCap)
        painter.setPen(pen_bg)
        painter.drawArc(rect, 0, 360 * 16)

        # Draw progress arc
        if self._percentage > 0:
            pen_fg = QPen(QColor(self._get_color()))
            pen_fg.setWidth(self._stroke_width)
            pen_fg.setCapStyle(Qt.RoundCap)
            painter.setPen(pen_fg)
            
            # Qt uses 1/16th of a degree. 90 * 16 starts at 12 o'clock (but standard drawArc starts at 3 o'clock).
            # To start at 12 o'clock (top), startAngle = 90 * 16.
            # Angles are counter-clockwise, so span is negative.
            start_angle = 90 * 16
            span_angle = int(-self._percentage / 100.0 * 360 * 16)
            painter.drawArc(rect, start_angle, span_angle)

    # Properties
    @Property(int)
    def percentage(self):
        return self._percentage

    @percentage.setter
    def percentage(self, value):
        value = max(0, min(100, value))
        if self._percentage != value:
            self._percentage = value
            self.text_label.setText(f"{value}%")
            self.update()

    @Property(str)
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        if value not in ["normal", "success", "warning", "exception"]:
            value = "normal"
        if self._status != value:
            self._status = value
            self._update_style()

    @Property(int)
    def stroke_width(self):
        return self._stroke_width

    @stroke_width.setter
    def stroke_width(self, value):
        if self._stroke_width != value:
            self._stroke_width = max(2, value)
            self.update()

    @Property(bool)
    def show_text(self):
        return self._show_text

    @show_text.setter
    def show_text(self, value):
        if self._show_text != value:
            self._show_text = value
            self.text_label.setVisible(value)

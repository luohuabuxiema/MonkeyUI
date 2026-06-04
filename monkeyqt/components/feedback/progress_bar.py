import os
from PySide6.QtWidgets import QWidget, QSizePolicy
from PySide6.QtCore import Qt, Property, QRectF
from PySide6.QtGui import QPainter, QPainterPath, QColor

class MkProgressBar(QWidget):
    """
    进度条 (Progress Bar) 组件
    使用 paintEvent 绘制，确保像素级完美和抗锯齿。
    状态: normal, success, warning, exception
    """
    def __init__(self, percentage=0, status="normal", stroke_width=6, show_text=True, text_inside=False, parent=None):
        super().__init__(parent)
        self._percentage = max(0, min(100, percentage))
        self._status = status
        self._stroke_width = stroke_width
        self._show_text = show_text
        self._text_inside = text_inside

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(max(16, self._stroke_width))

    def _get_color(self):
        colors = {
            "normal": "#409eff",
            "success": "#67c23a",
            "warning": "#e6a23c",
            "exception": "#f56c6c"
        }
        return colors.get(self._status, colors["normal"])

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()
        stroke = self._stroke_width
        
        # 设置字体和文本宽度
        text = f"{self._percentage}%"
        font = self.font()
        font.setPixelSize(max(12, stroke - 2 if self._text_inside else 14))
        painter.setFont(font)
        fm = painter.fontMetrics()
        text_width = fm.horizontalAdvance(text)
        
        track_x = 0
        track_y = (height - stroke) / 2
        track_width = width
        
        if self._show_text and not self._text_inside:
            track_width = width - text_width - 12
            
        # 绘制背景底轨
        bg_path = QPainterPath()
        bg_path.addRoundedRect(track_x, track_y, track_width, stroke, stroke / 2, stroke / 2)
        painter.fillPath(bg_path, QColor("#ebeef5"))
        
        # 绘制前景进度轨
        if self._percentage > 0:
            fg_width = track_width * (self._percentage / 100.0)
            fg_path = QPainterPath()
            fg_path.addRoundedRect(track_x, track_y, fg_width, stroke, stroke / 2, stroke / 2)
            painter.fillPath(fg_path, QColor(self._get_color()))
            
        # 绘制文本
        if self._show_text:
            if self._text_inside:
                # 仅在内部宽度足够时绘制文本
                if fg_width > text_width + 10:
                    painter.setPen(Qt.white)
                    text_rect = QRectF(track_x, track_y, fg_width - 6, stroke)
                    painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, text)
            else:
                painter.setPen(QColor("#606266"))
                text_rect = QRectF(track_width + 8, 0, text_width + 4, height)
                painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, text)

    # Properties
    @Property(int)
    def percentage(self):
        return self._percentage

    @percentage.setter
    def percentage(self, value):
        value = max(0, min(100, value))
        if self._percentage != value:
            self._percentage = value
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
            self.update()

    @Property(int)
    def stroke_width(self):
        return self._stroke_width

    @stroke_width.setter
    def stroke_width(self, value):
        if self._stroke_width != value:
            self._stroke_width = max(2, value)
            self.setMinimumHeight(max(16, self._stroke_width))
            self.update()

    @Property(bool)
    def show_text(self):
        return self._show_text

    @show_text.setter
    def show_text(self, value):
        if self._show_text != value:
            self._show_text = value
            self.update()

    @Property(bool)
    def text_inside(self):
        return self._text_inside

    @text_inside.setter
    def text_inside(self, value):
        if self._text_inside != value:
            self._text_inside = value
            self.update()

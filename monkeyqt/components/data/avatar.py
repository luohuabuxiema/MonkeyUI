import os
from PySide6.QtWidgets import QLabel, QSizePolicy
from PySide6.QtCore import Qt, Property, QRect
from PySide6.QtGui import QPainter, QPainterPath, QColor, QPixmap, QFont

class MkAvatar(QLabel):
    """
    头像组件 (Avatar)
    支持圆形和矩形，支持显示图片或文字。
    """
    def __init__(self, text="", image_path="", shape="circle", size=40, parent=None):
        super().__init__(parent)
        self._text = text
        self._image_path = image_path
        self._shape = shape # circle, square
        self._avatar_size = size
        
        self.setFixedSize(self._avatar_size, self._avatar_size)
        self.setAlignment(Qt.AlignCenter)
        self._setup_style()

    def _setup_style(self):
        font = self.font()
        font.setPixelSize(int(self._avatar_size * 0.4))
        self.setFont(font)
        
        # We handle drawing entirely in paintEvent
        self.setAttribute(Qt.WA_TranslucentBackground)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        rect = self.rect()
        path = QPainterPath()

        if self._shape == "circle":
            path.addEllipse(rect)
        else:
            # Rounded square
            path.addRoundedRect(rect, 4, 4)

        painter.setClipPath(path)

        if self._image_path and os.path.exists(self._image_path):
            pixmap = QPixmap(self._image_path)
            # Scale and crop to fill
            scaled = pixmap.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            
            # Center the pixmap
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
        else:
            # Draw background
            painter.fillPath(path, QColor("#c0c4cc"))
            
            # Draw text
            if self._text:
                painter.setPen(QColor("white"))
                painter.drawText(rect, Qt.AlignCenter, self._text[:2].upper())

    @Property(str)
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = value
        self.update()

    @Property(str)
    def image_path(self):
        return self._image_path

    @image_path.setter
    def image_path(self, value):
        self._image_path = value
        self.update()

    @Property(str)
    def shape(self):
        return self._shape

    @shape.setter
    def shape(self, value):
        if value in ["circle", "square"]:
            self._shape = value
            self.update()

    @Property(int)
    def size(self):
        return self._avatar_size

    @size.setter
    def size(self, value):
        self._avatar_size = value
        self.setFixedSize(value, value)
        self._setup_style()
        self.update()

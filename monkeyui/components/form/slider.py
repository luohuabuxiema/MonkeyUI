import os
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QSlider, QLabel, QToolTip, QSizePolicy
from PySide6.QtCore import Qt, Property, Signal, QEvent
from PySide6.QtGui import QCursor

class MkSlider(QWidget):
    """
    滑块组件 (Slider)
    基于 QWidget 封装，自带数值显示，
    且支持实心圆点高颜值滑块。
    """
    valueChanged = Signal(int)

    def __init__(self, orientation=Qt.Horizontal, parent=None):
        super().__init__(parent)
        self._orientation = orientation
        self._show_value = True

        self._setup_ui()
        self._setup_style()

    def _setup_ui(self):
        if self._orientation == Qt.Horizontal:
            self.layout = QHBoxLayout(self)
        else:
            self.layout = QVBoxLayout(self)
            
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(12)

        # 数值标签 (像前端左侧的 0.25)
        self.value_label = QLabel("0")
        self.value_label.setStyleSheet("color: #606266; font-size: 13px;")
        if self._orientation == Qt.Horizontal:
            self.value_label.setFixedWidth(30)
            self.value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        else:
            self.value_label.setAlignment(Qt.AlignCenter)

        # 滑块
        self.slider = QSlider(self._orientation)
        self.slider.setCursor(Qt.PointingHandCursor)

        if self._orientation == Qt.Horizontal:
            self.layout.addWidget(self.value_label)
            self.layout.addWidget(self.slider)
        else:
            self.layout.addWidget(self.slider)
            self.layout.addWidget(self.value_label)

        self.slider.valueChanged.connect(self._on_value_changed)
        
        # 修复 Qt 悬停时只局部重绘旧区域导致滑块被裁切变方的 Bug
        self.slider.setAttribute(Qt.WA_Hover)
        self.slider.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj == self.slider and event.type() in (QEvent.HoverEnter, QEvent.HoverLeave, QEvent.HoverMove):
            self.slider.update()
        return super().eventFilter(obj, event)

    def _on_value_changed(self, value):
        self.value_label.setText(str(value))
        # 拖动时显示当前的 value 气泡提示
        QToolTip.showText(QCursor.pos(), str(value), self.slider)
        self.valueChanged.emit(value)

    def _setup_style(self):
        # 模仿用户截图的绝美样式: 细轨 + 实心紫色圆点
        color_primary = "#7b61ff" # 类似图片中的淡紫色/紫蓝色
        color_hover = "#6548e5"
        
        self.slider.setStyleSheet(f"""
            QSlider:horizontal {{
                min-height: 24px;
            }}
            QSlider::groove:horizontal {{
                border: none;
                height: 4px;
                background: #E5E7EB;
                border-radius: 2px;
            }}
            QSlider::sub-page:horizontal {{
                background: {color_primary};
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {color_primary};
                border: none;
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {color_hover};
                border: none;
                width: 20px;
                height: 20px;
                margin: -8px 0;
                border-radius: 10px;
            }}
            
            QSlider:vertical {{
                min-width: 24px;
            }}
            QSlider::groove:vertical {{
                border: none;
                width: 4px;
                background: #E5E7EB;
                border-radius: 2px;
            }}
            QSlider::sub-page:vertical {{
                background: {color_primary};
                border-radius: 2px;
            }}
            QSlider::handle:vertical {{
                background: {color_primary};
                border: none;
                width: 16px;
                height: 16px;
                margin: 0 -6px;
                border-radius: 8px;
            }}
            QSlider::handle:vertical:hover {{
                background: {color_hover};
                border: none;
                width: 20px;
                height: 20px;
                margin: 0 -8px;
                border-radius: 10px;
            }}
        """)

    # 代理 QSlider 的常用方法
    def setRange(self, min_val, max_val):
        self.slider.setRange(min_val, max_val)

    def setValue(self, val):
        self.slider.setValue(val)
        self.value_label.setText(str(val))

    def value(self):
        return self.slider.value()

    def setSingleStep(self, step):
        self.slider.setSingleStep(step)
        
    @Property(bool)
    def show_value(self):
        return self._show_value
        
    @show_value.setter
    def show_value(self, val):
        self._show_value = val
        self.value_label.setVisible(val)

import os
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QSizePolicy
from PySide6.QtCore import Qt, Property, Signal
from PySide6.QtGui import QIcon, QPixmap, QPainter

from ...core.theme import ThemeManager

class MkAlert(QWidget):
    """
    信息条 (Alert) 组件
    用于页面中展示重要的提示信息。
    支持类型: info, success, warning, error
    """
    closed = Signal()

    def __init__(self, title="", description="", mk_type="info", closable=False, show_icon=False, parent=None):
        super().__init__(parent)
        self._title = title
        self._description = description
        self._mk_type = mk_type
        self._closable = closable
        self._show_icon = show_icon

        self._setup_ui()
        self._update_style()

    def _setup_ui(self):
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Main layout
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(16, 8, 16, 8)
        self.main_layout.setSpacing(12)

        # Icon
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(16, 16)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setVisible(self._show_icon)
        self.main_layout.addWidget(self.icon_label, 0, Qt.AlignTop | Qt.AlignLeft)

        # Content layout (Title + Description)
        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(4)
        
        self.title_label = QLabel(self._title)
        self.title_label.setWordWrap(True)
        self.title_label.setObjectName("alert-title")
        self.content_layout.addWidget(self.title_label)

        self.desc_label = QLabel(self._description)
        self.desc_label.setWordWrap(True)
        self.desc_label.setObjectName("alert-desc")
        self.desc_label.setVisible(bool(self._description))
        self.content_layout.addWidget(self.desc_label)

        self.main_layout.addLayout(self.content_layout, 1)

        # Close button
        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("alert-close-btn")
        self.close_btn.setFixedSize(16, 16)
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.clicked.connect(self.close_alert)
        self.close_btn.setVisible(self._closable)
        self.main_layout.addWidget(self.close_btn, 0, Qt.AlignTop | Qt.AlignRight)

        self._update_icon()

    def _update_icon(self):
        if not self._show_icon:
            return
        
        # Simple text icon based on type (in a real project, use SVG icons)
        icons = {
            "info": "ℹ",
            "success": "✓",
            "warning": "!",
            "error": "✕"
        }
        self.icon_label.setText(icons.get(self._mk_type, "ℹ"))
        self.icon_label.setObjectName(f"alert-icon-{self._mk_type}")

    def _update_style(self):
        # Base colors from Element Plus for Alerts
        colors = {
            "info": {"bg": "#f4f4f5", "text": "#909399", "border": "#e9e9eb", "icon": "#909399"},
            "success": {"bg": "#f0f9eb", "text": "#67c23a", "border": "#e1f3d8", "icon": "#67c23a"},
            "warning": {"bg": "#fdf6ec", "text": "#e6a23c", "border": "#faecd8", "icon": "#e6a23c"},
            "error": {"bg": "#fef0f0", "text": "#f56c6c", "border": "#fde2e2", "icon": "#f56c6c"}
        }
        
        c = colors.get(self._mk_type, colors["info"])
        
        qss = f"""
            MkAlert {{
                background-color: {c['bg']};
                border-radius: 4px;
                border: 1px solid {c['bg']}; /* Default without border, but can be customized */
            }}
            QLabel {{
                background-color: transparent;
            }}
            #alert-title {{
                color: {c['text'] if not self._description else '#303133'};
                font-size: 13px;
                font-weight: {'bold' if self._description else 'normal'};
            }}
            #alert-desc {{
                color: #606266;
                font-size: 12px;
                margin-top: 4px;
            }}
            #alert-close-btn {{
                background: transparent;
                border: none;
                color: #c0c4cc;
                font-size: 12px;
            }}
            #alert-close-btn:hover {{
                color: #909399;
            }}
            QLabel[objectName^="alert-icon-"] {{
                color: {c['icon']};
                font-weight: bold;
                font-size: 14px;
            }}
        """
        self.setStyleSheet(qss)

    def close_alert(self):
        self.hide()
        self.closed.emit()

    # Properties
    @Property(str)
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        self._title = value
        self.title_label.setText(value)

    @Property(str)
    def description(self):
        return self._description

    @description.setter
    def description(self, value):
        self._description = value
        self.desc_label.setText(value)
        self.desc_label.setVisible(bool(value))
        self._update_style()

    @Property(str)
    def mk_type(self):
        return self._mk_type

    @mk_type.setter
    def mk_type(self, value):
        if value not in ["info", "success", "warning", "error"]:
            value = "info"
        if self._mk_type != value:
            self._mk_type = value
            self._update_icon()
            self._update_style()

    @Property(bool)
    def closable(self):
        return self._closable

    @closable.setter
    def closable(self, value):
        self._closable = value
        self.close_btn.setVisible(value)

    @Property(bool)
    def show_icon(self):
        return self._show_icon

    @show_icon.setter
    def show_icon(self, value):
        self._show_icon = value
        self.icon_label.setVisible(value)
        self._update_icon()

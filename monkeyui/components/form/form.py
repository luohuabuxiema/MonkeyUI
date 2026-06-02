import os
from PySide6.QtWidgets import QWidget, QFormLayout, QLabel, QVBoxLayout, QSizePolicy
from PySide6.QtCore import Qt

class MkForm(QWidget):
    """
    表单组件 (Form)
    提供结构化的表单布局支持
    """
    def __init__(self, label_width=100, label_position="right", parent=None):
        super().__init__(parent)
        self._label_width = label_width
        self._label_position = label_position # right, left, top

        self._setup_ui()

    def _setup_ui(self):
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        if self._label_position in ["right", "left"]:
            self.form_layout = QFormLayout(self)
            self.form_layout.setContentsMargins(0, 0, 0, 0)
            self.form_layout.setSpacing(20)
            
            # Form style settings
            if self._label_position == "right":
                self.form_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
            else:
                self.form_layout.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                
            self.form_layout.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
        else:
            # Top layout
            self.form_layout = QVBoxLayout(self)
            self.form_layout.setContentsMargins(0, 0, 0, 0)
            self.form_layout.setSpacing(12)

    def add_item(self, label_text, widget):
        label = QLabel(label_text)
        label.setStyleSheet("""
            QLabel {
                color: #606266;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        
        if self._label_position in ["right", "left"]:
            label.setFixedWidth(self._label_width)
            self.form_layout.addRow(label, widget)
        else:
            # Top alignment means label is above the widget
            item_layout = QVBoxLayout()
            item_layout.setSpacing(4)
            item_layout.addWidget(label)
            item_layout.addWidget(widget)
            self.form_layout.addLayout(item_layout)

    def set_label_width(self, width):
        self._label_width = width
        # Updating existing labels is tricky in QFormLayout, typically set once at init

from PySide6.QtWidgets import QLineEdit, QLabel, QPushButton, QHBoxLayout, QWidget
from PySide6.QtCore import Qt, QSize, QPoint
from PySide6.QtGui import QAction, QFocusEvent
from monkeyui.core.icons import MkPhosphorIcon

class MkInput(QLineEdit):
    """
    MkInput - Modern Web-style text input field.
    Supports Phosphor leading icons, custom focus rings, and an interactive password visibility toggle.
    """
    def __init__(self, placeholder: str = "", is_password: bool = False, leading_icon: str = None, parent=None):
        super().__init__(parent)
        self.is_password = is_password
        self.leading_icon_name = leading_icon
        
        self.setPlaceholderText(placeholder)
        
        self.leading_label = None
        self.password_btn = None
        self._password_visible = False
        
        self._setup_ui()

    def _setup_ui(self):
        # Configure input margins
        left_margin = 12
        right_margin = 12
        
        # 1. Setup leading icon
        if self.leading_icon_name:
            left_margin = 32
            self.leading_label = QLabel(self)
            self.leading_label.setFixedSize(16, 16)
            self.leading_label.setPixmap(MkPhosphorIcon.get_pixmap(self.leading_icon_name, "#94a3b8", 16))
            self.leading_label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            self.leading_label.setStyleSheet("background: transparent;")
            
        # 2. Setup trailing password toggle eye button
        if self.is_password:
            right_margin = 32
            self.setEchoMode(QLineEdit.EchoMode.Password)
            
            self.password_btn = QPushButton(self)
            self.password_btn.setFixedSize(20, 20)
            self.password_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.password_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            self.password_btn.setAutoDefault(False)
            self.password_btn.setDefault(False)
            self.password_btn.setIcon(MkPhosphorIcon.get_icon("eye", "#94a3b8", "#3b82f6", 16))
            self.password_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    outline: none;
                }
            """)
            self.password_btn.clicked.connect(self._toggle_password_visibility)
            
            # Initially hide the button if there is no text
            self.password_btn.hide()
            self.textChanged.connect(self._on_text_changed)
            
        # Apply padding margins so text doesn't overlap icons
        self.setTextMargins(left_margin, 0, right_margin, 0)
        
        # Apply shadcn-style input styling (sleek borders, focus rings, round corners)
        self.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                color: #0f172a;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                font-size: 13px;
                min-height: 36px;
            }
            QLineEdit:hover {
                border-color: #cbd5e1;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
                background-color: #ffffff;
            }
            QLineEdit:disabled {
                background-color: #f1f5f9;
                color: #64748b;
            }
        """)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        h = self.height()
        w = self.width()
        
        # Dynamic positioning of overlays during resize
        if self.leading_label:
            # Centered vertically at x=10
            ly = (h - 16) // 2
            self.leading_label.move(10, ly)
            
        if self.password_btn:
            # Centered vertically at x = width - 26
            py = (h - 20) // 2
            self.password_btn.move(w - 26, py)

    def _toggle_password_visibility(self):
        self._password_visible = not self._password_visible
        if self._password_visible:
            self.setEchoMode(QLineEdit.EchoMode.Normal)
            self.password_btn.setIcon(MkPhosphorIcon.get_icon("eye-slash", "#3b82f6", "#94a3b8", 16))
        else:
            self.setEchoMode(QLineEdit.EchoMode.Password)
            self.password_btn.setIcon(MkPhosphorIcon.get_icon("eye", "#94a3b8", "#3b82f6", 16))

    def _on_text_changed(self, text):
        if self.password_btn:
            self.password_btn.setVisible(bool(text))
            
    def focusInEvent(self, event: QFocusEvent):
        super().focusInEvent(event)
        # Highlight leading icon color on focus if it exists
        if self.leading_label:
            self.leading_label.setPixmap(MkPhosphorIcon.get_pixmap(self.leading_icon_name, "#3b82f6", 16))

    def focusOutEvent(self, event: QFocusEvent):
        super().focusOutEvent(event)
        # Reset leading icon color on focus lost
        if self.leading_label:
            self.leading_label.setPixmap(MkPhosphorIcon.get_pixmap(self.leading_icon_name, "#94a3b8", 16))

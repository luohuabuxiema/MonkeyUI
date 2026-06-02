import random
import string
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLineEdit
from PySide6.QtCore import Qt, QSize, QTimer, Signal
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QFontMetrics, QPainterPath

class MkCaptchaWidget(QWidget):
    """
    MkCaptchaWidget - Self-contained graphical security captcha.
    Generates a 4-letter random code and draws skewed characters, lines, and noise dots.
    Refreshes dynamically when clicked.
    """
    codeChanged = Signal(str)

    def __init__(self, width: int = 100, height: int = 36, parent=None):
        super().__init__(parent)
        self.setFixedSize(width, height)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("点击刷新验证码")
        
        self._current_code = ""
        self.generate_new_code()

    def generate_new_code(self):
        """Generates a new random 4-character code and triggers redraw."""
        chars = string.ascii_uppercase + string.digits
        # Exclude easily confused characters like O, 0, I, 1 for premium UX
        for exclude in ["O", "0", "I", "1", "L", "Z", "2"]:
            chars = chars.replace(exclude, "")
            
        self._current_code = "".join(random.choice(chars) for _ in range(4))
        self.codeChanged.emit(self._current_code)
        self.update()

    def get_code(self) -> str:
        """Returns the current correct captcha code."""
        return self._current_code

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.generate_new_code()
            event.accept()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        w = rect.width()
        h = rect.height()
        
        # 1. Fill light background (soft Vercel gray)
        painter.fillRect(rect, QColor("#f8fafc"))
        
        # Draw clean border
        border_pen = QPen(QColor("#e2e8f0"))
        border_pen.setWidth(1)
        painter.setPen(border_pen)
        painter.drawRect(rect.adjusted(0, 0, -1, -1))
        
        # 2. Draw random noise dots
        painter.save()
        for _ in range(80):
            # Select random bright colors
            x = random.randint(2, w - 2)
            y = random.randint(2, h - 2)
            color = QColor(random.randint(100, 200), random.randint(100, 200), random.randint(100, 200), 120)
            painter.setPen(QPen(color, random.randint(1, 2)))
            painter.drawPoint(x, y)
        painter.restore()
        
        # 3. Draw interference lines (Bezier curves for extreme premium aesthetic)
        painter.save()
        line_pen = QPen(QColor(150, 150, 150, 80))
        line_pen.setWidth(1)
        painter.setPen(line_pen)
        for _ in range(3):
            path = QPainterPath()
            path.moveTo(0, random.randint(5, h - 5))
            path.cubicTo(
                w // 3, random.randint(0, h),
                2 * w // 3, random.randint(0, h),
                w, random.randint(5, h - 5)
            )
            painter.drawPath(path)
        painter.restore()
        
        # 4. Draw random characters skewed and colored
        char_w = w / 4
        fonts = ["Arial", "Courier New", "Georgia", "Verdana", "Times New Roman"]
        
        for idx, char in enumerate(self._current_code):
            painter.save()
            
            # Select unique font and sizing
            font_size = random.randint(int(h * 0.5), int(h * 0.65))
            font = QFont(random.choice(fonts), font_size, QFont.Weight.Bold)
            font.setItalic(random.choice([True, False]))
            painter.setFont(font)
            
            # Select high-contrast text color
            r = random.randint(20, 120)
            g = random.randint(20, 120)
            b = random.randint(20, 120)
            painter.setPen(QColor(r, g, b))
            
            # Translate and apply random rotation tilt (-25 to 25 degrees)
            angle = random.randint(-25, 25)
            cx = idx * char_w + char_w / 2
            cy = h / 2
            
            painter.translate(cx, cy)
            painter.rotate(angle)
            
            # Draw character centered at local coordinates
            metrics = QFontMetrics(font)
            tx = -metrics.horizontalAdvance(char) / 2
            ty = metrics.ascent() - metrics.descent() - metrics.height() / 2 + 2
            
            painter.drawText(int(tx), int(ty), char)
            painter.restore()
            
        painter.end()


# SMS CAPTCHA COUNTDOWN WIDGET
class MkSmsCodeWidget(QWidget):
    """
    MkSmsCodeWidget - Dual horizontal field containing text entry and a countdown button.
    Includes built-in 60s sending throttling.
    """
    sendClicked = Signal()

    def __init__(self, code_field: QLineEdit, parent=None):
        super().__init__(parent)
        self.code_field = code_field
        
        self.cooldown = 60
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._on_timer_tick)
        
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Add the code text field
        layout.addWidget(self.code_field, stretch=1)
        
        # Add the countdown trigger button
        self.send_btn = QPushButton("发送验证码", self)
        self.send_btn.setFixedWidth(96)
        self.send_btn.setFixedHeight(36)
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.send_btn.setAutoDefault(False)
        self.send_btn.setDefault(False)
        self.send_btn.clicked.connect(self._on_send_clicked)
        
        # Premium element buttons QSS (slate hover and smooth transition states)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                color: #0f172a;
                font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                font-size: 12px;
                font-weight: 500;
                outline: none;
            }
            QPushButton:hover {
                background-color: #e2e8f0;
                border-color: #cbd5e1;
            }
            QPushButton:disabled {
                background-color: #f8fafc;
                color: #94a3b8;
                border-color: #e2e8f0;
            }
        """)
        
        layout.addWidget(self.send_btn)

    def _on_send_clicked(self):
        self.send_btn.setEnabled(False)
        self.cooldown = 60
        self.send_btn.setText(f"{self.cooldown}s")
        self.timer.start()
        self.sendClicked.emit()

    def _on_timer_tick(self):
        self.cooldown -= 1
        if self.cooldown <= 0:
            self.timer.stop()
            self.send_btn.setEnabled(True)
            self.send_btn.setText("发送验证码")
        else:
            self.send_btn.setText(f"{self.cooldown}s")

    def reset(self):
        """Resets cooldown status and enables the button instantly."""
        self.timer.stop()
        self.send_btn.setEnabled(True)
        self.send_btn.setText("发送验证码")

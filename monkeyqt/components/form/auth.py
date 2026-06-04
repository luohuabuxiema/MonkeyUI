import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame,
    QStackedWidget, QSizePolicy, QGraphicsDropShadowEffect, QLineEdit
)
from PySide6.QtCore import Qt, QPoint, QSize, QPropertyAnimation, QEasingCurve, QTimer, Signal
from PySide6.QtGui import QPainter, QColor, QPixmap, QLinearGradient, QBrush, QFont, QPen, QImage
from monkeyqt.components.form.input import MkInput
from monkeyqt.components.form.captcha import MkCaptchaWidget, MkSmsCodeWidget
from monkeyqt.components.basic.checkbox import MkCheckBox
from monkeyqt.core.icons import MkPhosphorIcon


class MkMessage(QWidget):
    """
    MkMessage - Top-center floating toast notification (Element Plus style).
    Supports success, error, warning, and info themes with slide-down animations.
    """
    def __init__(self, text: str, msg_type: str = "info", parent=None):
        # We need parent to compute floating center positioning
        super().__init__(parent)
        self.msg_type = msg_type
        self.text = text
        self.setFixedWidth(320)
        self.setFixedHeight(48)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Self delete timers
        self.cooldown_timer = QTimer(self)
        self.cooldown_timer.setSingleShot(True)
        self.cooldown_timer.setInterval(3000)
        self.cooldown_timer.timeout.connect(self._slide_up_and_delete)
        
        self._setup_ui()
        self._animate_entry()

    def _setup_ui(self):
        # Layout container
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.card = QFrame(self)
        self.card.setObjectName("MessageCard")
        card_layout = QHBoxLayout(self.card)
        card_layout.setContentsMargins(15, 0, 15, 0)
        card_layout.setSpacing(10)
        
        # Style based on message type
        styles = {
            "success": {
                "bg": "#f0f9eb", "border": "#e1f3d8", "text": "#67c23a", "icon": "check"
            },
            "error": {
                "bg": "#fef0f0", "border": "#fde2e2", "text": "#f56c6c", "icon": "x"
            },
            "warning": {
                "bg": "#fdf6ec", "border": "#faecd8", "text": "#e6a23c", "icon": "eye" # eye as placeholder
            },
            "info": {
                "bg": "#f4f4f5", "border": "#e9e9eb", "text": "#909399", "icon": "eye"
            }
        }
        
        theme = styles.get(self.msg_type, styles["info"])
        
        self.card.setStyleSheet(f"""
            QFrame#MessageCard {{
                background-color: {theme["bg"]};
                border: 1px solid {theme["border"]};
                border-radius: 6px;
            }}
            QLabel {{
                color: {theme["text"]};
                font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                font-size: 13px;
                font-weight: 500;
                background: transparent;
            }}
        """)
        
        # Phosphor status icon
        icon_label = QLabel(self.card)
        icon_label.setFixedSize(16, 16)
        icon_label.setPixmap(MkPhosphorIcon.get_pixmap(theme["icon"], theme["text"], 16))
        card_layout.addWidget(icon_label)
        
        # Message text label
        text_label = QLabel(self.text, self.card)
        card_layout.addWidget(text_label, stretch=1)
        
        # Center card shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 4)
        self.card.setGraphicsEffect(shadow)
        
        main_layout.addWidget(self.card)

    def _animate_entry(self):
        # Calculate horizontal center position relative to parent window
        parent_w = self.parentWidget().width() if self.parentWidget() else 800
        cx = (parent_w - self.width()) // 2
        
        # Position animation (slides down from y = -50 to y = 24)
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(300)
        self.anim.setStartValue(QPoint(cx, -50))
        self.anim.setEndValue(QPoint(cx, 24))
        self.anim.setEasingCurve(QEasingCurve.Type.OutBack)
        
        self.anim.start()
        self.cooldown_timer.start()

    def _slide_up_and_delete(self):
        parent_w = self.parentWidget().width() if self.parentWidget() else 800
        cx = (parent_w - self.width()) // 2
        
        # Slide back up animation
        self.exit_anim = QPropertyAnimation(self, b"pos")
        self.exit_anim.setDuration(250)
        self.exit_anim.setStartValue(QPoint(cx, self.y()))
        self.exit_anim.setEndValue(QPoint(cx, -50))
        self.exit_anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self.exit_anim.finished.connect(self.deleteLater)
        self.exit_anim.start()

    # Static global utility helpers mirroring modern element plus API
    @staticmethod
    def success(parent, text: str):
        msg = MkMessage(text, "success", parent)
        msg.show()

    @staticmethod
    def error(parent, text: str):
        msg = MkMessage(text, "error", parent)
        msg.show()

    @staticmethod
    def warning(parent, text: str):
        msg = MkMessage(text, "warning", parent)
        msg.show()

    @staticmethod
    def info(parent, text: str):
        msg = MkMessage(text, "info", parent)
        msg.show()


class MkAuthScreen(QWidget):
    """
    MkAuthScreen - Advanced login and registration form card suite.
    Features customizable backgrounds (gradients, images), optional avatars,
    dual captchas, and fluid panel switching animations.
    """
    loginSubmitted = Signal(str, str, str, bool)         # (username, password, captcha_code, remember_me)
    registerSubmitted = Signal(str, str, str, str, dict) # (username, email, password, confirm_password, custom_fields)
    smsRequested = Signal(str)                           # (email/phone)
    forgotPasswordClicked = Signal()                     # Emitted when forgot password button is clicked

    def __init__(
        self,
        logo_text: str = "MONKEY UI",
        description: str = "企业级桌面快速开发组件库",
        avatar: str = None,
        avatar_shape: str = "circle",
        captcha_type: str = "graphic",  # "none", "graphic", "sms"
        background = None,
        register_custom_fields: list = None,
        parent = None
    ):
        super().__init__(parent)
        
        self.logo_text = logo_text
        self.description = description
        self.avatar_path = avatar
        self.avatar_shape = avatar_shape
        self.captcha_type = captcha_type
        self.background_config = background or "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1e293b, stop:1 #0f172a)"
        self.register_custom_fields = register_custom_fields or []
        self.reg_custom_inputs = {}
        
        self._setup_ui()
        # Steal initial focus so no QLineEdit shows a focus border on first render
        QTimer.singleShot(0, self._steal_focus_from_inputs)

    def _setup_ui(self):
        # 1. Main centered card frame overlay layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 2. Main Glassmorphic card frame
        self.auth_card = QFrame(self)
        self.auth_card.setObjectName("AuthCard")
        
        self.auth_card.setFixedWidth(380)
        self.auth_card.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        self.auth_card.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.auth_card.setStyleSheet("""
            QFrame#AuthCard {
                background-color: rgba(255, 255, 255, 240);
                border: 1px solid rgba(255, 255, 255, 180);
                border-radius: 12px;
                outline: none;
            }
        """)
        
        # Give card a premium soft blur shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 45))
        shadow.setOffset(0, 10)
        self.auth_card.setGraphicsEffect(shadow)
        
        card_layout = QVBoxLayout(self.auth_card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(0)
        
        # --- A. Header Area (Avatar + Logo + Slogan) ---
        self.header_layout = QVBoxLayout()
        self.header_layout.setSpacing(10)
        self.header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Render Avatar if provided
        if self.avatar_path:
            self.avatar_label = QLabel(self.auth_card)
            self.avatar_label.setFixedSize(60, 60)
            self.avatar_label.setStyleSheet("background: transparent;")
            # Dynamic avatar paint masking shape in QPainter
            self._render_avatar_image()
            self.header_layout.addWidget(self.avatar_label, alignment=Qt.AlignmentFlag.AlignCenter)
            
        # Title Logo
        logo_label = QLabel(self.logo_text, self.auth_card)
        logo_label.setStyleSheet("""
            QLabel {
                font-family: "Microsoft YaHei", -apple-system, sans-serif;
                font-size: 22px;
                font-weight: 800;
                color: #0f172a;
                background: transparent;
            }
        """)
        self.header_layout.addWidget(logo_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Slogan
        desc_label = QLabel(self.description, self.auth_card)
        desc_label.setStyleSheet("""
            QLabel {
                font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                font-size: 12px;
                color: #64748b;
                background: transparent;
            }
        """)
        self.header_layout.addWidget(desc_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        card_layout.addLayout(self.header_layout)
        card_layout.addSpacing(25)
        
        # --- B. Form Content Area (Stacked Panels for sliding transitions) ---
        self.form_stack = QStackedWidget(self.auth_card)
        self.form_stack.setFrameShape(QFrame.Shape.NoFrame)
        self.form_stack.setStyleSheet("QStackedWidget { background: transparent; border: none; }")
        
        self._setup_login_panel()
        self._setup_register_panel()
        
        card_layout.addWidget(self.form_stack)
        self.main_layout.addWidget(self.auth_card, alignment=Qt.AlignmentFlag.AlignCenter)

    def _render_avatar_image(self):
        """Draws the cropped avatar with circle or rounded square masks."""
        pixmap = QPixmap(self.avatar_path)
        if pixmap.isNull():
            # Draw initial avatar fallback using a colored circle
            pixmap = QPixmap(60, 60)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setBrush(QColor("#3b82f6"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(0, 0, 60, 60)
            painter.setPen(QColor("#ffffff"))
            font = QFont("Microsoft YaHei", 16, QFont.Weight.Bold)
            painter.setFont(font)
            painter.drawText(0, 0, 60, 60, Qt.AlignmentFlag.AlignCenter, "M")
            painter.end()
            self.avatar_label.setPixmap(pixmap)
            return

        size = QSize(60, 60)
        target = QPixmap(size)
        target.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(target)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Create clip path
        from PySide6.QtGui import QPainterPath
        path = QPainterPath()
        if self.avatar_shape == "circle":
            path.addEllipse(0, 0, 60, 60)
        else:
            path.addRoundedRect(0, 0, 60, 60, 8, 8)
            
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, 60, 60, pixmap.scaled(size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation))
        painter.end()
        
        self.avatar_label.setPixmap(target)

    def _setup_login_panel(self):
        """Builds the Login panel container widget."""
        panel = QWidget()
        panel.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # User input field
        self.login_user = MkInput("请输入用户名 / 邮箱", is_password=False, leading_icon="pencil", parent=panel)
        layout.addWidget(self.login_user)
        
        # Password input field
        self.login_pwd = MkInput("请输入密码", is_password=True, leading_icon="pencil", parent=panel)
        layout.addWidget(self.login_pwd)
        
        # Captcha field (conditional)
        self.login_captcha = None
        self.graphic_captcha_widget = None
        
        if self.captcha_type == "graphic":
            captcha_layout = QHBoxLayout()
            captcha_layout.setSpacing(10)
            
            self.login_captcha = MkInput("输入验证码", is_password=False, parent=panel)
            captcha_layout.addWidget(self.login_captcha, stretch=1)
            
            self.graphic_captcha_widget = MkCaptchaWidget(100, 36, panel)
            captcha_layout.addWidget(self.graphic_captcha_widget)
            
            layout.addLayout(captcha_layout)
            
        elif self.captcha_type == "sms":
            self.login_captcha = MkInput("输入短信验证码", is_password=False, parent=panel)
            sms_widget = MkSmsCodeWidget(self.login_captcha, panel)
            sms_widget.sendClicked.connect(self._on_sms_requested)
            layout.addWidget(sms_widget)
            
        # Remember me & Forgot password row
        self.login_options_layout = QHBoxLayout()
        self.login_options_layout.setContentsMargins(0, 2, 0, 2)
        
        # Remember Me Checkbox
        self.remember_checkbox = MkCheckBox("记住我", panel)
        self.remember_checkbox.setStyleSheet("""
            MkCheckBox {
                color: #64748b;
                font-size: 12px;
            }
            MkCheckBox:hover {
                color: #3b82f6;
            }
        """)
        self.login_options_layout.addWidget(self.remember_checkbox)
        
        self.login_options_layout.addStretch()
        
        # Forgot Password Button
        self.forgot_pwd_btn = QPushButton("忘记密码？", panel)
        self.forgot_pwd_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.forgot_pwd_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.forgot_pwd_btn.setAutoDefault(False)
        self.forgot_pwd_btn.setDefault(False)
        self.forgot_pwd_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #64748b;
                font-size: 12px;
                text-align: right;
                outline: none;
            }
            QPushButton:hover {
                color: #3b82f6;
                text-decoration: underline;
            }
        """)
        self.forgot_pwd_btn.clicked.connect(self.forgotPasswordClicked.emit)
        self.login_options_layout.addWidget(self.forgot_pwd_btn)
        
        layout.addLayout(self.login_options_layout)

        # Submit Button
        self.login_submit_btn = QPushButton("立即登录", panel)
        self.login_submit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_submit_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.login_submit_btn.setAutoDefault(False)
        self.login_submit_btn.setDefault(False)
        self.login_submit_btn.setFixedHeight(38)
        self.login_submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                border: none;
                border-radius: 6px;
                color: #ffffff;
                font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                font-size: 13px;
                font-weight: bold;
                outline: none;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
            QPushButton:pressed {
                background-color: #1d4ed8;
            }
        """)
        self.login_submit_btn.clicked.connect(self._on_login_submitted)
        layout.addWidget(self.login_submit_btn)
        
        # Toggle links
        link_layout = QHBoxLayout()
        link_layout.setContentsMargins(0, 5, 0, 0)
        
        register_link = QPushButton("没有账号？立即注册", panel)
        register_link.setCursor(Qt.CursorShape.PointingHandCursor)
        register_link.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        register_link.setAutoDefault(False)
        register_link.setDefault(False)
        register_link.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #3b82f6;
                font-size: 12px;
                text-align: left;
                outline: none;
            }
            QPushButton:hover {
                color: #2563eb;
                text-decoration: underline;
            }
        """)
        register_link.clicked.connect(lambda: self.switch_mode("register"))
        link_layout.addWidget(register_link)
        link_layout.addStretch()
        
        layout.addLayout(link_layout)
        
        self.form_stack.addWidget(panel)

    def _setup_register_panel(self):
        """Builds the Registration panel container widget."""
        panel = QWidget()
        panel.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Username field
        self.reg_user = MkInput("请设置用户名", is_password=False, leading_icon="pencil", parent=panel)
        layout.addWidget(self.reg_user)
        
        # Email field
        self.reg_email = MkInput("请输入邮箱地址", is_password=False, leading_icon="pencil", parent=panel)
        layout.addWidget(self.reg_email)
        
        # Password field
        self.reg_pwd = MkInput("请设置登录密码", is_password=True, leading_icon="pencil", parent=panel)
        layout.addWidget(self.reg_pwd)
        
        # Confirm Password field
        self.reg_pwd_confirm = MkInput("请再次确认密码", is_password=True, leading_icon="pencil", parent=panel)
        layout.addWidget(self.reg_pwd_confirm)
        
        # Dynamic Custom Fields
        for field in self.register_custom_fields:
            name = field.get("name")
            placeholder = field.get("placeholder", f"请输入{name}")
            icon = field.get("icon", "pencil")
            is_password = field.get("is_password", False)
            
            custom_input = MkInput(placeholder, is_password=is_password, leading_icon=icon, parent=panel)
            layout.addWidget(custom_input)
            self.reg_custom_inputs[name] = custom_input
            
        # Submit register
        self.reg_submit_btn = QPushButton("立即注册", panel)
        self.reg_submit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reg_submit_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.reg_submit_btn.setAutoDefault(False)
        self.reg_submit_btn.setDefault(False)
        self.reg_submit_btn.setFixedHeight(38)
        self.reg_submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                border: none;
                border-radius: 6px;
                color: #ffffff;
                font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                font-size: 13px;
                font-weight: bold;
                outline: none;
            }
            QPushButton:hover {
                background-color: #059669;
            }
            QPushButton:pressed {
                background-color: #047857;
            }
        """)
        self.reg_submit_btn.clicked.connect(self._on_register_submitted)
        layout.addWidget(self.reg_submit_btn)
        
        # Return login link
        link_layout = QHBoxLayout()
        link_layout.setContentsMargins(0, 5, 0, 0)
        
        login_link = QPushButton("已有账号？返回登录", panel)
        login_link.setCursor(Qt.CursorShape.PointingHandCursor)
        login_link.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        login_link.setAutoDefault(False)
        login_link.setDefault(False)
        login_link.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #64748b;
                font-size: 12px;
                text-align: left;
                outline: none;
            }
            QPushButton:hover {
                color: #475569;
                text-decoration: underline;
            }
        """)
        login_link.clicked.connect(lambda: self.switch_mode("login"))
        link_layout.addWidget(login_link)
        link_layout.addStretch()
        
        layout.addLayout(link_layout)
        
        self.form_stack.addWidget(panel)
        
        # After both panels are added, set non-current pages to Ignored so
        # QStackedWidget only sizes to the active page
        self._adjust_stacked_size(0)

    def _adjust_stacked_size(self, index):
        """Set non-active pages to Ignored so QStackedWidget shrinks to fit the current page."""
        for i in range(self.form_stack.count()):
            widget = self.form_stack.widget(i)
            if i == index:
                widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
            else:
                widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Ignored)
        self.form_stack.adjustSize()
        self.auth_card.adjustSize()

    def switch_mode(self, mode: str):
        """Seamlessly transitions the Stacked widget panels."""
        if mode == "login":
            self.form_stack.setCurrentIndex(0)
            self._adjust_stacked_size(0)
            if self.graphic_captcha_widget:
                self.graphic_captcha_widget.generate_new_code()
        else:
            self.form_stack.setCurrentIndex(1)
            self._adjust_stacked_size(1)
        
        # CRITICAL: After setCurrentIndex(), Qt's focus chain auto-assigns focus
        # to the first QLineEdit on the new panel, causing its blue focus border
        # (the "vertical line") to render. We MUST steal focus away from all
        # QLineEdits by redirecting it to the auth_card (which has outline:none
        # and renders no focus indicator). We use QTimer.singleShot(0) to ensure
        # this runs AFTER Qt finishes its internal focus chain processing.
        QTimer.singleShot(0, self._steal_focus_from_inputs)

    def _steal_focus_from_inputs(self):
        """Redirect focus to auth_card so no QLineEdit shows a focus border."""
        # Deactivate all QLineEdit cursors across both panels
        for i in range(self.form_stack.count()):
            panel = self.form_stack.widget(i)
            for line_edit in panel.findChildren(QLineEdit):
                line_edit.deselect()
                line_edit.setCursorPosition(0)
                line_edit.clearFocus()
        # Redirect focus to auth_card — it accepts StrongFocus but renders
        # no visual indicator thanks to outline:none in its stylesheet.
        self.auth_card.setFocus(Qt.FocusReason.OtherFocusReason)
        
        # CRITICAL: Force a full repaint of the card to eliminate the 1-px ghosting artifact
        # left by Qt's dirty region calculation when hiding rounded-corner buttons in transparent layouts.
        self.auth_card.update()
        self.auth_card.repaint()

    def add_register_field(self, name: str, placeholder: str = "", icon: str = "pencil", is_password: bool = False):
        """
        Dynamically appends a single custom input box to the registration form.
        Automatically handles card vertical sizing adjustments.
        """
        if name in self.reg_custom_inputs:
            return # Prevent duplicate additions
            
        # 1. Create input
        panel = self.reg_pwd_confirm.parentWidget()
        custom_input = MkInput(placeholder, is_password=is_password, leading_icon=icon, parent=panel)
        
        # 2. Find registration layout and submit button index
        reg_layout = panel.layout()
        idx = reg_layout.indexOf(self.reg_submit_btn)
        if idx == -1:
            idx = reg_layout.count() - 2
            
        # 3. Insert input above the submit button
        reg_layout.insertWidget(idx, custom_input)
        
        # 4. Save mapping
        self.reg_custom_inputs[name] = custom_input
        
        # Ensure the widget is rendered and shown
        custom_input.show()
        
        # 5. Automatically adjust card size based on layout size hints
        self._adjust_stacked_size(1)
        
        # Explicitly trigger updates
        self.auth_card.updateGeometry()
        if self.parentWidget():
            self.parentWidget().updateGeometry()

    def _on_login_submitted(self):
        username = self.login_user.text().strip()
        password = self.login_pwd.text()
        captcha = self.login_captcha.text().strip() if self.login_captcha else ""
        
        # Standard input validations
        if not username:
            MkMessage.error(self, "请输入用户名")
            return
        if not password:
            MkMessage.error(self, "请输入密码")
            return
            
        # Graphic captcha code checks
        if self.captcha_type == "graphic" and self.graphic_captcha_widget:
            correct_code = self.graphic_captcha_widget.get_code()
            if captcha.upper() != correct_code.upper():
                MkMessage.error(self, "图形验证码错误，请重新输入")
                self.graphic_captcha_widget.generate_new_code()
                return
                
        # Get remember state
        remember_me = self.remember_checkbox.isChecked()
        
        # Emit submission coordinates for parent validation logic (e.g. databases, SQL query callbacks)
        self.loginSubmitted.emit(username, password, captcha, remember_me)

    def _on_register_submitted(self):
        username = self.reg_user.text().strip()
        email = self.reg_email.text().strip()
        password = self.reg_pwd.text()
        confirm = self.reg_pwd_confirm.text()
        
        if not username:
            MkMessage.error(self, "请设置用户名")
            return
        if not email:
            MkMessage.error(self, "请输入邮箱")
            return
        if "@" not in email:
            MkMessage.error(self, "邮箱格式不正确")
            return
        if len(password) < 6:
            MkMessage.error(self, "密码长度必须大于等于 6 位")
            return
        if password != confirm:
            MkMessage.error(self, "两次输入的密码不一致")
            return
            
        # Collect dynamic custom fields data
        custom_data = {}
        for name, input_widget in self.reg_custom_inputs.items():
            custom_data[name] = input_widget.text().strip()
            
        self.registerSubmitted.emit(username, email, password, confirm, custom_data)

    def _on_sms_requested(self):
        # Notify sms triggers
        email = self.login_user.text().strip()
        if not email:
            MkMessage.error(self, "请先在上方输入账号 / 手机号")
            return
        self.smsRequested.emit(email)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        
        # 3. Dynamic background render engine
        if isinstance(self.background_config, str):
            if self.background_config.startswith("qlineargradient"):
                # Interpret CSS-like linear gradient variables
                gradient = self._parse_gradient_string(self.background_config, rect)
                painter.fillRect(rect, QBrush(gradient))
            elif self.background_config.startswith("#"):
                # Interpret hex colors
                painter.fillRect(rect, QColor(self.background_config))
            elif os.path.exists(self.background_config):
                # Interpret image files path
                bg_pix = QPixmap(self.background_config)
                painter.drawPixmap(rect, bg_pix.scaled(rect.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation))
            else:
                # Default backup color (dark slate color)
                painter.fillRect(rect, QColor("#0f172a"))
        elif isinstance(self.background_config, QPixmap):
            painter.drawPixmap(rect, self.background_config.scaled(rect.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation))
        else:
            painter.fillRect(rect, QColor("#0f172a"))
            
        painter.end()

    def _parse_gradient_string(self, css_grad: str, rect) -> QLinearGradient:
        """Parses custom gradient strings dynamically into QLinearGradients."""
        # Configures fallback royal deep purple gradients if values parse incorrectly
        grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
        grad.setColorAt(0.0, QColor("#4f46e5"))
        grad.setColorAt(1.0, QColor("#06b6d4"))
        
        try:
            # Example: "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1e293b, stop:1 #0f172a)"
            content = css_grad[css_grad.find("(")+1 : css_grad.rfind(")")]
            tokens = [t.strip() for t in content.split(",") if t.strip()]
            
            # Map start/ends coordinates
            x1, y1, x2, y2 = 0.0, 0.0, 1.0, 1.0
            stops = []
            
            for token in tokens:
                if ":" in token:
                    k, v = token.split(":")
                    k = k.strip()
                    v = v.strip()
                    if k == "x1": x1 = float(v)
                    elif k == "y1": y1 = float(v)
                    elif k == "x2": x2 = float(v)
                    elif k == "y2": y2 = float(v)
                    elif k == "stop":
                        stop_idx, stop_color = v.split(" ")
                        stops.append((float(stop_idx), stop_color.strip()))
            
            # Reconstruct linear coordinates
            g_start = QPoint(int(rect.x() + rect.width() * x1), int(rect.y() + rect.height() * y1))
            g_end = QPoint(int(rect.x() + rect.width() * x2), int(rect.y() + rect.height() * y2))
            grad = QLinearGradient(g_start, g_end)
            
            for idx, col in stops:
                grad.setColorAt(idx, QColor(col))
                
        except Exception:
            pass # Return royal purple gradient as fallback safety
            
        return grad

# -*- coding: utf-8 -*-
"""
@File ：window.py
@Desc ：Custom title bar and frameless window components for MonkeyQt.
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QGraphicsDropShadowEffect, QFrame,
    QSizePolicy, QSpacerItem
)
from PySide6.QtCore import Qt, QPoint, Signal, QEvent, QRect, QSize
from PySide6.QtGui import QFont, QCursor, QColor, QMouseEvent, QIcon
from monkeyqt.core.icons import MkPhosphorIcon

class MkTitleBar(QWidget):
    """
    Customizable title bar component mimicking modern UI designs.
    Supports presets: 'default', 'shadcn', 'ida', 'sunlogin', 'soda', 'antigravity'
    """
    
    closeClicked = Signal()
    minimizeClicked = Signal()
    maximizeClicked = Signal()
    
    def __init__(self, parent=None, preset="default"):
        super().__init__(parent)
        self.parent_window = parent
        self._preset = preset
        
        # Custom properties that can override presets
        self._bg_color = None
        self._text_color = None
        self._hover_color = None
        self._height = 40
        self._button_style = "windows"  # "windows" (right controls) or "macos" (left traffic lights)
        self._title_visible = True
        self._icon_visible = True
        self._border_bottom = ""
        
        # Dragging state
        self._drag_pos = None
        
        # Layouts
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(10, 0, 0, 0)
        self.main_layout.setSpacing(10)
        
        # UI Elements
        self.icon_label = QLabel()
        self.title_label = QLabel()
        self.title_label.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Medium))
        
        # Container for center custom widgets
        self.center_container = QWidget()
        self.center_layout = QHBoxLayout(self.center_container)
        self.center_layout.setContentsMargins(0, 0, 0, 0)
        self.center_layout.setSpacing(6)
        
        # Window control buttons
        self.btn_min = QPushButton()
        self.btn_min.setObjectName("TitleBarMinButton")
        self.btn_max = QPushButton()
        self.btn_max.setObjectName("TitleBarMaxButton")
        self.btn_close = QPushButton()
        self.btn_close.setObjectName("TitleBarCloseButton")
        
        self.btn_min.setFixedSize(28, 28)
        self.btn_max.setFixedSize(28, 28)
        self.btn_close.setFixedSize(28, 28)
        
        # Connect signals
        self.btn_min.clicked.connect(self._on_minimize)
        self.btn_max.clicked.connect(self._on_maximize)
        self.btn_close.clicked.connect(self._on_close)
        
        # Set cursor
        self.btn_min.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_max.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.apply_preset(preset)
        self.rebuild_layout()

    def set_title(self, title: str):
        self.title_label.setText(title)

    def set_icon(self, pixmap):
        if pixmap:
            self.icon_label.setPixmap(pixmap.scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            self.icon_label.setVisible(self._icon_visible)
        else:
            self.icon_label.setVisible(False)

    def apply_preset(self, preset: str):
        self._preset = preset
        
        # Clear any dynamic widgets in the center
        while self.center_layout.count():
            item = self.center_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        if preset == "shadcn":
            self._bg_color = "#ffffff" if not self._is_dark_theme() else "#09090b"
            self._text_color = "#09090b" if not self._is_dark_theme() else "#fafafa"
            self._hover_color = "#f4f4f5" if not self._is_dark_theme() else "#27272a"
            self._height = 40
            self._button_style = "windows"
            self.title_label.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
            self._border_bottom = f"1px solid {'#e4e4e7' if not self._is_dark_theme() else '#27272a'}"
            
        elif preset == "ida":
            self._bg_color = "#2d2d2d"
            self._text_color = "#d3d3d3"
            self._hover_color = "#3f3f3f"
            self._height = 36
            self._button_style = "windows"
            self.title_label.setFont(QFont("Consolas", 9))
            self._border_bottom = "1px solid #3f3f3f"
            
            # Decorative: Show a green ready status indicator and a code-style path
            status_dot = QFrame()
            status_dot.setFixedSize(8, 8)
            status_dot.setStyleSheet("background-color: #2ec872; border-radius: 4px;")
            self.center_layout.addWidget(status_dot)
            
            env_label = QLabel("[IDA Pro - Active Session]")
            env_label.setStyleSheet("color: #858585; font-family: Consolas; font-size: 11px;")
            self.center_layout.addWidget(env_label)
            self.center_layout.addStretch()
            
        elif preset == "sunlogin":
            self._bg_color = "#1e1f22"  # Dark Theme
            self._text_color = "#ffffff"
            self._hover_color = "#2d3035"
            self._height = 48
            self._button_style = "windows"
            self.title_label.setFont(QFont("Microsoft YaHei", 9, QFont.Weight.Bold))
            
            # Sunlogin Search Input decoration
            search_input = QLineEdit()
            search_input.setPlaceholderText("输入设备识别码以远程控制...")
            search_input.setFixedWidth(220)
            search_input.setStyleSheet("""
                QLineEdit {
                    background-color: #2b2d30;
                    border: 1px solid #3f4247;
                    border-radius: 4px;
                    padding: 2px 8px;
                    color: #cfd3dc;
                    font-size: 11px;
                }
                QLineEdit:focus {
                    border-color: #ff6b1a;
                }
            """)
            self.center_layout.addStretch()
            self.center_layout.addWidget(search_input)
            self.center_layout.addStretch()
            
        elif preset == "soda":
            # Soda Music style: Translucent acrylic look with macOS buttons on the left
            self._bg_color = "rgba(18, 18, 18, 0.85)"
            self._text_color = "#ffffff"
            self._hover_color = "rgba(255, 255, 255, 0.15)"
            self._height = 56
            self._button_style = "macos"
            self.title_label.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.DemiBold))
            
            # Central search bar mimicking music app
            search_input = QLineEdit()
            search_input.setPlaceholderText("🔍 搜索音乐、歌手、歌单...")
            search_input.setFixedWidth(260)
            search_input.setStyleSheet("""
                QLineEdit {
                    background-color: rgba(255, 255, 255, 0.1);
                    border: none;
                    border-radius: 14px;
                    padding: 4px 12px;
                    color: #eaeaea;
                    font-size: 12px;
                }
            """)
            self.center_layout.addStretch()
            self.center_layout.addWidget(search_input)
            self.center_layout.addStretch()
            
        elif preset == "antigravity":
            self._bg_color = "#1e1e2e"  # Deep Catppuccin Mocha style
            self._text_color = "#cdd6f4"
            self._hover_color = "#313244"
            self._height = 42
            self._button_style = "windows"
            self.title_label.setFont(QFont("Outfit", 9, QFont.Weight.Medium))
            self._border_bottom = "1px solid #313244"
            
            # Centered path & branch widget
            breadcrumb = QLabel("src/monkeyqt/components/layout/window.py")
            breadcrumb.setStyleSheet("color: #a6adc8; font-size: 11px; font-family: Consolas;")
            branch_info = QLabel("⌥ main")
            branch_info.setStyleSheet("color: #f9e2af; font-size: 11px; font-weight: bold; background-color: #313244; padding: 2px 6px; border-radius: 4px;")
            
            self.center_layout.addStretch()
            self.center_layout.addWidget(breadcrumb)
            self.center_layout.addWidget(branch_info)
            self.center_layout.addStretch()
            
        else:  # "default"
            self._bg_color = "#f3f4f6" if not self._is_dark_theme() else "#1f2937"
            self._text_color = "#374151" if not self._is_dark_theme() else "#f9fafb"
            self._hover_color = "#e5e7eb" if not self._is_dark_theme() else "#374151"
            self._height = 38
            self._button_style = "windows"
            self.title_label.setFont(QFont("Microsoft YaHei", 9))
            
        self.apply_theme_colors()

    def _is_dark_theme(self):
        # Fallback helper, standard light mode checking
        return False

    def apply_theme_colors(self):
        # Apply style sheet to titlebar background
        bg = self._bg_color if self._bg_color else "#ffffff"
        text = self._text_color if self._text_color else "#000000"
        border_css = f"border-bottom: {self._border_bottom};" if hasattr(self, '_border_bottom') and self._border_bottom else ""
        
        self.setObjectName("MkTitleBar")
        self.setStyleSheet(f"""
            QWidget#MkTitleBar {{
                background-color: {bg};
                color: {text};
                {border_css}
            }}
            QLabel {{
                color: {text};
                background: transparent;
            }}
        """)
        
        # Style buttons based on style choice
        self.update_buttons()

    def update_buttons(self):
        text_color = self._text_color if self._text_color else "#000000"
        hover_color = self._hover_color if self._hover_color else "rgba(0,0,0,0.1)"
        
        # Get icons (render at higher resolution for High-DPI crispness)
        icon_min = MkPhosphorIcon.get_icon("minus", text_color, text_color, 12)
        icon_close = MkPhosphorIcon.get_icon("x", text_color, "#ffffff" if self._preset != "soda" else text_color, 12)
        
        is_max = False
        if self.parent_window and self.parent_window.window():
            is_max = self.parent_window.window().isMaximized()
        icon_max = MkPhosphorIcon.get_icon("restore" if is_max else "square", text_color, text_color, 12)
        
        self.btn_min.setIcon(icon_min)
        self.btn_max.setIcon(icon_max)
        self.btn_close.setIcon(icon_close)
        
        if self._button_style == "macos":
            # Traffic Light style for macOS
            # Close: Red, Min: Yellow, Max: Green
            self.btn_close.setIcon(QIcon())
            self.btn_min.setIcon(QIcon())
            self.btn_max.setIcon(QIcon())
            
            self.btn_close.setStyleSheet(f"""
                QPushButton {{ background-color: #ff5f56; border: none; border-radius: 6px; }}
                QPushButton:hover {{ background-color: #e0443e; }}
            """)
            self.btn_min.setStyleSheet(f"""
                QPushButton {{ background-color: #ffbd2e; border: none; border-radius: 6px; }}
                QPushButton:hover {{ background-color: #dfa220; }}
            """)
            self.btn_max.setStyleSheet(f"""
                QPushButton {{ background-color: #27c93f; border: none; border-radius: 6px; }}
                QPushButton:hover {{ background-color: #1aab30; }}
            """)
            
            self.btn_close.setFixedSize(12, 12)
            self.btn_min.setFixedSize(12, 12)
            self.btn_max.setFixedSize(12, 12)
        else:
            # Standard Windows Style — full-height, flush buttons like native chrome
            btn_h = self._height
            btn_w = 46
            self.btn_min.setFixedSize(btn_w, btn_h)
            self.btn_max.setFixedSize(btn_w, btn_h)
            self.btn_close.setFixedSize(btn_w, btn_h)
            
            # Explicitly set icon size to prevent Qt from scaling small bitmaps, maintaining pixel sharpness
            from PySide6.QtCore import QSize
            self.btn_min.setIconSize(QSize(12, 12))
            self.btn_max.setIconSize(QSize(12, 12))
            self.btn_close.setIconSize(QSize(12, 12))
            
            self.btn_min.setStyleSheet(f"""
                QPushButton {{ background-color: transparent; border: none; border-radius: 0px; }}
                QPushButton:hover {{ background-color: {hover_color}; }}
            """)
            self.btn_max.setStyleSheet(f"""
                QPushButton {{ background-color: transparent; border: none; border-radius: 0px; }}
                QPushButton:hover {{ background-color: {hover_color}; }}
            """)
            self.btn_close.setStyleSheet(f"""
                QPushButton {{ background-color: transparent; border: none; border-radius: 0px; }}
                QPushButton:hover {{ background-color: #e81123; color: #ffffff; }}
            """)

    def rebuild_layout(self):
        # Remove all items first — handle both widgets and sub-layouts
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            if item.layout():
                # Clear sub-layout widgets (don't delete the buttons themselves)
                sub = item.layout()
                while sub.count():
                    sub.takeAt(0)
        
        # Build layout according to macOS or Windows styling
        if self._button_style == "macos":
            # Buttons on the left, then icon, title, center container
            # Spacing for macos traffic lights
            mac_buttons_layout = QHBoxLayout()
            mac_buttons_layout.setContentsMargins(6, 0, 6, 0)
            mac_buttons_layout.setSpacing(6)
            mac_buttons_layout.addWidget(self.btn_close)
            mac_buttons_layout.addWidget(self.btn_min)
            mac_buttons_layout.addWidget(self.btn_max)
            
            self.main_layout.addLayout(mac_buttons_layout)
            self.main_layout.addWidget(self.icon_label)
            self.main_layout.addWidget(self.title_label)
            self.main_layout.addWidget(self.center_container, stretch=1)
        else:
            # Icon, Title, Center Container, then Buttons flush-right
            self.main_layout.addWidget(self.icon_label)
            self.main_layout.addWidget(self.title_label)
            self.main_layout.addWidget(self.center_container, stretch=1)
            
            # Group buttons with 0 spacing for native Windows chrome look
            win_buttons_layout = QHBoxLayout()
            win_buttons_layout.setContentsMargins(0, 0, 0, 0)
            win_buttons_layout.setSpacing(0)
            win_buttons_layout.addWidget(self.btn_min)
            win_buttons_layout.addWidget(self.btn_max)
            win_buttons_layout.addWidget(self.btn_close)
            self.main_layout.addLayout(win_buttons_layout)

        # Enforce the height — sizeHint() alone is only advisory
        self.setFixedHeight(self._height)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._drag_pos is not None:
            delta = event.globalPosition().toPoint() - self._drag_pos
            window = self.window()
            if window.isMaximized():
                # If moving a maximized window, restore it first
                # Calculate proper ratio so it doesn't jump
                normal_width = window.normalGeometry().width()
                click_x_ratio = event.position().x() / self.width()
                
                window.showNormal()
                
                # Move window under mouse cursor
                new_x = event.globalPosition().toPoint().x() - int(normal_width * click_x_ratio)
                new_y = event.globalPosition().toPoint().y() - event.position().y()
                window.move(new_x, new_y)
            else:
                window.move(window.pos() + delta)
            self._drag_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = None
        event.accept()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._on_maximize()
            event.accept()

    def sizeHint(self) -> QSize:
        return QSize(100, self._height)

    def _on_minimize(self):
        self.minimizeClicked.emit()
        if self.parent_window:
            self.parent_window.showMinimized()

    def _on_maximize(self):
        self.maximizeClicked.emit()
        if self.parent_window:
            if self.parent_window.isMaximized():
                self.parent_window.showNormal()
            else:
                self.parent_window.showMaximized()
            self.update_buttons()

    def _on_close(self):
        self.closeClicked.emit()
        if self.parent_window:
            self.parent_window.close()

# Custom resize direction flags
RESIZE_NONE = 0
RESIZE_LEFT = 1
RESIZE_RIGHT = 2
RESIZE_TOP = 4
RESIZE_BOTTOM = 8

class MkWindow(QMainWindow):
    """
    Standard window class for MonkeyQt supporting native frames or custom title bars
    with border resizing, custom presets, and drop shadows.
    """
    
    def __init__(
        self,
        use_custom_title_bar=True,
        preset="default",
        parent=None,
        sidebar_full_height=False,
    ):
        super().__init__(parent)
        self.use_custom_title_bar = use_custom_title_bar
        self._preset = preset
        self._sidebar_full_height = bool(sidebar_full_height)
        self._close_behavior = "close"  # "close" or "hide"
        self._border_radius = 8
        self._normal_geometry = None
        
        # Resizing states
        self._resize_margin = 8
        self._resizing_dir = RESIZE_NONE
        self._resize_start_pos = None
        self._resize_start_geometry = None
        
        # Structure elements
        self._shadow_effect = None
        self.shadow_layout = None
        self.outer_layout = None
        self.container_frame = None
        self.container_layout = None
        self.titlebar = None
        self.user_central_widget = None
        self._desktop_shell = None
        self._desktop_shell_layout = None
        self._sidebar_host = None
        self._sidebar_host_layout = None
        self._content_host = None
        self._content_host_layout = None
        self._promoted_sidebar = None
        self._sidebar_source_layout = None
        self._sidebar_source_index = -1
        
        self.setMouseTracking(True)
        
        if self.use_custom_title_bar:
            self.init_custom_frame()
        else:
            self.init_native_frame()

    def init_native_frame(self):
        # Standard QMainWindow behavior
        self.setWindowFlags(Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

    def init_custom_frame(self):
        # Custom frameless behavior
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        # 1. Root outer layout to support padding for drop shadow
        self._root_widget = QWidget(self)
        self._root_widget.setMouseTracking(True)
        self.shadow_layout = QVBoxLayout(self._root_widget)
        # Margin of 10px gives space for the shadow to draw
        self.shadow_layout.setContentsMargins(10, 10, 10, 10)
        self.shadow_layout.setSpacing(0)
        
        # 2. Main container widget that has styling (border, radius, background)
        self.container_frame = QFrame(self._root_widget)
        self.container_frame.setObjectName("MkWindowContainer")
        self.container_frame.setFrameShape(QFrame.Shape.NoFrame)
        self.container_frame.setMouseTracking(True)
        
        self.container_layout = QVBoxLayout(self.container_frame)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(0)

        # Desktop shell. In the default mode the hidden sidebar host takes no
        # space, so the layout is identical to the original top/bottom layout.
        self._desktop_shell = QWidget(self.container_frame)
        self._desktop_shell.setObjectName("MkWindowDesktopShell")
        self._desktop_shell.setProperty("mkDesktopShell", True)
        self._desktop_shell_layout = QHBoxLayout(self._desktop_shell)
        self._desktop_shell_layout.setContentsMargins(0, 0, 0, 0)
        self._desktop_shell_layout.setSpacing(0)

        self._sidebar_host = QWidget(self._desktop_shell)
        self._sidebar_host.setObjectName("MkWindowSidebarHost")
        self._sidebar_host.setProperty("mkSidebarHost", True)
        self._sidebar_host.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Expanding,
        )
        self._sidebar_host_layout = QVBoxLayout(self._sidebar_host)
        self._sidebar_host_layout.setContentsMargins(0, 0, 0, 0)
        self._sidebar_host_layout.setSpacing(0)
        self._sidebar_host.hide()

        self._content_host = QWidget(self._desktop_shell)
        self._content_host.setObjectName("MkWindowContentHost")
        self._content_host.setProperty("mkContentHost", True)
        self._content_host.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self._content_host_layout = QVBoxLayout(self._content_host)
        self._content_host_layout.setContentsMargins(0, 0, 0, 0)
        self._content_host_layout.setSpacing(0)

        self._desktop_shell_layout.addWidget(self._sidebar_host)
        self._desktop_shell_layout.addWidget(self._content_host, stretch=1)
        self.container_layout.addWidget(self._desktop_shell, stretch=1)
        
        # Apply Shadow Effect
        self._shadow_effect = QGraphicsDropShadowEffect(self)
        self._shadow_effect.setBlurRadius(15)
        self._shadow_effect.setColor(QColor(0, 0, 0, 45))
        self._shadow_effect.setOffset(0, 4)
        self.container_frame.setGraphicsEffect(self._shadow_effect)
        
        # 3. Create Title Bar
        self.titlebar = MkTitleBar(self, preset=self._preset)
        self._sync_sidebar_mode_properties()
        self._content_host_layout.addWidget(self.titlebar)
        
        self.shadow_layout.addWidget(self.container_frame)
        super().setCentralWidget(self._root_widget)
        
        self.update_style()

    def set_preset(self, preset: str):
        self._preset = preset
        if self.titlebar:
            self.titlebar.apply_preset(preset)
            self.update_style()

    def set_close_behavior(self, behavior: str):
        if behavior in ["close", "hide"]:
            self._close_behavior = behavior

    def set_border_radius(self, radius: int):
        self._border_radius = radius
        self.update_style()

    def set_sidebar_full_height(self, enabled: bool):
        """
        Switch between the classic top title bar layout and a desktop layout
        where the sidebar occupies the full window height.

        The first direct MkMenu child in the central widget is detected
        automatically, so callers only need to toggle this one option.
        """
        self._sidebar_full_height = bool(enabled)
        self._sync_sidebar_mode_properties()
        self._apply_sidebar_layout()

    def _sync_sidebar_mode_properties(self):
        """Expose the desktop split mode to the global theme adapter."""
        if self.titlebar is None:
            return

        self.titlebar.setProperty(
            "mkContentAlignedTitleBar",
            self._sidebar_full_height,
        )
        self.titlebar.apply_theme_colors()
        style = self.titlebar.style()
        style.unpolish(self.titlebar)
        style.polish(self.titlebar)
        self.titlebar.update()

    def update_style(self):
        if not self.use_custom_title_bar:
            return
            
        radius = 0 if self.isMaximized() else self._border_radius
        bg_color = self.titlebar._bg_color if self.titlebar._bg_color else "#ffffff"
        
        # Container style with rounded corners and border
        border_color = "#e4e4e7" if self._preset == "shadcn" else "#3f3f3f" if self._preset == "ida" else "#313244" if self._preset == "antigravity" else "#d1d5db"
        
        # Dark presets backgrounds
        window_bg = "#ffffff"
        if self._preset in ["ida", "sunlogin", "soda", "antigravity"]:
            window_bg = "#1e1e2e" if self._preset == "antigravity" else "#1e1f22" if self._preset == "sunlogin" else "#121212" if self._preset == "soda" else "#1a1a1a"
            
        self.container_frame.setStyleSheet(f"""
            QFrame#MkWindowContainer {{
                background-color: {window_bg};
                border: 1px solid {border_color};
                border-radius: {radius}px;
            }}
        """)

    def setCentralWidget(self, widget: QWidget):
        if not self.use_custom_title_bar:
            super().setCentralWidget(widget)
            return
            
        # If custom frame, place the page under the title bar in the content
        # column. The sidebar can then be promoted beside this column.
        if self.user_central_widget:
            self._restore_promoted_sidebar()
            self._content_host_layout.removeWidget(self.user_central_widget)
            self.user_central_widget.deleteLater()
            
        self.user_central_widget = widget
        if widget:
            widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            widget.setMouseTracking(True)
            self._content_host_layout.addWidget(widget, stretch=1)
            self._apply_sidebar_layout()

    def _apply_sidebar_layout(self):
        if not self.use_custom_title_bar or not self.user_central_widget:
            return

        if not self._sidebar_full_height:
            self._restore_promoted_sidebar()
            return

        if self._promoted_sidebar is not None:
            return

        sidebar_info = self._find_sidebar_candidate(self.user_central_widget)
        if sidebar_info is None:
            return

        sidebar, source_layout, source_index = sidebar_info
        self._promoted_sidebar = sidebar
        self._sidebar_source_layout = source_layout
        self._sidebar_source_index = source_index

        source_layout.removeWidget(sidebar)
        sidebar.setParent(self._sidebar_host)
        sidebar.installEventFilter(self)
        self._sidebar_host_layout.addWidget(sidebar)
        self._sidebar_host.setFixedWidth(sidebar.width())
        self._sidebar_host.show()
        sidebar.show()
        self._sidebar_host.updateGeometry()
        self._desktop_shell.updateGeometry()

    def _restore_promoted_sidebar(self):
        sidebar = self._promoted_sidebar
        source_layout = self._sidebar_source_layout
        if sidebar is None:
            if self._sidebar_host:
                self._sidebar_host.hide()
            return

        self._sidebar_host_layout.removeWidget(sidebar)
        sidebar.removeEventFilter(self)
        sidebar.setParent(self.user_central_widget)

        if source_layout is not None:
            index = max(0, self._sidebar_source_index)
            if hasattr(source_layout, "insertWidget"):
                source_layout.insertWidget(index, sidebar)
            else:
                source_layout.addWidget(sidebar)

        sidebar.show()
        self._sidebar_host.hide()
        self._promoted_sidebar = None
        self._sidebar_source_layout = None
        self._sidebar_source_index = -1

    @staticmethod
    def _find_sidebar_candidate(widget: QWidget):
        layout = widget.layout()
        if layout is None:
            return None

        for index in range(layout.count()):
            candidate = layout.itemAt(index).widget()
            if candidate is None:
                continue

            class_name = candidate.__class__.__name__
            is_sidebar = (
                class_name == "MkMenu"
                or bool(candidate.property("mkSidebar"))
                or candidate.objectName() in {"MkMenu", "Sidebar", "AppSidebar"}
            )
            if is_sidebar:
                return candidate, layout, index

        return None

    def eventFilter(self, watched, event):
        if (
            watched is self._promoted_sidebar
            and event.type() in {
                QEvent.Type.Resize,
                QEvent.Type.Show,
                QEvent.Type.LayoutRequest,
            }
        ):
            self._sidebar_host.setFixedWidth(watched.width())
            self._sidebar_host.updateGeometry()

        return super().eventFilter(watched, event)

    def setWindowTitle(self, title: str):
        super().setWindowTitle(title)
        if self.titlebar:
            self.titlebar.set_title(title)

    def setWindowIcon(self, icon: QIcon):
        super().setWindowIcon(icon)
        if self.titlebar:
            pixmap = icon.pixmap(32, 32)
            self.titlebar.set_icon(pixmap)

    def changeEvent(self, event: QEvent):
        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange:
            if self.titlebar:
                self.titlebar.update_buttons()
            
            # If maximized, remove margins and drop shadow
            if self.use_custom_title_bar:
                if self.isMaximized():
                    self.shadow_layout.setContentsMargins(0, 0, 0, 0)
                    if self.container_frame.graphicsEffect():
                        self.container_frame.graphicsEffect().setEnabled(False)
                else:
                    self.shadow_layout.setContentsMargins(10, 10, 10, 10)
                    if self.container_frame.graphicsEffect():
                        self.container_frame.graphicsEffect().setEnabled(True)
                self.update_style()

    def closeEvent(self, event):
        if self._close_behavior == "hide":
            event.ignore()
            self.hide()
        else:
            event.accept()

    # --- Border Resizing Logic ---
    def mousePressEvent(self, event: QMouseEvent):
        if not self.use_custom_title_bar or self.isMaximized():
            super().mousePressEvent(event)
            return
            
        if event.button() == Qt.MouseButton.LeftButton:
            direction = self._get_resize_direction(event.position().toPoint())
            if direction != RESIZE_NONE:
                self._resizing_dir = direction
                self._resize_start_pos = event.globalPosition().toPoint()
                self._resize_start_geometry = self.geometry()
                event.accept()
                return
                
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if not self.use_custom_title_bar or self.isMaximized():
            super().mouseMoveEvent(event)
            return
            
        # 1. Handle actual resizing drag
        if self._resizing_dir != RESIZE_NONE:
            delta = event.globalPosition().toPoint() - self._resize_start_pos
            geom = QRect(self._resize_start_geometry)
            min_size = self.minimumSizeHint()
            
            # Horizontal resize
            if self._resizing_dir & RESIZE_LEFT:
                new_width = geom.width() - delta.x()
                if new_width >= min_size.width():
                    geom.setLeft(geom.left() + delta.x())
            elif self._resizing_dir & RESIZE_RIGHT:
                new_width = geom.width() + delta.x()
                if new_width >= min_size.width():
                    geom.setRight(geom.right() + delta.x())
                    
            # Vertical resize
            if self._resizing_dir & RESIZE_TOP:
                new_height = geom.height() - delta.y()
                if new_height >= min_size.height():
                    geom.setTop(geom.top() + delta.y())
            elif self._resizing_dir & RESIZE_BOTTOM:
                new_height = geom.height() + delta.y()
                if new_height >= min_size.height():
                    geom.setBottom(geom.bottom() + delta.y())
                    
            self.setGeometry(geom)
            event.accept()
            return
            
        # 2. Update hover cursor icon depending on position
        direction = self._get_resize_direction(event.position().toPoint())
        self._update_cursor(direction)
        
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._resizing_dir = RESIZE_NONE
        self.unsetCursor()
        super().mouseReleaseEvent(event)

    def leaveEvent(self, event):
        # Reset cursor when mouse leaves the window to prevent stale resize cursors
        if self._resizing_dir == RESIZE_NONE:
            self.unsetCursor()
        super().leaveEvent(event)

    def _get_resize_direction(self, pos: QPoint) -> int:
        direction = RESIZE_NONE
        w = self.width()
        h = self.height()
        margin = self._resize_margin
        
        # Detect margins
        if pos.x() < margin + 10:  # account for shadow margin
            direction |= RESIZE_LEFT
        elif pos.x() > w - margin - 10:
            direction |= RESIZE_RIGHT
            
        if pos.y() < margin + 10:
            direction |= RESIZE_TOP
        elif pos.y() > h - margin - 10:
            direction |= RESIZE_BOTTOM
            
        return direction

    def _update_cursor(self, direction: int):
        if direction == RESIZE_NONE:
            self.unsetCursor()
        elif (direction & RESIZE_LEFT and direction & RESIZE_TOP) or (direction & RESIZE_RIGHT and direction & RESIZE_BOTTOM):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif (direction & RESIZE_RIGHT and direction & RESIZE_TOP) or (direction & RESIZE_LEFT and direction & RESIZE_BOTTOM):
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        elif direction & RESIZE_LEFT or direction & RESIZE_RIGHT:
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        elif direction & RESIZE_TOP or direction & RESIZE_BOTTOM:
            self.setCursor(Qt.CursorShape.SizeVerCursor)

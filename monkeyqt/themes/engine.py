# -*- coding: utf-8 -*-
"""
MonkeyQt Theme Engine — 全局风格引擎
管理 67 套 Design Token 的切换与注入
"""

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal
from .tokens import THEME_TOKENS, THEME_NAMES
from .style_utils import darken, is_color, lighten, luminance, parse_px, qss_color, readable_text


class ThemeEngine(QObject):
    """
    全局风格引擎单例。

    用法:
        ThemeEngine.set_theme("Glassmorphism")
        color = ThemeEngine.get("--primary")
    """

    # 信号：风格切换时触发
    themeChanged = Signal(str)

    _instance = None
    DEFAULT_THEME_NAME = "MonkeyQt Default"
    DEFAULT_THEME_KEY = "__monkeyqt_default__"
    _default_tokens = {
        "name": DEFAULT_THEME_NAME,
        "type": "Built-in",
        "keywords": "MonkeyQt built-in default component styling",
        "--bg": "#FFFFFF",
        "--fg": "#1E293B",
        "--primary": "#409EFF",
        "--secondary": "#F8FAFC",
        "--accent": "#67C23A",
        "--border": "#E2E8F0",
        "--radius": "6px",
        "--shadow": "",
        "--border-width": "1px",
        "--blur": "",
        "--glow": "",
    }
    _current_name: str = ""
    _current_tokens: dict = {}
    _overrides: dict = {}

    @classmethod
    def instance(cls):
        """获取唯一的单例实例，用于连接信号"""
        if cls._instance is None:
            cls._instance = ThemeEngine()
            cls._ensure_current()
        return cls._instance

    # ──────────── 核心 API（类方法，全局可用） ────────────

    @classmethod
    def set_theme(cls, style_name: str) -> bool:
        """切换到指定风格，注入全局 QSS 并触发重绘"""
        if style_name in ("", cls.DEFAULT_THEME_KEY, cls.DEFAULT_THEME_NAME):
            return cls.clear_theme()

        if style_name not in THEME_TOKENS:
            return False

        cls._current_name = style_name
        cls._current_tokens = cls._normalize_tokens(THEME_TOKENS[style_name])

        # 注入全局 QSS 到 QApplication
        app = QApplication.instance()
        if app:
            qss = cls._build_global_qss()
            app.setStyleSheet(qss)

            # 强制刷新所有 widget
            for widget in app.allWidgets():
                try:
                    widget.style().unpolish(widget)
                    widget.style().polish(widget)
                    widget.update()
                except (TypeError, RuntimeError):
                    pass  # 某些 widget（如 QListWidget）的 update() 签名不同

        # 触发信号
        cls.instance().themeChanged.emit(style_name)

        return True

    @classmethod
    def clear_theme(cls) -> bool:
        """恢复 MonkeyQt 内置默认样式，不向 QApplication 注入 67 风格 QSS。"""
        cls._current_name = cls.DEFAULT_THEME_NAME
        cls._current_tokens = cls._normalize_tokens(cls._default_tokens)

        app = QApplication.instance()
        if app:
            app.setStyleSheet("")
            for widget in app.allWidgets():
                try:
                    widget.style().unpolish(widget)
                    widget.style().polish(widget)
                    widget.update()
                except (TypeError, RuntimeError):
                    pass

        cls.instance().themeChanged.emit(cls.DEFAULT_THEME_NAME)
        return True

    @classmethod
    def get(cls, key: str, default: str = "") -> str:
        """获取当前主题的 Token 值"""
        cls._ensure_current()
        if key in cls._overrides:
            return cls._overrides[key]
        return cls._current_tokens.get(key, default)

    @classmethod
    def has_override(cls, key: str) -> bool:
        """Return whether a token was explicitly overridden by the caller."""
        return key in cls._overrides

    @classmethod
    def current_theme(cls) -> str:
        """返回当前活跃的风格名"""
        cls._ensure_current()
        return cls._current_name

    @classmethod
    def current_tokens(cls) -> dict:
        """返回当前完整 Token 字典的副本"""
        cls._ensure_current()
        res = cls._current_tokens.copy()
        res.update(cls._overrides)
        return res

    @classmethod
    def set_override(cls, key: str, value: str) -> None:
        """设置全局 Token 重写（如单独控制侧边栏/标题栏颜色）"""
        cls._overrides[key] = value
        if cls._current_name:
            cls.set_theme(cls._current_name)

    @classmethod
    def set_overrides(cls, updates: dict[str, str] | None = None, *, remove: list[str] | None = None, refresh: bool = True) -> None:
        """Batch update global token overrides without repeatedly repainting the app."""
        for key in remove or []:
            cls._overrides.pop(key, None)
        for key, value in (updates or {}).items():
            cls._overrides[key] = value
        if refresh and cls._current_name:
            cls.set_theme(cls._current_name)

    @classmethod
    def clear_overrides(cls) -> None:
        """清除所有全局 Token 重写"""
        cls._overrides.clear()
        if cls._current_name:
            cls.set_theme(cls._current_name)

    @classmethod
    def list_themes(cls) -> list:
        """返回全部可用的风格名列表"""
        return THEME_NAMES.copy()

    @classmethod
    def list_theme_options(cls, include_default: bool = True) -> list:
        """返回主题选择器可用项，可包含 MonkeyQt 默认样式。"""
        if include_default:
            return [cls.DEFAULT_THEME_NAME] + THEME_NAMES.copy()
        return THEME_NAMES.copy()

    @classmethod
    def themes_by_type(cls, style_type: str) -> list:
        """按类型过滤风格名"""
        return [name for name, t in THEME_TOKENS.items() if t.get("type") == style_type]

    @classmethod
    def _ensure_current(cls):
        """Lazy initialize the active token set before components query it."""
        if not cls._current_name:
            cls._current_name = cls.DEFAULT_THEME_NAME
        if cls._current_name and not cls._current_tokens:
            source = cls._default_tokens if cls._current_name == cls.DEFAULT_THEME_NAME else THEME_TOKENS[cls._current_name]
            cls._current_tokens = cls._normalize_tokens(source)

    @classmethod
    def _normalize_tokens(cls, tokens: dict) -> dict:
        """Turn loose web-style CSV tokens into safe PySide/QSS tokens."""
        t = tokens.copy()
        name = t.get("name", "")
        lower_name = name.lower()

        bg = t.get("--bg", "")
        if not is_color(bg):
            if "glass" in lower_name or "spatial" in lower_name or "visionos" in lower_name:
                bg = "#EEF4FF"
            elif "aurora" in lower_name or "gradient mesh" in lower_name:
                bg = "#F3F7FF"
            elif "hud" in lower_name or "sci-fi" in lower_name:
                bg = "#050B18"
            else:
                bg = "#FFFFFF"

        fg = t.get("--fg", "")
        if not is_color(fg):
            fg = readable_text(bg)

        primary = t.get("--primary", "")
        if not is_color(primary):
            primary = "#409EFF"
        secondary = t.get("--secondary", "")
        if not is_color(secondary):
            secondary = lighten(primary, 0.86)
        accent = t.get("--accent", "")
        if not is_color(accent):
            accent = lighten(primary, 0.35)
        border = t.get("--border", "")
        if not is_color(border):
            border = "rgba(255, 255, 255, 0.36)" if "glass" in lower_name else "#E2E8F0"

        # Style-specific corrections for PySide widgets.
        if cls._name_has(name, ["dark", "oled", "cyberpunk", "hud", "sci-fi", "retro-futurism", "chromatic"]):
            fg = "#F8FAFC"
            if bg.upper() in ("#FFFFFF", "#F5F5F5"):
                bg = "#050816"
            border = "#334155"
        if cls._name_has(name, ["dark mode", "oled"]):
            bg = "#121212"
            fg = "#F5F5F5"
            primary = "#8AB4F8"
            secondary = "#242424"
            accent = "#5B8DEF"
            border = "#303030"
        if cls._name_has(name, ["liquid glass"]):
            bg = "#EAF2FF"
            primary = "#5B8CFF"
            secondary = "#D7ECFF"
            accent = "#E879F9"
            border = "rgba(255, 255, 255, 0.50)"
        elif cls._name_has(name, ["glassmorphism", "spatial", "visionos"]):
            bg = "#ECF4FF"
            border = "rgba(255, 255, 255, 0.44)"
        elif cls._name_has(name, ["brutal", "neubrutalism"]):
            border = "#000000"
        elif cls._name_has(name, ["pixel"]):
            border = "#000000"
            fg = "#111827"

        if cls._looks_dark(bg):
            bg_lum = luminance(bg)
            primary_lum = luminance(primary)
            accent_lum = luminance(accent)
            if abs(primary_lum - bg_lum) < 0.16 or primary_lum < 0.12:
                primary = "#60A5FA"
            if abs(accent_lum - bg_lum) < 0.12 or accent_lum < 0.10:
                accent = "#22D3EE"

        radius = f"{parse_px(t.get('--radius', '6px'), 6, 0, 32)}px"
        border_width = f"{parse_px(t.get('--border-width', '1px'), 1, 1, 5)}px"

        surface = "#FFFFFF"
        if cls._looks_dark(bg):
            surface = lighten(bg, 0.10)
            text_muted = "#94A3B8"
            surface_muted = lighten(bg, 0.16)
            if cls._name_has(name, ["dark mode", "oled"]):
                surface = "#242424"
                text_muted = "#A6A6A6"
                surface_muted = "#343434"
        else:
            surface = "#FFFFFF" if bg.upper() != "#FFFFFF" else "#F8FAFC"
            text_muted = "#64748B"
            surface_muted = darken(surface, 0.035)

        t.update({
            "--bg": qss_color(bg, "#FFFFFF"),
            "--fg": qss_color(fg, readable_text(bg)),
            "--primary": qss_color(primary, "#409EFF"),
            "--secondary": qss_color(secondary, "#EAF3FF"),
            "--accent": qss_color(accent, "#7DD3FC"),
            "--border": qss_color(border, "#E2E8F0"),
            "--radius": radius,
            "--border-width": border_width,
            "--surface": qss_color(surface, "#FFFFFF"),
            "--surface-muted": qss_color(surface_muted, "#F1F5F9"),
            "--text-muted": qss_color(text_muted, "#64748B"),
            "--focus-ring": qss_color(lighten(primary, 0.34), "#93C5FD"),
            "--hover-primary": qss_color(lighten(primary, 0.14), "#60A5FA"),
            "--pressed-primary": qss_color(darken(primary, 0.10), "#2563EB"),
            "--glass-surface": "rgba(255, 255, 255, 0.30)" if not cls._looks_dark(bg) else "rgba(255, 255, 255, 0.12)",
            "--glass-border": "rgba(255, 255, 255, 0.48)" if not cls._looks_dark(bg) else "rgba(255, 255, 255, 0.22)",
            "--glass-text": "#0F172A" if not cls._looks_dark(bg) else "#F8FAFC",
        })
        return t

    # ──────────── 风格特征判断（供组件 paintEvent 使用） ────────────

    @classmethod
    def is_neumorphic(cls) -> bool:
        """当前风格是否为软 UI / 新拟物化"""
        name = cls._current_name.lower()
        return any(kw in name for kw in ["neumorphism", "soft ui", "claymorphism"])

    @classmethod
    def is_glass(cls) -> bool:
        """当前风格是否为玻璃拟态"""
        name = cls._current_name.lower()
        return any(kw in name for kw in ["glass", "spatial", "visionos", "liquid"])

    @classmethod
    def is_liquid_glass(cls) -> bool:
        """当前风格是否为流态/液体玻璃"""
        return "liquid" in cls._current_name.lower()

    @classmethod
    def is_brutal(cls) -> bool:
        """当前风格是否为粗野主义"""
        name = cls._current_name.lower()
        return any(kw in name for kw in ["brutal", "neubrutalism"])

    @classmethod
    def is_dark(cls) -> bool:
        """当前风格是否为暗色系"""
        cls._ensure_current()
        name = cls._current_name.lower()
        bg = cls.get("--bg", "#FFFFFF")
        return ("dark" in name or "oled" in name or "cyberpunk" in name
                or "hud" in name or "sci-fi" in name
                or cls._looks_dark(bg))

    @classmethod
    def is_glow(cls) -> bool:
        """当前风格是否有发光 / 霓虹效果"""
        name = cls._current_name.lower()
        return any(kw in name for kw in ["cyberpunk", "retro-futurism", "hud",
                                          "sci-fi", "vaporwave", "chromatic", "aurora"])

    @classmethod
    def is_pixel(cls) -> bool:
        """当前风格是否为像素风"""
        return "pixel" in cls._current_name.lower()

    @classmethod
    def has_blur(cls) -> bool:
        """当前风格是否有模糊效果"""
        return bool(cls.get("--blur"))

    # ──────────── 内部：构建全局 QSS ────────────

    @classmethod
    def _build_global_qss(cls) -> str:
        """根据当前 Token 构建应用级 QSS"""
        t = cls.current_tokens()
        bg = t.get("--bg", "#FFFFFF")
        fg = t.get("--fg", "#1E293B")
        primary = t.get("--primary", "#409EFF")
        border = t.get("--border", "#E2E8F0")
        radius = t.get("--radius", "6px")
        border_w = t.get("--border-width", "1px")
        surface = t.get("--surface", "#FFFFFF")
        surface_muted = t.get("--surface-muted", "#F1F5F9")
        text_muted = t.get("--text-muted", "#64748B")
        focus = t.get("--focus-ring", primary)
        hover_primary = t.get("--hover-primary", primary)

        # 暗色模式自适应
        if cls.is_dark():
            disabled_bg = surface_muted
        else:
            disabled_bg = "#F1F5F9"

        selection_fg = readable_text(primary)
        panel_bg = t.get("--glass-surface", surface) if cls.is_glass() else surface
        panel_border = t.get("--glass-border", border) if cls.is_glass() else border
        page_bg = bg
        card_bg = surface
        if cls.is_glass():
            page_bg = "#EAF2FF" if not cls.is_dark() else "#020617"
            card_bg = "#F8FBFF" if not cls.is_dark() else "#111827"
            panel_bg = card_bg
            panel_border = "#D7E6F8" if not cls.is_dark() else "#334155"

        primary_hover = lighten(primary, 0.10)
        primary_pressed = darken(primary, 0.12)
        button_bg = card_bg
        button_hover = surface_muted
        handle_border = card_bg
        groove_bg = surface_muted

        qss = f"""
            /* ====== MonkeyQt Global Theme: {cls._current_name} ====== */

            QWidget {{
                font-family: "Segoe UI", "Microsoft YaHei", "PingFang SC", Helvetica, Arial, sans-serif;
                color: {fg};
                selection-background-color: {primary};
                selection-color: {selection_fg};
            }}

            QMainWindow, QDialog {{
                background-color: {page_bg};
            }}

            QWidget#centralwidget,
            QWidget#MainCentralWidget,
            QWidget#MainRightWidget,
            QStackedWidget,
            QStackedWidget > QWidget,
            QStackedWidget QWidget {{
                background-color: {page_bg};
                color: {fg};
            }}

            QFrame {{
                border-color: {panel_border};
            }}

            QFrame, QGroupBox, QScrollArea, QAbstractScrollArea {{
                background-color: {card_bg};
                color: {fg};
                border: {border_w} solid {panel_border};
                border-radius: {radius};
            }}

            QScrollArea QWidget, QAbstractScrollArea QWidget {{
                background-color: transparent;
            }}

            QLabel {{
                background: transparent;
                color: {fg};
                border: none;
            }}

            QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox,
            QDateEdit, QTimeEdit, QDateTimeEdit, QComboBox {{
                background-color: {panel_bg};
                color: {fg};
                border: {border_w} solid {panel_border};
                border-radius: {radius};
                padding: 7px 10px;
            }}

            QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover, QComboBox:hover,
            QSpinBox:hover, QDoubleSpinBox:hover, QDateEdit:hover, QTimeEdit:hover, QDateTimeEdit:hover {{
                border-color: {hover_primary};
            }}

            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus,
            QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus, QTimeEdit:focus, QDateTimeEdit:focus {{
                border-color: {primary};
            }}

            QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled, QComboBox:disabled,
            QSpinBox:disabled, QDoubleSpinBox:disabled, QDateEdit:disabled, QTimeEdit:disabled, QDateTimeEdit:disabled {{
                background-color: {disabled_bg};
                color: {text_muted};
                border-color: {border};
            }}

            QComboBox::drop-down {{
                border: none;
                width: 28px;
            }}

            QComboBox QAbstractItemView {{
                background-color: {card_bg};
                color: {fg};
                border: {border_w} solid {panel_border};
                selection-background-color: {primary};
                selection-color: {selection_fg};
                outline: none;
            }}

            QPushButton {{
                padding: 7px 14px;
                border-radius: {radius};
                border: {border_w} solid {panel_border};
                background-color: {button_bg};
                color: {fg};
                font-weight: 600;
            }}

            QPushButton:hover {{
                border-color: {hover_primary};
                background-color: {button_hover};
            }}

            QPushButton:focus {{
                border-color: {focus};
            }}

            QPushButton:checked, QPushButton:pressed {{
                background-color: {primary};
                border-color: {primary};
                color: {selection_fg};
            }}

            QPushButton:checked:hover {{
                background-color: {primary_hover};
                border-color: {primary_hover};
                color: {selection_fg};
            }}

            QPushButton:disabled {{
                background-color: {disabled_bg};
                border-color: {panel_border};
                color: {text_muted};
            }}

            QToolButton {{
                background-color: transparent;
                color: {fg};
                border: {border_w} solid transparent;
                border-radius: {radius};
                padding: 5px;
            }}

            QToolButton:hover, QToolButton:checked {{
                background-color: {button_hover};
                border-color: {hover_primary};
            }}

            QCheckBox, QRadioButton {{
                color: {fg};
                background: transparent;
                spacing: 8px;
            }}

            QCheckBox::indicator, QRadioButton::indicator {{
                width: 15px;
                height: 15px;
                background-color: {panel_bg};
                border: {border_w} solid {panel_border};
            }}

            QCheckBox::indicator {{
                border-radius: 4px;
            }}

            QRadioButton::indicator {{
                border-radius: 8px;
            }}

            QCheckBox::indicator:hover, QRadioButton::indicator:hover {{
                border-color: {primary};
            }}

            QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
                background-color: {primary};
                border-color: {primary};
            }}

            QSlider {{
                background: transparent;
                border: none;
            }}

            QSlider::groove:horizontal {{
                height: 6px;
                background: {groove_bg};
                border: none;
                border-radius: 3px;
            }}

            QSlider::sub-page:horizontal {{
                background: {primary};
                border-radius: 3px;
            }}

            QSlider::handle:horizontal {{
                background: {primary};
                border: 2px solid {handle_border};
                width: 16px;
                height: 16px;
                margin: -7px 0;
                border-radius: 8px;
            }}

            QSlider::handle:horizontal:hover, QSlider::handle:horizontal:pressed {{
                background: {primary_hover};
                border-color: {handle_border};
            }}

            QSlider::groove:vertical {{
                width: 6px;
                background: {groove_bg};
                border: none;
                border-radius: 3px;
            }}

            QSlider::sub-page:vertical {{
                background: {primary};
                border-radius: 3px;
            }}

            QSlider::handle:vertical {{
                background: {primary};
                border: 2px solid {handle_border};
                width: 16px;
                height: 16px;
                margin: 0 -7px;
                border-radius: 8px;
            }}

            QTabWidget::pane {{
                background-color: {card_bg};
                border: {border_w} solid {panel_border};
                border-radius: {radius};
            }}

            QTabBar::tab {{
                background-color: transparent;
                color: {text_muted};
                border: none;
                padding: 8px 14px;
            }}

            QTabBar::tab:selected {{
                color: {selection_fg};
                background-color: {primary};
                border-radius: {radius};
            }}

            QMenuBar, QMenu {{
                background-color: {card_bg};
                color: {fg};
                border: {border_w} solid {panel_border};
            }}

            QMenuBar::item:selected, QMenu::item:selected {{
                background-color: {primary};
                color: {selection_fg};
            }}

            QProgressBar {{
                background-color: {groove_bg};
                color: {fg};
                border: {border_w} solid {panel_border};
                border-radius: {radius};
                text-align: center;
            }}

            QProgressBar::chunk {{
                background-color: {primary};
                border-radius: {radius};
            }}

            QSplitter::handle {{
                background-color: {panel_border};
            }}

            QToolTip {{
                background-color: {card_bg};
                color: {fg};
                border: 1px solid {panel_border};
                border-radius: 6px;
                padding: 6px 8px;
            }}

            QScrollBar:vertical {{
                background: transparent;
                width: 10px;
                margin: 2px;
            }}

            QScrollBar::handle:vertical {{
                background: {text_muted};
                border-radius: 5px;
                min-height: 28px;
            }}

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: transparent;
                border: none;
            }}

            QListWidget, QListView, QTreeWidget, QTreeView,
            QTableWidget, QTableView {{
                background-color: {card_bg};
                color: {fg};
                border: {border_w} solid {panel_border};
                border-radius: {radius};
                outline: none;
            }}

            QListWidget::item, QListView::item, QTreeWidget::item, QTreeView::item {{
                min-height: 28px;
                border-radius: {radius};
            }}

            QListWidget::item:hover, QListView::item:hover, QTreeWidget::item:hover, QTreeView::item:hover {{
                background-color: {surface_muted};
            }}

            QListWidget::item:selected, QListView::item:selected,
            QTreeWidget::item:selected, QTreeView::item:selected,
            QTableWidget::item:selected, QTableView::item:selected {{
                background-color: {primary};
                color: {selection_fg};
            }}

            QHeaderView::section {{
                background-color: {surface_muted};
                color: {fg};
                border: none;
                border-bottom: {border_w} solid {panel_border};
                padding: 7px 9px;
                font-weight: 700;
            }}
        """
        return qss

    @staticmethod
    def _name_has(name: str, keywords: list[str]) -> bool:
        lower = name.lower()
        return any(keyword in lower for keyword in keywords)

    @staticmethod
    def _looks_dark(color: str) -> bool:
        try:
            from .style_utils import luminance
            return luminance(color) < 0.25
        except Exception:
            return str(color).lower() in ("#000000", "#121212", "#0a0e27", "#1a1a2e")

    @staticmethod
    def _lighten_hex(hex_color: str, factor: float) -> str:
        """将 HEX 颜色提亮指定系数"""
        if not hex_color.startswith("#") or len(hex_color) != 7:
            return hex_color
        try:
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            r = min(255, int(r + (255 - r) * factor))
            g = min(255, int(g + (255 - g) * factor))
            b = min(255, int(b + (255 - b) * factor))
            return f"#{r:02X}{g:02X}{b:02X}"
        except ValueError:
            return hex_color

    @staticmethod
    def _darken_hex(hex_color: str, factor: float) -> str:
        """将 HEX 颜色加深指定系数"""
        if not hex_color.startswith("#") or len(hex_color) != 7:
            return hex_color
        try:
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            r = max(0, int(r * (1 - factor)))
            g = max(0, int(g * (1 - factor)))
            b = max(0, int(b * (1 - factor)))
            return f"#{r:02X}{g:02X}{b:02X}"
        except ValueError:
            return hex_color

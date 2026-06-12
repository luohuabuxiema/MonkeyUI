# -*- coding: utf-8 -*-
"""Apply the 67 token themes to existing Mk* widgets without replacing them."""

from __future__ import annotations

import ctypes
import sys
import types

from PySide6.QtCore import QEvent, QObject, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPainterPath, QRegion
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QToolButton,
    QWidget,
)

from .engine import ThemeEngine
from .style_utils import darken, lighten, luminance, parse_px, qcolor, readable_text


_STYLE_PROP = "_mk_theme_original_stylesheet"
_THEME_ENABLED_PROP = "mk_theme_enabled"
_THEME_DISABLED_PROP = "mk_theme_disabled"
_DATE_THEME_ORIGINALS = None


def _set_windows_corner_preference(widget: QWidget, rounded: bool) -> bool:
    """Use Windows 11's anti-aliased DWM corners for a top-level window."""
    if sys.platform != "win32":
        return False
    try:
        hwnd = int(widget.winId())
        # ROUND_SMALL matches the restrained Windows 11/Codex window radius.
        preference = ctypes.c_int(3 if rounded else 1)  # ROUND_SMALL / DO_NOT_ROUND
        result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd,
            33,  # DWMWA_WINDOW_CORNER_PREFERENCE
            ctypes.byref(preference),
            ctypes.sizeof(preference),
        )
        if result != 0:
            return False

        border_color = ctypes.c_uint(0xFFFFFFFE)  # DWMWA_COLOR_NONE
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd,
            34,  # DWMWA_BORDER_COLOR
            ctypes.byref(border_color),
            ctypes.sizeof(border_color),
        )
        return True
    except (AttributeError, OSError, RuntimeError, ValueError):
        return False


def _apply_native_window_corners(widget: QWidget, p: dict[str, str | int | bool]) -> bool:
    if sys.platform != "win32" or not getattr(widget, "use_custom_title_bar", False):
        return False

    if not hasattr(widget, "_mk_theme_native_corner_state"):
        margins = widget.shadow_layout.contentsMargins() if getattr(widget, "shadow_layout", None) else None
        shadow = getattr(widget, "_shadow_effect", None)
        widget._mk_theme_native_corner_state = {
            "margins": (
                margins.left(),
                margins.top(),
                margins.right(),
                margins.bottom(),
            ) if margins is not None else None,
            "translucent": widget.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground),
            "shadow_enabled": shadow.isEnabled() if shadow is not None else None,
        }

    rounded = int(p["radius_px"]) > 0 and not bool(p["flat"])
    widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
    if getattr(widget, "shadow_layout", None) is not None:
        widget.shadow_layout.setContentsMargins(0, 0, 0, 0)
    shadow = getattr(widget, "_shadow_effect", None)
    if shadow is not None:
        shadow.setEnabled(False)

    applied = _set_windows_corner_preference(widget, rounded)
    widget._mk_theme_uses_native_corners = applied
    if applied:
        QTimer.singleShot(0, lambda w=widget, r=rounded: _set_windows_corner_preference(w, r))
    else:
        _restore_native_window_corners(widget)
    return applied


def _restore_native_window_corners(widget: QWidget) -> None:
    if not hasattr(widget, "_mk_theme_native_corner_state"):
        return
    state = widget._mk_theme_native_corner_state
    _set_windows_corner_preference(widget, False)
    margins = state.get("margins")
    if margins is not None and getattr(widget, "shadow_layout", None) is not None:
        widget.shadow_layout.setContentsMargins(*margins)
    shadow = getattr(widget, "_shadow_effect", None)
    if shadow is not None and state.get("shadow_enabled") is not None:
        shadow.setEnabled(bool(state["shadow_enabled"]))
    widget.setAttribute(
        Qt.WidgetAttribute.WA_TranslucentBackground,
        bool(state.get("translucent", True)),
    )
    delattr(widget, "_mk_theme_native_corner_state")
    if hasattr(widget, "_mk_theme_uses_native_corners"):
        delattr(widget, "_mk_theme_uses_native_corners")


class _RoundedMaskFilter(QObject):
    """Keep a real rounded clip in sync with a themed widget's geometry."""

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Type.Resize, QEvent.Type.Show):
            _update_rounded_mask(watched)
        return False


def _update_rounded_mask(widget: QWidget | None) -> None:
    if widget is None or not hasattr(widget, "_mk_theme_mask_radius"):
        return
    try:
        radius = int(widget._mk_theme_mask_radius)
        owner = getattr(widget, "_mk_theme_mask_owner", None)
        if owner is not None and owner.isMaximized():
            radius = 0
        if radius <= 0 or widget.width() <= 1 or widget.height() <= 1:
            widget.clearMask()
            return

        path = QPainterPath()
        rect = QRectF(0.0, 0.0, max(0.0, widget.width() - 0.5), max(0.0, widget.height() - 0.5))
        path.addRoundedRect(rect, radius, radius)
        widget.setMask(QRegion(path.toFillPolygon().toPolygon()))
    except RuntimeError:
        pass


def _apply_rounded_mask(widget: QWidget | None, radius: int, owner: QWidget | None = None) -> None:
    if widget is None:
        return
    if not hasattr(widget, "_mk_theme_original_mask"):
        widget._mk_theme_original_mask = widget.mask()
        widget._mk_theme_mask_filter = _RoundedMaskFilter(widget)
        widget.installEventFilter(widget._mk_theme_mask_filter)
    widget._mk_theme_mask_radius = max(0, int(radius))
    widget._mk_theme_mask_owner = owner
    _update_rounded_mask(widget)


def _restore_rounded_mask(widget: QWidget | None) -> None:
    if widget is None or not hasattr(widget, "_mk_theme_original_mask"):
        return
    try:
        mask_filter = getattr(widget, "_mk_theme_mask_filter", None)
        if mask_filter is not None:
            widget.removeEventFilter(mask_filter)
        original_mask = widget._mk_theme_original_mask
        if original_mask.isEmpty():
            widget.clearMask()
        else:
            widget.setMask(original_mask)
    except RuntimeError:
        pass
    for attr in (
        "_mk_theme_original_mask",
        "_mk_theme_mask_filter",
        "_mk_theme_mask_radius",
        "_mk_theme_mask_owner",
    ):
        if hasattr(widget, attr):
            delattr(widget, attr)


def _control_radius_px(p: dict[str, str | int | bool]) -> int:
    """Keep form controls restrained even when a theme uses large card radii."""
    return 0 if p["flat"] else min(8, int(p["radius_px"]))


def _popup_radius_px(p: dict[str, str | int | bool]) -> int:
    """Popups need a small physical radius to avoid oversized bubble corners."""
    return 0 if p["flat"] else min(6, int(p["radius_px"]))


def _table_radius_px(p: dict[str, str | int | bool]) -> int:
    """Tables use restrained corners even for highly rounded themes."""
    return 0 if p["flat"] else min(8, int(p["radius_px"]))


def _table_border(p: dict[str, str | int | bool]) -> str:
    if p["flat"]:
        return _tint("#111827", 0.68, str(p["panel"]))
    if p["glass"]:
        return _control_border(p)
    return str(p["border"])


def _table_rule(p: dict[str, str | int | bool]) -> str:
    return f"1px solid {_table_border(p)}"


def _table_surface(p: dict[str, str | int | bool]) -> str:
    if p["glass"]:
        return _control_surface(p, floating=True)
    return str(p["panel"])


def _table_header_surface(p: dict[str, str | int | bool]) -> str:
    if p["glass"]:
        return _control_muted_surface(p)
    return str(p["surface_muted"])


def _table_selected_surface(p: dict[str, str | int | bool]) -> str:
    if p["dark"]:
        return _soft_hover(p, str(p["surface_muted"]))
    return _tint(str(p["primary"]), 0.86, str(p["surface_muted"]))


def _with_radius(p: dict[str, str | int | bool], radius: int) -> dict[str, str | int | bool]:
    result = dict(p)
    result["radius_px"] = radius
    result["radius"] = f"{radius}px"
    return result


def _apply_popup_window_shape(widget: QWidget | None, radius: int) -> None:
    if widget is None:
        return
    try:
        if widget.isWindow() and _set_windows_corner_preference(widget, radius > 0):
            _restore_rounded_mask(widget)
            return
    except RuntimeError:
        return
    _apply_rounded_mask(widget, radius)


_SUPPORTED_THEME_CLASSES = {
    # Custom Mk* components
    "MkButton", "MkDropdown", "MkCheckBox", "MkInput", "MkDatePicker",
    "MkComboBox", "MkMultiComboBox", "MkSlider", "MkSwitch", "MkForm",
    "MkAlert", "MkProgressBar", "MkProgressRing", "MkMenu", "MkMenuItem",
    "MkSubMenu", "MkTopbar", "MkTopbarItem", "MkTabs", "MkTabButton",
    "MkPagination", "MkBreadcrumbItem", "MkTable", "MkDataTable", "MkUpload",
    "MkCaptchaWidget", "MkAuthScreen", "MkMessage", "MkAvatar", "MkTitleBar",
    "MkWindow", "YoloDashboardWidget",
    
    # Native PySide6 widgets
    "QLabel", "QPushButton", "QCommandLinkButton", "QToolButton", "QLineEdit",
    "QTextEdit", "QPlainTextEdit", "QTextBrowser", "QComboBox", "QSlider",
    "QDial", "QCheckBox", "QRadioButton", "QStackedWidget", "QScrollArea",
    "QAbstractScrollArea", "QGroupBox", "QTabWidget", "QTabBar", "QListWidget",
    "QTreeWidget", "QTableWidget", "QTableView", "QListView", "QTreeView",
    "QHeaderView", "QProgressBar", "QSplitter", "QSpinBox", "QDoubleSpinBox",
    "QDateEdit", "QTimeEdit", "QDateTimeEdit", "QCalendarWidget", "QDialog",
    "QMainWindow", "QMenuBar", "QMenu", "QStatusBar", "QToolBar", "QDockWidget",
    "QDialogButtonBox", "QGraphicsView", "QMdiArea", "QLCDNumber", "QScrollBar",
    "QFrame", "QWidget"
}


def _theme_class_name(widget: QWidget) -> str:
    for cls in widget.__class__.__mro__:
        name = cls.__name__
        if name in _SUPPORTED_THEME_CLASSES:
            return name
    return widget.__class__.__name__


def apply_monkeyqt_theme(root: QWidget | None = None) -> None:
    """Apply or restore token styling for the existing MonkeyQt components below root."""
    widgets = list(_iter_widgets(root))
    if ThemeEngine.current_theme() == ThemeEngine.DEFAULT_THEME_NAME:
        _restore_date_picker_theme()
        for widget in widgets:
            if _should_skip(widget):
                continue
            if _is_theme_supported(widget) or widget.property(_STYLE_PROP) is not None:
                _restore_widget(widget)
        return

    palette = _palette()
    _apply_date_picker_theme(palette)
    for widget in widgets:
        if _should_skip(widget) or not _is_theme_supported(widget):
            continue
        _save_widget(widget)
        _apply_widget(widget, palette)


def restore_monkeyqt_theme(root: QWidget | None = None) -> None:
    """Restore original styles for MonkeyQt widgets below root."""
    for widget in list(_iter_widgets(root)):
        if _should_skip(widget, include_disabled=False):
            continue
        if _is_theme_supported(widget) or widget.property(_STYLE_PROP) is not None:
            _restore_widget(widget)


def _iter_widgets(root: QWidget | None):
    if root is not None:
        yield root
        for widget in root.findChildren(QWidget):
            yield widget
        return

    app = QApplication.instance()
    if app is not None:
        yield from app.allWidgets()


def _should_skip(widget: QWidget, *, include_disabled: bool = True) -> bool:
    name = widget.__class__.__name__
    object_name = widget.objectName()
    shell_widgets = {
        "GalleryCentralWidget",
        "GalleryContentArea",
        "GalleryThemeLabel",
    }
    paint_only_widgets = {"MkImageCompare", "MkImageSplit", "MkImagePanel", "MkSplitterHandle"}
    skip_object_names = {
        "TitleBarMinButton",
        "TitleBarMaxButton",
        "TitleBarCloseButton",
        "TitleBarCenterContainer",
        "MkWindowRootWidget",
        "SidebarHamburgerButton",
        "SidebarCollapseButton",
        "SidebarTitleArea",
        "SidebarContentWidget",
        "SubMenuTitleButton",
        "SidebarInnerFrame",
        "SidebarScrollArea",
        "MultiComboFaceScrollArea",
        "MultiComboPopupScrollArea",
    }
    return (
        (include_disabled and _is_theme_disabled(widget))
        or _is_multicombobox_internal(widget)
        or (
            _combobox_owner(widget) is not None
            and not _is_combobox_popup_view(widget)
        )
        or object_name in shell_widgets
        or object_name in skip_object_names
        or name == "MkThemeSelector"
        or name.startswith("Themed")
        or name in paint_only_widgets
    )


def _is_theme_disabled(widget: QWidget) -> bool:
    current = widget
    while current is not None:
        if current.property(_THEME_DISABLED_PROP) is True or current.property(_THEME_ENABLED_PROP) is False:
            return True
        current = current.parentWidget()
    return False


def _is_theme_supported(widget: QWidget) -> bool:
    name = _theme_class_name(widget)
    return (
        name in {
            "MkButton",
            "MkDropdown",
            "MkCheckBox",
            "MkInput",
            "MkDatePicker",
            "MkComboBox",
            "MkMultiComboBox",
            "MkSlider",
            "MkSwitch",
            "MkForm",
            "MkAlert",
            "MkProgressBar",
            "MkProgressRing",
            "MkMenu",
            "MkMenuItem",
            "MkSubMenu",
            "MkTopbar",
            "MkTopbarItem",
            "MkTabs",
            "MkTabButton",
            "MkPagination",
            "MkBreadcrumbItem",
            "MkTable",
            "MkDataTable",
            "MkUpload",
            "MkCaptchaWidget",
            "MkAuthScreen",
            "MkMessage",
            "MkAvatar",
            "MkTitleBar",
            "MkWindow",
            "YoloDashboardWidget",
            "QLabel",
            "QPushButton",
            "QCommandLinkButton",
            "QToolButton",
            "QLineEdit",
            "QTextEdit",
            "QPlainTextEdit",
            "QTextBrowser",
            "QComboBox",
            "QSlider",
            "QDial",
            "QCheckBox",
            "QRadioButton",
            "QStackedWidget",
            "QScrollArea",
            "QAbstractScrollArea",
            "QGroupBox",
            "QTabWidget",
            "QTabBar",
            "QListWidget",
            "QTreeWidget",
            "QTableWidget",
            "QTableView",
            "QListView",
            "QTreeView",
            "QHeaderView",
            "QProgressBar",
            "QSplitter",
            "QSpinBox",
            "QDoubleSpinBox",
            "QDateEdit",
            "QTimeEdit",
            "QDateTimeEdit",
            "QCalendarWidget",
            "QDialog",
            "QMainWindow",
            "QMenuBar",
            "QMenu",
            "QStatusBar",
            "QToolBar",
            "QDockWidget",
            "QDialogButtonBox",
            "QGraphicsView",
            "QMdiArea",
            "QLCDNumber",
            "QScrollBar",
        }
        or name == "QFrame"
        or (name == "QWidget" and bool(widget.objectName() or widget.styleSheet()))
        or (name == "QFrame" and widget.objectName() == "MkWindowContainer")
        or (name == "QFrame" and widget.objectName() == "AuthControlPanel")
        or (name == "QFrame" and widget.objectName() == "DataTableInteractionCard")
        or (name == "QLabel" and widget.objectName() == "UploadLogArea")
    )


def _save_widget(widget: QWidget | None) -> None:
    if widget is None:
        return
    if widget.property(_STYLE_PROP) is None:
        widget.setProperty(_STYLE_PROP, widget.styleSheet())


def _restore_widget(widget: QWidget | None) -> None:
    if widget is None:
        return

    _restore_rounded_mask(widget)
    name = _theme_class_name(widget)
    if name == "MkWindow":
        _restore_window(widget)
    if name == "MkTitleBar":
        _restore_titlebar(widget)
    if name in ("MkComboBox", "QComboBox"):
        _restore_combobox(widget)
    if name == "MkMultiComboBox":
        _restore_multicombobox(widget)

    if hasattr(widget, "_mk_theme_original_methods"):
        for m_name, m_func in widget._mk_theme_original_methods.items():
            setattr(widget, m_name, m_func)
        delattr(widget, "_mk_theme_original_methods")

    if hasattr(widget, "_mk_theme_original_switch_colors"):
        active, inactive = widget._mk_theme_original_switch_colors
        widget._active_color = QColor(active)
        widget._inactive_color = QColor(inactive)
        delattr(widget, "_mk_theme_original_switch_colors")
        widget.update()

    if hasattr(widget, "_mk_theme_original_get_color"):
        widget._get_color = widget._mk_theme_original_get_color
        delattr(widget, "_mk_theme_original_get_color")
        widget.update()

    if hasattr(widget, "_mk_theme_original_menu_styles"):
        (
            widget._base_style,
            widget._label_style,
            widget._label_checked_style,
            widget._label_hover_style,
        ) = widget._mk_theme_original_menu_styles
        delattr(widget, "_mk_theme_original_menu_styles")
        if hasattr(widget, "_update_label_styles"):
            widget._update_label_styles()

    if hasattr(widget, "_mk_theme_original_event_filter"):
        widget.eventFilter = widget._mk_theme_original_event_filter
        delattr(widget, "_mk_theme_original_event_filter")

    if hasattr(widget, "_mk_theme_original_apply_theme_colors"):
        widget.apply_theme_colors = widget._mk_theme_original_apply_theme_colors
        delattr(widget, "_mk_theme_original_apply_theme_colors")

    if hasattr(widget, "_mk_theme_original_paint_event"):
        widget.paintEvent = widget._mk_theme_original_paint_event
        delattr(widget, "_mk_theme_original_paint_event")

    if hasattr(widget, "_mk_theme_original_refresh_table"):
        widget.refresh_table = widget._mk_theme_original_refresh_table
        delattr(widget, "_mk_theme_original_refresh_table")

    if hasattr(widget, "_mk_theme_original_pagination_update_ui"):
        widget._update_ui = widget._mk_theme_original_pagination_update_ui
        delattr(widget, "_mk_theme_original_pagination_update_ui")

    for method_name in ("switch_mode", "add_register_field"):
        original_name = f"_mk_theme_original_auth_{method_name}"
        if hasattr(widget, original_name):
            setattr(widget, method_name, getattr(widget, original_name))
            delattr(widget, original_name)

    if hasattr(widget, "_mk_theme_original_set_drag_state"):
        widget.set_drag_state = widget._mk_theme_original_set_drag_state
        delattr(widget, "_mk_theme_original_set_drag_state")
        try:
            widget.set_drag_state(False)
        except RuntimeError:
            pass

    if hasattr(widget, "set_checkbox_palette"):
        widget.set_checkbox_palette(None)

    original = widget.property(_STYLE_PROP)
    if original is not None:
        widget.setStyleSheet(original)

    forced_height = widget.property("_mk_theme_fixed_height")
    forced_width = widget.property("_mk_theme_fixed_width")
    if forced_width is not None and forced_height is not None:
        widget.setFixedSize(int(forced_width), int(forced_height))
    elif forced_height is not None:
        widget.setFixedHeight(int(forced_height))
    elif forced_width is not None:
        widget.setFixedWidth(int(forced_width))
    elif name == "MkMenuItem" and hasattr(widget, "_item_height"):
        widget.setFixedHeight(widget._item_height)

    try:
        widget.updateGeometry()
    except RuntimeError:
        pass


def _theme_name_has(*keywords: str) -> bool:
    name = ThemeEngine.current_theme().lower()
    return any(keyword in name for keyword in keywords)


def _hsv_color(hue: int, saturation: float, value: float) -> str:
    if hue < 0:
        hue = 215
    color = QColor.fromHsv(
        int(hue) % 360,
        int(max(0, min(255, saturation))),
        int(max(0, min(255, value))),
    )
    return color.name(QColor.NameFormat.HexRgb).upper()


def _theme_hue(bg: str, primary: str) -> tuple[int, int]:
    primary_color = qcolor(primary)
    bg_color = qcolor(bg)
    primary_h, primary_s, primary_v, _ = primary_color.getHsv()
    bg_h, bg_s, _, _ = bg_color.getHsv()

    if primary_s >= 24 and primary_v >= 60:
        return primary_h, primary_s
    if bg_s >= 18:
        return bg_h, bg_s
    return 215, max(primary_s, bg_s)


def _readable_muted(background: str) -> str:
    if luminance(background) < 0.45:
        return "#A3A3A3"
    return "#64748B"


def _auto_chrome_surfaces(bg: str, primary: str, surface: str, surface_muted: str, *, dark: bool, glass: bool, glow: bool) -> tuple[str, str]:
    """Return theme-aware sidebar and titlebar colors for all token themes."""
    if _theme_name_has("dark mode", "oled"):
        return "#202020", "#202020"

    hue, saturation = _theme_hue(bg, primary)

    if glass:
        if dark:
            return _hsv_color(hue, max(18, min(48, saturation * 0.32)), 30), _hsv_color(hue, max(14, min(38, saturation * 0.24)), 24)
        return _hsv_color(hue, max(7, min(26, saturation * 0.18)), 246), _hsv_color(hue, max(5, min(18, saturation * 0.12)), 252)

    if dark:
        if glow or saturation >= 58:
            return _hsv_color(hue, max(20, min(68, saturation * 0.34)), 30), _hsv_color(hue, max(16, min(52, saturation * 0.26)), 25)
        return lighten(bg, 0.08), lighten(bg, 0.06)

    bg_color = qcolor(bg)
    _, bg_s, bg_v, _ = bg_color.getHsv()
    if bg_s >= 45 and bg_v >= 140:
        return _hsv_color(hue, max(8, min(30, saturation * 0.18)), 246), _hsv_color(hue, max(6, min(22, saturation * 0.12)), 251)
    if bg.upper() in ("#FFFFFF", "#FAFAFA", "#F8FAFC", "#F5F5F7", "#F5F5F5"):
        return _hsv_color(hue, max(4, min(16, saturation * 0.10)), 246), _hsv_color(hue, max(2, min(10, saturation * 0.06)), 251)
    return darken(bg, 0.045), darken(bg, 0.025)


def _palette() -> dict[str, str | int | bool]:
    t = ThemeEngine
    tokens = t.current_tokens()

    bg = tokens.get("--bg", "#FFFFFF")
    fg = tokens.get("--fg", "#1E293B")
    primary = tokens.get("--primary", "#409EFF")
    accent = tokens.get("--accent", "#67C23A")
    border = tokens.get("--glass-border", tokens.get("--border", "#E2E8F0")) if t.is_glass() else tokens.get("--border", "#E2E8F0")
    surface = tokens.get("--glass-surface", tokens.get("--surface", "#FFFFFF")) if t.is_glass() else tokens.get("--surface", "#FFFFFF")
    panel = surface
    sidebar_surface = surface
    muted = tokens.get("--text-muted", "#64748B")
    surface_muted = tokens.get("--surface-muted", "#F1F5F9")
    text = tokens.get("--glass-text", fg) if t.is_glass() else fg

    sidebar_surface, chrome_surface = _auto_chrome_surfaces(
        bg,
        primary,
        surface,
        surface_muted,
        dark=t.is_dark(),
        glass=t.is_glass(),
        glow=t.is_glow(),
    )

    sidebar_surface = tokens.get("--sidebar-bg", sidebar_surface)
    chrome_surface = tokens.get("--titlebar-bg", chrome_surface)
    sidebar_text = readable_text(sidebar_surface)
    chrome_text = readable_text(chrome_surface)
    sidebar_muted = _readable_muted(sidebar_surface)
    sidebar_accent = "#E5E5E5" if _theme_name_has("dark mode", "oled") else primary

    flat = t.is_brutal() or t.is_pixel()
    radius_px = 0 if flat else parse_px(tokens.get("--radius", "6px"), 6, 0, 32)
    border_width = "2px" if flat else tokens.get("--border-width", "1px")
    border_rule = "2px solid #000000" if flat else f"{border_width} solid {border}"
    font_family = "Consolas" if t.is_pixel() else '"Segoe UI", "Microsoft YaHei", "PingFang SC", Arial, sans-serif'
    selection_fg = readable_text(primary)

    return {
        "bg": bg,
        "fg": fg,
        "text": text,
        "muted": muted,
        "primary": primary,
        "primary_text": selection_fg,
        "accent": accent,
        "border": border,
        "border_rule": border_rule,
        "border_width": border_width,
        "surface": surface,
        "panel": panel,
        "sidebar_surface": sidebar_surface,
        "chrome_surface": chrome_surface,
        "sidebar_text": sidebar_text,
        "chrome_text": chrome_text,
        "sidebar_muted": sidebar_muted,
        "sidebar_accent": sidebar_accent,
        "surface_muted": surface_muted,
        "radius": f"{radius_px}px",
        "radius_px": radius_px,
        "font": font_family,
        "flat": flat,
        "dark": t.is_dark(),
        "glass": t.is_glass(),
        "glow": t.is_glow(),
        "neumorphic": t.is_neumorphic(),
    }



def _apply_widget(widget: QWidget, p: dict[str, str | int | bool]) -> None:
    name = _theme_class_name(widget)

    if _apply_datatable_descendant(widget, p):
        return
    if _apply_table_descendant(widget, p):
        return
    if _apply_pagination_descendant(widget, p):
        return
    if _apply_auth_descendant(widget, p):
        return

    if name in ("MkButton", "MkDropdown"):
        if name == "MkButton" and _is_yolo_mode_button(widget):
            _apply_yolo_mode_button(widget, p)
        else:
            _apply_button(widget, p)
        if name == "MkDropdown" and hasattr(widget, "menu"):
            _save_widget(widget.menu)
            widget.menu.setStyleSheet(_menu_qss(p))
    elif name == "MkCheckBox":
        if widget.objectName() == "DataTableRowCheckBox":
            widget.setStyleSheet(_table_checkbox_qss(p))
        else:
            widget.setStyleSheet(_checkbox_qss(p))
    elif name in ("MkInput", "MkDatePicker"):
        widget.setStyleSheet(_input_qss(p))
    elif name == "MkComboBox":
        widget.setStyleSheet(_combobox_qss(p))
        _apply_combobox_view(widget, p)
    elif name == "MkMultiComboBox":
        _apply_multicombobox(widget, p)
    elif name == "MkSlider":
        _apply_slider(widget, p)
    elif name == "MkSwitch":
        _apply_switch(widget, p)
    elif name == "MkForm":
        _apply_form(widget, p)
    elif name == "MkAlert":
        widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        widget.setStyleSheet(_alert_qss(widget, p))
    elif name in ("MkProgressBar", "MkProgressRing"):
        _apply_progress(widget, p)
    elif name == "MkMenu":
        _apply_menu(widget, p)
    elif name == "MkMenuItem":
        _apply_menu_item(widget, p)
    elif name == "MkSubMenu":
        _apply_submenu(widget, p)
    elif name == "MkTopbar":
        widget.setStyleSheet(_topbar_qss(p))
        if hasattr(widget, "logo_label"):
            _style_label(widget.logo_label, f"color: {p['primary_text']}; font-size: 20px; font-weight: 800; background: transparent;")
    elif name == "MkTopbarItem":
        widget.setStyleSheet(_topbar_item_qss(p))
    elif name == "MkTabs":
        _apply_panel(widget, p)
        if hasattr(widget, "header_widget"):
            _save_widget(widget.header_widget)
            widget.header_widget.setStyleSheet(f"QWidget {{ background: transparent; border-bottom: {p['border_rule']}; }}")
    elif name == "MkTabButton":
        widget.setStyleSheet(_tab_button_qss(p))
    elif name == "MkPagination":
        _apply_pagination(widget, p)
    elif name == "MkBreadcrumbItem":
        widget.setStyleSheet(_breadcrumb_item_qss(widget, p))
    elif name == "MkTable":
        _apply_table(widget, p)
    elif name == "MkDataTable":
        _apply_datatable(widget, p)
    elif name == "MkUpload":
        _apply_upload(widget, p)
    elif name == "MkAuthScreen":
        _apply_auth_screen(widget, p)
    elif name in ("MkCaptchaWidget", "MkMessage", "MkAvatar"):
        _apply_panel(widget, p)
    elif name == "MkWindow":
        _apply_window(widget, p)
    elif name == "MkTitleBar":
        _apply_titlebar(widget, p)
    elif name == "YoloDashboardWidget":
        _apply_yolo_dashboard(widget, p)
    elif name == "QFrame" and widget.objectName() == "MkWindowContainer":
        _apply_window_container(widget, p)
    elif name == "QFrame" and widget.objectName() == "AuthControlPanel":
        _apply_auth_control_panel(widget, p)
    elif name == "QFrame" and widget.objectName() == "DataTableInteractionCard":
        _apply_status_card(widget, p)
    elif name == "QLabel" and widget.objectName() == "UploadLogArea":
        _apply_log_label(widget, p)
    elif widget.objectName() in {"ctrl_panel", "cam_panel", "specs_card", "display_frame"}:
        _apply_yolo_dashboard_panel(widget, p)
    elif name == "QLabel" and widget.objectName() == "dashboard_status":
        _apply_yolo_dashboard_status(widget, p)
    elif name == "QLabel" and widget.objectName() == "dashboard_status_dot":
        widget.setStyleSheet("QLabel#dashboard_status_dot { background-color: #22C55E; border-radius: 3px; border: none; }")
    elif name == "QLabel" and widget.objectName() == "dashboard_cam_icon":
        _apply_yolo_dashboard_icon(widget, p)
    elif name == "QLabel" and _ancestor(widget, "MkMenuItem") is not None:
        _apply_menu_item(_ancestor(widget, "MkMenuItem"), p)
    elif name == "QLabel" and _ancestor(widget, "MkSubMenu") is not None:
        _apply_submenu(_ancestor(widget, "MkSubMenu"), p)
    elif name == "QPushButton" and _is_submenu_title_button(widget):
        _apply_submenu(_ancestor(widget, "MkSubMenu"), p)
    elif _is_combobox_popup_view(widget):
        combo = _ancestor(widget, "MkComboBox") or _ancestor(widget, "QComboBox")
        if combo is not None:
            _apply_combobox_view(combo, p)
    elif _is_yolo_plain_helper(widget):
        _apply_yolo_plain_helper(widget)
    elif _is_native_pyside_widget(widget):
        _apply_native_widget(widget, p)

    try:
        widget.update()
    except (TypeError, RuntimeError):
        pass


_NATIVE_PYSIDE_WIDGETS = {
    "QWidget",
    "QFrame",
    "QGroupBox",
    "QScrollArea",
    "QAbstractScrollArea",
    "QStackedWidget",
    "QLabel",
    "QPushButton",
    "QCommandLinkButton",
    "QToolButton",
    "QLineEdit",
    "QTextEdit",
    "QPlainTextEdit",
    "QTextBrowser",
    "QComboBox",
    "QSlider",
    "QDial",
    "QCheckBox",
    "QRadioButton",
    "QTabWidget",
    "QTabBar",
    "QListWidget",
    "QTreeWidget",
    "QTableWidget",
    "QTableView",
    "QListView",
    "QTreeView",
    "QHeaderView",
    "QProgressBar",
    "QSplitter",
    "QSpinBox",
    "QDoubleSpinBox",
    "QDateEdit",
    "QTimeEdit",
    "QDateTimeEdit",
    "QCalendarWidget",
    "QDialog",
    "QMainWindow",
    "QMenuBar",
    "QMenu",
    "QStatusBar",
    "QToolBar",
    "QDockWidget",
    "QDialogButtonBox",
    "QGraphicsView",
    "QMdiArea",
    "QLCDNumber",
    "QScrollBar",
}


def _is_native_pyside_widget(widget: QWidget) -> bool:
    return widget.__class__.__name__ in _NATIVE_PYSIDE_WIDGETS


def _ancestor(widget: QWidget, class_name: str) -> QWidget | None:
    current = widget.parentWidget()
    while current is not None:
        if current.__class__.__name__ == class_name:
            return current
        current = current.parentWidget()
    return None


def _is_descendant_of(widget: QWidget, ancestor: QWidget | None) -> bool:
    if ancestor is None:
        return False
    current = widget.parentWidget()
    while current is not None:
        if current is ancestor:
            return True
        current = current.parentWidget()
    return False


def _transparent_helper_qss(widget: QWidget) -> str:
    selector = _native_selector(widget)
    return f"{selector} {{ background: transparent; border: none; }}"


def _apply_datatable_descendant(widget: QWidget, p: dict[str, str | int | bool]) -> bool:
    owner = _ancestor(widget, "MkDataTable")
    if owner is None:
        return False

    table = getattr(owner, "table_widget", None)
    header = getattr(owner, "header_view", None)
    if widget is getattr(owner, "table_card", None):
        widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        widget.setStyleSheet(_datatable_card_qss(p))
        return True
    if widget is table:
        widget.setStyleSheet(_datatable_table_qss(p))
        return True
    if table is not None and widget is table.viewport():
        widget.setStyleSheet(
            f"QWidget {{ background-color: {_table_surface(p)}; border: none; }}"
        )
        return True
    if widget is header:
        widget.setStyleSheet(_datatable_header_qss(p))
        if hasattr(widget, "set_checkbox_palette"):
            widget.set_checkbox_palette(_checkbox_palette(p, table=True))
        return True

    inside_table = table is not None and _is_descendant_of(widget, table)
    if not inside_table:
        return False

    name = _theme_class_name(widget)
    if name == "MkCheckBox":
        widget.setStyleSheet(_table_checkbox_qss(p))
    elif name in ("QPushButton", "QToolButton"):
        widget.setStyleSheet(_table_action_button_qss(p))
    elif name == "QLabel":
        _style_label(widget, f"color: {p['text']}; background: transparent; border: none;")
    elif name in ("QWidget", "QFrame"):
        widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        widget.setStyleSheet(_transparent_helper_qss(widget))
    elif name == "QHeaderView":
        widget.setStyleSheet(_datatable_header_qss(p))
    else:
        return False
    return True


def _apply_table_descendant(widget: QWidget, p: dict[str, str | int | bool]) -> bool:
    owner = _ancestor(widget, "MkTable")
    if owner is None:
        return False

    if widget is owner.viewport():
        widget.setStyleSheet(
            f"QWidget {{ background-color: {_table_surface(p)}; border: none; }}"
        )
        return True
    if widget is owner.horizontalHeader() or widget is owner.verticalHeader():
        widget.setStyleSheet(_datatable_header_qss(p))
        return True
    if _theme_class_name(widget) == "QHeaderView":
        widget.setStyleSheet(_datatable_header_qss(p))
        return True
    return False


def _apply_pagination_descendant(widget: QWidget, p: dict[str, str | int | bool]) -> bool:
    owner = _ancestor(widget, "MkPagination")
    if owner is None:
        return False

    name = _theme_class_name(widget)
    if name == "QPushButton":
        widget.setStyleSheet(_pagination_button_qss(widget, p))
    elif name == "QLabel":
        widget.setStyleSheet(_pagination_label_qss(p))
    elif name == "QLineEdit":
        widget.setStyleSheet(_pagination_input_qss(p))
    else:
        return False
    return True


def _apply_auth_descendant(widget: QWidget, p: dict[str, str | int | bool]) -> bool:
    owner = _ancestor(widget, "MkAuthScreen")
    if owner is None:
        return False

    auth_card = getattr(owner, "auth_card", None)
    form_stack = getattr(owner, "form_stack", None)
    name = _theme_class_name(widget)
    compact = _with_radius(
        p,
        0 if p["flat"] else min(8, _control_radius_px(p)),
    )

    if widget is auth_card:
        widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        widget.setStyleSheet(_auth_card_qss(p))
    elif (
        widget is form_stack
        or (
            widget is not auth_card
            and _is_descendant_of(widget, auth_card)
            and name in ("QWidget", "QFrame", "QStackedWidget")
        )
    ):
        widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        widget.setStyleSheet(_transparent_helper_qss(widget))
    elif name == "MkInput":
        widget.setStyleSheet(_input_qss(compact))
    elif name == "MkCheckBox":
        widget.setStyleSheet(_checkbox_qss(compact))
    elif name in ("MkCaptchaWidget", "MkSmsCodeWidget"):
        widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        widget.setStyleSheet(_transparent_helper_qss(widget))
    elif name == "QLabel":
        color = p["muted"] if widget.text() == getattr(owner, "description", "") else p["text"]
        _style_label(widget, f"color: {color}; background: transparent; border: none;")
    elif name in ("QPushButton", "QToolButton"):
        widget.setStyleSheet(_auth_button_qss(widget, owner, compact))
    else:
        return False
    return True


def _combobox_owner(widget: QWidget) -> QWidget | None:
    if _theme_class_name(widget) in {"MkComboBox", "QComboBox"}:
        return None
    return _ancestor(widget, "MkComboBox") or _ancestor(widget, "QComboBox")


def _is_multicombobox_internal(widget: QWidget) -> bool:
    if _theme_class_name(widget) == "MkMultiComboBox":
        return False

    current = widget
    while current is not None:
        if current.__class__.__name__ == "MkMultiComboBox":
            return True
        if current.__class__.__name__ == "MkMultiComboPopup":
            return getattr(current, "parent_combo", None) is not None
        current = current.parentWidget()
    return False


def _is_yolo_mode_button(widget: QWidget) -> bool:
    dashboard = _ancestor(widget, "YoloDashboardWidget")
    if dashboard is None:
        return False
    return widget in {
        getattr(dashboard, "btn_mode_img", None),
        getattr(dashboard, "btn_mode_video", None),
        getattr(dashboard, "btn_mode_cam", None),
    }


def _is_yolo_plain_helper(widget: QWidget) -> bool:
    if _ancestor(widget, "YoloDashboardWidget") is None:
        return False
    name = _theme_class_name(widget)
    if name == "QStackedWidget":
        return True
    return name == "QWidget" and widget.objectName() in ("", "dashboard_select_group")


def _is_combobox_popup_view(widget: QWidget) -> bool:
    if _theme_class_name(widget) not in {"QListView", "QTreeView", "QTableView"}:
        return False
    return _ancestor(widget, "MkComboBox") is not None or _ancestor(widget, "QComboBox") is not None


def _apply_yolo_plain_helper(widget: QWidget) -> None:
    widget.setProperty("_mk_yolo_plain_helper", True)
    selector = f'{widget.__class__.__name__}[_mk_yolo_plain_helper="true"]'
    widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
    widget.setStyleSheet(f"""
        {selector} {{
            background: transparent;
            border: none;
        }}
    """)


def _is_submenu_title_button(widget: QWidget) -> bool:
    submenu = _ancestor(widget, "MkSubMenu")
    return submenu is not None and widget is getattr(submenu, "title_btn", None)


def _is_upload_remove_button(widget: QWidget) -> bool:
    if _theme_class_name(widget) != "QPushButton" or widget.text():
        return False

    current = widget.parentWidget()
    inside_file_card = False
    while current is not None:
        if current.objectName() == "FileCard":
            inside_file_card = True
        if current.__class__.__name__ == "MkUpload":
            return inside_file_card
        current = current.parentWidget()
    return False


def _apply_native_widget(widget: QWidget, p: dict[str, str | int | bool]) -> None:
    name = _theme_class_name(widget)

    if name == "QLabel":
        widget.setStyleSheet(_native_label_qss(widget, p))
    elif name in ("QPushButton", "QCommandLinkButton", "QToolButton"):
        if _is_upload_remove_button(widget):
            widget.setStyleSheet(_upload_remove_button_qss(p))
        else:
            widget.setStyleSheet(_native_button_qss(name, p))
    elif name in ("QLineEdit", "QTextEdit", "QPlainTextEdit", "QTextBrowser"):
        widget.setStyleSheet(_native_input_qss(name, p))
    elif name in ("QSpinBox", "QDoubleSpinBox", "QDateEdit", "QTimeEdit", "QDateTimeEdit"):
        widget.setStyleSheet(_native_input_qss(name, p))
    elif name == "QComboBox":
        widget.setStyleSheet(_combobox_qss(p))
        _apply_combobox_view(widget, p)
    elif name in ("QCheckBox", "QRadioButton"):
        widget.setStyleSheet(_native_choice_qss(name, p))
    elif name in ("QSlider", "QDial"):
        widget.setStyleSheet(_native_slider_qss(name, p))
    elif name in ("QTabWidget", "QTabBar"):
        widget.setStyleSheet(_native_tabs_qss(p))
    elif name in ("QListWidget", "QTreeWidget", "QTableWidget", "QTableView", "QListView", "QTreeView"):
        widget.setStyleSheet(_native_item_view_qss(name, p))
    elif name == "QHeaderView":
        widget.setStyleSheet(_native_header_qss(p))
    elif name == "QProgressBar":
        widget.setStyleSheet(_native_progress_qss(p))
    elif name == "QSplitter":
        widget.setStyleSheet(_native_splitter_qss(p))
    elif name == "QScrollBar":
        widget.setStyleSheet(_native_scrollbar_qss(p))
    elif name in ("QMenu", "QMenuBar"):
        widget.setStyleSheet(_native_menu_qss(name, p))
    elif name in ("QStatusBar", "QToolBar", "QDockWidget", "QDialogButtonBox"):
        widget.setStyleSheet(_native_panel_qss(widget, p))
    elif name in ("QCalendarWidget", "QGraphicsView", "QMdiArea", "QLCDNumber"):
        widget.setStyleSheet(_native_panel_qss(widget, p))
    else:
        widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        widget.setStyleSheet(_native_panel_qss(widget, p))


def _native_selector(widget: QWidget, fallback: str | None = None) -> str:
    name = fallback or widget.__class__.__name__
    object_name = widget.objectName()
    if object_name:
        return f"{name}#{object_name}"
    return name


def _native_panel_qss(widget: QWidget, p: dict[str, str | int | bool]) -> str:
    name = widget.__class__.__name__
    selector = _native_selector(widget)
    object_name = widget.objectName().lower()
    is_page = name in ("QWidget", "QStackedWidget", "QMainWindow", "QDialog", "QMdiArea")
    is_panel = (
        name in ("QFrame", "QGroupBox", "QScrollArea", "QAbstractScrollArea", "QDockWidget", "QToolBar")
        or "panel" in object_name
        or "card" in object_name
        or "container" in object_name
    )
    bg = _control_surface(p, floating=True) if p["glass"] and is_panel else str(p["panel"] if is_panel else p["bg"])
    border = f"{p['border_width']} solid {_control_border(p)}" if p["glass"] and is_panel else (str(p["border_rule"]) if is_panel else "none")
    radius = p["radius"] if is_panel and not is_page else "0px"
    return f"""
        {selector} {{
            background-color: {bg};
            color: {p['text']};
            border: {border};
            border-radius: {radius};
        }}
    """


def _native_label_qss(widget: QWidget, p: dict[str, str | int | bool]) -> str:
    selector = _native_selector(widget, "QLabel")
    color = p["muted"] if widget.property("muted") is True else p["text"]
    return f"""
        {selector} {{
            color: {color};
            background: transparent;
            border: none;
            font-family: {p['font']};
        }}
    """


def _native_button_qss(selector: str, p: dict[str, str | int | bool]) -> str:
    surface = _control_surface(p) if p["glass"] else str(p["surface"])
    hover = _control_muted_surface(p) if p["glass"] else str(p["surface_muted"])
    border = _control_border(p) if p["glass"] else str(p["border"])
    primary = qcolor(str(p["primary"])).name(QColor.NameFormat.HexRgb)
    primary_hover = lighten(primary, 0.10)
    primary_pressed = darken(primary, 0.08)
    return f"""
        {selector} {{
            background-color: {surface};
            color: {p['text']};
            border: {p['border_width']} solid {border if not p['flat'] else '#000000'};
            border-radius: {p['radius']};
            padding: 7px 14px;
            min-height: 28px;
            font-family: {p['font']};
            font-size: 13px;
            font-weight: 700;
            outline: none;
        }}
        {selector}:hover {{
            background-color: {hover};
            border-color: {primary};
            color: {p['text']};
        }}
        {selector}:pressed, {selector}:checked {{
            background-color: {primary};
            border-color: {primary if not p['flat'] else '#000000'};
            color: {p['primary_text']};
        }}
        {selector}:checked:hover {{
            background-color: {primary_hover};
            border-color: {primary_hover if not p['flat'] else '#000000'};
            color: {p['primary_text']};
        }}
        {selector}:pressed {{
            background-color: {primary_pressed};
        }}
        {selector}:disabled {{
            background-color: {_control_muted_surface(p)};
            color: {p['muted']};
            border-color: {border};
        }}
        {selector}::menu-indicator {{
            image: none;
        }}
    """


def _text_button_qss(p: dict[str, str | int | bool]) -> str:
    primary = qcolor(str(p["primary"])).name(QColor.NameFormat.HexRgb)
    hover = lighten(primary, 0.12) if p["dark"] else darken(primary, 0.10)
    return f"""
        MkButton, QPushButton {{
            background: transparent;
            border: none;
            color: {primary};
            font-family: {p['font']};
            font-size: 12px;
            font-weight: 700;
            padding: 0px;
            min-height: 0px;
            outline: none;
        }}
        MkButton:hover, QPushButton:hover {{
            color: {hover};
            background: transparent;
            text-decoration: underline;
        }}
        MkButton:pressed, QPushButton:pressed {{
            color: {primary};
            background: transparent;
        }}
        MkButton:disabled, QPushButton:disabled {{
            color: {p['muted']};
            background: transparent;
        }}
    """


def _upload_remove_button_qss(p: dict[str, str | int | bool]) -> str:
    hover = "#3A2024" if p["dark"] else "#FEECEC"
    pressed = "#4A2026" if p["dark"] else "#FDDDDD"
    return f"""
        QPushButton {{
            background-color: transparent;
            border: none;
            border-radius: {0 if p['flat'] else 4}px;
            padding: 0px;
            margin: 0px;
            min-width: 0px;
            min-height: 0px;
            outline: none;
        }}
        QPushButton:hover {{
            background-color: {hover};
            border: none;
        }}
        QPushButton:pressed {{
            background-color: {pressed};
            border: none;
        }}
        QPushButton:focus {{
            border: none;
            outline: none;
        }}
    """


def _native_input_qss(selector: str, p: dict[str, str | int | bool]) -> str:
    return _input_qss(p).replace("QLineEdit, MkInput, MkDatePicker", selector).replace(
        "QLineEdit:hover, MkInput:hover, MkDatePicker:hover", f"{selector}:hover"
    ).replace(
        "QLineEdit:focus, MkInput:focus, MkDatePicker:focus", f"{selector}:focus"
    ).replace(
        "QLineEdit:disabled, MkInput:disabled, MkDatePicker:disabled", f"{selector}:disabled"
    )


def _native_choice_qss(selector: str, p: dict[str, str | int | bool]) -> str:
    surface = _control_surface(p) if p["glass"] else str(p["surface"])
    muted_surface = _control_muted_surface(p)
    border = _control_border(p) if p["glass"] else str(p["border"])
    primary = qcolor(str(p["primary"])).name(QColor.NameFormat.HexRgb)
    is_radio = selector == "QRadioButton"
    return f"""
        {selector} {{
            color: {p['text']};
            spacing: 8px;
            background: transparent;
            font-family: {p['font']};
            font-size: 13px;
            outline: none;
        }}
        {selector}:hover {{
            color: {primary};
        }}
        {selector}:disabled {{
            color: {p['muted']};
        }}
        {selector}::indicator {{
            width: 16px;
            height: 16px;
            background-color: {surface};
            border: {p['border_width']} solid {border if not p['flat'] else '#000000'};
            border-radius: {8 if is_radio else (0 if p['flat'] else 4)}px;
        }}
        {selector}::indicator:hover {{
            border-color: {primary};
            background-color: {muted_surface};
        }}
        {selector}::indicator:checked {{
            background-color: {primary};
            border-color: {primary if not p['flat'] else '#000000'};
        }}
        {selector}::indicator:disabled {{
            background-color: {muted_surface};
            border-color: {border};
        }}
    """


def _native_slider_qss(selector: str, p: dict[str, str | int | bool]) -> str:
    if selector == "QDial":
        return f"""
            QDial {{
                background: transparent;
                color: {p['text']};
            }}
        """
    groove_border = "1px solid #000000" if p["flat"] else "none"
    groove_bg = _control_muted_surface(p)
    handle_border = "#000000" if p["flat"] else _control_surface(p, floating=True)
    primary = qcolor(str(p["primary"])).name(QColor.NameFormat.HexRgb)
    primary_hover = lighten(primary, 0.10)
    radius = 0 if p["flat"] else 3
    handle_radius = 0 if p["flat"] else 8
    return f"""
        QSlider {{
            background: transparent;
            border: none;
            min-height: 28px;
        }}
        QSlider::groove:horizontal {{
            border: {groove_border};
            height: 6px;
            background: {groove_bg};
            border-radius: {radius}px;
        }}
        QSlider::sub-page:horizontal {{
            background: {primary};
            border-radius: {radius}px;
        }}
        QSlider::add-page:horizontal {{
            background: {groove_bg};
            border-radius: {radius}px;
        }}
        QSlider::handle:horizontal {{
            background: {primary};
            border: 2px solid {handle_border};
            width: 16px;
            height: 16px;
            margin: -7px 0;
            border-radius: {handle_radius}px;
        }}
        QSlider::handle:horizontal:hover, QSlider::handle:horizontal:pressed {{
            background: {primary_hover};
            border-color: {handle_border};
        }}
        QSlider::groove:vertical {{
            border: {groove_border};
            width: 6px;
            background: {groove_bg};
            border-radius: {radius}px;
        }}
        QSlider::sub-page:vertical {{
            background: {primary};
            border-radius: {radius}px;
        }}
        QSlider::add-page:vertical {{
            background: {groove_bg};
            border-radius: {radius}px;
        }}
        QSlider::handle:vertical {{
            background: {primary};
            border: 2px solid {handle_border};
            width: 16px;
            height: 16px;
            margin: 0 -7px;
            border-radius: {handle_radius}px;
        }}
    """


def _native_tabs_qss(p: dict[str, str | int | bool]) -> str:
    panel = _control_surface(p, floating=True) if p["glass"] else str(p["panel"])
    border = _control_border(p) if p["glass"] else str(p["border"])
    return f"""
        QTabWidget::pane {{
            background-color: {panel};
            border: {p['border_width']} solid {border};
            border-radius: {p['radius']};
        }}
        QTabBar::tab {{
            background: transparent;
            color: {p['muted']};
            border: none;
            padding: 8px 14px;
            font-family: {p['font']};
            font-weight: 700;
        }}
        QTabBar::tab:hover {{
            color: {p['primary']};
            background-color: {_control_muted_surface(p)};
        }}
        QTabBar::tab:selected {{
            color: {p['primary_text']};
            background-color: {p['primary']};
            border-radius: {p['radius']};
        }}
    """


def _native_item_view_qss(selector: str, p: dict[str, str | int | bool]) -> str:
    panel = _control_surface(p, floating=True) if p["glass"] else str(p["panel"])
    border = _control_border(p) if p["glass"] else str(p["border"])
    return f"""
        {selector} {{
            background-color: {panel};
            alternate-background-color: {_control_muted_surface(p)};
            color: {p['text']};
            border: {p['border_width']} solid {border if not p['flat'] else '#000000'};
            border-radius: {p['radius']};
            gridline-color: {border};
            outline: none;
            selection-background-color: {p['primary']};
            selection-color: {p['primary_text']};
        }}
        {selector}::item {{
            color: {p['text']};
            background: transparent;
            border-bottom: {p['border_width']} solid {border};
            padding: 6px 8px;
        }}
        {selector}::item:hover {{
            background-color: {_control_muted_surface(p)};
        }}
        {selector}::item:selected {{
            background-color: {p['primary']};
            color: {p['primary_text']};
        }}
    """


def _native_header_qss(p: dict[str, str | int | bool]) -> str:
    bg = _control_muted_surface(p)
    border = _control_border(p) if p["glass"] else str(p["border"])
    return f"""
        QHeaderView {{
            background-color: {bg};
            color: {p['muted']};
            border: none;
        }}
        QHeaderView::section {{
            background-color: {bg};
            color: {p['muted']};
            border: none;
            border-bottom: {p['border_width']} solid {border};
            padding: 8px 10px;
            font-family: {p['font']};
            font-weight: 800;
        }}
    """


def _native_progress_qss(p: dict[str, str | int | bool]) -> str:
    return f"""
        QProgressBar {{
            background-color: {_control_muted_surface(p)};
            color: {p['text']};
            border: {p['border_width']} solid {_control_border(p)};
            border-radius: {p['radius']};
            text-align: center;
            font-family: {p['font']};
            font-weight: 700;
        }}
        QProgressBar::chunk {{
            background-color: {p['primary']};
            border-radius: {p['radius']};
        }}
    """


def _native_splitter_qss(p: dict[str, str | int | bool]) -> str:
    return f"""
        QSplitter {{
            background: transparent;
            border: none;
        }}
        QSplitter::handle {{
            background-color: {_control_border(p)};
        }}
        QSplitter::handle:hover {{
            background-color: {p['primary']};
        }}
    """


def _native_scrollbar_qss(p: dict[str, str | int | bool]) -> str:
    return _scroll_qss(p, vertical=True, horizontal=True)


def _native_menu_qss(selector: str, p: dict[str, str | int | bool]) -> str:
    surface = _control_surface(p, floating=True) if p["glass"] else str(p["surface"])
    border = _control_border(p) if p["glass"] else str(p["border"])
    return f"""
        {selector} {{
            background-color: {surface};
            color: {p['text']};
            border: {p['border_width']} solid {border};
        }}
        {selector}::item {{
            background: transparent;
            color: {p['text']};
            padding: 6px 12px;
        }}
        {selector}::item:selected {{
            background-color: {p['primary']};
            color: {p['primary_text']};
        }}
    """


def _apply_yolo_dashboard(widget: QWidget, p: dict[str, str | int | bool]) -> None:
    widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    widget.setStyleSheet(f"""
        YoloDashboardWidget {{
            background: transparent;
            color: {p['text']};
        }}
        QLabel {{
            color: {p['text']};
            background: transparent;
            border: none;
            font-family: {p['font']};
        }}
    """)

    for frame_name, muted in (
        ("ctrl_panel", False),
        ("cam_panel", True),
        ("specs_card", False),
        ("display_frame", True),
    ):
        frame = getattr(widget, frame_name, None) or widget.findChild(QWidget, frame_name)
        if frame is None:
            continue
        _save_widget(frame)
        _apply_yolo_dashboard_panel(frame, p)

    status_label = getattr(widget, "lbl_status", None) or widget.findChild(QLabel, "dashboard_status")
    if status_label is not None:
        _style_label(status_label, f"""
            QLabel#dashboard_status {{
                font-family: Consolas, "Microsoft YaHei", monospace;
                font-size: 11px;
                color: {p['muted']};
                background-color: {_control_muted_surface(p)};
                border: {p['border_width']} solid {_control_border(p)};
                border-radius: {0 if p['flat'] else 4}px;
                padding: 8px;
            }}
        """)

    clear_btn = getattr(widget, "btn_clear_classes", None)
    if clear_btn is not None:
        _save_widget(clear_btn)
        clear_btn.setStyleSheet(_text_button_qss(p))

    for button_name in ("btn_mode_img", "btn_mode_video", "btn_mode_cam"):
        mode_button = getattr(widget, button_name, None)
        if mode_button is None:
            continue
        _save_widget(mode_button)
        _apply_yolo_mode_button(mode_button, p)

    icon_label = getattr(widget, "cam_icon", None)
    if icon_label is not None:
        _apply_yolo_dashboard_icon(icon_label, p)

    status_dot = getattr(widget, "status_dot", None)
    if status_dot is not None:
        _save_widget(status_dot)
        status_dot.setStyleSheet("background-color: #22C55E; border-radius: 3px;")

    input_stack = getattr(widget, "input_stack", None)
    if input_stack is not None:
        _save_widget(input_stack)
        if not input_stack.objectName():
            input_stack.setObjectName("dashboard_input_stack")
        input_stack.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        input_stack.setStyleSheet("""
            QStackedWidget#dashboard_input_stack {
                background: transparent;
                border: none;
            }
        """)

    for upload_name in ("upload_img", "upload_video"):
        upload = getattr(widget, upload_name, None)
        if upload is not None:
            _save_widget(upload)
            _apply_upload(upload, p)

    for combo_name in ("model_combo", "camera_combo"):
        combo = getattr(widget, combo_name, None)
        if combo is not None:
            _save_widget(combo)
            combo.setStyleSheet(_combobox_qss(p))
            _apply_combobox_view(combo, p)

    class_combo = getattr(widget, "class_combo", None)
    if class_combo is not None:
        _save_widget(class_combo)
        _apply_multicombobox(class_combo, p)

    camera_combo = getattr(widget, "camera_combo", None)
    if camera_combo is not None and camera_combo.parentWidget() is not None:
        select_group = camera_combo.parentWidget()
        if not select_group.objectName():
            select_group.setObjectName("dashboard_select_group")
        _save_widget(select_group)
        select_group.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        select_group.setStyleSheet("""
            QWidget#dashboard_select_group {
                background: transparent;
                border: none;
            }
        """)

    for slider_name in ("slider_conf", "slider_iou"):
        slider = getattr(widget, slider_name, None)
        if slider is not None:
            _save_widget(slider)
            _apply_slider(slider, p)

    for button_name in (
        "btn_browse_model",
        "btn_refresh_cam",
        "btn_detect_run",
        "btn_pause",
        "btn_resume",
        "btn_stop",
    ):
        button = getattr(widget, button_name, None)
        if button is not None:
            _save_widget(button)
            _apply_button(button, p)


def _apply_yolo_dashboard_panel(widget: QWidget, p: dict[str, str | int | bool]) -> None:
    object_name = widget.objectName()
    selector = f"{widget.__class__.__name__}#{object_name}"
    bg = _yolo_panel_surface(p, object_name)
    border = _yolo_panel_border(p, object_name)
    widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    widget.setStyleSheet(f"""
        {selector} {{
            background-color: {bg};
            border: {border};
            border-radius: {p['radius']};
        }}
        QLabel {{
            color: {p['text']};
            background: transparent;
            border: none;
        }}
    """)


def _apply_yolo_dashboard_status(widget: QWidget, p: dict[str, str | int | bool]) -> None:
    widget.setStyleSheet(f"""
        QLabel#dashboard_status {{
            font-family: Consolas, "Microsoft YaHei", monospace;
            font-size: 11px;
            color: {p['muted']};
            background-color: {_control_muted_surface(p)};
            border: {p['border_width']} solid {_control_border(p)};
            border-radius: {0 if p['flat'] else 4}px;
            padding: 8px;
        }}
    """)


def _apply_yolo_dashboard_icon(widget: QWidget, p: dict[str, str | int | bool]) -> None:
    widget.setStyleSheet("QLabel#dashboard_cam_icon { background: transparent; border: none; }")
    try:
        from monkeyqt.core.icons import MkPhosphorIcon
        widget.setPixmap(MkPhosphorIcon.get_pixmap("video-camera", str(p["primary"]), 18))
    except Exception:
        pass


def _apply_yolo_mode_button(widget: QWidget, p: dict[str, str | int | bool]) -> None:
    mk_type = str(getattr(widget, "mk_type", "") or getattr(widget, "_mk_type", "") or widget.property("mk_type") or "default")
    widget.setProperty("mk_type", mk_type)

    is_oled = _theme_name_has("dark mode", "oled")
    primary = "#E5E5E5" if is_oled else qcolor(str(p["primary"])).name(QColor.NameFormat.HexRgb)
    border = "transparent" if is_oled else _control_border(p)
    inactive_bg = "#202020" if is_oled else (_control_surface(p) if p["glass"] else str(p["surface"]))
    inactive_hover = "#2A2A2A" if is_oled else (_control_muted_surface(p) if p["glass"] else str(p["surface_muted"]))
    active_bg = "#303030" if is_oled else ("#122033" if p["dark"] else lighten(primary, 0.48))
    active_hover = "#383838" if is_oled else ("#172A45" if p["dark"] else lighten(primary, 0.40))
    active_border = "#454545" if is_oled else primary
    disabled_bg = _control_muted_surface(p) if p["glass"] else str(p["surface_muted"])
    disabled_fg = "#64748B" if p["glass"] and not p["dark"] else str(p["muted"])
    radius = 6 if not p["flat"] else 0

    widget.setStyleSheet(f"""
        MkButton {{
            background-color: {inactive_bg};
            color: {p['text']};
            border: {p['border_width']} solid {border};
            border-radius: {radius}px;
            padding: 8px 12px;
            min-height: 28px;
            font-family: {p['font']};
            font-size: 13px;
            font-weight: 700;
            outline: none;
        }}
        MkButton:hover {{
            background-color: {inactive_hover};
            border-color: {active_border if not is_oled else 'transparent'};
            color: {p['text']};
        }}
        MkButton[mk_type="primary"] {{
            background-color: {active_bg};
            border-color: {active_border};
            color: {primary};
        }}
        MkButton[mk_type="primary"]:hover {{
            background-color: {active_hover};
            border-color: {active_border};
            color: {primary};
        }}
        MkButton:pressed {{
            background-color: {_pressed(inactive_bg)};
            border-color: {active_border};
        }}
        MkButton[mk_type="primary"]:pressed {{
            background-color: {_pressed(active_bg)};
            color: {primary};
        }}
        MkButton:disabled,
        MkButton[mk_type="primary"]:disabled {{
            background-color: {disabled_bg};
            border-color: {border};
            color: {disabled_fg};
        }}
    """)


def _yolo_panel_surface(p: dict[str, str | int | bool], object_name: str) -> str:
    if object_name in {"ctrl_panel", "specs_card"}:
        return _control_surface(p, floating=True)
    if p["glass"] and not p["dark"]:
        return "#F8FBFF" if object_name == "display_frame" else "#FFFFFF"
    if p["neumorphic"] and not p["dark"]:
        return str(p["surface"])
    if object_name == "cam_panel":
        return _control_surface(p, floating=True)
    return _control_muted_surface(p)


def _yolo_panel_border(p: dict[str, str | int | bool], object_name: str) -> str:
    style = "dashed" if object_name == "cam_panel" and not p["flat"] else "solid"
    color = _control_border(p)
    width = str(p["border_width"])
    if p["flat"] and object_name in {"cam_panel", "specs_card"}:
        width = "1px"
    return f"{width} {style} {color}"


def _apply_button(widget: QWidget, p: dict[str, str | int | bool]) -> None:
    mk_type = str(getattr(widget, "mk_type", "") or getattr(widget, "_mk_type", "") or widget.property("mk_type") or "default")
    widget.setProperty("mk_type", mk_type)
    cls = widget.__class__.__name__
    default_bg = _control_surface(p) if p["glass"] else str(p["surface"])
    default_hover = _control_muted_surface(p) if p["glass"] else str(p["surface_muted"])
    default_border = _control_border(p) if p["glass"] else str(p["border"])
    disabled_bg = _control_muted_surface(p) if p["glass"] else str(p["surface_muted"])
    disabled_fg = "#64748B" if p["glass"] and not p["dark"] else str(p["muted"])
    text_hover = lighten(str(p["primary"]), 0.12) if p["dark"] else darken(str(p["primary"]), 0.10)
    accents = {
        "primary": (str(p["primary"]), str(p["primary_text"])),
        "success": ("#22C55E", "#FFFFFF"),
        "warning": ("#F59E0B", "#111827"),
        "danger": ("#EF4444", "#FFFFFF"),
        "error": ("#EF4444", "#FFFFFF"),
        "info": (str(p["accent"]), readable_text(str(p["accent"]))),
    }
    accent_qss = []
    for btn_type, (bg, fg) in accents.items():
        border = "#000000" if p["flat"] else bg
        hover_bg = _soft_hover(p, bg)
        hover_fg = fg
        accent_qss.append(f"""
        {cls}[mk_type="{btn_type}"] {{
            background-color: {bg};
            border-color: {border};
            color: {fg};
        }}
        {cls}[mk_type="{btn_type}"]:hover {{
            background-color: {hover_bg};
            border-color: {border};
            color: {hover_fg};
        }}
        {cls}[mk_type="{btn_type}"]:pressed {{
            background-color: {_pressed(bg)};
            border-color: {border};
            color: {fg};
        }}
        {cls}[mk_type="{btn_type}"]:disabled {{
            background-color: {disabled_bg};
            border-color: {_control_border(p) if p['glass'] else p['border']};
            color: {disabled_fg};
        }}
        """)

    widget.setStyleSheet(f"""
        {cls} {{
            background-color: {default_bg};
            color: {p['text']};
            border: {p['border_width']} solid {default_border if not p['flat'] else '#000000'};
            border-radius: {p['radius']};
            padding: 8px 15px;
            font-family: {p['font']};
            font-size: 13px;
            font-weight: 700;
            outline: none;
        }}
        {cls}:hover {{
            background-color: {default_hover};
            border-color: {p['primary']};
            color: {p['text']};
        }}
        {cls}:pressed {{
            background-color: {_pressed(default_bg)};
        }}
        {cls}:disabled {{
            background-color: {disabled_bg};
            color: {disabled_fg};
            border-color: {_control_border(p) if p['glass'] else p['border']};
        }}
        {cls}[mk_type="text"] {{
            background: transparent;
            border: none;
            color: {p['primary']};
            padding: 0px;
            min-height: 0px;
        }}
        {cls}[mk_type="text"]:hover {{
            background: transparent;
            color: {text_hover};
            text-decoration: underline;
        }}
        {cls}::menu-indicator {{
            image: none;
        }}
        {''.join(accent_qss)}
    """)


def _apply_window(widget: QWidget, p: dict[str, str | int | bool]) -> None:
    if not hasattr(widget, "_mk_theme_original_update_style") and hasattr(widget, "update_style"):
        widget._mk_theme_original_update_style = widget.update_style

        def _theme_update_style(self):
            result = self._mk_theme_original_update_style()
            if ThemeEngine.current_theme() != ThemeEngine.DEFAULT_THEME_NAME:
                _apply_window(self, _palette())
            return result

        widget.update_style = types.MethodType(_theme_update_style, widget)

    if getattr(widget, "use_custom_title_bar", False):
        _apply_native_window_corners(widget, p)
        if getattr(widget, "_root_widget", None) is not None:
            if not widget._root_widget.objectName():
                widget._root_widget.setObjectName("MkWindowRootWidget")
            _save_widget(widget._root_widget)
            widget._root_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            widget._root_widget.setStyleSheet("""
                QWidget#MkWindowRootWidget {
                    background: transparent;
                    border: none;
                }
            """)
        if getattr(widget, "container_frame", None) is not None:
            _save_widget(widget.container_frame)
            _apply_window_container(widget.container_frame, p)
        if getattr(widget, "titlebar", None) is not None:
            _save_widget(widget.titlebar)
            _apply_titlebar(widget.titlebar, p)


def _restore_window(widget: QWidget) -> None:
    _restore_native_window_corners(widget)
    if hasattr(widget, "_mk_theme_original_update_style"):
        widget.update_style = widget._mk_theme_original_update_style
        delattr(widget, "_mk_theme_original_update_style")
        try:
            widget.update_style()
        except RuntimeError:
            pass


def _apply_window_container(widget: QWidget, p: dict[str, str | int | bool]) -> None:
    window = widget.window()
    native_corners = bool(getattr(window, "_mk_theme_uses_native_corners", False))
    radius = 0 if native_corners else min(int(p["radius_px"]), 8)
    border = _control_border(p) if p["glass"] else str(p["border"])
    border_rule = "none" if native_corners else f"{p['border_width']} solid {border}"
    surface = _control_surface(p, floating=True) if p["glass"] else str(p["chrome_surface"] if p["dark"] else p["bg"])
    widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    widget.setStyleSheet(f"""
        QFrame#MkWindowContainer {{
            background-color: {surface};
            border: {border_rule};
            border-radius: {radius}px;
        }}
    """)
    if native_corners:
        _restore_rounded_mask(widget)
    else:
        _apply_rounded_mask(widget, radius, window)

    shadow = getattr(window, "_shadow_effect", None)
    if shadow is not None:
        try:
            shadow.setColor(QColor(0, 0, 0, 90 if p["dark"] else 45))
            shadow.setBlurRadius(22 if p["glass"] else 15)
        except RuntimeError:
            pass

    content_host = getattr(window, "_content_host", None)
    if content_host is not None:
        _save_widget(content_host)
        content_host.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        content_host.setStyleSheet(f"""
            QWidget#MkWindowContentHost {{
                background-color: {p['bg']};
                border: none;
            }}
        """)

    desktop_shell = getattr(window, "_desktop_shell", None)
    if desktop_shell is not None:
        _save_widget(desktop_shell)
        desktop_shell.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        desktop_shell.setStyleSheet(f"""
            QWidget#MkWindowDesktopShell {{
                background-color: {p['bg']};
                border: none;
            }}
        """)

    sidebar_host = getattr(window, "_sidebar_host", None)
    if sidebar_host is not None:
        _save_widget(sidebar_host)
        sidebar_host.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        sidebar_host.setStyleSheet(f"""
            QWidget#MkWindowSidebarHost {{
                background-color: {p['sidebar_surface']};
                border: none;
            }}
        """)


def _titlebar_surface(widget: QWidget, p: dict[str, str | int | bool]) -> str:
    follows_content = bool(widget.property("mkContentAlignedTitleBar"))
    if not follows_content:
        window = widget.window()
        follows_content = bool(getattr(window, "_sidebar_full_height", False))
    use_content_surface = (
        follows_content
        and not ThemeEngine.has_override("--titlebar-bg")
    )
    return str(p["bg"] if use_content_surface else p["chrome_surface"])


def _apply_titlebar(widget: QWidget, p: dict[str, str | int | bool]) -> None:
    if not hasattr(widget, "_mk_theme_original_titlebar_state"):
        widget._mk_theme_original_titlebar_state = {
            "bg": getattr(widget, "_bg_color", None),
            "text": getattr(widget, "_text_color", None),
            "hover": getattr(widget, "_hover_color", None),
            "border": getattr(widget, "_border_bottom", ""),
        }

    if not hasattr(widget, "_mk_theme_original_apply_theme_colors") and hasattr(widget, "apply_theme_colors"):
        widget._mk_theme_original_apply_theme_colors = widget.apply_theme_colors

        def _theme_apply_theme_colors(self):
            if ThemeEngine.current_theme() == ThemeEngine.DEFAULT_THEME_NAME:
                return self._mk_theme_original_apply_theme_colors()
            _apply_titlebar(self, _palette())
            return None

        widget.apply_theme_colors = types.MethodType(_theme_apply_theme_colors, widget)

    if not hasattr(widget, "_mk_theme_original_paint_event"):
        widget._mk_theme_original_paint_event = widget.paintEvent

        def _theme_paint_event(self, event):
            if ThemeEngine.current_theme() == ThemeEngine.DEFAULT_THEME_NAME:
                return self._mk_theme_original_paint_event(event)

            palette = _palette()
            surface = _titlebar_surface(self, palette)

            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
            painter.fillRect(self.rect(), QColor(surface))
            painter.end()

        widget.paintEvent = types.MethodType(_theme_paint_event, widget)

    _force_titlebar_theme(widget, p)


def _force_titlebar_theme(widget: QWidget, p: dict[str, str | int | bool]) -> None:
    surface = _titlebar_surface(widget, p)
    hover = _control_muted_surface(p) if p["glass"] else str(p["surface_muted"])
    text = readable_text(surface)

    widget._bg_color = surface
    widget._text_color = text
    widget._hover_color = hover
    widget._border_bottom = "none"
    widget.setObjectName("MkTitleBar")
    widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

    if hasattr(widget, "_mk_theme_original_apply_theme_colors"):
        widget._mk_theme_original_apply_theme_colors()
    elif hasattr(widget, "apply_theme_colors"):
        widget.apply_theme_colors()

    widget.setStyleSheet(f"""
        QWidget#MkTitleBar {{
            background-color: {surface};
            color: {text};
            border: none;
        }}
        QWidget#MkTitleBar QLabel {{
            color: {text};
            background: transparent;
            border: none;
        }}
        QWidget#MkTitleBar QWidget {{
            background: transparent;
            border: none;
        }}
    """)

    center = getattr(widget, "center_container", None)
    if center is not None:
        _save_widget(center)
        if not center.objectName():
            center.setObjectName("TitleBarCenterContainer")
        center.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        center.setStyleSheet("""
            QWidget#TitleBarCenterContainer {
                background: transparent;
                border: none;
            }
        """)

    if hasattr(widget, "apply_theme_colors"):
        for btn_name, is_close in (
            ("btn_min", False),
            ("btn_max", False),
            ("btn_close", True),
        ):
            btn = getattr(widget, btn_name, None)
            if btn is None:
                continue
            _save_widget(btn)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: none;
                    border-radius: 0px;
                    color: {text};
                }}
                QPushButton:hover {{
                    background-color: {'#E81123' if is_close else hover};
                    color: {'#FFFFFF' if is_close else text};
                }}
            """)


def _restore_titlebar(widget: QWidget) -> None:
    state = getattr(widget, "_mk_theme_original_titlebar_state", None)
    if not state:
        return
    widget._bg_color = state["bg"]
    widget._text_color = state["text"]
    widget._hover_color = state["hover"]
    widget._border_bottom = state["border"]
    delattr(widget, "_mk_theme_original_titlebar_state")
    if hasattr(widget, "apply_theme_colors"):
        widget.apply_theme_colors()


def _checkbox_qss(p: dict[str, str | int | bool]) -> str:
    surface = _control_surface(p) if p["glass"] else str(p["surface"])
    muted_surface = _control_muted_surface(p) if p["glass"] else str(p["surface_muted"])
    border_rule = f"{p['border_width']} solid {_control_border(p)}" if p["glass"] else str(p["border_rule"])
    border = _control_border(p) if p["glass"] else str(p["border"])
    primary = qcolor(str(p["primary"])).name(QColor.NameFormat.HexRgb) if p["glass"] else str(p["primary"])
    return f"""
        MkCheckBox {{
            color: {p['text']};
            spacing: 8px;
            font-family: {p['font']};
            font-size: 13px;
            background: transparent;
            outline: none;
        }}
        MkCheckBox:hover {{ color: {p['primary']}; }}
        MkCheckBox:disabled {{ color: {p['muted']}; }}
        MkCheckBox::indicator {{
            width: 15px;
            height: 15px;
            background-color: {surface};
            border: {border_rule};
            border-radius: {0 if p['flat'] else 4}px;
        }}
        MkCheckBox::indicator:hover {{
            border-color: {primary};
        }}
        MkCheckBox::indicator:checked {{
            background-color: {primary};
            border-color: {primary if not p['flat'] else '#000000'};
        }}
        MkCheckBox::indicator:disabled {{
            background-color: {muted_surface};
            border-color: {border};
        }}
    """


def _table_checkbox_border(p: dict[str, str | int | bool]) -> str:
    surface = qcolor(str(p["panel"]))
    primary = qcolor(str(p["primary"]))
    border = primary if (p["dark"] or p["glass"]) else qcolor(str(p["border"]))

    if abs(luminance(surface) - luminance(border)) < 0.08:
        border = qcolor(str(p["muted"]))
    if abs(luminance(surface) - luminance(border)) < 0.08:
        border = primary

    return border.name(QColor.NameFormat.HexRgb)


def _checkbox_palette(p: dict[str, str | int | bool], table: bool = False) -> dict[str, str | int | float]:
    surface = qcolor(str(p["surface"]))
    border = qcolor(_table_checkbox_border(p) if table else str(p["border"]))
    if abs(luminance(surface) - luminance(border)) < 0.02:
        border = qcolor(str(p["muted"]))

    return {
        "surface": surface.name(QColor.NameFormat.HexRgb),
        "border": border.name(QColor.NameFormat.HexRgb),
        "primary": qcolor(str(p["primary"])).name(QColor.NameFormat.HexRgb),
        "check": qcolor(str(p["primary_text"])).name(QColor.NameFormat.HexRgb),
        "radius": 0 if p["flat"] else 3,
        "border_width": 1.0 if table else 1.2,
    }


def _control_surface(p: dict[str, str | int | bool], *, floating: bool = False) -> str:
    if p["glass"]:
        if p["dark"]:
            return "#111827" if floating else "#0F172A"
        return "#F8FBFF" if floating else "#F2F7FF"
    return str(p["surface"])


def _control_muted_surface(p: dict[str, str | int | bool]) -> str:
    if p["glass"]:
        return "#1E293B" if p["dark"] else "#EAF3FF"
    return str(p["surface_muted"])


def _control_border(p: dict[str, str | int | bool]) -> str:
    if p["glass"]:
        return "#334155" if p["dark"] else "#D7E6F8"
    return str(p["border"])


def _embedded_input_surface(p: dict[str, str | int | bool]) -> str:
    if p["dark"]:
        return str(p["bg"])
    if p["glass"] or p["neumorphic"]:
        return "#FFFFFF"
    return str(p["surface"])


def _embedded_popup_surface(p: dict[str, str | int | bool]) -> str:
    if p["dark"]:
        return str(p["surface"])
    if p["glass"] or p["neumorphic"]:
        return "#FFFFFF"
    return str(p["surface"])


def _soft_selection_surface(p: dict[str, str | int | bool]) -> str:
    primary = qcolor(str(p["primary"])).name(QColor.NameFormat.HexRgb)
    if p["dark"]:
        return lighten(primary, 0.18)
    if p["glass"] or p["neumorphic"]:
        return lighten(primary, 0.72)
    return lighten(primary, 0.62)


def _soft_selection_text(p: dict[str, str | int | bool]) -> str:
    if p["dark"]:
        return str(p["primary_text"])
    return qcolor(str(p["primary"])).name(QColor.NameFormat.HexRgb)


def _table_checkbox_qss(p: dict[str, str | int | bool]) -> str:
    border = _table_checkbox_border(p)
    primary = qcolor(str(p["primary"])).name(QColor.NameFormat.HexRgb)
    primary_hover = lighten(primary, 0.10)
    raw_surface = p["panel"] if (p["dark"] or p["glass"]) else p["surface"]
    surface = qcolor(str(raw_surface)).name(QColor.NameFormat.HexRgb)
    hover_bg = qcolor(str(p["surface_muted"])).name(QColor.NameFormat.HexRgb)
    disabled_bg = qcolor(str(p["surface_muted"] if not p["dark"] else p["panel"])).name(QColor.NameFormat.HexRgb)
    disabled_border = qcolor(str(p["border"])).name(QColor.NameFormat.HexRgb)
    return f"""
        MkCheckBox {{
            color: {p['text']};
            spacing: 0px;
            background: transparent;
            outline: none;
            padding: 0px;
            margin: 0px;
        }}
        MkCheckBox::indicator {{
            width: 16px;
            height: 16px;
            background-color: {surface};
            border: 1px solid {border};
            border-radius: {0 if p['flat'] else 4}px;
        }}
        MkCheckBox::indicator:unchecked {{
            background-color: {surface};
            border: 1px solid {border};
        }}
        MkCheckBox::indicator:hover {{
            background-color: {hover_bg};
            border-color: {primary};
        }}
        MkCheckBox::indicator:checked {{
            background-color: {primary};
            border-color: {primary};
        }}
        MkCheckBox::indicator:checked:hover {{
            background-color: {primary_hover};
            border-color: {primary_hover};
        }}
        MkCheckBox::indicator:disabled {{
            background-color: {disabled_bg};
            border: 1px solid {disabled_border};
        }}
    """


def _input_qss(p: dict[str, str | int | bool]) -> str:
    surface = _control_surface(p) if p["glass"] else (str(p["bg"]) if p["dark"] else str(p["surface"]))
    focus_surface = _control_surface(p, floating=True) if p["glass"] else str(p["panel"])
    muted_surface = _control_muted_surface(p) if p["glass"] else str(p["surface_muted"])
    border_rule = f"{p['border_width']} solid {_control_border(p)}" if p["glass"] else str(p["border_rule"])
    primary = qcolor(str(p["primary"])).name(QColor.NameFormat.HexRgb) if p["glass"] else str(p["primary"])
    return f"""
        QLineEdit, MkInput, MkDatePicker {{
            background-color: {surface};
            color: {p['text']};
            border: {border_rule};
            border-radius: {p['radius']};
            padding: 6px 12px;
            min-height: 30px;
            font-family: {p['font']};
            font-size: 13px;
            selection-background-color: {p['primary']};
            selection-color: {p['primary_text']};
        }}
        QLineEdit:hover, MkInput:hover, MkDatePicker:hover {{
            border-color: {primary};
        }}
        QLineEdit:focus, MkInput:focus, MkDatePicker:focus {{
            border-color: {primary};
            background-color: {focus_surface};
        }}
        QLineEdit:disabled, MkInput:disabled, MkDatePicker:disabled {{
            background-color: {muted_surface};
            color: {p['muted']};
        }}
    """


def _combobox_qss(p: dict[str, str | int | bool]) -> str:
    surface = _embedded_input_surface(p)
    popup_surface = _embedded_popup_surface(p)
    focus_surface = _control_surface(p, floating=True) if p["glass"] else surface
    hover_surface = _control_muted_surface(p) if p["glass"] else str(p["surface_muted"])
    border_rule = f"1px solid {_control_border(p)}"
    primary = qcolor(str(p["primary"])).name(QColor.NameFormat.HexRgb) if p["glass"] else str(p["primary"])
    selected_text = _soft_selection_text(p)
    control_radius = _control_radius_px(p)
    popup_radius = _popup_radius_px(p)
    return f"""
        QComboBox, MkComboBox {{
            background-color: {surface};
            color: {p['text']};
            border: {border_rule};
            border-radius: {control_radius}px;
            padding: 6px 34px 6px 12px;
            min-height: 28px;
            font-family: {p['font']};
            font-size: 13px;
        }}
        QComboBox:hover, MkComboBox:hover {{
            border-color: {primary};
        }}
        QComboBox:on, QComboBox:focus, MkComboBox:on, MkComboBox:focus {{
            border-color: {primary};
            background-color: {focus_surface};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 28px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {popup_surface};
            color: {p['text']};
            border: {border_rule};
            border-radius: {popup_radius}px;
            padding: 4px;
            outline: none;
            selection-background-color: transparent;
            selection-color: {p['text']};
        }}
        QComboBox QAbstractItemView::item {{
            min-height: 30px;
            padding: 4px 10px;
            margin: 2px;
            border-radius: {0 if p['flat'] else 4}px;
            background: transparent;
            color: {p['text']};
        }}
        QComboBox QAbstractItemView::item:hover {{
            background-color: {hover_surface};
            color: {p['text']};
        }}
        QComboBox QAbstractItemView::item:selected {{
            background-color: transparent;
            color: {selected_text};
        }}
        QComboBox QAbstractItemView::item:selected:hover {{
            background-color: {hover_surface};
            color: {selected_text};
        }}
    """


def _apply_combobox_view(widget: QWidget, p: dict[str, str | int | bool]) -> None:
    if not hasattr(widget, "view"):
        return
    try:
        view = widget.view()
    except RuntimeError:
        return
    if view is None:
        return
    if not hasattr(widget, "_mk_theme_original_combobox_show_popup") and hasattr(widget, "showPopup"):
        widget._mk_theme_original_combobox_show_popup = widget.showPopup

        def _theme_show_popup(self):
            _apply_combobox_view(self, _palette())
            self._mk_theme_original_combobox_show_popup()
            _apply_combobox_view(self, _palette())
            QTimer.singleShot(0, lambda: _refresh_combobox_popup(self))

        widget.showPopup = types.MethodType(_theme_show_popup, widget)

    _save_widget(view)
    view.setStyleSheet(_combobox_view_qss(p))
    popup_surface = _embedded_popup_surface(p)
    radius = _popup_radius_px(p)
    _apply_popup_window_shape(view, radius)
    try:
        container = view.parentWidget()
        if container is not None and container is not widget:
            _save_widget(container)
            container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            container.setStyleSheet(f"""
                QFrame {{
                    background-color: {popup_surface};
                    border: none;
                    border-radius: {radius}px;
                    padding: 0px;
                    margin: 0px;
                }}
            """)
            _apply_popup_window_shape(container, radius)
    except RuntimeError:
        pass
    try:
        _save_widget(view.viewport())
        view.viewport().setStyleSheet(f"background-color: {popup_surface}; border: none;")
    except RuntimeError:
        pass


def _refresh_combobox_popup(widget: QWidget) -> None:
    try:
        if ThemeEngine.current_theme() != ThemeEngine.DEFAULT_THEME_NAME:
            _apply_combobox_view(widget, _palette())
            widget.update()
    except RuntimeError:
        pass


def _restore_combobox(widget: QWidget) -> None:
    if hasattr(widget, "_mk_theme_original_combobox_show_popup"):
        widget.showPopup = widget._mk_theme_original_combobox_show_popup
        delattr(widget, "_mk_theme_original_combobox_show_popup")
    if not hasattr(widget, "view"):
        return
    try:
        view = widget.view()
        if view is None:
            return
        _restore_rounded_mask(view)
        _restore_widget(view)
        _restore_widget(view.viewport())
        container = view.parentWidget()
        if container is not None and container is not widget:
            _restore_rounded_mask(container)
            _restore_widget(container)
    except RuntimeError:
        pass


def _combobox_view_qss(p: dict[str, str | int | bool]) -> str:
    popup_surface = _embedded_popup_surface(p)
    hover_surface = _control_muted_surface(p)
    selected_text = _soft_selection_text(p)
    border = _control_border(p)
    radius = _popup_radius_px(p)
    return f"""
        QAbstractItemView, QListView {{
            background-color: {popup_surface};
            color: {p['text']};
            border: 1px solid {border};
            border-radius: {radius}px;
            padding: 4px;
            outline: none;
            selection-background-color: transparent;
            selection-color: {p['text']};
        }}
        QAbstractItemView::item, QListView::item {{
            min-height: 30px;
            padding: 4px 10px;
            margin: 2px;
            border-radius: {0 if p['flat'] else 4}px;
            background: transparent;
            color: {p['text']};
        }}
        QAbstractItemView::item:hover, QListView::item:hover {{
            background-color: {hover_surface};
            color: {p['text']};
        }}
        QAbstractItemView::item:selected, QListView::item:selected {{
            background-color: transparent;
            color: {selected_text};
        }}
        QAbstractItemView::item:selected:hover, QListView::item:selected:hover {{
            background-color: {hover_surface};
            color: {selected_text};
        }}
        {_scroll_qss(p, vertical=True)}
    """


def _apply_multicombobox(widget: QWidget, p: dict[str, str | int | bool]) -> None:
    face_surface = _embedded_input_surface(p)
    popup_surface = _embedded_popup_surface(p)
    hover_surface = _control_muted_surface(p)
    border = _control_border(p)
    primary = qcolor(str(p["primary"])).name(QColor.NameFormat.HexRgb)
    text = qcolor(str(p["text"])).name(QColor.NameFormat.HexRgb)
    muted = qcolor(str(p["muted"])).name(QColor.NameFormat.HexRgb)
    selected_text = _soft_selection_text(p)
    control_radius = _control_radius_px(p)
    popup_radius = _popup_radius_px(p)
    _patch_multicombobox_lifecycle(widget)
    if not hasattr(widget, "_mk_theme_original_multicombo_update_text") and hasattr(widget, "_update_text"):
        widget._mk_theme_original_multicombo_update_text = widget._update_text

        def _theme_update_text(self):
            checked_texts = self.get_checked_texts()
            full_text = ", ".join(checked_texts) if checked_texts else "默认检测所有类别"
            self.text_label.setText(full_text)
            color = str(_palette()["text"] if checked_texts else _palette()["muted"])
            _style_label(self.text_label, f"color: {color}; background: transparent; border: none; font-family: {_palette()['font']}; font-size: 13px;")
            if checked_texts:
                self.text_label.adjustSize()

        widget._update_text = types.MethodType(_theme_update_text, widget)

    widget.setStyleSheet(f"""
        QFrame#combo_frame {{
            background-color: {face_surface};
            border: 1px solid {border};
            border-radius: {control_radius}px;
            min-height: 32px;
            max-height: 32px;
        }}
        QFrame#combo_frame:hover, QFrame#combo_frame[focused="true"] {{
            border-color: {primary};
        }}
    """)
    if hasattr(widget, "text_label"):
        label_color = text if getattr(widget.text_label, "text", lambda: "")() else muted
        _style_label(widget.text_label, f"color: {label_color}; background: transparent; border: none; font-family: {p['font']}; font-size: 13px;")
        try:
            widget._update_text()
        except RuntimeError:
            pass
    if hasattr(widget, "scroll_area"):
        _save_widget(widget.scroll_area)
        widget.scroll_area.setStyleSheet(f"""
            QScrollArea#MultiComboFaceScrollArea {{
                background-color: {face_surface};
                border: none;
            }}
            QScrollArea#MultiComboFaceScrollArea > QWidget {{
                background-color: {face_surface};
                border: none;
            }}
            {_scroll_qss(p, horizontal=True)}
        """)
        _save_widget(widget.scroll_area.viewport())
        widget.scroll_area.viewport().setStyleSheet(f"background-color: {face_surface}; border: none;")
    if hasattr(widget, "popup"):
        popup = widget.popup
        if not hasattr(popup, "_mk_theme_original_show_popup") and hasattr(popup, "show_popup"):
            popup._mk_theme_original_show_popup = popup.show_popup

            def _theme_show_popup(self):
                _apply_multicombobox(self.parent_combo, _palette())
                self._mk_theme_original_show_popup()
                _position_multicombobox_popup(self)
                _apply_multicombobox(self.parent_combo, _palette())
                QTimer.singleShot(0, lambda: _position_multicombobox_popup(self))

            popup.show_popup = types.MethodType(_theme_show_popup, popup)

        _save_widget(popup)
        popup.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        popup.setStyleSheet(f"""
            QFrame#popup_frame {{
                background-color: {popup_surface};
                border: 1px solid {border};
                border-radius: {popup_radius}px;
                padding: 0px;
            }}
            QWidget#scroll_widget {{
                background-color: {popup_surface};
                border: none;
            }}
        """)
        _apply_popup_window_shape(popup, popup_radius)
        if hasattr(popup, "scroll_area"):
            _save_widget(popup.scroll_area)
            popup.scroll_area.setStyleSheet(f"""
                QScrollArea#MultiComboPopupScrollArea {{
                    background-color: {popup_surface};
                    border: none;
                }}
                QScrollArea#MultiComboPopupScrollArea > QWidget {{
                    background-color: {popup_surface};
                    border: none;
                }}
                {_scroll_qss(p, vertical=True)}
            """)
            _save_widget(popup.scroll_area.viewport())
            popup.scroll_area.viewport().setStyleSheet(f"background-color: {popup_surface}; border: none;")
        if hasattr(popup, "scroll_widget"):
            _save_widget(popup.scroll_widget)
            popup.scroll_widget.setStyleSheet(f"QWidget#scroll_widget {{ background-color: {popup_surface}; border: none; }}")
        for _, _, checkbox, item_widget in getattr(popup, "items", []):
            _save_widget(checkbox)
            checkbox.setStyleSheet(_checkbox_qss(p))
            _save_widget(item_widget)
            item_widget.setStyleSheet(f"""
                MkMultiComboItem {{
                    background-color: transparent;
                    border: none;
                    border-radius: {0 if p['flat'] else 6}px;
                    margin: 1px;
                }}
                MkMultiComboItem:hover {{
                    background-color: {hover_surface};
                    color: {p['text']};
                }}
                MkMultiComboItem[checked="true"] {{
                    background-color: transparent;
                    color: {selected_text};
                }}
            """)
            try:
                item_widget.setProperty("checked", checkbox.isChecked())
            except RuntimeError:
                pass


def _position_multicombobox_popup(popup: QWidget) -> None:
    try:
        combo = popup.parent_combo
        if not popup.isVisible() or not getattr(popup, "items", None):
            return

        top_left = combo.mapToGlobal(combo.rect().topLeft())
        screen = QApplication.screenAt(top_left)
        if screen is None:
            screen = combo.screen()
        available = screen.availableGeometry()

        width = max(combo.width(), popup.minimumWidth())
        desired_height = min(220, len(popup.items) * 28 + 12)
        gap = 4
        below_y = top_left.y() + combo.height() + gap
        below_space = available.bottom() - below_y + 1
        above_space = top_left.y() - available.top() - gap

        if below_space >= desired_height or below_space >= above_space:
            height = min(desired_height, max(72, below_space))
            y = below_y
        else:
            height = min(desired_height, max(72, above_space))
            y = top_left.y() - height - gap

        x = min(max(top_left.x(), available.left()), available.right() - width + 1)
        y = min(max(y, available.top()), available.bottom() - height + 1)
        popup.setGeometry(x, y, width, height)
        popup.raise_()
    except (AttributeError, RuntimeError):
        pass


def _patch_multicombobox_lifecycle(widget: QWidget) -> None:
    if hasattr(widget, "_mk_theme_original_multicombo_lifecycle"):
        return

    method_names = (
        "addItem",
        "addItems",
        "clear",
        "setCheckedData",
        "clear_checked",
        "_on_item_state_changed",
    )
    originals = {
        name: getattr(widget, name)
        for name in method_names
        if hasattr(widget, name)
    }
    widget._mk_theme_original_multicombo_lifecycle = originals

    for method_name in originals:
        def _themed_method(self, *args, _method_name=method_name, **kwargs):
            nesting = getattr(self, "_mk_theme_multicombo_update_depth", 0)
            self._mk_theme_multicombo_update_depth = nesting + 1
            try:
                original = self._mk_theme_original_multicombo_lifecycle[_method_name]
                if _method_name == "_on_item_state_changed":
                    # Qt signals may supply the checkbox state even though the
                    # original slot intentionally accepts no arguments.
                    return original()
                return original(*args, **kwargs)
            finally:
                self._mk_theme_multicombo_update_depth -= 1
                if self._mk_theme_multicombo_update_depth == 0:
                    _apply_multicombobox(self, _palette())

        setattr(widget, method_name, types.MethodType(_themed_method, widget))


def _restore_multicombobox(widget: QWidget) -> None:
    if hasattr(widget, "_mk_theme_original_multicombo_update_text"):
        widget._update_text = widget._mk_theme_original_multicombo_update_text
        delattr(widget, "_mk_theme_original_multicombo_update_text")
    if hasattr(widget, "_mk_theme_original_multicombo_lifecycle"):
        for method_name, method in widget._mk_theme_original_multicombo_lifecycle.items():
            setattr(widget, method_name, method)
        delattr(widget, "_mk_theme_original_multicombo_lifecycle")
    if hasattr(widget, "_mk_theme_multicombo_update_depth"):
        delattr(widget, "_mk_theme_multicombo_update_depth")
    for extra in ("scroll_area", "text_label", "popup"):
        if hasattr(widget, extra):
            _restore_widget(getattr(widget, extra))
    if hasattr(widget, "scroll_area"):
        _restore_widget(widget.scroll_area.viewport())
    if hasattr(widget, "popup"):
        popup = widget.popup
        if hasattr(popup, "_mk_theme_original_show_popup"):
            popup.show_popup = popup._mk_theme_original_show_popup
            delattr(popup, "_mk_theme_original_show_popup")
        _restore_rounded_mask(popup)
        if hasattr(popup, "scroll_area"):
            _restore_widget(popup.scroll_area)
            _restore_widget(popup.scroll_area.viewport())
        if hasattr(popup, "scroll_widget"):
            _restore_widget(popup.scroll_widget)
        for _, _, checkbox, item_widget in getattr(popup, "items", []):
            _restore_widget(checkbox)
            _restore_widget(item_widget)


def _apply_slider(widget: QWidget, p: dict[str, str | int | bool]) -> None:
    if hasattr(widget, "value_label"):
        _style_label(widget.value_label, f"color: {p['text']}; background: transparent; font-family: {p['font']}; font-size: 13px; font-weight: 600;")
    if not hasattr(widget, "slider"):
        return
    slider = widget.slider
    _save_widget(slider)
    handle_radius = 0 if p["flat"] else 8
    groove_border = "1px solid #000000" if p["flat"] else "none"
    groove_bg = _control_muted_surface(p)
    handle_border = "#000000" if p["flat"] else _control_surface(p, floating=True)
    primary = qcolor(str(p["primary"])).name(QColor.NameFormat.HexRgb)
    primary_hover = lighten(primary, 0.10)
    slider.setStyleSheet(f"""
        QSlider:horizontal {{
            min-height: 28px;
            border: none;
            background: transparent;
        }}
        QSlider::groove:horizontal {{
            border: {groove_border};
            height: 6px;
            background: {groove_bg};
            border-radius: {0 if p['flat'] else 3}px;
        }}
        QSlider::sub-page:horizontal {{
            background: {primary};
            border-radius: {0 if p['flat'] else 3}px;
        }}
        QSlider::handle:horizontal {{
            background: {primary};
            border: 2px solid {handle_border};
            width: 16px;
            height: 16px;
            margin: -7px 0;
            border-radius: {handle_radius}px;
        }}
        QSlider::handle:horizontal:hover {{
            background: {primary_hover};
            width: 20px;
            height: 20px;
            margin: -9px 0;
            border-radius: {0 if p['flat'] else 10}px;
        }}
        QSlider:vertical {{
            min-width: 28px;
            border: none;
            background: transparent;
        }}
        QSlider::groove:vertical {{
            border: {groove_border};
            width: 6px;
            background: {groove_bg};
            border-radius: {0 if p['flat'] else 3}px;
        }}
        QSlider::sub-page:vertical {{
            background: {primary};
            border-radius: {0 if p['flat'] else 3}px;
        }}
        QSlider::handle:vertical {{
            background: {primary};
            border: 2px solid {handle_border};
            width: 16px;
            height: 16px;
            margin: 0 -7px;
            border-radius: {handle_radius}px;
        }}
    """)


def _apply_switch(widget: QWidget, p: dict[str, str | int | bool]) -> None:
    if not hasattr(widget, "_mk_theme_original_switch_colors"):
        widget._mk_theme_original_switch_colors = (QColor(widget._active_color), QColor(widget._inactive_color))
    widget._active_color = qcolor(str(p["primary"]))
    widget._inactive_color = qcolor(str(p["surface_muted"]))
    widget.update()


def _apply_form(widget: QWidget, p: dict[str, str | int | bool]) -> None:
    widget.setStyleSheet("MkForm { background: transparent; border: none; }")
    for label in widget.findChildren(QLabel):
        if label.parent() is widget:
            _style_label(label, f"color: {p['muted']}; background: transparent; font-size: 14px; font-weight: 700; font-family: {p['font']};")


def _apply_auth_control_panel(widget: QWidget, p: dict[str, str | int | bool]) -> None:
    widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    widget.setStyleSheet(f"""
        QFrame#AuthControlPanel {{
            background-color: {p['panel']};
            border: {p['border_rule']};
            border-radius: {p['radius']};
            padding: 15px;
        }}
    """)
    for label in widget.findChildren(QLabel):
        if label.objectName() == "AuthPanelTitle":
            _style_label(label, f"font-size: 15px; color: {p['text']}; font-weight: 800; margin-bottom: 5px; background: transparent;")
        else:
            _style_label(label, f"font-size: 13px; color: {p['muted']}; font-weight: 700; margin-top: 10px; background: transparent;")


def _reapply_table(widget: QWidget) -> None:
    try:
        if ThemeEngine.current_theme() != ThemeEngine.DEFAULT_THEME_NAME:
            _apply_table(widget, _palette())
    except RuntimeError:
        pass


def _apply_table(widget: QWidget, p: dict[str, str | int | bool]) -> None:
    widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    widget.setStyleSheet(_table_qss(p))
    if hasattr(widget, "setAlternatingRowColors"):
        widget.setAlternatingRowColors(False)
    if hasattr(widget, "setShowGrid"):
        widget.setShowGrid(False)

    try:
        viewport = widget.viewport()
        _save_widget(viewport)
        viewport.setStyleSheet(
            f"QWidget {{ background-color: {_table_surface(p)}; border: none; }}"
        )
        for header in (widget.horizontalHeader(), widget.verticalHeader()):
            _save_widget(header)
            header.setStyleSheet(_datatable_header_qss(p))
    except (AttributeError, RuntimeError):
        pass

    if not getattr(widget, "_mk_theme_initial_table_reapply", False):
        widget._mk_theme_initial_table_reapply = True
        QTimer.singleShot(0, lambda w=widget: _reapply_table(w))


def _reapply_datatable(widget: QWidget) -> None:
    try:
        if ThemeEngine.current_theme() != ThemeEngine.DEFAULT_THEME_NAME:
            _apply_datatable(widget, _palette())
    except RuntimeError:
        pass


def _apply_datatable(widget: QWidget, p: dict[str, str | int | bool]) -> None:
    if not hasattr(widget, "_mk_theme_original_refresh_table"):
        widget._mk_theme_original_refresh_table = widget.refresh_table

        def _theme_refresh_table(self):
            result = self._mk_theme_original_refresh_table()
            if ThemeEngine.current_theme() != ThemeEngine.DEFAULT_THEME_NAME:
                _reapply_datatable(self)
                QTimer.singleShot(0, lambda w=self: _reapply_datatable(w))
            return result

        widget.refresh_table = types.MethodType(_theme_refresh_table, widget)

    widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    widget.setStyleSheet(f"""
        MkDataTable {{
            background-color: transparent;
            color: {p['text']};
            border: none;
        }}
    """)

    if hasattr(widget, "table_card"):
        _save_widget(widget.table_card)
        widget.table_card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        widget.table_card.setStyleSheet(_datatable_card_qss(p))

    if hasattr(widget, "table_widget"):
        table = widget.table_widget
        _save_widget(table)
        table.setStyleSheet(_datatable_table_qss(p))
        _save_widget(table.viewport())
        table.viewport().setStyleSheet(
            f"QWidget {{ background-color: {_table_surface(p)}; border: none; }}"
        )

    if hasattr(widget, "header_view"):
        _save_widget(widget.header_view)
        widget.header_view.setStyleSheet(_datatable_header_qss(p))
        if hasattr(widget.header_view, "set_checkbox_palette"):
            widget.header_view.set_checkbox_palette(_checkbox_palette(p, table=True))

    if hasattr(widget, "pagination"):
        _save_widget(widget.pagination)
        _apply_pagination(widget.pagination, p)

    if hasattr(widget, "table_widget"):
        for button_type in (QPushButton, QToolButton):
            for btn in widget.table_widget.findChildren(button_type):
                _save_widget(btn)
                btn.setStyleSheet(_table_action_button_qss(p))

    for child in widget.findChildren(QWidget):
        cname = child.__class__.__name__
        if child.objectName() == "DataTableCheckCell":
            _save_widget(child)
            child.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
            child.setStyleSheet("""
                QWidget#DataTableCheckCell {
                    background: transparent;
                    border: none;
                }
            """)
        elif cname == "MkCheckBox":
            _save_widget(child)
            child.setStyleSheet(_table_checkbox_qss(p))
        elif cname == "QLabel":
            _style_label(child, f"color: {p['text']}; background: transparent; border: none;")
        elif (
            hasattr(widget, "table_widget")
            and _is_descendant_of(child, widget.table_widget)
            and cname in ("QWidget", "QFrame")
        ):
            _save_widget(child)
            child.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
            child.setStyleSheet(_transparent_helper_qss(child))

    if not getattr(widget, "_mk_theme_initial_datatable_reapply", False):
        widget._mk_theme_initial_datatable_reapply = True
        QTimer.singleShot(0, lambda w=widget: _reapply_datatable(w))


def _apply_pagination(widget: QWidget, p: dict[str, str | int | bool]) -> None:
    if hasattr(widget, "_update_ui") and not hasattr(widget, "_mk_theme_original_pagination_update_ui"):
        widget._mk_theme_original_pagination_update_ui = widget._update_ui

        def _themed_update_ui(self, *args, **kwargs):
            result = self._mk_theme_original_pagination_update_ui(*args, **kwargs)
            if ThemeEngine.current_theme() != ThemeEngine.DEFAULT_THEME_NAME:
                _apply_pagination(self, _palette())
                QTimer.singleShot(0, lambda w=self: _apply_pagination(w, _palette()))
            return result

        widget._update_ui = types.MethodType(_themed_update_ui, widget)

    widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
    widget.setStyleSheet(_pagination_qss(p))
    for button in widget.findChildren(QPushButton):
        _save_widget(button)
        button.setStyleSheet(_pagination_button_qss(button, p))
    for label in widget.findChildren(QLabel):
        _save_widget(label)
        label.setStyleSheet(_pagination_label_qss(p))
    for line_edit in widget.findChildren(QLineEdit):
        _save_widget(line_edit)
        line_edit.setStyleSheet(_pagination_input_qss(p))


def _apply_upload(widget: QWidget, p: dict[str, str | int | bool]) -> None:
    if not hasattr(widget, "_mk_theme_original_set_drag_state"):
        widget._mk_theme_original_set_drag_state = widget.set_drag_state

        def _theme_set_drag_state(self, active: bool):
            _apply_upload_state(self, _palette(), active)

        widget.set_drag_state = types.MethodType(_theme_set_drag_state, widget)

    widget.setStyleSheet("MkUpload { background: transparent; border: none; }")
    _apply_upload_state(widget, p, False)

    if hasattr(widget, "file_list_widget"):
        _save_widget(widget.file_list_widget)
        widget.file_list_widget.setStyleSheet("background: transparent; border: none;")
    for card in widget.findChildren(QWidget, "FileCard"):
        _save_widget(card)
        card.setStyleSheet(f"""
            QFrame#FileCard {{
                background-color: {p['panel']};
                border: {p['border_rule']};
                border-radius: {p['radius']};
            }}
            QFrame#FileCard:hover {{
                background-color: {p['surface_muted']};
                border-color: {p['primary']};
            }}
        """)
        for button in card.findChildren(QPushButton):
            if _is_upload_remove_button(button):
                _save_widget(button)
                button.setStyleSheet(_upload_remove_button_qss(p))


def _apply_upload_state(widget: QWidget, p: dict[str, str | int | bool], active: bool) -> None:
    border_color = p["primary"] if active else p["border"]
    if p["glass"]:
        bg = _control_surface(p, floating=True)
        if active:
            bg = _control_muted_surface(p)
        border_color = p["primary"] if active else _control_border(p)
    elif p["neumorphic"] and not p["dark"]:
        bg = str(p["surface"])
        if active:
            bg = _tint(p["primary"], 0.86, str(p["surface_muted"]))
    else:
        bg = _tint(p["primary"], 0.88, p["panel"]) if active and not p["dark"] else p["panel"]

    if active and p["dark"] and not p["glass"]:
        bg = p["surface_muted"]

    if hasattr(widget, "drop_area"):
        _save_widget(widget.drop_area)
        widget.drop_area.setStyleSheet(f"""
            QFrame#MkDropArea {{
                border: 2px dashed {border_color};
                border-radius: {p['radius']};
                background-color: {bg};
            }}
            QFrame#MkDropArea:hover {{
                border-color: {p['primary']};
                background-color: {p['surface_muted']};
            }}
        """)
    if hasattr(widget, "main_text_label"):
        _style_label(widget.main_text_label, f"color: {p['text']}; background: transparent; font-weight: 700;")
    if hasattr(widget, "tip_label"):
        _style_label(widget.tip_label, f"color: {p['muted']}; background: transparent;")
    if hasattr(widget, "icon_label"):
        try:
            from monkeyqt.core.icons import MkPhosphorIcon
            widget.icon_label.setPixmap(MkPhosphorIcon.get_pixmap("upload-simple", str(p["primary"] if active else p["muted"]), 48))
        except Exception:
            pass


def _apply_auth_screen(widget: QWidget, p: dict[str, str | int | bool]) -> None:
    for method_name in ("switch_mode", "add_register_field"):
        original_name = f"_mk_theme_original_auth_{method_name}"
        if hasattr(widget, method_name) and not hasattr(widget, original_name):
            setattr(widget, original_name, getattr(widget, method_name))

            def _themed_auth_method(self, *args, _method_name=method_name, **kwargs):
                result = getattr(self, f"_mk_theme_original_auth_{_method_name}")(*args, **kwargs)
                if ThemeEngine.current_theme() != ThemeEngine.DEFAULT_THEME_NAME:
                    _reapply_auth_screen(self)
                    QTimer.singleShot(0, lambda w=self: _reapply_auth_screen(w))
                return result

            setattr(widget, method_name, types.MethodType(_themed_auth_method, widget))

    widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    widget.setStyleSheet("MkAuthScreen { background: transparent; border: none; }")

    if hasattr(widget, "auth_card"):
        _save_widget(widget.auth_card)
        widget.auth_card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        widget.auth_card.setStyleSheet(_auth_card_qss(p))
        for child in widget.auth_card.findChildren(QWidget):
            if (
                child is not widget.auth_card
                and _theme_class_name(child) in ("QWidget", "QFrame", "QStackedWidget")
            ):
                _save_widget(child)
                child.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
                child.setStyleSheet(_transparent_helper_qss(child))

    if hasattr(widget, "form_stack"):
        _save_widget(widget.form_stack)
        widget.form_stack.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        widget.form_stack.setStyleSheet(
            "QStackedWidget { background: transparent; border: none; }"
        )
        for page_index in range(widget.form_stack.count()):
            page = widget.form_stack.widget(page_index)
            _save_widget(page)
            page.setProperty("_mk_auth_page", True)
            page.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
            page.setStyleSheet("""
                QWidget[_mk_auth_page="true"] {
                    background: transparent;
                    border: none;
                }
            """)

    compact = _with_radius(
        p,
        0 if p["flat"] else min(8, _control_radius_px(p)),
    )
    for label in widget.findChildren(QLabel):
        if not label.text():
            continue
        color = p["muted"] if label.text() == getattr(widget, "description", "") else p["text"]
        _style_label(label, f"color: {color}; background: transparent; border: none;")

    for line_edit in widget.findChildren(QWidget):
        if line_edit.__class__.__name__ == "MkInput":
            _save_widget(line_edit)
            line_edit.setStyleSheet(_input_qss(compact))
        elif line_edit.__class__.__name__ == "MkCheckBox":
            _save_widget(line_edit)
            line_edit.setStyleSheet(_checkbox_qss(compact))

    for btn in widget.findChildren(QPushButton):
        _save_widget(btn)
        btn.setStyleSheet(_auth_button_qss(btn, widget, compact))

    if not getattr(widget, "_mk_theme_initial_auth_reapply", False):
        widget._mk_theme_initial_auth_reapply = True
        QTimer.singleShot(0, lambda w=widget: _reapply_auth_screen(w))


def _reapply_auth_screen(widget: QWidget) -> None:
    try:
        if ThemeEngine.current_theme() != ThemeEngine.DEFAULT_THEME_NAME:
            _apply_auth_screen(widget, _palette())
    except RuntimeError:
        pass


def _apply_status_card(widget: QWidget, p: dict[str, str | int | bool]) -> None:
    widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    widget.setStyleSheet(f"""
        QFrame#DataTableInteractionCard {{
            background-color: {p['panel']};
            border: {p['border_rule']};
            border-radius: {p['radius']};
        }}
        QLabel {{
            color: {p['muted']};
            background: transparent;
            border: none;
            font-size: 12px;
        }}
    """)


def _apply_log_label(widget: QWidget, p: dict[str, str | int | bool]) -> None:
    widget.setStyleSheet(f"""
        QLabel#UploadLogArea {{
            background-color: {p['panel']};
            border: {p['border_rule']};
            border-radius: {p['radius']};
            padding: 10px;
            font-family: Consolas;
            font-size: 11px;
            color: {p['text']};
        }}
    """)


def _alert_qss(widget: QWidget, p: dict[str, str | int | bool]) -> str:
    mk_type = str(getattr(widget, "_mk_type", "info"))
    accents = {
        "info": p["primary"],
        "success": "#22C55E",
        "warning": "#F59E0B",
        "error": "#EF4444",
    }
    accent = accents.get(mk_type, p["primary"])
    bg = _tint(accent, 0.88, p["bg"]) if not p["dark"] else p["surface"]
    return f"""
        MkAlert {{
            background-color: {bg};
            border: {p['border_width']} solid {accent if not p['flat'] else '#000000'};
            border-radius: {p['radius']};
        }}
        MkAlert QLabel {{
            background: transparent;
        }}
        QLabel#alert-title {{
            color: {p['text']};
            font-size: 13px;
            font-weight: 700;
        }}
        QLabel#alert-desc {{
            color: {p['muted']};
            font-size: 12px;
        }}
        QPushButton#alert-close-btn {{
            background: transparent;
            border: none;
            color: {accent};
        }}
    """


def _apply_progress(widget: QWidget, p: dict[str, str | int | bool]) -> None:
    if not hasattr(widget, "_mk_theme_original_get_color"):
        widget._mk_theme_original_get_color = widget._get_color

    def _theme_color(self):
        colors = {
            "normal": p["primary"],
            "success": "#22C55E",
            "warning": "#F59E0B",
            "exception": "#EF4444",
        }
        return colors.get(getattr(self, "_status", "normal"), p["primary"])

    widget._get_color = types.MethodType(_theme_color, widget)
    if hasattr(widget, "text_label"):
        _style_label(widget.text_label, f"color: {p['text']}; background: transparent; font-weight: 700;")
    widget.update()

def _apply_menu(widget: QWidget, p: dict[str, str | int | bool]) -> None:
    widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    widget.setStyleSheet(f"""
        MkMenu {{
            background-color: {p['sidebar_surface']};
            border: none;
        }}
    """)
    if hasattr(widget, "inner_frame"):
        _save_widget(widget.inner_frame)
        border_right = getattr(widget, "_border_right_style", str(p['border_rule']))
        widget.inner_frame.setStyleSheet(f"""
            QFrame#SidebarInnerFrame {{
                background-color: {p['sidebar_surface']};
                border: none;
                border-right: {border_right};
                border-radius: 0px;
            }}
        """)
    if hasattr(widget, "hamburger_btn"):
        _save_widget(widget.hamburger_btn)
        widget.hamburger_btn.setStyleSheet(f"""
            QPushButton#SidebarHamburgerButton {{
                border: none;
                background: transparent;
                font-size: 20px;
                color: {p['sidebar_muted']};
                padding: 0px;
                margin: 0px;
            }}
            QPushButton#SidebarHamburgerButton:hover {{
                color: {p['sidebar_accent']};
            }}
        """)
    if hasattr(widget, "scroll_area"):
        _save_widget(widget.scroll_area)
        widget.scroll_area.setStyleSheet(f"""
            QScrollArea#SidebarScrollArea {{
                background-color: {p['sidebar_surface']};
                border: none;
            }}
            QScrollArea#SidebarScrollArea QWidget {{
                background-color: {p['sidebar_surface']};
                border: none;
            }}
            {_scroll_qss(p, vertical=True)}
        """)
    if hasattr(widget, "content_widget"):
        _save_widget(widget.content_widget)
        if not widget.content_widget.objectName():
            widget.content_widget.setObjectName("SidebarContentWidget")
        widget.content_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        widget.content_widget.setStyleSheet(f"""
            QWidget#SidebarContentWidget {{
                background-color: {p['sidebar_surface']};
                border: none;
            }}
        """)
    if hasattr(widget, "title_area"):
        _save_widget(widget.title_area)
        if not widget.title_area.objectName():
            widget.title_area.setObjectName("SidebarTitleArea")
        widget.title_area.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        widget.title_area.setStyleSheet(f"""
            QWidget#SidebarTitleArea {{
                background-color: {p['sidebar_surface']};
                border: none;
            }}
        """)
    if hasattr(widget, "title_label"):
        _style_label(widget.title_label, f"font-size: 16px; font-weight: 800; color: {p['sidebar_text']}; background: transparent;")
    if hasattr(widget, "collapse_btn"):
        _save_widget(widget.collapse_btn)
        widget.collapse_btn.setProperty("_mk_theme_fixed_width", 24)
        widget.collapse_btn.setProperty("_mk_theme_fixed_height", 24)
        widget.collapse_btn.setFixedSize(24, 24)
        widget.collapse_btn.setStyleSheet(f"""
            QPushButton#SidebarCollapseButton {{
                background-color: {p['sidebar_surface']};
                border: {p['border_rule']};
                border-radius: 12px;
                color: {p['sidebar_text']};
                font-size: 12px;
                font-weight: 800;
            }}
            QPushButton#SidebarCollapseButton:hover {{
                color: {p['sidebar_accent']};
                border-color: {p['sidebar_accent']};
                background-color: {p['surface_muted']};
            }}
        """)

    for child in widget.findChildren(QWidget):
        child_name = child.__class__.__name__
        if child_name == "MkMenuItem":
            _save_widget(child)
            _apply_menu_item(child, p)
        elif child_name == "MkSubMenu":
            _save_widget(child)
            _apply_submenu(child, p)


def _apply_menu_item(widget: QWidget, p: dict[str, str | int | bool]) -> None:
    if not hasattr(widget, "_mk_theme_original_menu_styles"):
        widget._mk_theme_original_menu_styles = (
            widget._base_style,
            widget._label_style,
            widget._label_checked_style,
            widget._label_hover_style,
        )

    widget._base_style = """
        MkMenuItem {
            border: none;
            background: transparent;
            padding: 0px;
            margin: 0px;
        }
        MkMenuItem:hover { background-color: transparent; }
        MkMenuItem:checked { background-color: transparent; }
    """
    widget._label_style = f"""
        QLabel {{
            color: {p['sidebar_muted']};
            font-size: 14px;
            font-family: {p['font']};
            border: none;
            background: transparent;
        }}
    """
    widget._label_checked_style = f"""
        QLabel {{
            color: {p['sidebar_accent']};
            font-size: 14px;
            font-weight: 800;
            font-family: {p['font']};
            border: none;
            background: transparent;
        }}
    """
    widget._label_hover_style = f"""
        QLabel {{
            color: {p['sidebar_accent']};
            font-size: 14px;
            font-family: {p['font']};
            border: none;
            background: transparent;
        }}
    """
    widget.setStyleSheet(widget._base_style)
    if hasattr(widget, "_item_height"):
        widget.setProperty("_mk_theme_fixed_height", widget._item_height)
        widget.setFixedHeight(widget._item_height)

    # Patch hardcoded text & icon colors so that they correctly adapt to the active theme's colors
    if not hasattr(widget, "_mk_theme_original_methods"):
        widget._mk_theme_original_methods = {
            "_update_label_styles": widget._update_label_styles,
            "enterEvent": widget.enterEvent,
            "leaveEvent": widget.leaveEvent,
        }

    def _themed_update_label_styles(self):
        if ThemeEngine.current_theme() == ThemeEngine.DEFAULT_THEME_NAME:
            if hasattr(self, "_mk_theme_original_methods"):
                return self._mk_theme_original_methods["_update_label_styles"]()
            return

        palette = _palette()
        primary_color = str(palette["sidebar_accent"])
        muted_color = str(palette["sidebar_muted"])

        if self.isChecked():
            self.icon_label.setStyleSheet(self._label_checked_style)
            self.text_label.setStyleSheet(self._label_checked_style)
            self._update_icon_color(primary_color)
        else:
            self.icon_label.setStyleSheet(self._label_style)
            self.text_label.setStyleSheet(self._label_style)
            self._update_icon_color(muted_color)

    def _themed_enter_event(self, event):
        if ThemeEngine.current_theme() == ThemeEngine.DEFAULT_THEME_NAME:
            if hasattr(self, "_mk_theme_original_methods"):
                return self._mk_theme_original_methods["enterEvent"](event)
            return

        from PySide6.QtWidgets import QPushButton
        QPushButton.enterEvent(self, event)

        if not self.isChecked():
            palette = _palette()
            primary_color = str(palette["sidebar_accent"])
            self.icon_label.setStyleSheet(self._label_hover_style)
            self.text_label.setStyleSheet(self._label_hover_style)
            self._update_icon_color(primary_color)

    def _themed_leave_event(self, event):
        if ThemeEngine.current_theme() == ThemeEngine.DEFAULT_THEME_NAME:
            if hasattr(self, "_mk_theme_original_methods"):
                return self._mk_theme_original_methods["leaveEvent"](event)
            return

        from PySide6.QtWidgets import QPushButton
        QPushButton.leaveEvent(self, event)
        self._update_label_styles()

    widget._update_label_styles = types.MethodType(_themed_update_label_styles, widget)
    widget.enterEvent = types.MethodType(_themed_enter_event, widget)
    widget.leaveEvent = types.MethodType(_themed_leave_event, widget)

    widget._update_label_styles()


def _apply_submenu(widget: QWidget, p: dict[str, str | int | bool]) -> None:
    if hasattr(widget, "title_btn"):
        _save_widget(widget.title_btn)
        item_height = getattr(widget, "_item_height", 50)
        widget.title_btn.setProperty("_mk_theme_fixed_height", item_height)
        widget.title_btn.setFixedHeight(item_height)
        widget.title_btn.setStyleSheet(f"""
            QPushButton {{
                border: none;
                background: transparent;
                padding: 0px;
                margin: 0px;
                min-height: {item_height}px;
                max-height: {item_height}px;
            }}
            QPushButton:hover {{
                background: transparent;
            }}
        """)
    normal_text_style = f"color: {p['text']}; font-size: 14px; font-weight: 800; font-family: {p['font']}; background: transparent; border: none;"
    normal_icon_style = f"color: {p['text']}; font-size: 16px; background: transparent; border: none;"
    hover_text_style = f"color: {p['primary']}; font-size: 14px; font-weight: 800; font-family: {p['font']}; background: transparent; border: none;"
    hover_icon_style = f"color: {p['primary']}; font-size: 16px; background: transparent; border: none;"

    if hasattr(widget, "text_label"):
        _style_label(widget.text_label, normal_text_style)
    if hasattr(widget, "icon_label"):
        _style_label(widget.icon_label, normal_icon_style)

    widget._mk_theme_submenu_normal_text_style = normal_text_style
    widget._mk_theme_submenu_normal_icon_style = normal_icon_style
    widget._mk_theme_submenu_hover_text_style = hover_text_style
    widget._mk_theme_submenu_hover_icon_style = hover_icon_style
    widget._mk_theme_submenu_primary = str(p["primary"])
    widget._mk_theme_submenu_text = str(p["text"])

    if not hasattr(widget, "_mk_theme_original_event_filter"):
        try:
            from monkeyqt.core.icons import MkPhosphorIcon, PHOSPHOR_ICONS
        except Exception:
            MkPhosphorIcon = None
            PHOSPHOR_ICONS = set()

        widget._mk_theme_original_event_filter = widget.eventFilter

        def _theme_submenu_event_filter(self, obj, event):
            if obj == getattr(self, "title_btn", None):
                if event.type() == event.Type.Enter:
                    if hasattr(self, "text_label"):
                        self.text_label.setStyleSheet(self._mk_theme_submenu_hover_text_style)
                    if hasattr(self, "icon_label"):
                        self.icon_label.setStyleSheet(self._mk_theme_submenu_hover_icon_style)
                    if MkPhosphorIcon is not None and getattr(self, "_icon_str", None) and self._icon_str in PHOSPHOR_ICONS:
                        self.icon_label.setPixmap(MkPhosphorIcon.get_pixmap(self._icon_str, self._mk_theme_submenu_primary, 18))
                    return False
                if event.type() == event.Type.Leave:
                    if hasattr(self, "text_label"):
                        self.text_label.setStyleSheet(self._mk_theme_submenu_normal_text_style)
                    if hasattr(self, "icon_label"):
                        self.icon_label.setStyleSheet(self._mk_theme_submenu_normal_icon_style)
                    if MkPhosphorIcon is not None and getattr(self, "_icon_str", None) and self._icon_str in PHOSPHOR_ICONS:
                        self.icon_label.setPixmap(MkPhosphorIcon.get_pixmap(self._icon_str, self._mk_theme_submenu_text, 18))
                    return False
            return self._mk_theme_original_event_filter(obj, event)

        widget.eventFilter = types.MethodType(_theme_submenu_event_filter, widget)


def _topbar_qss(p: dict[str, str | int | bool]) -> str:
    bg = p["primary"] if not p["dark"] else p["surface"]
    return f"""
        #mk-topbar {{
            background-color: {bg};
            border: {p['border_rule']};
            border-radius: {p['radius']};
        }}
    """


def _topbar_item_qss(p: dict[str, str | int | bool]) -> str:
    return f"""
        MkTopbarItem {{
            border: none;
            border-bottom: 2px solid transparent;
            background: transparent;
            color: {p['muted']};
            font-size: 14px;
            padding: 0 20px;
            font-family: {p['font']};
            font-weight: 700;
        }}
        MkTopbarItem:hover {{
            color: {p['primary_text']};
            background-color: rgba(255, 255, 255, 42);
        }}
        MkTopbarItem:checked {{
            color: {p['primary_text']};
            border-bottom: 2px solid {p['primary_text']};
        }}
    """


def _tab_button_qss(p: dict[str, str | int | bool]) -> str:
    return f"""
        MkTabButton {{
            border: none;
            border-bottom: 2px solid transparent;
            background: transparent;
            color: {p['text']};
            font-size: 14px;
            padding: 10px 20px;
            font-family: {p['font']};
            font-weight: 700;
        }}
        MkTabButton:hover {{
            color: {p['primary']};
        }}
        MkTabButton:checked {{
            color: {p['primary']};
            border-bottom: 2px solid {p['primary']};
        }}
    """


def _pagination_qss(p: dict[str, str | int | bool]) -> str:
    return """
        MkPagination {
            background: transparent;
            border: none;
        }
    """


def _pagination_button_qss(widget: QWidget, p: dict[str, str | int | bool]) -> str:
    active = str(widget.property("class") or "") == "active"
    radius = 0 if p["flat"] else min(6, _control_radius_px(p))
    background = str(p["primary"]) if active else "transparent"
    foreground = str(p["primary_text"]) if active else str(p["text"])
    border = str(p["primary"]) if active else "transparent"
    return f"""
        QPushButton {{
            border: 1px solid {border};
            background-color: {background};
            color: {foreground};
            min-width: 32px;
            min-height: 32px;
            border-radius: {radius}px;
            font-size: 13px;
            font-weight: 700;
            padding: 0 6px;
            outline: none;
        }}
        QPushButton:hover {{
            color: {p['primary']};
            background-color: {_soft_hover(p, str(p['surface_muted']))};
            border-color: transparent;
        }}
        QPushButton:disabled {{
            color: {p['muted']};
            background-color: transparent;
            border-color: transparent;
        }}
    """


def _pagination_label_qss(p: dict[str, str | int | bool]) -> str:
    return f"""
        QLabel {{
            color: {p['muted']};
            font-size: 13px;
            margin: 0 4px;
            background: transparent;
            border: none;
        }}
    """


def _pagination_input_qss(p: dict[str, str | int | bool]) -> str:
    radius = 0 if p["flat"] else min(6, _control_radius_px(p))
    return f"""
        QLineEdit {{
            background-color: {_control_surface(p)};
            border: 1px solid {_control_border(p)};
            border-radius: {radius}px;
            color: {p['text']};
            min-width: 40px;
            max-width: 40px;
            min-height: 28px;
            padding: 0 4px;
            selection-background-color: {p['primary']};
        }}
        QLineEdit:focus {{
            border-color: {p['primary']};
        }}
    """


def _breadcrumb_item_qss(widget: QWidget, p: dict[str, str | int | bool]) -> str:
    current = bool(getattr(widget, "is_current", False))
    color = p["text"] if current else p["muted"]
    weight = 700 if current else 600
    return f"""
        MkBreadcrumbItem {{
            border: none;
            background: transparent;
            color: {color};
            font-size: 14px;
            font-weight: {weight};
            padding: 0;
            font-family: {p['font']};
        }}
        MkBreadcrumbItem:hover {{
            color: {p['primary']};
        }}
    """


def _table_qss(p: dict[str, str | int | bool]) -> str:
    surface = _table_surface(p)
    header = _table_header_surface(p)
    rule = _table_rule(p)
    radius = _table_radius_px(p)
    selected = _table_selected_surface(p)
    return f"""
        QTableWidget {{
            border: {rule};
            border-radius: {radius}px;
            background-color: {surface};
            gridline-color: transparent;
            show-decoration-selected: 0;
            font-size: 13px;
            color: {p['text']};
            selection-background-color: {selected};
            selection-color: {p['text']};
            outline: none;
        }}
        QTableWidget::corner {{
            background-color: {header};
            border: none;
        }}
        QHeaderView::section {{
            background-color: {header};
            color: {p['text']};
            font-weight: 700;
            border: none;
            border-bottom: {rule};
            padding: 10px 8px;
        }}
        QTableWidget::item {{
            background-color: {surface};
            border-bottom: {rule};
            padding: 8px;
        }}
        QTableWidget::item:hover {{
            background-color: {_soft_hover(p, surface)};
        }}
        QTableWidget::item:selected {{
            background-color: {selected};
            color: {p['text']};
        }}
        QTableWidget::item:selected:active,
        QTableWidget::item:selected:!active {{
            background-color: {selected};
            color: {p['text']};
        }}
    """


def _data_table_qss(p: dict[str, str | int | bool]) -> str:
    return f"""
        MkDataTable, QFrame {{
            background-color: {p['panel']};
            color: {p['text']};
            border-color: {p['border']};
        }}
        QLabel {{
            color: {p['text']};
            background: transparent;
        }}
        QPushButton {{
            background-color: {p['surface']};
            color: {p['text']};
            border: {p['border_rule']};
            border-radius: {p['radius']};
            padding: 5px 10px;
        }}
        QPushButton:hover {{
            color: {p['primary']};
            border-color: {p['primary']};
        }}
        QLineEdit {{
            background-color: {p['surface']};
            color: {p['text']};
            border: {p['border_rule']};
            border-radius: {p['radius']};
            padding: 6px 10px;
        }}
        {_table_qss(p)}
    """


def _datatable_table_qss(p: dict[str, str | int | bool]) -> str:
    surface = _table_surface(p)
    rule = _table_rule(p)
    selected = _table_selected_surface(p)
    return f"""
        QTableWidget {{
            background-color: {surface};
            border: none;
            gridline-color: transparent;
            show-decoration-selected: 0;
            font-family: {p['font']};
            font-size: 13px;
            color: {p['text']};
            selection-background-color: {selected};
            selection-color: {p['text']};
            outline: none;
        }}
        QTableWidget::item {{
            background-color: {surface};
            color: {p['text']};
            border-bottom: {rule};
            padding: 12px 10px;
        }}
        QTableWidget::item:hover {{
            background-color: {_soft_hover(p, surface)};
        }}
        QTableWidget::item:selected {{
            background-color: {selected};
            color: {p['text']};
        }}
        QTableWidget::item:selected:active,
        QTableWidget::item:selected:!active {{
            background-color: {selected};
            color: {p['text']};
        }}
    """


def _datatable_header_qss(p: dict[str, str | int | bool]) -> str:
    surface = _table_header_surface(p)
    rule = _table_rule(p)
    return f"""
        QHeaderView {{
            background-color: {surface};
            color: {p['text']};
            border: none;
        }}
        QHeaderView::section {{
            background-color: {surface};
            color: {p['text']};
            font-weight: 700;
            font-size: 12px;
            border: none;
            border-bottom: {rule};
            padding: 10px 10px;
        }}
    """


def _datatable_card_qss(p: dict[str, str | int | bool]) -> str:
    border = "none" if p["glass"] or p["neumorphic"] else _table_rule(p)
    return f"""
        QFrame#TableCard {{
            background-color: {_table_surface(p)};
            border: {border};
            border-radius: {_table_radius_px(p)}px;
        }}
    """


def _table_action_button_qss(p: dict[str, str | int | bool]) -> str:
    return f"""
        QPushButton, QToolButton {{
            background-color: transparent;
            border: none;
            border-radius: {0 if p['flat'] else 4}px;
            color: {p['muted']};
            padding: 0px;
        }}
        QPushButton:hover, QToolButton:hover {{
            background-color: {_soft_hover(p, str(p['surface_muted']))};
            border: none;
            color: {p['primary']};
        }}
        QPushButton:pressed, QToolButton:pressed {{
            background-color: {_table_selected_surface(p)};
            border: none;
        }}
    """


def _auth_card_qss(p: dict[str, str | int | bool]) -> str:
    radius = 0 if p["flat"] else min(12, int(p["radius_px"]))
    border = "none" if p["glass"] or p["neumorphic"] else _table_rule(p)
    return f"""
        QFrame#AuthCard {{
            background-color: {_table_surface(p)};
            border: {border};
            border-radius: {radius}px;
            outline: none;
        }}
    """


def _solid_native_button_qss(p: dict[str, str | int | bool], bg: str) -> str:
    fg = readable_text(bg)
    radius = 0 if p["flat"] else min(6, _control_radius_px(p))
    return f"""
        QPushButton {{
            background-color: {bg};
            border: 1px solid {bg};
            border-radius: {radius}px;
            color: {fg};
            font-family: {p['font']};
            font-size: 13px;
            font-weight: 800;
            outline: none;
        }}
        QPushButton:hover {{
            background-color: {_soft_hover(p, bg)};
            border-color: {_soft_hover(p, bg)};
        }}
        QPushButton:pressed {{
            background-color: {_pressed(bg)};
        }}
    """


def _secondary_native_button_qss(p: dict[str, str | int | bool]) -> str:
    radius = 0 if p["flat"] else min(6, _control_radius_px(p))
    return f"""
        QPushButton {{
            background-color: {_control_surface(p)};
            border: 1px solid {_control_border(p)};
            border-radius: {radius}px;
            color: {p['text']};
            font-family: {p['font']};
            font-size: 12px;
            font-weight: 700;
            outline: none;
            padding: 4px 10px;
        }}
        QPushButton:hover {{
            background-color: {_soft_hover(p, str(p['surface_muted']))};
            border-color: {p['primary']};
            color: {p['primary']};
        }}
        QPushButton:pressed {{
            background-color: {_table_selected_surface(p)};
        }}
    """


def _icon_native_button_qss(p: dict[str, str | int | bool]) -> str:
    return f"""
        QPushButton {{
            background: transparent;
            border: none;
            border-radius: 4px;
            color: {p['muted']};
            outline: none;
            padding: 0px;
        }}
        QPushButton:hover {{
            background-color: {_soft_hover(p, str(p['surface_muted']))};
            border: none;
            color: {p['primary']};
        }}
    """


def _auth_button_qss(
    widget: QWidget,
    owner: QWidget,
    p: dict[str, str | int | bool],
) -> str:
    submit_buttons = {
        getattr(owner, "login_submit_btn", None),
        getattr(owner, "reg_submit_btn", None),
    }
    if widget in submit_buttons:
        return _solid_native_button_qss(p, str(p["primary"]))
    if widget is getattr(owner, "forgot_pwd_btn", None):
        return _link_button_qss(p)
    if _ancestor(widget, "MkInput") is not None:
        return _icon_native_button_qss(p)
    if _ancestor(widget, "MkSmsCodeWidget") is not None:
        return _secondary_native_button_qss(p)
    form_stack = getattr(owner, "form_stack", None)
    if _is_descendant_of(widget, form_stack):
        return _link_button_qss(p)
    return _secondary_native_button_qss(p)


def _link_button_qss(p: dict[str, str | int | bool]) -> str:
    return f"""
        QPushButton {{
            background: transparent;
            border: none;
            color: {p['primary']};
            font-size: 12px;
            text-align: left;
            outline: none;
            padding: 0px;
        }}
        QPushButton:hover {{
            color: {_soft_hover(p, p['primary'])};
            text-decoration: underline;
        }}
    """


def _menu_qss(p: dict[str, str | int | bool]) -> str:
    return f"""
        QMenu {{
            background-color: {p['surface']};
            color: {p['text']};
            border: {p['border_rule']};
            border-radius: {p['radius']};
            padding: 5px;
        }}
        QMenu::item {{
            padding: 8px 20px;
            font-size: 13px;
            color: {p['text']};
            border-radius: {p['radius']};
        }}
        QMenu::item:selected {{
            background-color: {p['primary']};
            color: {p['primary_text']};
        }}
        QMenu::separator {{
            height: {p['border_width']};
            background: {p['border']};
            margin: 5px 8px;
        }}
    """


def _scroll_qss(p: dict[str, str | int | bool], *, vertical: bool = False, horizontal: bool = False) -> str:
    vertical_part = f"""
        QScrollBar:vertical {{
            background: transparent;
            width: 8px;
            margin: 2px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical {{
            background: {p['muted']};
            min-height: 20px;
            border-radius: 4px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: transparent;
            border: none;
            height: 0px;
        }}
    """ if vertical else ""
    horizontal_part = f"""
        QScrollBar:horizontal {{
            background: transparent;
            height: 7px;
            margin: 0px;
            border-radius: 3px;
        }}
        QScrollBar::handle:horizontal {{
            background: {p['muted']};
            min-width: 15px;
            border-radius: 3px;
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            background: transparent;
            border: none;
            width: 0px;
        }}
    """ if horizontal else ""
    return f"""
        QScrollArea {{
            background: transparent;
            border: none;
        }}
        {vertical_part}
        {horizontal_part}
    """


def _apply_panel(widget: QWidget, p: dict[str, str | int | bool]) -> None:
    widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    widget.setStyleSheet(f"""
        {widget.__class__.__name__} {{
            background-color: {p['panel']};
            color: {p['text']};
            border: {p['border_rule']};
            border-radius: {p['radius']};
        }}
        QLabel {{
            color: {p['text']};
            background: transparent;
        }}
        QPushButton {{
            background-color: {p['surface']};
            color: {p['text']};
            border: {p['border_rule']};
            border-radius: {p['radius']};
            padding: 6px 12px;
        }}
        QPushButton:hover {{
            border-color: {p['primary']};
            color: {p['primary']};
        }}
    """)


def _style_label(label: QLabel, qss: str) -> None:
    _save_widget(label)
    label.setStyleSheet(qss)


def _soft_hover(p: dict[str, str | int | bool], color: str) -> str:
    if p["glass"]:
        if str(color).startswith("#"):
            return lighten(color, 0.10) if p["dark"] else darken(color, 0.08)
        return _control_muted_surface(p)
    if p["dark"] or p["glow"]:
        return lighten(color, 0.10) if str(color).startswith("#") else p["surface_muted"]
    return lighten(color, 0.14) if str(color).startswith("#") else p["surface_muted"]


def _pressed(color: str) -> str:
    return darken(color, 0.10) if str(color).startswith("#") else color


def _tint(color: str, amount: float, fallback: str) -> str:
    if str(color).startswith("#"):
        return lighten(color, amount)
    return fallback


def _apply_date_picker_theme(p: dict[str, str | int | bool]) -> None:
    global _DATE_THEME_ORIGINALS
    try:
        from monkeyqt.components.form import date_picker
    except Exception:
        return

    theme = date_picker.Theme
    if _DATE_THEME_ORIGINALS is None:
        _DATE_THEME_ORIGINALS = {
            "BG_COLOR": theme.BG_COLOR,
            "TEXT_PRIMARY": theme.TEXT_PRIMARY,
            "TEXT_SECONDARY": theme.TEXT_SECONDARY,
            "ACCENT_COLOR": theme.ACCENT_COLOR,
            "ACCENT_HOVER": theme.ACCENT_HOVER,
            "HOVER_BG": theme.HOVER_BG,
            "BORDER_COLOR": theme.BORDER_COLOR,
        }
    theme.BG_COLOR = str(p["surface"])
    theme.TEXT_PRIMARY = str(p["text"])
    theme.TEXT_SECONDARY = str(p["muted"])
    theme.ACCENT_COLOR = str(p["primary"])
    theme.ACCENT_HOVER = _soft_hover(p, str(p["primary"]))
    theme.HOVER_BG = str(p["surface_muted"])
    theme.BORDER_COLOR = str(p["border"])


def _restore_date_picker_theme() -> None:
    global _DATE_THEME_ORIGINALS
    if _DATE_THEME_ORIGINALS is None:
        return
    try:
        from monkeyqt.components.form import date_picker
    except Exception:
        return
    for key, value in _DATE_THEME_ORIGINALS.items():
        setattr(date_picker.Theme, key, value)

# -*- coding: utf-8 -*-
"""
@File ：multicombobox.py
@Desc ：Modern web-style multi-select combobox (checklist popup) component for PySide6.
"""
import time
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QScrollArea, QWidget, QLabel
from PySide6.QtCore import Qt, Signal, QPoint, QEvent
from PySide6.QtGui import QPainter, QPen, QColor
from monkeyqt import MkCheckBox

class MkMultiComboItem(QWidget):
    """Container widget representing a single item in the checklist dropdown."""
    def __init__(self, checkbox, parent=None):
        super().__init__(parent)
        self.checkbox = checkbox
        self.checkbox.setParent(self)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(8)
        layout.addWidget(self.checkbox)
        
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border-radius: 4px;
            }
            QWidget:hover {
                background-color: #f1f5f9;
            }
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.checkbox.toggle()
            event.accept()
        else:
            super().mousePressEvent(event)

class MkMultiComboPopup(QFrame):
    """Dropdown list panel appearing below MkMultiComboBox with a checklist."""
    def __init__(self, parent_combo):
        super().__init__(None, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.parent_combo = parent_combo
        
        self.setObjectName("popup_frame")
        self.setStyleSheet("""
            QFrame#popup_frame {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Scroll Area
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: #f1f5f9;
                width: 10px;
                margin: 4px 2px 4px 2px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #cbd5e1;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #94a3b8;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
                border: none;
                height: 0px;
            }
        """)
        
        self.scroll_widget = QWidget(self.scroll_area)
        self.scroll_widget.setObjectName("scroll_widget")
        self.scroll_widget.setStyleSheet("QWidget#scroll_widget { background: transparent; }")
        
        self.list_layout = QVBoxLayout(self.scroll_widget)
        self.list_layout.setContentsMargins(2, 2, 2, 2)
        self.list_layout.setSpacing(2)
        self.list_layout.addStretch() # Push items to top
        
        self.scroll_area.setWidget(self.scroll_widget)
        layout.addWidget(self.scroll_area)
        
        self.items = []
        
    def add_item(self, text, data):
        chk = MkCheckBox(text, self.scroll_widget)
        chk.mk_size = "small"
        
        item_widget = MkMultiComboItem(chk, self.scroll_widget)
        # Insert before stretch item
        self.list_layout.insertWidget(self.list_layout.count() - 1, item_widget)
        
        self.items.append((data, text, chk, item_widget))
        chk.stateChanged.connect(self.parent_combo._on_item_state_changed)
        
    def clear(self):
        for data, text, chk, item_widget in self.items:
            self.list_layout.removeWidget(item_widget)
            item_widget.deleteLater()
        self.items.clear()
        
    def show_popup(self):
        if not self.items:
            return
            
        w = self.parent_combo.width()
        item_count = len(self.items)
        # Calculate visual height with a reasonable maximum height (220px)
        h = min(220, item_count * 28 + 12)
        
        pos = self.parent_combo.mapToGlobal(QPoint(0, self.parent_combo.height()))
        self.setGeometry(pos.x(), pos.y() + 2, w, h)
        self.show()
        self.raise_()
        
    def hideEvent(self, event):
        self.parent_combo._last_close_time = time.time()
        self.parent_combo.setProperty("focused", "false")
        self.parent_combo.style().unpolish(self.parent_combo)
        self.parent_combo.style().polish(self.parent_combo)
        super().hideEvent(event)

class MkMultiComboBox(QFrame):
    """
    MkMultiComboBox - Element Plus styled multi-select dropdown.
    Displays selected options in a horizontal scroll area face, showing checklist popover on click.
    """
    selectionChanged = Signal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("combo_frame")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        
        self._last_close_time = 0
        self.setProperty("focused", "false")
        
        # Main Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 2, 28, 2) # Extra right padding for chevron arrow
        layout.setSpacing(0)
        
        # Scroll Area for the selected text labels
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Beautified horizontal scrollbar style
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:horizontal {
                background: #f1f5f9;
                height: 6px;
                margin: 0px;
                border-radius: 3px;
            }
            QScrollBar::handle:horizontal {
                background: #cbd5e1;
                min-width: 15px;
                border-radius: 3px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #94a3b8;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                background: none;
                border: none;
                width: 0px;
            }
        """)
        
        # Content label for text display
        self.text_label = QLabel(self.scroll_area)
        self.text_label.setObjectName("text_label")
        self.text_label.setWordWrap(False)
        self.text_label.setStyleSheet("""
            QLabel#text_label {
                color: #94a3b8;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                font-size: 13px;
                background: transparent;
                border: none;
            }
        """)
        self.text_label.setText("默认检测所有类别")
        
        self.scroll_area.setWidget(self.text_label)
        layout.addWidget(self.scroll_area)
        
        # Setup popup
        self.popup = MkMultiComboPopup(self)
        
        # QFrame Stylesheet matching Element Plus Select border colors
        self.setStyleSheet("""
            QFrame#combo_frame {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                min-height: 32px;
                max-height: 32px;
            }
            QFrame#combo_frame:hover {
                border-color: #cbd5e1;
            }
            QFrame#combo_frame[focused="true"] {
                border-color: #3b82f6;
            }
        """)
        
        # Install event filters to handle clicks on child components
        self.scroll_area.installEventFilter(self)
        self.scroll_area.viewport().installEventFilter(self)
        self.text_label.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                self._handle_click()
                return True
        return super().eventFilter(obj, event)

    def _handle_click(self):
        # Debounce popup reopen clicks
        now = time.time()
        if now - self._last_close_time < 0.15:
            return
            
        self.setProperty("focused", "true")
        self.style().unpolish(self)
        self.style().polish(self)
        
        self.popup.show_popup()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._handle_click()
        else:
            super().mousePressEvent(event)

    def addItem(self, text, data=None):
        if data is None:
            data = text
        self.popup.add_item(text, data)
        self._update_text()

    def addItems(self, items):
        if isinstance(items, dict):
            for data, text in sorted(items.items()):
                self.addItem(f"{data}: {text}", data)
        elif isinstance(items, list):
            for item in items:
                if isinstance(item, tuple) and len(item) == 2:
                    self.addItem(item[0], item[1])
                else:
                    self.addItem(str(item), item)
        self._update_text()

    def clear(self):
        self.popup.clear()
        self._update_text()

    def get_checked_data(self):
        return [data for data, text, chk, item_widget in self.popup.items if chk.isChecked()]

    def get_checked_texts(self):
        return [text for data, text, chk, item_widget in self.popup.items if chk.isChecked()]

    def setCheckedData(self, datas):
        for data, text, chk, item_widget in self.popup.items:
            chk.blockSignals(True)
            chk.setChecked(data in datas)
            chk.blockSignals(False)
        self._update_text()
        self.selectionChanged.emit(self.get_checked_data())

    def clear_checked(self):
        for data, text, chk, item_widget in self.popup.items:
            chk.blockSignals(True)
            chk.setChecked(False)
            chk.blockSignals(False)
        self._update_text()
        self.selectionChanged.emit([])

    def _on_item_state_changed(self):
        self._update_text()
        self.selectionChanged.emit(self.get_checked_data())

    def _update_text(self):
        checked_texts = self.get_checked_texts()
        if checked_texts:
            full_text = ", ".join(checked_texts)
            self.text_label.setText(full_text)
            self.text_label.setStyleSheet("""
                QLabel#text_label {
                    color: #0f172a;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                    font-size: 13px;
                    background: transparent;
                    border: none;
                }
            """)
            self.text_label.adjustSize()
        else:
            self.text_label.setText("默认检测所有类别")
            self.text_label.setStyleSheet("""
                QLabel#text_label {
                    color: #94a3b8;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                    font-size: 13px;
                    background: transparent;
                    border: none;
                }
            """)

    def paintEvent(self, event):
        super().paintEvent(event)
        
        # Draw custom chevron-down arrow icon on the right
        from PySide6.QtGui import QPainter, QPen, QColor
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        r = self.rect()
        arrow_w = 8
        arrow_h = 4
        x = r.width() - 18
        y = (r.height() - arrow_h) // 2
        
        pen = QPen(QColor("#64748b"), 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        
        painter.drawLine(x, y, x + arrow_w // 2, y + arrow_h)
        painter.drawLine(x + arrow_w // 2, y + arrow_h, x + arrow_w, y)
        painter.end()

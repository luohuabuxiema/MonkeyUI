# -*- coding: utf-8 -*-
"""
@File ：combobox.py
@Desc ：Modern web-style (Element Plus / shadcn-ui) dropdown select component for PySide6.
"""
from PySide6.QtWidgets import QComboBox, QListView, QFrame
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor

class MkComboBox(QComboBox):
    """
    MkComboBox - Modern Web-style Select Dropdown.
    Subclasses QComboBox and customizes styling, dropdown menu, and scrollbars.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        # Use QListView for popup view to ensure QSS applies correctly to list items
        list_view = QListView(self)
        list_view.setFrameShape(QFrame.Shape.NoFrame)
        list_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        list_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setView(list_view)
        
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Embedded chevron-down icon base64 SVG (color: #64748b)
        svg_base64 = "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNTYgMjU2Ij48cGF0aCBmaWxsPSJub25lIiBzdHJva2U9IiM2NDc0OGIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIgc3Ryb2tlLXdpZHRoPSIyNCIgZD0ibTIwOCA5Ni04MCA4MC04MC04MCIvPjwvc3ZnPg=="
        
        self.setStyleSheet(f"""
            QComboBox {{
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 6px 36px 6px 12px;
                color: #0f172a;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                font-size: 13px;
                min-height: 24px;
            }}
            QComboBox:hover {{
                border-color: #cbd5e1;
            }}
            QComboBox:focus, QComboBox:on {{
                border-color: #3b82f6;
                background-color: #ffffff;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 28px;
                border-left: none;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
            }}
            QComboBox::down-arrow {{
                image: url(data:image/svg+xml;base64,{svg_base64});
                width: 14px;
                height: 14px;
            }}
            QComboBox:disabled {{
                background-color: #f1f5f9;
                color: #94a3b8;
                border-color: #e2e8f0;
            }}
            
            /* Dropdown popup style */
            QComboBox QAbstractItemView {{
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                outline: none;
                padding: 4px;
            }}
            QComboBox QAbstractItemView::item {{
                min-height: 32px;
                padding-left: 10px;
                border-radius: 4px;
                color: #334155;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                font-size: 13px;
            }}
            QComboBox QAbstractItemView::item:hover {{
                background-color: #f1f5f9;
                color: #0f172a;
            }}
            QComboBox QAbstractItemView::item:selected {{
                background-color: #eff6ff;
                color: #2563eb;
                font-weight: 500;
            }}
            
            /* Custom thin scrollbar */
            QComboBox QAbstractItemView QScrollBar:vertical {{
                background: transparent;
                width: 6px;
                margin: 4px 2px 4px 2px;
            }}
            QComboBox QAbstractItemView QScrollBar::handle:vertical {{
                background: #cbd5e1;
                min-height: 20px;
                border-radius: 3px;
            }}
            QComboBox QAbstractItemView QScrollBar::handle:vertical:hover {{
                background: #94a3b8;
            }}
            QComboBox QAbstractItemView QScrollBar::add-line:vertical,
            QComboBox QAbstractItemView QScrollBar::sub-line:vertical {{
                background: none;
                border: none;
                height: 0px;
            }}
        """)

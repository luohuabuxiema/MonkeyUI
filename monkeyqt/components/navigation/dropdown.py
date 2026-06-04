import os
from PySide6.QtWidgets import QPushButton, QMenu, QWidget, QVBoxLayout
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor

class MkDropdown(QPushButton):
    """
    下拉菜单 (Dropdown)
    提供点击触发下拉列表的功能。
    """
    itemClicked = Signal(str)

    def __init__(self, text="Dropdown", parent=None):
        super().__init__(text, parent)
        self._setup_ui()

    def _setup_ui(self):
        self.setCursor(Qt.PointingHandCursor)
        self.menu = QMenu(self)
        
        # We handle showing the menu manually on click for better alignment/styling if needed
        # Or we can just use the built-in setMenu.
        self.setMenu(self.menu)

        self.setStyleSheet("""
            MkDropdown {
                color: #606266;
                background-color: #ffffff;
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 8px 15px;
                font-size: 14px;
            }
            MkDropdown:hover {
                color: #00a896;
                border-color: #00a896;
                background-color: #e6f6f4;
            }
            MkDropdown::menu-indicator {
                image: none; /* Hide the default arrow */
            }
        """)

        self.menu.setStyleSheet("""
            QMenu {
                background-color: #ffffff;
                border: 1px solid #e4e7ed;
                border-radius: 4px;
                padding: 5px 0;
            }
            QMenu::item {
                padding: 8px 20px;
                font-size: 14px;
                color: #606266;
            }
            QMenu::item:selected {
                background-color: #f5f7fa;
                color: #00a896;
            }
        """)

    def add_item(self, text, item_id=""):
        if not item_id:
            item_id = text
        action = self.menu.addAction(text)
        action.setData(item_id)
        action.triggered.connect(lambda checked=False, i=item_id: self.itemClicked.emit(i))
        return action

    def add_separator(self):
        self.menu.addSeparator()

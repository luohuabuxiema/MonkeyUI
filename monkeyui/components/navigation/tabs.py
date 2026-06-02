from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget, QButtonGroup
from PySide6.QtCore import Qt, Signal

class MkTabButton(QPushButton):
    """标签页的单个标签按钮"""
    def __init__(self, tab_id, title, parent=None):
        super().__init__(title, parent)
        self.tab_id = tab_id
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            MkTabButton {
                border: none;
                border-bottom: 2px solid transparent;
                background: transparent;
                color: #303133;
                font-size: 14px;
                padding: 10px 20px;
                font-family: "Helvetica Neue", Helvetica, "PingFang SC", "Microsoft YaHei", Arial, sans-serif;
            }
            MkTabButton:hover {
                color: #409eff;
            }
            MkTabButton:checked {
                color: #409eff;
                border-bottom: 2px solid #409eff;
            }
        """)

class MkTabs(QWidget):
    """
    MkTabs 标签页组件
    用于平级区域大块内容的的收纳和展现。
    """
    tabChanged = Signal(str) # 切换标签时发射 tab_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(15)

        # 1. 顶部的标签头区域
        self.header_widget = QWidget()
        self.header_widget.setStyleSheet("""
            QWidget {
                border-bottom: 1px solid #e4e7ed;
            }
        """)
        self.header_layout = QHBoxLayout(self.header_widget)
        self.header_layout.setContentsMargins(0, 0, 0, 0)
        self.header_layout.setSpacing(0)
        self.header_layout.addStretch() # 靠左对齐

        self._layout.addWidget(self.header_widget)

        # 管理标签按钮的互斥
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        self.button_group.buttonClicked.connect(self._on_tab_clicked)

        # 2. 下方的内容区域
        self.content_area = QStackedWidget()
        self._layout.addWidget(self.content_area, stretch=1)

        self._tabs = {} # tab_id -> widget

    def add_tab(self, tab_id: str, title: str, widget: QWidget):
        """添加一个新标签页"""
        # 添加头部按钮
        btn = MkTabButton(tab_id, title)
        self.button_group.addButton(btn)
        self.header_layout.insertWidget(self.header_layout.count() - 1, btn)

        # 添加内容
        self.content_area.addWidget(widget)
        self._tabs[tab_id] = widget

        # 如果是第一个标签，默认选中
        if len(self._tabs) == 1:
            btn.setChecked(True)
            self.content_area.setCurrentWidget(widget)

    def _on_tab_clicked(self, btn):
        tab_id = btn.tab_id
        widget = self._tabs.get(tab_id)
        if widget:
            self.content_area.setCurrentWidget(widget)
            self.tabChanged.emit(tab_id)

    def set_active(self, tab_id: str):
        """代码切换标签"""
        for btn in self.button_group.buttons():
            if btn.tab_id == tab_id:
                btn.setChecked(True)
                self._on_tab_clicked(btn)
                break

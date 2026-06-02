from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal

class MkBreadcrumbItem(QPushButton):
    """面包屑节点"""
    def __init__(self, text, is_current=False, parent=None):
        super().__init__(text, parent)
        self.is_current = is_current
        self.setCursor(Qt.CursorShape.PointingHandCursor if not is_current else Qt.CursorShape.ArrowCursor)
        self._apply_style()

    def _apply_style(self):
        if self.is_current:
            # 当前页，灰色且不可点击
            self.setStyleSheet("""
                MkBreadcrumbItem {
                    border: none;
                    background: transparent;
                    color: #606266; /* 深灰 */
                    font-size: 14px;
                    font-weight: 500;
                    padding: 0;
                    font-family: "Helvetica Neue", Helvetica, "PingFang SC", "Microsoft YaHei", Arial, sans-serif;
                }
            """)
        else:
            # 祖先节点，可点击，Hover时变蓝
            self.setStyleSheet("""
                MkBreadcrumbItem {
                    border: none;
                    background: transparent;
                    color: #909399; /* 浅灰 */
                    font-size: 14px;
                    font-weight: bold;
                    padding: 0;
                    font-family: "Helvetica Neue", Helvetica, "PingFang SC", "Microsoft YaHei", Arial, sans-serif;
                }
                MkBreadcrumbItem:hover {
                    color: #409eff;
                }
            """)

class MkBreadcrumb(QWidget):
    """
    MkBreadcrumb 面包屑组件
    显示当前页面的路径，快速返回之前的任意页面。
    """
    itemClicked = Signal(str)

    def __init__(self, separator="/", parent=None):
        super().__init__(parent)
        self.separator_text = separator
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(8)
        self.layout.addStretch() # 靠左对齐

        self._items_data = []

    def set_items(self, items: list):
        """
        批量设置面包屑项
        items 格式: [{"id": "home", "text": "首页"}, {"id": "user", "text": "用户管理"}]
        最后一个项会自动变为当前项。
        """
        # 清空之前的
        while self.layout.count() > 1: # 留下 stretch
            item = self.layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        self._items_data = items
        total = len(items)

        for i, data in enumerate(items):
            is_current = (i == total - 1)
            
            # 添加节点按钮
            btn = MkBreadcrumbItem(data["text"], is_current=is_current)
            if not is_current:
                btn.clicked.connect(lambda checked=False, d=data: self.itemClicked.emit(d["id"]))
            self.layout.insertWidget(self.layout.count() - 1, btn)

            # 添加分隔符 (除了最后一个)
            if not is_current:
                sep_label = QLabel(self.separator_text)
                sep_label.setStyleSheet("""
                    QLabel {
                        color: #c0c4cc;
                        font-weight: bold;
                        font-size: 14px;
                    }
                """)
                self.layout.insertWidget(self.layout.count() - 1, sep_label)

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QButtonGroup, QSizePolicy, QWidget
from PySide6.QtCore import Qt, Signal

class MkTopbarItem(QPushButton):
    """顶部导航栏菜单项"""
    def __init__(self, item_id, text, parent=None):
        super().__init__(text, parent)
        self.item_id = item_id
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 允许按钮在垂直方向上充满父容器，这样底部边框才会贴紧底边
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.setMinimumWidth(80) # 保证每个菜单项有足够的宽度
        
        self.setStyleSheet("""
            MkTopbarItem {
                border: none;
                border-bottom: 2px solid transparent; /* 预留底部边框空间 */
                background: transparent;
                color: #909399; /* 浅灰色，未选中状态 */
                font-size: 14px;
                padding: 0 20px;
                font-family: "Helvetica Neue", Helvetica, "PingFang SC", "Microsoft YaHei", Arial, sans-serif;
            }
            MkTopbarItem:hover {
                color: #ffffff;
                background-color: rgba(255, 255, 255, 0.05); /* 轻微的高亮背景 */
            }
            MkTopbarItem:checked {
                color: #ffffff;
                border-bottom: 2px solid #a0cfff; /* 底部高亮蓝条，模拟图片中的效果 */
            }
        """)

class MkTopbar(QFrame):
    """
    MkTopbar 顶部导航栏组件
    适用于全站的主导航，默认带有深色背景和左侧 LOGO。
    """
    itemClicked = Signal(str)

    def __init__(self, logo_text="LOGO", parent=None):
        super().__init__(parent)
        self.setObjectName("mk-topbar")
        
        # 锁定导航栏高度，这在桌面端非常常见
        self.setFixedHeight(60)
        
        # 深色主题背景
        self.setStyleSheet("""
            #mk-topbar {
                background-color: #334155; /* Element 风格的深色石板灰 */
                border: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
        """)

        # 主布局，横向排列
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(20, 0, 20, 0) # 上下边距为0，让 Item 占满高度
        self.layout.setSpacing(10)

        # 1. 左侧 LOGO
        if logo_text:
            self.logo_label = QLabel(logo_text)
            self.logo_label.setStyleSheet("""
                QLabel {
                    color: #ffffff;
                    font-size: 20px;
                    font-weight: bold;
                    letter-spacing: 2px;
                    font-family: "Helvetica Neue", Helvetica, "PingFang SC", "Microsoft YaHei", Arial, sans-serif;
                    padding-right: 30px; /* 和右边菜单拉开距离 */
                }
            """)
            self.layout.addWidget(self.logo_label)

        # 2. 管理所有菜单项的互斥逻辑
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        self.button_group.buttonClicked.connect(self._on_button_clicked)

        # 3. 菜单项容器
        # 这里专门套一层 Layout，不使用主 layout 的 stretch，防止菜单项被过度拉伸
        self.items_layout = QHBoxLayout()
        self.items_layout.setContentsMargins(0, 0, 0, 0)
        self.items_layout.setSpacing(0) # 菜单项之间无缝衔接
        self.layout.addLayout(self.items_layout)

        # 4. 右侧添加弹簧，将所有菜单项向左推
        self.layout.addStretch()

    def add_item(self, item_id: str, text: str) -> MkTopbarItem:
        """动态向导航栏添加一级菜单"""
        btn = MkTopbarItem(item_id, text)
        self.button_group.addButton(btn)
        self.items_layout.addWidget(btn)
        return btn

    def _on_button_clicked(self, btn):
        self.itemClicked.emit(btn.item_id)
        
    def set_active(self, item_id: str):
        """手动设置某个项为高亮状态"""
        for btn in self.button_group.buttons():
            if btn.item_id == item_id:
                btn.setChecked(True)
                break

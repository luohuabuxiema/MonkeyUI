from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QScrollArea, QFrame, QSizePolicy
from PySide6.QtCore import Qt, Signal, Property, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QIcon, QPainter, QColor
from monkeyui.core.icons import MkPhosphorIcon, PHOSPHOR_ICONS

class MkMenuItem(QPushButton):
    """最底层的菜单项"""
    def __init__(self, item_id, text, icon=None, height=50, parent=None):
        super().__init__(parent) # Do not pass text here, we use labels
        self.item_id = item_id
        self._original_text = text
        self._icon_str = icon
        self._item_height = height
        self.setFixedHeight(self._item_height) # 设置前端标准高度
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(20, 0, 20, 0)
        self._layout.setSpacing(20) # Text starts at 20 + 24 + 20 = 64
        
        self.icon_label = QLabel()
        self.icon_label.setFixedWidth(24)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        if self._icon_str:
            if self._icon_str in PHOSPHOR_ICONS:
                self.icon_label.setPixmap(MkPhosphorIcon.get_pixmap(self._icon_str, "#606266", 18))
            else:
                self.icon_label.setText(self._icon_str)
        
        self.text_label = QLabel(self._original_text)
        self.text_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        
        self._layout.addWidget(self.icon_label)
        self._layout.addWidget(self.text_label)
        self._layout.addStretch()
        
        self._base_style = """
            MkMenuItem {
                border: none;
                background: transparent;
                padding: 0px;
                margin: 0px;
            }
            MkMenuItem:hover {
                background-color: transparent;
            }
            MkMenuItem:checked {
                background-color: transparent;
            }
        """
        
        self._label_style = """
            QLabel {
                color: #606266;
                font-size: 14px;
                font-family: "Helvetica Neue", Helvetica, "PingFang SC", "Microsoft YaHei", Arial, sans-serif;
                border: none;
                background: transparent;
            }
        """
        self._label_checked_style = """
            QLabel {
                color: #409eff;
                font-size: 14px;
                font-weight: bold;
                font-family: "Helvetica Neue", Helvetica, "PingFang SC", "Microsoft YaHei", Arial, sans-serif;
                border: none;
                background: transparent;
            }
        """
        self._label_hover_style = """
            QLabel {
                color: #409eff;
                font-size: 14px;
                font-family: "Helvetica Neue", Helvetica, "PingFang SC", "Microsoft YaHei", Arial, sans-serif;
                border: none;
                background: transparent;
            }
        """
        
        self.setStyleSheet(self._base_style)
        self._update_label_styles()
        self.toggled.connect(self._on_toggled)

    def _on_toggled(self, checked):
        self._update_label_styles()

    def _update_icon_color(self, color_hex):
        if self._icon_str and self._icon_str in PHOSPHOR_ICONS:
            self.icon_label.setPixmap(MkPhosphorIcon.get_pixmap(self._icon_str, color_hex, 18))

    def enterEvent(self, event):
        super().enterEvent(event)
        if not self.isChecked():
            self.icon_label.setStyleSheet(self._label_hover_style)
            self.text_label.setStyleSheet(self._label_hover_style)
            self._update_icon_color("#409eff")

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self._update_label_styles()

    def _update_label_styles(self):
        if self.isChecked():
            self.icon_label.setStyleSheet(self._label_checked_style)
            self.text_label.setStyleSheet(self._label_checked_style)
            self._update_icon_color("#409eff")
        else:
            self.icon_label.setStyleSheet(self._label_style)
            self.text_label.setStyleSheet(self._label_style)
            self._update_icon_color("#606266")

    def set_collapsed(self, is_collapsed):
        if is_collapsed:
            self.text_label.hide()
            self.setToolTip(self._original_text)
            self._layout.setContentsMargins(20, 0, 20, 0)
            self.icon_label.setAlignment(Qt.AlignCenter)
        else:
            self.text_label.show()
            self.setToolTip("")
            # Submenu items might need more left margin, we can handle that by setting margins externally
            self._layout.setContentsMargins(self._current_left_margin, 0, 20, 0)

    @property
    def _current_left_margin(self):
        return getattr(self, '_left_margin_val', 20)

    def set_left_margin(self, margin):
        self._left_margin_val = margin
        if not self.text_label.isHidden(): # meaning not collapsed
            self._layout.setContentsMargins(margin, 0, 20, 0)

class MkSubMenu(QWidget):
    """带折叠功能的子菜单容器"""
    toggled = Signal(bool)

    def __init__(self, title, icon=None, height=50, parent=None):
        super().__init__(parent)
        self._original_title = title
        self._icon_str = icon
        self._is_expanded = False
        self._item_height = height
        self._items = [] # 存储子项
        
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        # 标题按钮（使用与 MkMenuItem 类似的布局以保证对齐）
        self.title_btn = QPushButton()
        self.title_btn.setFixedHeight(self._item_height) # 设置前端标准高度
        self.title_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.title_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                padding: 0px;
                margin: 0px;
            }
            QPushButton:hover {
                background-color: transparent;
            }
        """)
        
        self.title_layout = QHBoxLayout(self.title_btn)
        self.title_layout.setContentsMargins(20, 0, 20, 0)
        self.title_layout.setSpacing(20) # 保证文字在 64px 处开始
        
        self.icon_label = QLabel()
        self.icon_label.setFixedWidth(24)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.icon_label.setStyleSheet("color: #303133; font-size: 16px;")
        if self._icon_str:
            if self._icon_str in PHOSPHOR_ICONS:
                self.icon_label.setPixmap(MkPhosphorIcon.get_pixmap(self._icon_str, "#303133", 18))
            else:
                self.icon_label.setText(self._icon_str)
        
        self.text_label = QLabel(self._original_title)
        self.text_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.text_label.setStyleSheet("color: #303133; font-size: 14px; font-weight: bold;")
        
        self.title_layout.addWidget(self.icon_label)
        self.title_layout.addWidget(self.text_label)
        self.title_layout.addStretch()

        self.title_btn.clicked.connect(self.toggle)
        
        # 为了实现悬浮变色，需要重写 enterEvent 和 leaveEvent 或使用事件过滤器
        self.title_btn.installEventFilter(self)
        
        self._layout.addWidget(self.title_btn)

        # 子菜单容器
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        
        # 初始状态隐藏
        self.content_widget.setVisible(False)
        self._layout.addWidget(self.content_widget)

    def eventFilter(self, obj, event):
        if obj == self.title_btn:
            if event.type() == event.Type.Enter:
                self.text_label.setStyleSheet("color: #409eff; font-size: 14px; font-weight: bold;")
                self.icon_label.setStyleSheet("color: #409eff; font-size: 16px;")
                if self._icon_str and self._icon_str in PHOSPHOR_ICONS:
                    self.icon_label.setPixmap(MkPhosphorIcon.get_pixmap(self._icon_str, "#409eff", 18))
            elif event.type() == event.Type.Leave:
                self.text_label.setStyleSheet("color: #303133; font-size: 14px; font-weight: bold;")
                self.icon_label.setStyleSheet("color: #303133; font-size: 16px;")
                if self._icon_str and self._icon_str in PHOSPHOR_ICONS:
                    self.icon_label.setPixmap(MkPhosphorIcon.get_pixmap(self._icon_str, "#303133", 18))
        return super().eventFilter(obj, event)

    def add_item(self, item: MkMenuItem):
        self._items.append(item)
        self.content_layout.addWidget(item)

    def toggle(self):
        # 折叠模式下，暂不支持展开子菜单
        self._is_expanded = not self._is_expanded
        self.content_widget.setVisible(self._is_expanded)
        self.toggled.emit(self._is_expanded)

    def set_collapsed(self, is_collapsed):
        if is_collapsed:
            self.text_label.hide()
            self.title_btn.setToolTip(self._original_title)
            self.content_widget.setVisible(False) # 强制收起子项
            self.title_layout.setContentsMargins(20, 0, 20, 0)
        else:
            self.text_label.show()
            self.title_btn.setToolTip("")
            self.content_widget.setVisible(self._is_expanded) # 恢复原来的展开状态
            self.title_layout.setContentsMargins(20, 0, 20, 0)
        
        for item in self._items:
            item.set_collapsed(is_collapsed)

class MkMenu(QWidget):
    """
    Element Plus 风格的侧边栏 (ElMenu)
    支持多级折叠 (SubMenu)、菜单项 (MenuItem) 和顶部标题区，
    支持悬浮折叠按钮或汉堡包按钮收缩。
    """
    itemClicked = Signal(str)

    def __init__(self, title="", icon=None, collapse_mode="floating", item_height=50, parent=None):
        super().__init__(parent)
        self._is_collapsed = False
        self._title = title
        self._icon = icon
        self._collapse_mode = collapse_mode
        self._item_height = item_height
        
        # 整体主布局
        self.main_layout = QVBoxLayout(self)
        if self._collapse_mode == "floating":
            self.main_layout.setContentsMargins(0, 0, 12, 0)
        else:
            self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # 带有右边框的内部框架
        self.inner_frame = QFrame(self)
        self.inner_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-right: 1px solid #dcdfe6;
            }
        """)
        self.inner_layout = QVBoxLayout(self.inner_frame)
        self.inner_layout.setContentsMargins(0, 0, 0, 0)
        self.inner_layout.setSpacing(0)
        
        # --- 1. 顶部标题区域 ---
        self.title_area = QWidget()
        self.title_area.setFixedHeight(60)
        self.title_area.setStyleSheet("border: none;")
        self.title_layout = QHBoxLayout(self.title_area)
        self.title_layout.setContentsMargins(0, 0, 0, 0)
        self.title_layout.setSpacing(0) # Remove default spacing
        
        # 汉堡包按钮 (如果模式为 hamburger)
        self.hamburger_btn = QPushButton("≡")
        self.hamburger_btn.setFixedSize(64, 60)
        self.hamburger_btn.setCursor(Qt.PointingHandCursor)
        self.hamburger_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                font-size: 20px;
                color: #606266;
                padding: 0px;
                margin: 0px;
            }
            QPushButton:hover {
                color: #409eff;
            }
        """)
        self.hamburger_btn.clicked.connect(self.toggle_collapse)
        if self._collapse_mode == "hamburger":
            self.title_layout.addWidget(self.hamburger_btn)
            # 汉堡包模式下，如果仍有图标，放到汉堡包后面
            if self._icon:
                self.icon_label = QLabel(self._icon)
                self.icon_label.setFixedWidth(24)
                self.icon_label.setAlignment(Qt.AlignCenter)
                self.icon_label.setStyleSheet("font-size: 18px;")
                self.title_layout.addWidget(self.icon_label)
                self.title_layout.addSpacing(8) # 图标与文字的间距
            else:
                self.icon_label = QLabel() # placeholder
                self.icon_label.hide()
        else:
            self.hamburger_btn.hide()
            self.title_layout.addSpacing(20) # 悬浮模式左侧留白 20
            
            # 标题图标
            self.icon_label = QLabel()
            self.icon_label.setFixedWidth(24) # Match MkMenuItem icon width
            self.icon_label.setAlignment(Qt.AlignCenter)
            self.icon_label.setStyleSheet("font-size: 18px;")
            if self._icon:
                if self._icon in PHOSPHOR_ICONS:
                    self.icon_label.setPixmap(MkPhosphorIcon.get_pixmap(self._icon, "#303133", 20))
                else:
                    self.icon_label.setText(self._icon)
            self.title_layout.addWidget(self.icon_label)
            self.title_layout.addSpacing(20) # 20 + 24 + 20 = 64
            
        # 标题文本
        self.title_label = QLabel(self._title)
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #303133;")
        self.title_layout.addWidget(self.title_label)
        
        self.title_layout.addStretch()
        self.inner_layout.addWidget(self.title_area)
        
        # --- 2. 核心滚动区域 ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 6px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #c0c4cc;
                border-radius: 3px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #909399;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)

        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background: transparent; border: none;")
        self._layout = QVBoxLayout(self.content_widget)
        self._layout.setContentsMargins(0, 10, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addStretch()

        self.scroll_area.setWidget(self.content_widget)
        self.inner_layout.addWidget(self.scroll_area)
        
        self.main_layout.addWidget(self.inner_frame)

        # 设置初始宽度
        self.setFixedWidth(200)

        # 存储所有 item 以便管理排他性高亮
        self._all_items = []
        self._all_submenus = []
        
        # --- 3. 悬浮在边框上的收缩展开按钮 ---
        # 作为 MkMenu 的子组件，使用 resizeEvent 进行绝对定位
        self.collapse_btn = QPushButton("❮", self)
        self.collapse_btn.setFixedSize(24, 24)
        self.collapse_btn.setCursor(Qt.PointingHandCursor)
        self.collapse_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                border: 1px solid #dcdfe6;
                border-radius: 12px;
                color: #606266;
                font-size: 12px;
                font-weight: bold;
                padding-bottom: 2px;
            }
            QPushButton:hover {
                color: #409eff;
                border-color: #c6e2ff;
                background-color: #ecf5ff;
            }
        """)
        self.collapse_btn.clicked.connect(self.toggle_collapse)
        if self._collapse_mode == "hamburger":
            self.collapse_btn.hide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._collapse_mode == "floating":
            # 将按钮定位在右侧边缘内侧，避免被裁剪和引入额外的 layout margin
            self.collapse_btn.move(self.width() - 24, 28)
            self.collapse_btn.raise_()

    def enable_collapse_button(self, enable=True):
        """兼容老接口，现在折叠按钮默认显示"""
        self.collapse_btn.setVisible(enable)

    def set_border_right(self, border_style: str):
        """设置右侧边框样式，例如 'none' 或者 '1px solid #dcdfe6'"""
        self.inner_frame.setStyleSheet(f"""
            QFrame {{
                background-color: #ffffff;
                border-right: {border_style};
            }}
        """)

    def add_item(self, item_id: str, text: str, icon=None) -> MkMenuItem:
        """添加一级菜单项"""
        item = MkMenuItem(item_id, text, icon, height=self._item_height)
        item.set_left_margin(20)
        self._register_item(item)
        self._layout.insertWidget(self._layout.count() - 1, item)
        return item

    def add_submenu(self, title: str, icon=None) -> MkSubMenu:
        """添加一个折叠子菜单"""
        submenu = MkSubMenu(title, icon, height=self._item_height)
        self._all_submenus.append(submenu)
        self._layout.insertWidget(self._layout.count() - 1, submenu)
        return submenu
        
    def add_submenu_item(self, submenu: MkSubMenu, item_id: str, text: str, icon=None) -> MkMenuItem:
        """向子菜单中添加项"""
        item = MkMenuItem(item_id, text, icon, height=self._item_height)
        item.set_left_margin(40) # 子菜单项缩进
        self._register_item(item)
        submenu.add_item(item)
        return item

    def _register_item(self, item: MkMenuItem):
        self._all_items.append(item)
        item.clicked.connect(lambda checked=False, i=item: self._on_item_clicked(i))

    def _on_item_clicked(self, clicked_item: MkMenuItem):
        # 实现类似 QButtonGroup 的排他性（互斥）
        for item in self._all_items:
            if item != clicked_item:
                item.setChecked(False)
        clicked_item.setChecked(True)
        self.itemClicked.emit(clicked_item.item_id)

    def set_active(self, item_id: str):
        """代码层面设置高亮"""
        for item in self._all_items:
            if item.item_id == item_id:
                self._on_item_clicked(item)
                # 提示：如果该项在 submenu 里，理想情况应该自动展开 submenu
                break

    def toggle_collapse(self):
        """切换菜单折叠/展开状态"""
        self._is_collapsed = not self._is_collapsed
        target_width = 64 if self._is_collapsed else 200
        self.setFixedWidth(target_width)
        
        if self._is_collapsed:
            self.title_label.hide()
            self.icon_label.hide()
            if self._collapse_mode == "floating":
                self.collapse_btn.setText("❯")
        else:
            self.title_label.show()
            if self._collapse_mode == "floating":
                # Only show icon_label if we are in floating mode, or in hamburger mode but with an icon
                if self._icon or self._collapse_mode == "floating":
                    self.icon_label.show()
                self.collapse_btn.setText("❮")
            else:
                if self._icon:
                    self.icon_label.show()
            
        # 告诉所有子元素当前的状态，让他们隐藏文字
        for item in self._all_items:
            item.set_collapsed(self._is_collapsed)
        for submenu in self._all_submenus:
            submenu.set_collapsed(self._is_collapsed)

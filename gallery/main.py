import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QStackedWidget, QFrame, QComboBox, QCheckBox, QPushButton, QLineEdit, QSlider
from PySide6.QtGui import QFont, QPixmap, QIcon
from PySide6.QtCore import Qt
from monkeyui import (
    MkButton, MkCheckBox, MkMenu, MkTopbar, MkBreadcrumb, MkTabs,
    MkAlert, MkProgressBar, MkProgressRing,
    MkPagination, MkDropdown, MkSwitch, MkSlider, MkDatePicker, MkForm,
    MkInput, MkCaptchaWidget, MkAuthScreen, MkMessage,
    MkAvatar, MkTable, MkDataTable, MkImageCompare, MkImageSplit,
    MkTitleBar, MkWindow, MkUpload, MkComboBox, MkMultiComboBox
)

class ButtonGallery(QWidget):
    """按钮组件的展示页"""
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        title_font = QFont("Microsoft YaHei", 12, QFont.Bold)
        
        # 1. 基础用法
        label_basic = QLabel("基础用法 (Basic Types)")
        label_basic.setFont(title_font)
        layout.addWidget(label_basic)
        
        basic_layout = QHBoxLayout()
        basic_layout.addWidget(MkButton("Default"))
        basic_layout.addWidget(MkButton("Primary", type="primary"))
        basic_layout.addWidget(MkButton("Success", type="success"))
        basic_layout.addWidget(MkButton("Info", type="info"))
        basic_layout.addWidget(MkButton("Warning", type="warning"))
        basic_layout.addWidget(MkButton("Danger", type="danger"))
        basic_layout.addStretch()
        layout.addLayout(basic_layout)

        # 2. 禁用状态
        label_disabled = QLabel("禁用状态 (Disabled State)")
        label_disabled.setFont(title_font)
        layout.addWidget(label_disabled)
        
        disabled_layout = QHBoxLayout()
        for t, name in [("default", "Default"), ("primary", "Primary"), ("success", "Success"), 
                       ("info", "Info"), ("warning", "Warning"), ("danger", "Danger")]:
            btn = MkButton(name, type=t)
            btn.setEnabled(False)
            disabled_layout.addWidget(btn)
        disabled_layout.addStretch()
        layout.addLayout(disabled_layout)

        # 3. 尺寸
        label_sizes = QLabel("不同尺寸 (Sizes)")
        label_sizes.setFont(title_font)
        layout.addWidget(label_sizes)
        
        size_layout = QHBoxLayout()
        size_layout.addWidget(MkButton("Large", type="primary", size="large"))
        size_layout.addWidget(MkButton("Default", type="primary", size="default"))
        size_layout.addWidget(MkButton("Small", type="primary", size="small"))
        size_layout.addStretch()
        layout.addLayout(size_layout)

        layout.addStretch()

class CheckboxGallery(QWidget):
    """复选框组件的展示页"""
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        title_font = QFont("Microsoft YaHei", 12, QFont.Bold)
        
        label_checkbox = QLabel("复选框 (CheckBox)")
        label_checkbox.setFont(title_font)
        layout.addWidget(label_checkbox)
        
        checkbox_layout = QHBoxLayout()
        checkbox_layout.addWidget(MkCheckBox("Option 1"))
        
        chk2 = MkCheckBox("Option 2 (Checked)")
        chk2.setChecked(True)
        checkbox_layout.addWidget(chk2)
        
        chk3 = MkCheckBox("Disabled")
        chk3.setEnabled(False)
        checkbox_layout.addWidget(chk3)
        
        chk4 = MkCheckBox("Disabled & Checked")
        chk4.setChecked(True)
        chk4.setEnabled(False)
        checkbox_layout.addWidget(chk4)
        
        checkbox_layout.addStretch()
        layout.addLayout(checkbox_layout)

        layout.addStretch()

class TopbarGallery(QWidget):
    """顶部导航栏组件的展示页"""
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 为了演示顶部导航栏的完整效果，我们在这个页面模拟一个完整的窗口结构
        
        # 1. 顶部导航栏
        self.topbar = MkTopbar(logo_text="MONKEY UI")
        self.topbar.add_item("home", "处理中心")
        self.topbar.add_item("workspace", "我的工作台")
        self.topbar.add_item("orders", "订单管理")
        self.topbar.add_item("settings", "系统设置")
        
        # 默认选中处理中心
        self.topbar.set_active("home")
        
        layout.addWidget(self.topbar)
        
        # 2. 下方的模拟内容区域
        content_area = QWidget()
        content_area.setStyleSheet("background-color: #f0f2f5;") # 浅灰色的内容区
        
        content_layout = QVBoxLayout(content_area)
        
        self.status_label = QLabel("当前选中：处理中心 (home)")
        self.status_label.setStyleSheet("font-size: 16px; color: #606266; margin: 20px;")
        content_layout.addWidget(self.status_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(content_area, stretch=1)
        
        # 连接信号
        self.topbar.itemClicked.connect(self._on_topbar_clicked)
        
    def _on_topbar_clicked(self, item_id):
        self.status_label.setText(f"当前选中：{item_id}")

class NavMiscGallery(QWidget):
    """面包屑与标签页展示"""
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(30)
        
        title_font = QFont("Microsoft YaHei", 12, QFont.Bold)
        
        # 1. 面包屑
        label_breadcrumb = QLabel("面包屑导航 (Breadcrumb)")
        label_breadcrumb.setFont(title_font)
        layout.addWidget(label_breadcrumb)
        
        self.breadcrumb1 = MkBreadcrumb(separator="/")
        self.breadcrumb1.set_items([
            {"id": "home", "text": "首页"},
            {"id": "nav", "text": "导航组件"},
            {"id": "breadcrumb", "text": "面包屑"}
        ])
        layout.addWidget(self.breadcrumb1)
        
        self.breadcrumb2 = MkBreadcrumb(separator=">")
        self.breadcrumb2.set_items([
            {"id": "home", "text": "Home"},
            {"id": "user", "text": "User Management"},
            {"id": "detail", "text": "User Detail"}
        ])
        layout.addWidget(self.breadcrumb2)

        # 2. 标签页
        label_tabs = QLabel("标签页 (Tabs)")
        label_tabs.setFont(title_font)
        layout.addWidget(label_tabs)
        
        self.tabs = MkTabs()
        self.tabs.setFixedHeight(200) # 限定一下高度，方便展示
        
        # 标签1内容
        tab1_content = QWidget()
        t1_layout = QVBoxLayout(tab1_content)
        t1_layout.addWidget(QLabel("用户个人中心，支持放置任意自定义 QWidget"))

        
        # 标签2内容
        tab2_content = QWidget()
        t2_layout = QVBoxLayout(tab2_content)
        t2_layout.addWidget(QLabel("这是 配置管理 的内容面板"))
        
        self.tabs.add_tab("user", "用户管理", tab1_content)
        self.tabs.add_tab("config", "配置管理", tab2_content)
        
        layout.addWidget(self.tabs)
        
        # 3. 分页器
        label_pagination = QLabel("分页器 (Pagination)")
        label_pagination.setFont(title_font)
        layout.addWidget(label_pagination)
        
        self.pagination = MkPagination(total=200, page_size=10, current=1)
        layout.addWidget(self.pagination)

        # 4. 下拉菜单
        label_dropdown = QLabel("下拉菜单 (Dropdown)")
        label_dropdown.setFont(title_font)
        layout.addWidget(label_dropdown)
        
        dropdown_layout = QHBoxLayout()
        self.dropdown = MkDropdown("操作菜单")
        self.dropdown.add_item("新增", "add")
        self.dropdown.add_item("编辑", "edit")
        self.dropdown.add_separator()
        self.dropdown.add_item("删除", "delete")
        
        dropdown_layout.addWidget(self.dropdown)
        dropdown_layout.addStretch()
        layout.addLayout(dropdown_layout)

        layout.addStretch()

class FeedbackGallery(QWidget):
    """反馈类组件展示页 (Alert, Progress)"""
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(30)
        
        title_font = QFont("Microsoft YaHei", 12, QFont.Bold)
        
        # 1. 警告提示 (Alert)
        label_alert = QLabel("警告提示 (Alert)")
        label_alert.setFont(title_font)
        layout.addWidget(label_alert)
        
        layout.addWidget(MkAlert(title="成功提示的文案", mk_type="success", show_icon=True))
        layout.addWidget(MkAlert(title="消息提示的文案", mk_type="info", show_icon=True, closable=True))
        layout.addWidget(MkAlert(title="警告提示的文案", mk_type="warning", show_icon=True))
        layout.addWidget(MkAlert(
            title="错误提示的文案", 
            description="这是一句绕口令：黑化肥发灰，灰化肥发黑。黑化肥发灰会挥发；灰化肥挥发会发黑。",
            mk_type="error", 
            show_icon=True, 
            closable=True
        ))

        # 2. 进度条 (Progress Bar)
        label_progress_bar = QLabel("进度条 (Progress Bar)")
        label_progress_bar.setFont(title_font)
        layout.addWidget(label_progress_bar)
        
        layout.addWidget(MkProgressBar(percentage=50, status="normal"))
        layout.addWidget(MkProgressBar(percentage=100, status="success"))
        layout.addWidget(MkProgressBar(percentage=80, status="warning", stroke_width=10, text_inside=True))
        layout.addWidget(MkProgressBar(percentage=50, status="exception"))

        # 3. 进度环 (Progress Ring)
        label_progress_ring = QLabel("进度环 (Progress Ring)")
        label_progress_ring.setFont(title_font)
        layout.addWidget(label_progress_ring)
        
        ring_layout = QHBoxLayout()
        ring_layout.addWidget(MkProgressRing(percentage=0, status="normal"))
        ring_layout.addWidget(MkProgressRing(percentage=25, status="normal"))
        ring_layout.addWidget(MkProgressRing(percentage=100, status="success"))
        ring_layout.addWidget(MkProgressRing(percentage=75, status="warning"))
        ring_layout.addWidget(MkProgressRing(percentage=50, status="exception"))
        ring_layout.addStretch()
        
        layout.addLayout(ring_layout)
        layout.addStretch()

class DataGallery(QWidget):
    """数据展示组件展示页 (Avatar, Table)"""
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(30)
        
        title_font = QFont("Microsoft YaHei", 12, QFont.Bold)
        
        # 1. 头像 (Avatar)
        label_avatar = QLabel("头像 (Avatar)")
        label_avatar.setFont(title_font)
        layout.addWidget(label_avatar)
        
        avatar_layout = QHBoxLayout()
        avatar_layout.addWidget(MkAvatar(text="User", size=50, shape="circle"))
        avatar_layout.addWidget(MkAvatar(text="Admin", size=50, shape="square"))
        avatar_layout.addStretch()
        layout.addLayout(avatar_layout)

        # 2. 表格 (Table)
        label_table = QLabel("表格 (Table)")
        label_table.setFont(title_font)
        layout.addWidget(label_table)
        
        self.table = MkTable()
        self.table.set_headers(["日期", "姓名", "地址"])
        self.table.set_data([
            ["2016-05-02", "王小虎", "上海市普陀区金沙江路 1518 弄"],
            ["2016-05-04", "王小虎", "上海市普陀区金沙江路 1517 弄"],
            ["2016-05-01", "王小虎", "上海市普陀区金沙江路 1519 弄"],
            ["2016-05-03", "王小虎", "上海市普陀区金沙江路 1516 弄"]
        ])
        # Give table some height for demo
        self.table.setFixedHeight(200)
        layout.addWidget(self.table)
        
        layout.addStretch()

class DataTableGallery(QWidget):
    """高级 DataTable 数据表格的展示页"""
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        title_font = QFont("Microsoft YaHei", 12, QFont.Bold)
        
        # 1. 标题
        label_title = QLabel("高级数据表格 (DataTable)")
        label_title.setFont(title_font)
        layout.addWidget(label_title)
        
        desc = QLabel(
            "自适应 shadcn-ui 风格的高级数据表格。支持全选/跨页多选、Phosphor SVG 图标操作列、"
            "图片/视频类型列点击灯箱大图与视频播放器交互预览，开箱即用自动分页。"
        )
        desc.setStyleSheet("color: #64748b; font-size: 13px; line-height: 18px;")
        layout.addWidget(desc)
        
        # 获取图片的绝对路径，确保能在各种工作目录下正确加载
        base_dir = os.path.dirname(os.path.abspath(__file__))
        before_path = os.path.join(base_dir, "assets", "before.png")
        after_path = os.path.join(base_dir, "assets", "after.png")
        video_path = os.path.join(base_dir, "assets", "demo_video.mp4")
        
        # 2. 列配置 (Declarative configuration)
        columns = [
            {"key": "date", "label": "录入日期", "width": 120},
            {"key": "name", "label": "操作人", "width": 80},
            {"key": "avatar", "label": "结果图片", "type": "image", "width": 80},
            {"key": "video", "label": "演示视频", "type": "video", "width": 80},
            {"key": "status", "label": "状态"},
            {"key": "action", "label": "操作", "type": "action", "width": 100}
        ]
        
        # 12条精美数据展示分页 (每页 5 条)
        mock_data = [
            {"id": "101", "date": "2026-06-01", "name": "王小虎", "avatar": before_path, "video": video_path, "status": "进行中"},
            {"id": "102", "date": "2026-06-02", "name": "李二狗", "avatar": after_path, "video": video_path, "status": "已完成"},
            {"id": "103", "date": "2026-06-03", "name": "张三疯", "avatar": before_path, "video": video_path, "status": "已完成"},
            {"id": "104", "date": "2026-06-04", "name": "赵四爷", "avatar": after_path, "video": video_path, "status": "审核中"},
            {"id": "105", "date": "2026-06-05", "name": "钱掌柜", "avatar": before_path, "video": video_path, "status": "待处理"},
            {"id": "106", "date": "2026-06-06", "name": "孙大圣", "avatar": after_path, "video": video_path, "status": "进行中"},
            {"id": "107", "date": "2026-06-07", "name": "猪八戒", "avatar": before_path, "video": video_path, "status": "已完成"},
            {"id": "108", "date": "2026-06-08", "name": "沙和尚", "avatar": after_path, "video": video_path, "status": "进行中"},
            {"id": "109", "date": "2026-06-09", "name": "唐三藏", "avatar": before_path, "video": video_path, "status": "已完成"},
            {"id": "110", "date": "2026-06-10", "name": "白龙马", "avatar": after_path, "video": video_path, "status": "待处理"},
            {"id": "111", "date": "2026-06-11", "name": "观音姐", "avatar": before_path, "video": video_path, "status": "已完成"},
            {"id": "112", "date": "2026-06-12", "name": "如来佛", "avatar": after_path, "video": video_path, "status": "审核中"},
        ]
        
        # 实例化数据表格 (每页 5 行)
        self.data_table = MkDataTable(columns=columns, data=mock_data, page_size=5, selection_enabled=True, parent=self)
        layout.addWidget(self.data_table, stretch=1)
        
        # 3. 实时交互回显区域
        self.interaction_card = QFrame(self)
        self.interaction_card.setStyleSheet("""
            QFrame {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
            }
            QLabel {
                color: #475569;
                font-size: 12px;
            }
        """)
        card_layout = QVBoxLayout(self.interaction_card)
        card_layout.setContentsMargins(10, 8, 10, 8)
        
        self.selected_label = QLabel("当前选中：0 项")
        card_layout.addWidget(self.selected_label)
        
        self.action_label = QLabel("操作日志：等待用户交互...")
        card_layout.addWidget(self.action_label)
        
        layout.addWidget(self.interaction_card)
        
        # 信号连接
        self.data_table.selectionChanged.connect(self._on_selection_changed)
        self.data_table.editRequested.connect(self._on_edit_requested)
        self.data_table.deleteRequested.connect(self._on_delete_requested)

    def _on_selection_changed(self, selected_items):
        names = [item.get("name") for item in selected_items]
        self.selected_label.setText(f"当前选中：{len(selected_items)} 项 ({', '.join(names) if names else '无'})")

    def _on_edit_requested(self, index, row_dict):
        self.action_label.setText(f"操作日志：[编辑信号] 触发绝对行号 {index}，数据内容: {row_dict['name']}")

    def _on_delete_requested(self, index, row_dict):
        self.action_label.setText(f"操作日志：[删除信号] 触发绝对行号 {index}，数据内容: {row_dict['name']}")

class FormGallery(QWidget):
    """表单录入组件展示页 (Switch, Slider, DatePicker, ComboBox, MultiComboBox, Form)"""
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(30)
        
        title_font = QFont("Microsoft YaHei", 12, QFont.Bold)
        
        # 1. 结构化表单
        label_form = QLabel("表单与输入组件 (Form, Switch, Slider, DatePicker, ComboBox, MultiComboBox)")
        label_form.setFont(title_font)
        layout.addWidget(label_form)
        
        self.form = MkForm(label_width=100, label_position="right")
        
        # Switch
        self.switch = MkSwitch(checked=True)
        self.form.add_item("即时配送", self.switch)
        
        # Slider
        self.slider = MkSlider(Qt.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(40)
        self.form.add_item("优先级", self.slider)
        
        # DatePicker
        self.date_picker = MkDatePicker()
        self.form.add_item("活动时间", self.date_picker)
        
        # ComboBox (Single Select)
        self.combobox = MkComboBox()
        self.combobox.addItems(["选项一 (Option 1)", "选项二 (Option 2)", "选项三 (Option 3)"])
        self.form.add_item("单选下拉框", self.combobox)
        
        # MultiComboBox (Multi Select)
        self.multi_combobox = MkMultiComboBox()
        self.multi_combobox.addItems({
            0: "苹果 (Apple)",
            1: "香蕉 (Banana)",
            2: "橙子 (Orange)",
            3: "葡萄 (Grape)",
            4: "西瓜 (Watermelon)"
        })
        self.form.add_item("多选下拉框", self.multi_combobox)
        
        layout.addWidget(self.form)
        layout.addStretch()

class AuthGallery(QWidget):
    """登录与注册组件展示页"""
    def __init__(self):
        super().__init__()
        # Horizontal layout: left control panel, right auth screen preview
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(30)
        
        # --- 1. Left Control Panel ---
        control_panel = QFrame(self)
        control_panel.setFixedWidth(260)
        control_panel.setStyleSheet("""
            QFrame {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 15px;
            }
            QLabel {
                font-family: "Microsoft YaHei", sans-serif;
                font-size: 13px;
                font-weight: bold;
                color: #334155;
                margin-top: 10px;
                background: transparent;
            }
            QComboBox, QCheckBox {
                font-size: 12px;
                color: #475569;
            }
            QComboBox {
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 4px;
                background-color: #ffffff;
            }
        """)
        
        control_layout = QVBoxLayout(control_panel)
        control_layout.setSpacing(12)
        
        panel_title = QLabel("Auth 自定义控制台")
        panel_title.setStyleSheet("font-size: 15px; color: #0f172a; margin-bottom: 5px;")
        control_layout.addWidget(panel_title)
        
        # Background setting
        control_layout.addWidget(QLabel("背景主题配置"))
        self.bg_combo = QComboBox()
        self.bg_combo.addItems([
            "极光深蓝渐变",
            "皇家魅紫渐变",
            "高级纯灰背景",
            "本地大图背景"
        ])
        control_layout.addWidget(self.bg_combo)
        
        # Avatar option
        control_layout.addWidget(QLabel("头像配置"))
        self.avatar_check = QCheckBox("启用顶部头像")
        self.avatar_check.setChecked(True)
        control_layout.addWidget(self.avatar_check)
        
        self.avatar_shape_combo = QComboBox()
        self.avatar_shape_combo.addItems(["圆形头像 (circle)", "方形头像 (square)"])
        control_layout.addWidget(self.avatar_shape_combo)
        
        # Captcha Type
        control_layout.addWidget(QLabel("安全验证码"))
        self.captcha_combo = QComboBox()
        self.captcha_combo.addItems([
            "图形验证码 (graphic)",
            "短信验证码 (sms)",
            "无验证码 (none)"
        ])
        control_layout.addWidget(self.captcha_combo)
        
        # Register Custom Fields Config
        control_layout.addWidget(QLabel("注册页自定义字段"))
        self.custom_fields_combo = QComboBox()
        self.custom_fields_combo.addItems([
            "默认字段 (用户名+邮箱+密码)",
            "性别 + 手机号",
            "地址 + 个人简介 + 年龄"
        ])
        control_layout.addWidget(self.custom_fields_combo)
        
        # Rebuild trigger button
        self.rebuild_btn = QPushButton("一键生成登录界面")
        self.rebuild_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.rebuild_btn.setFixedHeight(36)
        self.rebuild_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        self.rebuild_btn.clicked.connect(self.rebuild_auth_screen)
        control_layout.addWidget(self.rebuild_btn)
        
        # Dynamic Custom Fields Input & Button
        control_layout.addWidget(QLabel("动态添加单字段"))
        self.custom_field_input = QLineEdit()
        self.custom_field_input.setPlaceholderText("例如: 兴趣爱好 / 毕业院校")
        self.custom_field_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 5px;
                background-color: #ffffff;
                color: #0f172a;
                font-size: 12px;
                min-height: 24px;
            }
        """)
        control_layout.addWidget(self.custom_field_input)
        
        self.add_field_btn = QPushButton("一键添加此字段")
        self.add_field_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_field_btn.setFixedHeight(36)
        self.add_field_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        self.add_field_btn.clicked.connect(self.add_single_custom_field)
        control_layout.addWidget(self.add_field_btn)
        
        control_layout.addStretch()
        main_layout.addWidget(control_panel)
        
        # --- 2. Right Preview Panel ---
        self.preview_container = QWidget(self)
        self.preview_layout = QVBoxLayout(self.preview_container)
        self.preview_layout.setContentsMargins(0, 0, 0, 0)
        
        main_layout.addWidget(self.preview_container, stretch=1)
        
        # Initial build
        self.auth_screen = None
        self.rebuild_auth_screen()

    def rebuild_auth_screen(self):
        # 1. Clear old screen
        if self.auth_screen:
            self.auth_screen.deleteLater()
            
        # 2. Resolve background config
        bg_opt = self.bg_combo.currentText()
        if bg_opt == "极光深蓝渐变":
            bg = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1e293b, stop:1 #0f172a)"
        elif bg_opt == "皇家魅紫渐变":
            bg = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4f46e5, stop:1 #06b6d4)"
        elif bg_opt == "高级纯灰背景":
            bg = "#f1f5f9"
        else:
            # Use local gallery before.png
            base_dir = os.path.dirname(os.path.abspath(__file__))
            bg = os.path.join(base_dir, "assets", "before.png")
            
        # 3. Resolve avatar path & shape
        avatar_path = None
        if self.avatar_check.isChecked():
            # Use local after.png as user avatar
            base_dir = os.path.dirname(os.path.abspath(__file__))
            avatar_path = os.path.join(base_dir, "assets", "after.png")
            
        avatar_shape = "circle" if "circle" in self.avatar_shape_combo.currentText() else "square"
        
        # 4. Resolve captcha
        captcha_text = self.captcha_combo.currentText()
        if "graphic" in captcha_text:
            captcha_type = "graphic"
        elif "sms" in captcha_text:
            captcha_type = "sms"
        else:
            captcha_type = "none"
            
        # 4b. Resolve register custom fields
        custom_fields = None
        fields_opt = self.custom_fields_combo.currentText()
        if "性别" in fields_opt:
            custom_fields = [
                {"name": "gender", "placeholder": "请设置您的性别 (例如: 男/女)", "icon": "pencil"},
                {"name": "phone", "placeholder": "请输入您的密保手机号码", "icon": "pencil"}
            ]
        elif "地址" in fields_opt:
            custom_fields = [
                {"name": "address", "placeholder": "请输入您的常住居住地址", "icon": "pencil"},
                {"name": "bio", "placeholder": "请输入一句话个性签名", "icon": "pencil"},
                {"name": "age", "placeholder": "请输入您的真实年龄", "icon": "pencil"}
            ]
            
        # 5. Instantiate new MkAuthScreen
        self.auth_screen = MkAuthScreen(
            logo_text="MONKEY UI",
            description="风格极简授权中心",
            avatar=avatar_path,
            avatar_shape=avatar_shape,
            captcha_type=captcha_type,
            background=bg,
            register_custom_fields=custom_fields,
            parent=self.preview_container
        )
        
        # Connect callbacks
        self.auth_screen.loginSubmitted.connect(self._on_login_submitted)
        self.auth_screen.registerSubmitted.connect(self._on_register_submitted)
        self.auth_screen.smsRequested.connect(self._on_sms_requested)
        self.auth_screen.forgotPasswordClicked.connect(self._on_forgot_password_clicked)
        
        self.preview_layout.addWidget(self.auth_screen)
 
    def _on_login_submitted(self, username, password, captcha_code, remember_me=False):
        remember_str = " (记住密码: 是)" if remember_me else " (记住密码: 否)"
        # Mock checks (database validation callback simulation)
        if username == "admin" and password == "admin123":
            MkMessage.success(self.window(), f"登录成功，欢迎尊贵的管理员回来！{remember_str}")
        else:
            # Failure popups
            MkMessage.error(self.window(), f"用户名或密码错误，请检查！(提示: admin / admin123){remember_str}")
 
    def _on_register_submitted(self, username, email, password, confirm_password, custom_fields=None):
        custom_str = ""
        if custom_fields:
            custom_str = " | 自定义: " + str(custom_fields)
        MkMessage.success(self.window(), f"注册成功！您的账号: {username}，我们已向 {email} 发送激活信！{custom_str}")
        # Toggle back to login mode
        self.auth_screen.switch_mode("login")
 
    def _on_sms_requested(self, email):
        MkMessage.info(self.window(), f"验证码已发送至：{email}，请查收短信/邮件！")

    def _on_forgot_password_clicked(self):
        MkMessage.warning(self.window(), "找回密码提示：系统已拦截点击事件，请接入您的找回密码业务逻辑！")

    def add_single_custom_field(self):
        field_name = self.custom_field_input.text().strip()
        if not field_name:
            MkMessage.error(self.window(), "请先在输入框中输入需要添加的字段名称！")
            return
        if self.auth_screen:
            self.auth_screen.add_register_field(field_name, f"请输入您的{field_name}", "pencil")
            MkMessage.success(self.window(), f"成功添加字段：{field_name}！切换至注册面板即可预览效果")
            self.custom_field_input.clear()

class ImageCompareGallery(QWidget):
    """图像对比组件展示页 (MkImageCompare)"""
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        title_font = QFont("Microsoft YaHei", 12, QFont.Bold)
        
        label_title = QLabel("图像对比 (Image Compare)")
        label_title.setFont(title_font)
        layout.addWidget(label_title)
        
        desc = QLabel("交互式双图对比组件，常用于展示风格迁移、超分辨率、深度图像修复等模型的前后结果对比。")
        desc.setStyleSheet("color: #606266; font-size: 13px;")
        layout.addWidget(desc)
        
        # 获取图片的绝对路径，确保能在各种工作目录下正确加载
        base_dir = os.path.dirname(os.path.abspath(__file__))
        before_path = os.path.join(base_dir, "assets", "before.png")
        after_path = os.path.join(base_dir, "assets", "after.png")
        
        # 风格迁移对比实例 (带标签)
        compare_widget = MkImageCompare(before_path, after_path)
        layout.addWidget(compare_widget, stretch=1)
        
        tip_label = QLabel("💡 提示：可以在上方图片中任意位置点击或拖动滑块，以交互式查看“迁移结果”与“原图”细节。")
        tip_label.setStyleSheet("color: #909399; font-size: 12px; font-style: italic;")
        layout.addWidget(tip_label)

class ImageSplitGallery(QWidget):
    """分屏对比组件展示页 (MkImageSplit)"""
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        title_font = QFont("Microsoft YaHei", 12, QFont.Bold)
        
        label_title = QLabel("分屏对比 (Image Split)")
        label_title.setFont(title_font)
        layout.addWidget(label_title)
        
        desc = QLabel("左右分屏无损对比组件。双图完整并排渲染，拖拽中间的手柄可以改变分屏比例；点击手柄上的左右箭头，能优雅地平滑收缩折叠某一边，实现单图与双图对比的快速切换。")
        desc.setStyleSheet("color: #606266; font-size: 13px;")
        layout.addWidget(desc)
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        before_path = os.path.join(base_dir, "assets", "before.png")
        after_path = os.path.join(base_dir, "assets", "after.png")
        
        # 实例化分屏对比组件
        split_widget = MkImageSplit(before_path, after_path)
        layout.addWidget(split_widget, stretch=1)
        
        tip_label = QLabel("💡 提示：您可以拖拽中央的垂直胶囊手柄调节分屏比例，或者点击手柄上的 ❮ ❯ 箭头平滑收缩/还原左侧或右侧图片！")
        tip_label.setStyleSheet("color: #909399; font-size: 12px; font-style: italic;")
        layout.addWidget(tip_label)

class WindowGallery(QWidget):
    """自定义窗口与标题栏展示页"""
    def __init__(self):
        super().__init__()
        # Use a horizontal layout for the split page: controls on the left, preview on the right
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(30)
        
        # Left Panel (Controls)
        control_panel = QFrame(self)
        control_panel.setFixedWidth(280)
        control_panel.setStyleSheet("""
            QFrame {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 15px;
            }
            QLabel {
                font-family: "Microsoft YaHei", sans-serif;
                font-size: 13px;
                font-weight: bold;
                color: #334155;
                margin-top: 10px;
                background: transparent;
            }
            QComboBox, QSlider {
                background: transparent;
            }
        """)
        control_layout = QVBoxLayout(control_panel)
        control_layout.setSpacing(10)
        
        title_label = QLabel("自定义窗口控制台")
        title_label.setStyleSheet("font-size: 15px; color: #0f172a; margin-bottom: 5px;")
        control_layout.addWidget(title_label)
        
        # 1. Preset Selector
        control_layout.addWidget(QLabel("选择主题预设风格 (Presets)"))
        self.preset_combo = QComboBox()
        self.preset_combo.addItem("默认风格 (default)", "default")
        self.preset_combo.addItem("Shadcn UI风格 (shadcn)", "shadcn")
        self.preset_combo.addItem("IDA Pro风格 (ida)", "ida")
        self.preset_combo.addItem("向日葵风格 (sunlogin)", "sunlogin")
        self.preset_combo.addItem("汽水音乐风格 (soda)", "soda")
        self.preset_combo.addItem("Antigravity风格 (antigravity)", "antigravity")
        self.preset_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 4px;
                background-color: #ffffff;
                color: #475569;
                font-size: 12px;
            }
        """)
        control_layout.addWidget(self.preset_combo)
        
        # 2. Custom Background Color override
        control_layout.addWidget(QLabel("自定义背景色 (Hex/RGBA)"))
        self.bg_color_input = QLineEdit()
        self.bg_color_input.setPlaceholderText("留空则使用预设默认色")
        self.bg_color_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 4px 8px;
                background-color: #ffffff;
                color: #475569;
                font-size: 12px;
            }
        """)
        control_layout.addWidget(self.bg_color_input)
        
        # 3. Custom Text Color override
        control_layout.addWidget(QLabel("自定义文字色 (Hex)"))
        self.text_color_input = QLineEdit()
        self.text_color_input.setPlaceholderText("留空则使用预设默认色")
        self.text_color_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 4px 8px;
                background-color: #ffffff;
                color: #475569;
                font-size: 12px;
            }
        """)
        control_layout.addWidget(self.text_color_input)
        
        # 4. Height override
        control_layout.addWidget(QLabel("标题栏高度 (30 - 70 px)"))
        self.height_slider = QSlider(Qt.Horizontal)
        self.height_slider.setRange(30, 70)
        self.height_slider.setValue(40)
        control_layout.addWidget(self.height_slider)
        
        # 5. Radius override
        control_layout.addWidget(QLabel("窗口圆角半径 (0 - 20 px)"))
        self.radius_slider = QSlider(Qt.Horizontal)
        self.radius_slider.setRange(0, 20)
        self.radius_slider.setValue(8)
        control_layout.addWidget(self.radius_slider)
        
        # 6. Close button behavior
        control_layout.addWidget(QLabel("关闭按钮行为"))
        self.close_combo = QComboBox()
        self.close_combo.addItem("销毁窗口并退出 (close)", "close")
        self.close_combo.addItem("隐藏到后台/托盘 (hide)", "hide")
        self.close_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 4px;
                background-color: #ffffff;
                color: #475569;
                font-size: 12px;
            }
        """)
        control_layout.addWidget(self.close_combo)
        
        # 7. Action Button
        self.btn_launch = MkButton("启动独立无边框窗口 🚀", type="primary")
        self.btn_launch.clicked.connect(self.launch_demo_window)
        control_layout.addWidget(self.btn_launch)
        
        control_layout.addStretch()
        
        main_layout.addWidget(control_panel)
        
        # Right Panel (Live Mini Preview)
        preview_panel = QFrame(self)
        preview_panel.setStyleSheet("""
            QFrame {
                background-color: #f1f5f9;
                border: 1px dashed #cbd5e1;
                border-radius: 8px;
            }
        """)
        preview_layout = QVBoxLayout(preview_panel)
        preview_layout.setContentsMargins(20, 20, 20, 20)
        preview_layout.setSpacing(15)
        
        preview_header = QLabel("标题栏实时外观预览 (Local Mini Mock)")
        preview_header.setStyleSheet("font-size: 14px; font-weight: bold; color: #334155; border: none; background: transparent;")
        preview_layout.addWidget(preview_header)
        
        # Container to hold the mock window preview
        self.mock_win_frame = QFrame()
        self.mock_win_frame.setObjectName("MockWindowFrame")
        self.mock_win_frame.setFrameShape(QFrame.Shape.NoFrame)
        self.mock_win_frame.setStyleSheet("""
            QFrame#MockWindowFrame {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
        """)
        mock_win_layout = QVBoxLayout(self.mock_win_frame)
        mock_win_layout.setContentsMargins(0, 0, 0, 0)
        mock_win_layout.setSpacing(0)
        
        # Add the MkTitleBar inside the mock frame
        self.mock_titlebar = MkTitleBar(preset="default")
        self.mock_titlebar.set_title("MonkeyUI - YOLO Target Detection Console")
        # Set a dummy icon
        base_dir = os.path.dirname(os.path.abspath(__file__))
        after_path = os.path.join(base_dir, "assets", "after.png")
        if os.path.exists(after_path):
            self.mock_titlebar.set_icon(QPixmap(after_path))
            
        mock_win_layout.addWidget(self.mock_titlebar)
        
        # Fake client area in mock
        self.mock_client = QWidget()
        self.mock_client.setObjectName("MockClient")
        self.mock_client_layout = QVBoxLayout(self.mock_client)
        self.mock_client_layout.setContentsMargins(20, 40, 20, 40)
        
        self.mock_desc = QLabel("这里是子页面的模拟客户端区域。\n选择左侧的预设风格或滑动高度/圆角，以直接观察此处的实时变化。")
        self.mock_desc.setStyleSheet("color: #94a3b8; font-size: 12px; line-height: 18px;")
        self.mock_desc.setAlignment(Qt.AlignCenter)
        self.mock_client_layout.addWidget(self.mock_desc)
        
        mock_win_layout.addWidget(self.mock_client, stretch=1)
        
        preview_layout.addWidget(self.mock_win_frame, stretch=1)
        
        main_layout.addWidget(preview_panel, stretch=1)
        
        # Connect settings signals
        self.preset_combo.currentIndexChanged.connect(self.update_mini_preview)
        self.bg_color_input.textChanged.connect(self.update_mini_preview)
        self.text_color_input.textChanged.connect(self.update_mini_preview)
        self.height_slider.valueChanged.connect(self.update_mini_preview)
        self.radius_slider.valueChanged.connect(self.update_mini_preview)
        
        # Initial trigger
        self.update_mini_preview()
        
    def update_mini_preview(self):
        preset = self.preset_combo.currentData()
        bg_color = self.bg_color_input.text().strip()
        text_color = self.text_color_input.text().strip()
        height = self.height_slider.value()
        radius = self.radius_slider.value()
        
        # Apply configurations to mock titlebar
        self.mock_titlebar.apply_preset(preset)
        
        # Override values
        if bg_color:
            self.mock_titlebar._bg_color = bg_color
        if text_color:
            self.mock_titlebar._text_color = text_color
            
        self.mock_titlebar._height = height
        
        # Refresh drawing
        self.mock_titlebar.apply_theme_colors()
        self.mock_titlebar.rebuild_layout()
        
        # Refresh Mock window container styling (border, radius)
        border_color = "#e4e4e7" if preset == "shadcn" else "#3f3f3f" if preset == "ida" else "#313244" if preset == "antigravity" else "#e2e8f0"
        
        window_bg = "#ffffff"
        client_text = "#94a3b8"
        if preset in ["ida", "sunlogin", "soda", "antigravity"]:
            window_bg = "#1e1e2e" if preset == "antigravity" else "#1e1f22" if preset == "sunlogin" else "#121212" if preset == "soda" else "#1a1a1a"
            client_text = "#64748b"
            
        self.mock_win_frame.setStyleSheet(f"""
            QFrame#MockWindowFrame {{
                background-color: {window_bg};
                border: 1px solid {border_color};
                border-radius: {radius}px;
            }}
        """)
        self.mock_desc.setStyleSheet(f"color: {client_text}; font-size: 12px; line-height: 18px;")
        
    def launch_demo_window(self):
        preset = self.preset_combo.currentData()
        bg_color = self.bg_color_input.text().strip()
        text_color = self.text_color_input.text().strip()
        height = self.height_slider.value()
        radius = self.radius_slider.value()
        close_behavior = self.close_combo.currentData()
        
        # Spawn MkWindow
        self.demo_win = MkWindow(use_custom_title_bar=True, preset=preset)
        self.demo_win.setWindowTitle("MonkeyUI - YOLO Target Detection System")
        
        # Set Window icon
        base_dir = os.path.dirname(os.path.abspath(__file__))
        after_path = os.path.join(base_dir, "assets", "after.png")
        if os.path.exists(after_path):
            self.demo_win.setWindowIcon(QIcon(after_path))
            
        self.demo_win.set_border_radius(radius)
        self.demo_win.set_close_behavior(close_behavior)
        
        # Apply overrides if specified
        if bg_color:
            self.demo_win.titlebar._bg_color = bg_color
        if text_color:
            self.demo_win.titlebar._text_color = text_color
        self.demo_win.titlebar._height = height
        self.demo_win.titlebar.apply_theme_colors()
        self.demo_win.titlebar.rebuild_layout()
        self.demo_win.update_style()
        
        # Central contents dashboard for YOLO Detection mock
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 25, 30, 25)
        content_layout.setSpacing(15)
        
        title_font = QFont("Microsoft YaHei", 14, QFont.Bold)
        info_label = QLabel("🚀 独立自定义无边框窗口示例")
        info_label.setFont(title_font)
        
        # Select title color based on preset theme
        title_color = "#ffffff" if preset in ["ida", "sunlogin", "soda", "antigravity"] else "#0f172a"
        info_label.setStyleSheet(f"color: {title_color};")
        
        desc_label = QLabel(
            f"<b>当前标题预设:</b> {preset}<br>"
            f"<b>窗体圆角半径:</b> {radius}px<br>"
            f"<b>高度大小:</b> {height}px<br>"
            f"<b>关闭处理行为:</b> {close_behavior}<br><br>"
            "💡 <b>核心交互提示:</b><br>"
            "• 拖拽顶部的自定义标题栏可以<b>移动</b>该无边框窗口。<br>"
            "• 双击顶部标题栏可以<b>最大化 / 还原</b>窗口大小。<br>"
            "• 将鼠标指针悬停在<b>窗口外沿四周及四角</b>，会显现大小缩放箭头，拖拽即可直接<b>调整窗口大小</b>。<br>"
            "• 窗体周围在无边框下自带高档<b>卡片式投影效果</b>，视觉十分丝滑！"
        )
        desc_color = "#94a3b8" if preset in ["ida", "sunlogin", "soda", "antigravity"] else "#475569"
        desc_label.setStyleSheet(f"font-size: 12px; line-height: 20px; color: {desc_color};")
        
        close_btn = MkButton("关闭该独立窗口", type="danger")
        close_btn.clicked.connect(self.demo_win.close)
        
        content_layout.addWidget(info_label, alignment=Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(desc_label, alignment=Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.demo_win.setCentralWidget(content)
        self.demo_win.resize(640, 420)
        self.demo_win.show()

class UploadGallery(QWidget):
    """文件上传组件展示页 (MkUpload)"""
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(25)
        
        title_font = QFont("Microsoft YaHei", 12, QFont.Bold)
        
        # Title & Desc
        label_title = QLabel("文件上传 (Upload)")
        label_title.setFont(title_font)
        layout.addWidget(label_title)
        
        desc = QLabel("支持拖拽文件和点击选择上传，内置文件类型限制、体积上限过滤以及美观的已选择文件列表。")
        desc.setStyleSheet("color: #64748b; font-size: 13px;")
        layout.addWidget(desc)
        
        # 1. Single File Upload
        label_single = QLabel("单文件上传 (Single File)")
        label_single.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        layout.addWidget(label_single)
        
        self.upload_single = MkUpload(multiple=False, max_size_mb=10, tip_text="支持任意单文件，文件体积不超过 10MB")
        layout.addWidget(self.upload_single)
        
        # 2. Image-only Multi-file Upload
        label_multi_img = QLabel("图片多选上传 (Image Files Only)")
        label_multi_img.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        layout.addWidget(label_multi_img)
        
        self.upload_images = MkUpload(
            multiple=True, 
            accept_filters=["*.png", "*.jpg", "*.jpeg", "*.gif"], 
            max_size_mb=5, 
            tip_text="仅支持图片格式 (png, jpg, jpeg, gif)，单个不超过 5MB"
        )
        layout.addWidget(self.upload_images)
        
        # Log Box to display drop/upload logs
        label_logs = QLabel("上传操作日志 (Interaction Logs)")
        label_logs.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        layout.addWidget(label_logs)
        
        self.log_area = QLabel("等待上传交互...")
        self.log_area.setStyleSheet("""
            QLabel {
                background-color: #f1f5f9;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 10px;
                font-family: Consolas;
                font-size: 11px;
                color: #334155;
            }
        """)
        layout.addWidget(self.log_area)
        
        # Connect signals to update log box
        self.upload_single.filesSelected.connect(self._on_single_selected)
        self.upload_images.filesSelected.connect(self._on_images_selected)
        self.upload_single.fileRemoved.connect(lambda f: self._on_file_removed("单文件", f))
        self.upload_images.fileRemoved.connect(lambda f: self._on_file_removed("图片列表", f))
        
        layout.addStretch()

    def _on_single_selected(self, files):
        if files:
            self.log_area.setText(f"[单文件已选择]: {files[0]}")
        else:
            self.log_area.setText("[单文件已选择]: 无")
            
    def _on_images_selected(self, files):
        files_str = "\n  - ".join(files)
        self.log_area.setText(f"[多图已选择 ({len(files)}个)]:\n  - {files_str}" if files else "[多图已选择]: 无")
        
    def _on_file_removed(self, category, file_path):
        self.log_area.setText(f"[{category} 移除了文件]: {os.path.basename(file_path)}")

class MainGallery(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MonkeyUI - Enterprise Gallery")
        self.resize(900, 600)
        self.setStyleSheet("background-color: #ffffff;")
        
        # 主布局是水平的：左侧侧边栏，右侧内容区
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- 1. 初始化侧边栏 ---
        self.sidebar = MkMenu()
        
        # 添加带图标的菜单 (这里省略了真实的 QIcon，用文字代替演示层级)
        sub_basic = self.sidebar.add_submenu("🎯 基础组件")
        self.sidebar.add_submenu_item(sub_basic, "btn", "Button 按钮")
        self.sidebar.add_submenu_item(sub_basic, "chk", "CheckBox 复选框")
        
        sub_nav = self.sidebar.add_submenu("🧭 导航")
        self.sidebar.add_submenu_item(sub_nav, "sidebar", "侧边导航")
        self.sidebar.add_submenu_item(sub_nav, "topbar", "顶部导航栏")
        self.sidebar.add_submenu_item(sub_nav, "navmisc", "面包屑与标签页等")
        
        sub_form = self.sidebar.add_submenu("📝 表单组件")
        self.sidebar.add_submenu_item(sub_form, "form", "开关、滑块与日期")
        self.sidebar.add_submenu_item(sub_form, "authscreen", "Auth 登录与注册")
        self.sidebar.add_submenu_item(sub_form, "upload", "Upload 上传组件")
        
        sub_data = self.sidebar.add_submenu("📊 数据展示")
        self.sidebar.add_submenu_item(sub_data, "data", "头像与表格")
        self.sidebar.add_submenu_item(sub_data, "datatable", "DataTable 数据表格")
        self.sidebar.add_submenu_item(sub_data, "image_compare", "图像对比 Slider")
        self.sidebar.add_submenu_item(sub_data, "image_split", "图像分屏 Split")
        
        sub_feedback = self.sidebar.add_submenu("💬 反馈组件")
        self.sidebar.add_submenu_item(sub_feedback, "feedback", "信息提示与进度")
        
        sub_layout = self.sidebar.add_submenu("🪟 窗口与布局")
        self.sidebar.add_submenu_item(sub_layout, "window", "Window 自定义窗口")
        
        self.sidebar.add_item("collapse", "🔄 折叠/展开侧边栏")
        
        main_layout.addWidget(self.sidebar)
        
        # --- 2. 初始化右侧的内容区 (使用 QStackedWidget 进行页面切换) ---
        self.content_area = QStackedWidget()
        
        self.page_button = ButtonGallery()
        self.page_checkbox = CheckboxGallery()
        self.page_topbar = TopbarGallery()
        self.page_navmisc = NavMiscGallery()
        self.page_feedback = FeedbackGallery()
        self.page_form = FormGallery()
        self.page_auth = AuthGallery()
        self.page_data = DataGallery()
        self.page_datatable = DataTableGallery()
        self.page_image_compare = ImageCompareGallery()
        self.page_image_split = ImageSplitGallery()
        self.page_window = WindowGallery()
        self.page_upload = UploadGallery()
        self.page_empty = QWidget()
        
        self.content_area.addWidget(self.page_button)
        self.content_area.addWidget(self.page_checkbox)
        self.content_area.addWidget(self.page_topbar)
        self.content_area.addWidget(self.page_navmisc)
        self.content_area.addWidget(self.page_feedback)
        self.content_area.addWidget(self.page_form)
        self.content_area.addWidget(self.page_auth)
        self.content_area.addWidget(self.page_data)
        self.content_area.addWidget(self.page_datatable)
        self.content_area.addWidget(self.page_image_compare)
        self.content_area.addWidget(self.page_image_split)
        self.content_area.addWidget(self.page_window)
        self.content_area.addWidget(self.page_upload)
        self.content_area.addWidget(self.page_empty)
        
        main_layout.addWidget(self.content_area, stretch=1)
        
        # --- 3. 信号与槽的连接 ---
        self.sidebar.itemClicked.connect(self.switch_page)
        
        # 默认选中第一项
        self.sidebar.set_active("btn")
        self.switch_page("btn")

    def switch_page(self, item_id):
        # 演示侧边栏收缩
        if item_id == "collapse":
            self.sidebar.toggle_collapse()
            return
            
        # 根据当前页面设置内容区域的 padding
        # 比如 topbar 需要占满全屏演示效果，不需要外边距
        if item_id == "topbar":
            self.content_area.setContentsMargins(0, 0, 0, 0)
        else:
            self.content_area.setContentsMargins(30, 30, 30, 30)

        if item_id == "btn":
            self.content_area.setCurrentWidget(self.page_button)
        elif item_id == "chk":
            self.content_area.setCurrentWidget(self.page_checkbox)
        elif item_id == "topbar":
            self.content_area.setCurrentWidget(self.page_topbar)
        elif item_id == "navmisc":
            self.content_area.setCurrentWidget(self.page_navmisc)
        elif item_id == "feedback":
            self.content_area.setCurrentWidget(self.page_feedback)
        elif item_id == "form":
            self.content_area.setCurrentWidget(self.page_form)
        elif item_id == "authscreen":
            self.content_area.setCurrentWidget(self.page_auth)
        elif item_id == "data":
            self.content_area.setCurrentWidget(self.page_data)
        elif item_id == "datatable":
            self.content_area.setCurrentWidget(self.page_datatable)
        elif item_id == "image_compare":
            self.content_area.setCurrentWidget(self.page_image_compare)
        elif item_id == "image_split":
            self.content_area.setCurrentWidget(self.page_image_split)
        elif item_id == "window":
            self.content_area.setCurrentWidget(self.page_window)
        elif item_id == "upload":
            self.content_area.setCurrentWidget(self.page_upload)
        else:
            self.content_area.setCurrentWidget(self.page_empty)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainGallery()
    window.show()
    sys.exit(app.exec())
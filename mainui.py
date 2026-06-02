# -*- coding: utf-8 -*- 
""" 
@Auth ：落花不写码 
@File ：mainui.py 
@Motto :学习新思想，争做新青年 
""" 
import sys 
import os
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QStackedWidget
from PySide6.QtCore import Qt
from monkeyui import MkButton, MkAlert, MkSwitch, MkSlider, MkMenu, MkImageCompare


class QuickStartApp(QWidget): 
    def __init__(self): 
        super().__init__() 
        self.setWindowTitle("MonkeyUI 企业级侧边栏布局")
        # --- 创建主布局（左右结构） ---
        # 使用 QHBoxLayout（水平布局）
        # 左侧放侧边栏(MkMenu)，右侧放内容区(QStackedWidget)
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)  # 去掉窗口周围的空白边距
        self.main_layout.setSpacing(0)                  # 去掉组件之间的空隙

        # --- 创建并配置侧边栏 ---
        # 传入标题、图标和收缩模式
        self.sidebar = MkMenu(title="测试系统", collapse_mode="hamburger")
        
        # 给侧边栏添加菜单项
        self.sidebar.add_item("home", "首页控制台", icon="house")
        self.sidebar.add_item("data", "数据中心", icon="chart-bar")
        self.sidebar.add_item("settings", "系统设置", icon="gear")
        
        # 将侧边栏加入到主布局的左侧
        self.main_layout.addWidget(self.sidebar)

        # --- 3. 创建右侧整体容器（上下结构） ---
        self.right_widget = QWidget()
        self.right_layout = QVBoxLayout(self.right_widget)
        self.right_layout.setContentsMargins(20, 20, 20, 20) # 给右侧内容留出舒服的边距
        self.right_layout.setSpacing(20)
        self.right_widget.setStyleSheet("background-color: #f5f7fa;")

        # --- 3.1 底部放置主体内容区 (QStackedWidget) ---
        self.content_area = QStackedWidget()

        # 创建对应的测试页面
        self.page_home = self._create_placeholder_page("这里是首页控制台的内容", "#409eff")
        self.page_data = self._create_image_compare_page()  # 图像对比中心页面
        self.page_settings = self._create_placeholder_page("这里是系统设置的内容", "#e6a23c")

        # 将页面加入到堆叠内容区中
        self.content_area.addWidget(self.page_home)
        self.content_area.addWidget(self.page_data)
        self.content_area.addWidget(self.page_settings)

        # 将堆叠内容区加入到右侧垂直布局中
        self.right_layout.addWidget(self.content_area, stretch=1)

        # 最后，将整个右侧容器加入到主布局的右侧
        self.main_layout.addWidget(self.right_widget, stretch=1)

        # --- 4. 连接信号，实现点击侧边栏切换页面 ---
        self.sidebar.itemClicked.connect(self.on_menu_clicked)
        
        # 默认选中第一项
        self.sidebar.set_active("home")

    def on_menu_clicked(self, item_id):
        """当侧边栏菜单项被点击时触发的函数"""
        # 1. 切换页面内容
        if item_id == "home":
            self.content_area.setCurrentWidget(self.page_home)
        elif item_id == "data":
            self.content_area.setCurrentWidget(self.page_data)
        elif item_id == "settings":
            self.content_area.setCurrentWidget(self.page_settings)

    def _create_image_compare_page(self):
        """创建一个集成了图片对比组件的页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 页面标题
        title_label = QLabel("图像修复与对比中心")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #303133;")
        layout.addWidget(title_label)
        
        desc_label = QLabel("通过拖拽中央滑条，直观对比深度学习模型的输入（原图）与输出（修复结果）细节。")
        desc_label.setStyleSheet("font-size: 13px; color: #909399;")
        layout.addWidget(desc_label)
        
        # 获取图片的绝对路径，确保在不同目录下运行均可加载
        base_dir = os.path.dirname(os.path.abspath(__file__))
        before_path = os.path.join(base_dir, "test_images", "out.png")
        after_path = os.path.join(base_dir, "test_images", "input.png")
        
        # 实例化图片对比组件并配置标签
        compare_widget = MkImageCompare(before_path, after_path)
        # 限制最小尺寸，防止被压缩得太小
        compare_widget.setMinimumSize(400, 300)
        # 限制最大尺寸，防止过度放大
        compare_widget.setMaximumSize(800, 600)

        compare_widget.set_labels("修复结果", "原图")
        
        layout.addWidget(compare_widget, stretch=1)
        return page

    def _create_placeholder_page(self, text, color):
        """辅助函数：用于创建一个简单的占位页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        label = QLabel(text)
        label.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: bold;")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        return page

if __name__ == "__main__": 
    app = QApplication(sys.argv) 
    window = QuickStartApp() 
    window.show() 
    sys.exit(app.exec()) 

import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt

from monkeyqt import MkButton, MkAlert, MkSwitch, MkSlider

class QuickStartApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MonkeyQt 快速开始示例")
        self.resize(400, 300)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # 1. 警告提示 (Alert)
        alert = MkAlert(
            title="安装成功！", 
            description="恭喜你，你已经成功将 MonkeyQt 作为第三方包导入并运行了！",
            mk_type="success", 
            show_icon=True
        )
        layout.addWidget(alert)
        
        # 2. 按钮组件 (Button)
        btn_layout = QHBoxLayout()
        btn1 = MkButton("主要按钮", type="primary")
        btn2 = MkButton("成功按钮", type="success", size="large")
        btn_layout.addWidget(btn1)
        btn_layout.addWidget(btn2)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # 3. 开关与滑块 (Form)
        form_layout = QHBoxLayout()
        form_layout.addWidget(QLabel("深色模式:"))
        form_layout.addWidget(MkSwitch(checked=False))
        form_layout.addSpacing(20)
        form_layout.addWidget(QLabel("音量:"))
        
        slider = MkSlider(Qt.Horizontal)
        slider.setRange(0, 100)
        slider.setValue(50)
        form_layout.addWidget(slider)
        
        layout.addLayout(form_layout)
        
        layout.addStretch()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QuickStartApp()
    window.show()
    sys.exit(app.exec())

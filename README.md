# MonkeyQt

MonkeyQt 是一个专为 PySide6 打造的**企业级 UI 组件库**。设计灵感来源于前端极其流行的 Element Plus、shadcn-ui，为桌面应用程序开发者提供极高颜值、一致交互、并且开箱即用的 Web 风格组件。

## ✨ 特性

- **现代化风格**：复刻流行的前端组件。
- **组件丰富**：支持按钮、复选框、下拉菜单、表格、时间选择器、导航栏、分页器、进度条、滑块等丰富组件。
- **开箱即用**：一键导入即可使用，极其简单。
- **无缝集成**：纯 PySide6 原生实现（QWidget、QSS、QPainter），不依赖任何第三方重量级渲染引擎。

## 📦 安装

在正式发布到 PyPI 之前，你可以在本地将本项目作为开发者包进行安装：

```bash
# 1. 进入 MonkeyQt 根目录
cd MonkeyQt

# 2. 使用 pip 以可编辑模式安装 (-e 参数代表可编辑，你修改源码会立即生效)
pip install -e .
```

## 🚀 快速开始

一旦安装完成，你在电脑上的任何 Python 脚本中都可以直接 `import monkeyqt` 来使用它了，不需要再手动把路径加入 `sys.path`。

新建一个 `main.py` 测试：

```python
import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout
# 极简引入
from monkeyqt import MkButton, MkAlert

class MyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MonkeyQt 快速开始")
        self.resize(400, 300)
        
        layout = QVBoxLayout(self)
        
        # 1. 警告提示组件
        alert = MkAlert(title="欢迎使用 MonkeyQt", mk_type="success", show_icon=True)
        layout.addWidget(alert)
        
        # 2. 按钮组件
        btn = MkButton("主要按钮", type="primary")
        btn.clicked.connect(lambda: print("MonkeyQt is awesome!"))
        layout.addWidget(btn)
        
        layout.addStretch()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec())
```


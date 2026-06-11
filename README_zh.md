# MonkeyQt

[English](./README.md) | 简体中文

MonkeyQt 是一个专为 PySide6 打造的**企业级 UI 组件库**。设计灵感来源于前端极其流行的 Element Plus、shadcn-ui，为桌面应用程序开发者提供极高颜值、一致交互、并且开箱即用的 Web 风格组件。

📖 **[在线使用文档](https://luohuabuxiema.github.io/MonkeyQt/)** | 🚀 **[快速开始](#🚀-快速开始)** | 🎨 **[主题预览](https://luohuabuxiema.github.io/MonkeyQt/guide/theme/)**

## ✨ 特性

- **现代化风格**：复刻流行的前端组件。
- **组件丰富**：支持按钮、复选框、下拉菜单、表格、时间选择器、导航栏、分页器、进度条、滑块等丰富组件。
- **开箱即用**：一键导入即可使用，极其简单。
- **无缝集成**：纯 PySide6 原生实现（QWidget、QSS、QPainter），不依赖任何第三方重量级渲染引擎。

## 📖 使用文档

你可以通过以下链接访问我们的完整使用指南、主题样式预览以及所有组件的使用手册：

👉 **[MonkeyQt 官方使用文档](https://luohuabuxiema.github.io/MonkeyQt/)**

文档内包含：
- **安装与配置指南**
- **快速开始范例**
- **67 种内置设计风格（主题样式）的滑动切换与定制 API**
- **所有基础/高级组件开发预览与参数详解（包括 MkButton、MkDataTable、MkAuthScreen、MkUpload、MkImageCompare 等）**

## 📦 安装

你可以直接从 PyPI 安装官方发布版本（推荐）：

```bash
pip install monkeyqt
```

### 从源码安装（开发模式）

如果你需要修改源码或贡献代码：

```bash
# 1. 进入 MonkeyQt 根目录
cd MonkeyQt

# 2. 使用 pip 以可编辑模式安装
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

# MonkeyQt

English | [简体中文](./README_zh.md)

MonkeyQt is an enterprise-grade UI component library tailored for **PySide6**. Inspired by highly popular web frontend frameworks like Element Plus and shadcn-ui, it provides desktop application developers with highly aesthetic, consistent interactions, and out-of-the-box web-style components.

📖 **[Online Documentation](https://luohuabuxiema.github.io/MonkeyQt/)** | 🚀 **[Quick Start](#🚀-quick-start)** | 🎨 **[Theme Preview](https://luohuabuxiema.github.io/MonkeyQt/guide/theme/)**

## ✨ Features

- **Modern Style**: Replicates popular web frontend components and design systems.
- **Rich Components**: Supports buttons, checkboxes, dropdowns, tables, date pickers, topbars, pagination, progress bars, sliders, and other rich components.
- **Out-of-the-box**: One-click import for extremely simple usage.
- **Seamless Integration**: Built entirely with native PySide6 (QWidget, QSS, QPainter), with no dependencies on third-party heavy rendering engines.

## 📖 Documentation

You can access our complete usage guide, theme style preview, and all component manuals via the following link:

👉 **[Official MonkeyQt Documentation](https://luohuabuxiema.github.io/MonkeyQt/)**

The documentation includes:
- **Installation & Configuration Guide**
- **Quick Start Examples**
- **67 Built-in Design Styles (Themes) with Smooth Sliding Switching & Customization APIs**
- **Detailed Development Previews & Parameters for all basic/advanced components (including MkButton, MkDataTable, MkAuthScreen, MkUpload, MkImageCompare, etc.)**

## 📦 Installation

You can install the official release directly from PyPI:

```bash
pip install monkeyqt
```

### Installation from Source (Development Mode)

If you want to modify the source code or contribute:

```bash
# 1. Clone the repository
git clone https://github.com/luohuabuxiema/MonkeyQt.git
cd MonkeyQt

# 2. Install in editable mode
pip install -e .
```

## 🚀 Quick Start

Once the installation is complete, you can directly `import monkeyqt` in any Python script on your computer without manually adding paths to `sys.path`.

Create a new `main.py` to test:

```python
import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout
# Simple import
from monkeyqt import MkButton, MkAlert

class MyApp(QWidget):
      def __init__(self):
          super().__init__()
          self.setWindowTitle("MonkeyQt Quick Start")
          self.resize(400, 300)
          
          layout = QVBoxLayout(self)
          
          # 1. Alert component
          alert = MkAlert(title="Welcome to MonkeyQt", mk_type="success", show_icon=True)
          layout.addWidget(alert)
          
          # 2. Button component
          btn = MkButton("Primary Button", type="primary")
          btn.clicked.connect(lambda: print("MonkeyQt is awesome!"))
          layout.addWidget(btn)
          
          layout.addStretch()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec())
```

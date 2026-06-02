import os
import sys

def create_component(category: str, name: str):
    """
    用法: python scripts/create_component.py navigation breadcrumb
    """
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'monkeyui', 'components'))
    cat_dir = os.path.join(base_dir, category)
    
    if not os.path.exists(cat_dir):
        os.makedirs(cat_dir)
        with open(os.path.join(cat_dir, '__init__.py'), 'w') as f:
            pass

    class_name = f"Mk{name.capitalize()}"
    file_path = os.path.join(cat_dir, f"{name.lower()}.py")
    
    if os.path.exists(file_path):
        print(f"❌ 组件 {class_name} 已存在!")
        return

    template = f"""from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Property

class {class_name}(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        
    def _init_ui(self):
        pass
"""
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(template)
        
    try:
        print(f"✅ 成功创建组件: {class_name} -> {file_path}")
    except UnicodeEncodeError:
        print(f"Success create component: {class_name} -> {file_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("用法: python create_component.py <类别> <组件名>\n示例: python create_component.py form input")
        sys.exit(1)
    create_component(sys.argv[1], sys.argv[2])

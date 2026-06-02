import os
from pathlib import Path

class ThemeManager:
    """全局主题管理器，负责解析 QSS 变量并注入"""
    
    # 定义一套全局的 Design Token (类似前端的 CSS 变量)
    TOKENS = {
        "light": {
            "--primary-color": "#409eff",
            "--primary-hover": "#66b1ff",
            "--success-color": "#67c23a",
            "--bg-color": "#ffffff",
            "--border-color": "#dcdfe6",
            "--text-color": "#606266",
            "--radius": "4px"
        },
        "dark": {
            "--primary-color": "#337ecc",
            "--primary-hover": "#409eff",
            "--success-color": "#529b2e",
            "--bg-color": "#141414",
            "--border-color": "#4c4d4f",
            "--text-color": "#E4E7ED",
            "--radius": "4px"
        }
    }

    @classmethod
    def load_qss(cls, qss_path: Path, theme: str = "light") -> str:
        """读取 QSS 文件，并替换其中的主题变量"""
        if not qss_path.exists():
            return ""
            
        with open(qss_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # 动态替换变量
        tokens = cls.TOKENS.get(theme, cls.TOKENS["light"])
        for key, value in tokens.items():
            content = content.replace(f"var({key})", value)
            
        return content

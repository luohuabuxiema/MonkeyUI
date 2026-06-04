from PySide6.QtWidgets import QCheckBox, QWidget
from PySide6.QtCore import Property, Qt
from monkeyqt.common.enums import MkSize

class MkCheckBox(QCheckBox):
    """
    MkCheckBox 组件
    对标 Element Plus 的 Checkbox，支持自定义尺寸和现代化的选中动画（通过 QSS）。
    """
    
    def __init__(self, text="", parent=None, size=MkSize.DEFAULT.value):
        # 兼容 Qt Designer
        if isinstance(text, QWidget):
            parent = text
            text = ""
            
        super().__init__(text, parent)
        
        self._mk_size = size
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self._apply_style()

    def _apply_style(self):
        """注入 Element Plus 风格的 QSS 样式"""
        self.setStyleSheet("""
            /* 基础样式与文本颜色 */
            MkCheckBox {
                font-family: "Helvetica Neue", Helvetica, "PingFang SC", "Microsoft YaHei", Arial, sans-serif;
                color: #606266;
                spacing: 8px; /* 框与文字的间距 */
                outline: none;
            }
            MkCheckBox:hover {
                color: #409eff;
            }
            MkCheckBox:disabled {
                color: #c0c4cc;
            }

            /* 自定义勾选框 (Indicator) */
            MkCheckBox::indicator {
                width: 14px;
                height: 14px;
                background-color: #ffffff;
                border: 1px solid #dcdfe6;
                border-radius: 2px;
                transition: border-color .25s cubic-bezier(.71,-.46,.29,1.46),background-color .25s cubic-bezier(.71,-.46,.29,1.46);
            }

            /* 悬浮时的框边框变蓝 */
            MkCheckBox::indicator:hover {
                border-color: #409eff;
            }

            /* 选中状态 */
            MkCheckBox::indicator:checked {
                background-color: #409eff;
                border-color: #409eff;
                /* Qt 的 QSS 不支持绘制复杂的 SVG，这里我们用一个 unicode 字符模拟对号，或者依赖背景图。
                   为保持纯代码，我们先利用自带的选中样式或后续加载本地 svg */
                image: url(none); /* 阻止原生丑陋渲染 */
            }
            
            /* 禁用状态 */
            MkCheckBox::indicator:disabled {
                background-color: #edf2fc;
                border-color: #dcdfe6;
            }
            MkCheckBox::indicator:checked:disabled {
                background-color: #a0cfff;
                border-color: #a0cfff;
            }

            /* --- 尺寸控制 --- */
            MkCheckBox[mk_size="large"] {
                font-size: 14px;
                height: 40px;
            }
            MkCheckBox[mk_size="large"]::indicator {
                width: 16px;
                height: 16px;
            }
            
            MkCheckBox[mk_size="default"] {
                font-size: 14px;
                height: 32px;
            }
            
            MkCheckBox[mk_size="small"] {
                font-size: 12px;
                height: 24px;
            }
            MkCheckBox[mk_size="small"]::indicator {
                width: 12px;
                height: 12px;
            }
        """)

    # --- 暴露属性 ---
    @Property(str)
    def mk_size(self):
        return self._mk_size

    @mk_size.setter
    def mk_size(self, value):
        if self._mk_size == value:
            return
        self._mk_size = value
        self.setProperty("mk_size", value)
        self.style().unpolish(self)
        self.style().polish(self)

from PySide6.QtWidgets import QPushButton, QWidget
from PySide6.QtCore import Property, Qt
from monkeyui.common.enums import MkType, MkSize

class MkButton(QPushButton):
    """MkButton 组件"""
    
    def __init__(self, text="", parent=None, type=MkType.DEFAULT.value, size=MkSize.DEFAULT.value):
        # 兼容 Qt Designer (它实例化时会将 parent 传给第一个参数)
        if isinstance(text, QWidget):
            parent = text
            text = ""
            
        super().__init__(text, parent)
        
        self._mk_type = type
        self._mk_size = size
        
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 实际开发中，这里应该调用 ThemeManager 加载 QSS
        # 以下是完整的 Element Plus 风格按钮样式
        self.setStyleSheet("""
            /* Default 基础样式 */
            MkButton {
                border-radius: 4px;
                font-family: "Helvetica Neue", Helvetica, "PingFang SC", "Microsoft YaHei", Arial, sans-serif;
                font-weight: 500;
                border: 1px solid #dcdfe6;
                background-color: #ffffff;
                color: #606266;
                outline: none;
            }
            MkButton:hover {
                color: #409eff;
                border-color: #c6e2ff;
                background-color: #ecf5ff;
            }
            MkButton:pressed {
                color: #3a8ee6;
                border-color: #3a8ee6;
                outline: none;
            }
            MkButton:disabled {
                color: #c0c4cc;
                background-color: #ffffff;
                border-color: #ebeef5;
            }

            /* Primary */
            MkButton[mk_type="primary"] {
                color: #ffffff;
                background-color: #409eff;
                border-color: #409eff;
            }
            MkButton[mk_type="primary"]:hover {
                background-color: #66b1ff;
                border-color: #66b1ff;
            }
            MkButton[mk_type="primary"]:pressed {
                background-color: #3a8ee6;
                border-color: #3a8ee6;
            }
            MkButton[mk_type="primary"]:disabled {
                color: #ffffff;
                background-color: #a0cfff;
                border-color: #a0cfff;
            }

            /* Success */
            MkButton[mk_type="success"] {
                color: #ffffff;
                background-color: #67c23a;
                border-color: #67c23a;
            }
            MkButton[mk_type="success"]:hover {
                background-color: #85ce61;
                border-color: #85ce61;
            }
            MkButton[mk_type="success"]:pressed {
                background-color: #5daf34;
                border-color: #5daf34;
            }
            MkButton[mk_type="success"]:disabled {
                color: #ffffff;
                background-color: #b3e19d;
                border-color: #b3e19d;
            }

            /* Warning */
            MkButton[mk_type="warning"] {
                color: #ffffff;
                background-color: #e6a23c;
                border-color: #e6a23c;
            }
            MkButton[mk_type="warning"]:hover {
                background-color: #ebb563;
                border-color: #ebb563;
            }
            MkButton[mk_type="warning"]:pressed {
                background-color: #cf9236;
                border-color: #cf9236;
            }
            MkButton[mk_type="warning"]:disabled {
                color: #ffffff;
                background-color: #f3d19e;
                border-color: #f3d19e;
            }

            /* Danger */
            MkButton[mk_type="danger"] {
                color: #ffffff;
                background-color: #f56c6c;
                border-color: #f56c6c;
            }
            MkButton[mk_type="danger"]:hover {
                background-color: #f78989;
                border-color: #f78989;
            }
            MkButton[mk_type="danger"]:pressed {
                background-color: #dd6161;
                border-color: #dd6161;
            }
            MkButton[mk_type="danger"]:disabled {
                color: #ffffff;
                background-color: #fab6b6;
                border-color: #fab6b6;
            }

            /* Info */
            MkButton[mk_type="info"] {
                color: #ffffff;
                background-color: #909399;
                border-color: #909399;
            }
            MkButton[mk_type="info"]:hover {
                background-color: #a6a9ad;
                border-color: #a6a9ad;
            }
            MkButton[mk_type="info"]:pressed {
                background-color: #82848a;
                border-color: #82848a;
            }
            MkButton[mk_type="info"]:disabled {
                color: #ffffff;
                background-color: #c8c9cc;
                border-color: #c8c9cc;
            }

            /* 尺寸 Sizes */
            MkButton[mk_size="large"] {
                padding: 12px 19px;
                font-size: 14px;
            }
            MkButton[mk_size="default"] {
                padding: 8px 15px;
                font-size: 14px;
            }
            MkButton[mk_size="small"] {
                padding: 5px 11px;
                font-size: 12px;
                border-radius: 3px;
            }
        """)

    # 暴露给 Qt Designer 的右侧属性面板
    @Property(str)
    def mk_type(self):
        return self._mk_type

    @mk_type.setter
    def mk_type(self, value):
        if self._mk_type == value:
            return
        self._mk_type = value
        self.setProperty("mk_type", value)
        self.style().unpolish(self)
        self.style().polish(self)

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

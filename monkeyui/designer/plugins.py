from PySide6.QtDesigner import QPyDesignerCustomWidgetPlugin
from PySide6.QtGui import QIcon
from monkeyui.components.basic.button import MkButton

class MkButtonPlugin(QPyDesignerCustomWidgetPlugin):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initialized = False

    def initialize(self, core):
        if self.initialized: return
        self.initialized = True

    def isInitialized(self): return self.initialized
    def createWidget(self, parent): return MkButton(parent)
    def name(self): return "MkButton"
    def group(self): return "MonkeyUI Basic" # 在 Designer 左侧的分类名
    def icon(self): return QIcon()
    def toolTip(self): return "MonkeyUI Button"
    def whatsThis(self): return "MonkeyUI Button"
    def isContainer(self): return False
    def domXml(self):
        return '<widget class="MkButton" name="mkButton">\n</widget>\n'
    def includeFile(self): return "monkeyui.components.basic.button"

import sys
from PySide6.QtWidgets import QApplication
from mainui import QuickStartApp

app = QApplication(sys.argv)
window = QuickStartApp()
window.show()

# Dump geometries
def dump_geo():
    sidebar = window.sidebar
    print("hamburger_btn geometry:", sidebar.hamburger_btn.geometry())
    print("hamburger_btn pos:", sidebar.hamburger_btn.mapTo(sidebar, sidebar.hamburger_btn.rect().topLeft()))
    print("title_label pos:", sidebar.title_label.mapTo(sidebar, sidebar.title_label.rect().topLeft()))
    
    item = sidebar._all_items[0] # home
    print("item geometry:", item.geometry())
    print("item pos:", item.mapTo(sidebar, item.rect().topLeft()))
    print("icon_label pos:", item.icon_label.mapTo(sidebar, item.icon_label.rect().topLeft()))
    print("text_label pos:", item.text_label.mapTo(sidebar, item.text_label.rect().topLeft()))

from PySide6.QtCore import QTimer
QTimer.singleShot(1000, dump_geo)
QTimer.singleShot(1500, app.quit)

app.exec()

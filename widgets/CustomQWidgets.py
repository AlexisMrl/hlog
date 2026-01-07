
from PyQt5.QtWidgets import QTabWidget, QTabBar
from PyQt5.QtCore import Qt

class MiddleClickTabBar(QTabBar):
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            index = self.tabAt(event.pos())
            if index >= 0:
                self.parent().removeTab(index)
        else:
            super().mouseReleaseEvent(event)

class CustomTabWidget(QTabWidget):
    def __init__(self, main_view):
        super().__init__()
        self.main_view = main_view
        self.setTabBar(MiddleClickTabBar())
        self.setTabsClosable(True)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        print(event.mimeData().hasUrls())
        if event.mimeData().hasUrls(): event.accept()
        else: event.ignore()

    def dropEvent(self, event):
        self.main_view.dropEvent(event)

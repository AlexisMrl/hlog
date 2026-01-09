
from PyQt5.QtWidgets import QTabWidget, QTabBar
from PyQt5.QtCore import Qt

class MiddleClickTabBar(QTabBar):
    def __init__(self, parent=None):
        super().__init__(parent)

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
        #self.setTabsClosable(True)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): 
            event.acceptProposedAction()
        else: event.ignore()

    def dropEvent(self, event):
        shift = bool(event.keyboardModifiers() & Qt.ShiftModifier)
        self.main_view.onDrop(event, shift=shift)
        event.acceptProposedAction()
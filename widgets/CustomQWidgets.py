
from PyQt5.QtWidgets import QTabWidget, QTabBar, QMenu, QApplication
from PyQt5.QtCore import Qt

class MiddleClickTabBar(QTabBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.clipboard = QApplication.clipboard()

    def mouseReleaseEvent(self, event):
        index = self.tabAt(event.pos())
        if event.button() == Qt.MiddleButton:
            if index >= 0:
                self.parent().removeTab(index)

        elif event.button() == Qt.RightButton:
            if index >= 0:
                layout = self.parent().widget(index)
                
                menu = QMenu(self)

                menu.addAction("Copy path", lambda: self.clipboard.setText(layout.filepath))
                menu.addAction("Reload", layout.update_fn)

                menu.exec_(event.globalPos())

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
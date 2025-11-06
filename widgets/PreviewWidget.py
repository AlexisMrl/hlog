from PyQt5.QtWidgets import QLabel, QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

class PreviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.resize(150, 150)

    def show_preview(self, png_bytes, pos=None, size=150):
        pixmap = QPixmap()
        pixmap.loadFromData(png_bytes)
        if pixmap.isNull():
            return
        scaled = pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.label.setPixmap(scaled)
        self.resize(scaled.size())

        if pos:
            self.move(pos)
        else:
            self.move(50, 50)

        # Show without activating focus
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.show()
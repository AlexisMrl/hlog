from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt


class PreviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # parent is the parent splitter
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout(self)
        layout.addWidget(self.label)

    def showPng(self, png_bytes):
        src = QPixmap()
        src.loadFromData(png_bytes, "PNG")

        pixmap = QPixmap(self.label.size())
        pixmap.fill(Qt.transparent)

        pixmap = src.scaled(
            self.label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )

        self.label.setPixmap(pixmap)

    def clear(self):
        self.label.clear()

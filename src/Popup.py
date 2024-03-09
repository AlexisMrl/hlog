from PyQt5.QtWidgets import QMessageBox
from PyQt5 import QtGui
import traceback

class Popup:
    
    def _excToStr(self, exception):
        return "".join(traceback.format_tb(exception.__traceback__))
    
    def popError(self, win_type, title, message, details=None):
        msg = QMessageBox(win_type, title, message)
        msg.setWindowIcon(QtGui.QIcon("./resources/icon.png"))
        if details: msg.setDetailedText(details)
        msg.exec_()
    
    def popErrorExc(self, title, exception, message='', win_type_str='warning'):
        win_type = {'warning': QMessageBox.Warning,
                    'critical': QMessageBox.Critical,
                    'information': QMessageBox.Information,
                    'question': QMessageBox.Question}.get(win_type_str.lower(), QMessageBox.Critical)
        self.popError(win_type, title, message, self._excToStr(exception))
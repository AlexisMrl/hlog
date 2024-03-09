from PyQt5 import QtCore
from PyQt5.QtCore import QThread

class QuickThread(QThread):
    # a class to create a thread that runs a function
    # and then emits a signal when it is done
    # the function to run is passed as a parameter
    # the signal is emitted with the return value of the function

    def __init__(self, function, *args, **kwargs):
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.result = None

    def run(self):
        try:
            self.result = self.function(*self.args, **self.kwargs)
        except Exception as e:
            self.sig_error.emit(e)
        self.sig_finished.emit(self.result)

    sig_finished = QtCore.pyqtSignal(object)
    sig_error = QtCore.pyqtSignal(object)

    
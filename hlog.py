from PyQt5.QtWidgets import QApplication, QSplashScreen
from PyQt5.QtCore import QObject, Qt, pyqtSignal, QThread
from PyQt5.QtGui import QPixmap

import pyHegel.commands as c
import os, sys

from views.MainView import MainView
from src.ReadfileData import ReadfileData
from src.QuickThread import QuickThread
from src.Popup import Popup

class hlog(QObject):

    sig_fileOpened = pyqtSignal(ReadfileData, bool)

    def __init__(self, path:str, app:QApplication=None, file=None):
        super().__init__()
        self.app = app

        self.main_view = mv = MainView(self)
        self.pop = Popup()
        
        self.loading_thread = None
        self.current_data = None

        # SIGNALS ingoing from views
        mv.file_tree.sig_askOpenFile.connect(self.openFile)

        # SIGNALS outgoing
        self.sig_fileOpened.connect(mv.onFileOpened)

        # First exec:
        self.main_view.file_tree.changePath(path)
        #self.write(':)')
        if file: self.open_file(file)

    def openFile(self, path):
        self.main_view.write('Opening file: '+path)

        # ReadfileData in a thread
        # ReadfileData.from_filepath(path)
        self.loading_thread = QuickThread(ReadfileData.from_filepath, filepath=path)
        self.loading_thread.sig_finished.connect(self.onFileOpened)
        self.loading_thread.sig_error.connect(self.onFileOpenError)
        self.loading_thread.start()

        #else:
        #    self.main_view.write('File type not supported :(\n'+path)
        
    def onFileOpened(self, rfdata, fn_args, fn_kwargs):
        # called on thread success
        filepath = fn_kwargs.get("filepath")
        self.main_view.write('Successfully opened: '+filepath)
        self.rfdata = rfdata # DEBUG
        print(self.main_view.file_tree.new_tab_asked)
        self.sig_fileOpened.emit(rfdata, self.main_view.file_tree.new_tab_asked)
        self.main_view.file_tree.new_tab_asked = False
    
    def onFileOpenError(self, exception, fn_args, fn_kwargs):
        filepath = fn_kwargs.get("filepath")
        self.main_view.write('Could not open file: '+filepath)
        print(exception)

    def close(self):
        pass

if __name__ == '__main__':
    # Start with no arguments => current directory
    # Start with a directory => load in that directory
    # Start with a file => load that file, and set the directory to the directory above
    # arg --with-app => start with a QApplication (for standalone use)
    
    app = None
    path, file = os.getcwd(), None

    if '--with-app' in sys.argv:
        app = QApplication([])
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        app.setApplicationName('hlog')
        sys.argv.remove('--with-app')
    
    if len(sys.argv) > 1:
        if os.path.isdir(sys.argv[1]):
            path = sys.argv[1]
        elif os.path.isfile(sys.argv[1]):
            file = sys.argv[1]
            path = os.path.dirname(file)

    pixmap = QPixmap('./resources/icon.png')
    pixmap = pixmap.scaledToWidth(200, mode=Qt.SmoothTransformation)
    splash = QSplashScreen(pixmap)
    splash.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
    msg = 'Loading...' + '\n' + path
    splash.showMessage(msg, alignment=Qt.AlignBottom | Qt.AlignHCenter, color=Qt.white)
    splash.show()

    hl = hlog(path, app, file=file)
    splash.finish(hl.main_view)
    hl.main_view.show()

    if app is not None:
        sys.exit(app.exec_())

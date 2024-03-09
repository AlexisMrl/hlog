from PyQt5.QtWidgets import QApplication, QSplashScreen
from PyQt5.QtCore import QObject, Qt, pyqtSignal, QThread
from PyQt5.QtGui import QPixmap

import pyHegel.commands as c
import os, sys

from views.MainView import MainView
from widgets.FileTreeWidget import FileTreeWidget
from src.ReadfileData import ReadfileData
from src.QuickThread import QuickThread
from src.Popup import Popup

## V1: initialisation
# backend matplotlib
#x view 1d sweep
#x view 2d sweep map
#x some plot customisation: title, labels, colormap
#x open file in notepad
## V2: traitement update
#x filter data
#x draggable line with slope
# fix bug for reversed sweep
# v and h markers
# better draggable line
# export plotting code
# checkbox: ignore nan. for incomplete map
# log scale
# error messaeg on file open
## V3: random update:
# read csv files ?



class hlog(QObject):

    def __init__(self, path, app=None, file=None):
        super().__init__()
        self.path = path
        self.app = app

        self.file_tree = FileTreeWidget(self)
        self.window = MainView(self, self.file_tree.view)
        self.pop = Popup()
        self.cb = QApplication.clipboard()

        self.changePath(path)
        
        self.loading_thread = None
        self.current_data = None
        
        
        # SIGNALS outgoing
        self.sig_fileOpened.connect(self.window.onFileOpened)
        

        self.write(':)') # TODO: put a random quote
        if file: self.openFile(file)
    
    def write(self, text):
        self.window.statusBar().showMessage(text)
        self.window.graphic.write(text)

    def changePath(self, path):
        if not os.path.exists(path):
            self.write('Path does not exist: '+path)
            return
        self.file_tree.model.setRootPath(path)
        self.file_tree.view.setRootIndex(self.file_tree.model.index(path))
        self.path = path
        print('Path changed to:', path)
        
    sig_fileOpened = pyqtSignal(ReadfileData)
    def openFile(self, path):
        self.write('Opening file: '+path)

        if path[-3:]=='txt': 
            # readfile in a thread
            self.current_data = ReadfileData(path)
            self.loading_thread = QuickThread(self.current_data.readfile)
            self.loading_thread.sig_finished.connect(self.onFileOpened)
            self.loading_thread.sig_error.connect(self.onFileOpenError)
            self.loading_thread.start()

        else:
            self.write('File type not supported :(\n'+path)
        
    def onFileOpened(self):
        self.write('File opened: '+self.current_data.filepath)
        self.window.onFileOpened(self.current_data)
    
    def onFileOpenError(self, exception):
        msg = 'Could not open file: '+self.current_data.filepath
        self.write(msg)
        self.pop.popErrorExc('Error', exception, msg)
        


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
    splash.finish(hl.window)
    hl.window.show()

    if app is not None:
        sys.exit(app.exec_())
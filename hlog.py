from PyQt5.QtWidgets import QApplication, QSplashScreen
from PyQt5.QtCore import QObject, Qt, pyqtSignal, QThread
from PyQt5.QtGui import QPixmap

import pyHegel.commands as c
import os, sys

from views.MainView import MainView
from widgets.FileTreeWidget import FileTreeWidget
from widgets.PreviewWidget import PreviewWidget
from src.ReadfileData import ReadfileData
from src.QuickThread import QuickThread
from src.Popup import Popup
from src.Database import DBPlots

# tasks:
# v and h markers
# draggable lines
# checkbox: alternate
# checkbox: ignore nan. for incomplete map
# log scale on images



class hlog(QObject):

    def __init__(self, path:str, app:QApplication=None, file=None):
        super().__init__()
        self.path = path
        self.app = app

        self.file_tree = FileTreeWidget(self)
        self.main_view = MainView(self, self.file_tree.view)
        self.pop = Popup()
        self.cb = QApplication.clipboard()

        self.changePath(path)
        
        self.loading_thread = None
        self.current_data = None
        
        self.enable_previews = False
        self.db = DBPlots()
        self.previewer = PreviewWidget()

        # SIGNALS outgoing
        self.sig_fileOpened.connect(self.main_view.on_file_opened)
        self.sig_fileOpened.connect(self.previewer.on_file_opened)


        self.write(':)')
        if file: self.open_file(file)
    
    sig_fileOpened = pyqtSignal(ReadfileData)

    
    def write(self, text):
        self.main_view.statusBar().showMessage(text)
        self.main_view.current_graph().write(text)

    def changePath(self, path):
        if not os.path.exists(path):
            self.write('Path does not exist: '+path)
            return
        self.file_tree.model.setRootPath(path)
        self.file_tree.view.setRootIndex(self.file_tree.model.index(path))
        self.path = path
        print('Path changed to:', path)
        
    def open_file(self, path):
        self.write('Opening file: '+path)

        if path[-3:]=='txt': 
            # ReadfileData in a thread
            # ReadfileData.from_filepath(path)
            self.loading_thread = QuickThread(ReadfileData.from_filepath, filepath=path)
            self.loading_thread.sig_finished.connect(self.onFileOpened)
            self.loading_thread.sig_error.connect(self.onFileOpenError)
            self.loading_thread.start()

        else:
            self.write('File type not supported :(\n'+path)
        
    def onFileOpened(self, rfdata, fn_args, fn_kwargs):
        # called on thread success
        filepath = fn_kwargs.get("filepath")
        self.write('File opened: '+filepath)
        self.sig_fileOpened.emit(rfdata)
        
        if self.enable_previews:
            self.db.add_fig(self.current_data, self.main_view.graphic.figure)
    
    def onFileOpenError(self, exception, fn_args, fn_kwargs):
        filepath = fn_kwargs.get("filepath")
        self.write('Could not open file: '+filepath)
        print(exception)
    



    def askPreview(self, path, pos):
        if not self.enable_previews: return

        png = self.db.get_fig(path)
        if png:
            self.previewer.show_preview(png, pos)
        else:
            self.previewer.hide_preview()

    def togglePreview(self):
        if self.enable_previews: 
            self.previewer.hide_preview()
        self.enable_previews = not self.enable_previews
        text = f"preview "
        text += "on" if self.enable_previews else "off"
        self.main_view.statusBar().showMessage(text)

    #def close(self):
        #print("hi")
        #self.previewer.hide()
        #self.db.close()
        #self.main_view.close()

    def close(self):
        self.previewer.hide()

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

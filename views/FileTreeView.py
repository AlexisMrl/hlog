from PyQt5.QtWidgets import QWidget, QFileSystemModel, QTreeView, QMenu, QApplication
from PyQt5.QtGui import QKeyEvent, QPaintEvent
from PyQt5.QtCore import Qt, QProcess, QEvent, QPoint, pyqtSignal
import os

class FileTreeView(QWidget):
    
    sig_askOpenFile = pyqtSignal(str)

    def __init__(self, main_view):
        super().__init__()
        self.main_view = main_view
        self.clipboard = QApplication.clipboard()
        
        self.model = QFileSystemModel()
        self.view = QTreeView()
        self.view.setModel(self.model)

        self.new_tab_asked = False
        
        # arrange columns
        self.view.setColumnHidden(2, True) # hide type
        self.view.setColumnWidth(0, 300) # resize name
        
        # right click menu
        self.view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.view.customContextMenuRequested.connect(self.showContextMenu)    

        # key press
        self.view.keyPressEvent = self.onKeyPress

        self.view.doubleClicked.connect(self.askOpenFile)
        # on item changed
        self.view.selectionModel().currentChanged.connect(self.onItemChanged)


    def makeMenu(self, type):
        menu = QMenu()
        menu.addAction('Open in new tab', self.openInNewTab)
        menu.addAction('Copy path', self.copyPath)
        file_action = [
            ('Open in notepad', self.openInTE), 
            ('Read file', self.sig_askOpenFile.emit)
        ]
        dir_action = [
            ('Open', self.openDir)
        ]
        for action in file_action if type=='file' else dir_action:
            menu.addAction(action[0], action[1])
        menu.addSeparator()
        menu.addAction('Go up a dir', self.goUpDir)
        #menu.addAction('Open in file explorer', self.openInFE)
        expand_all_action = [('Expand all', self.view.expandAll), ('Collapse all', self.view.collapseAll)]
        for action in expand_all_action:
            menu.addAction(action[0], action[1])
        menu.addAction('Refresh', self.refresh)
        return menu

    def showContextMenu(self, pos):
        index = self.view.indexAt(pos)
        if not index.isValid():
            return
        # check if file or dir
        type = 'file' if not self.model.isDir(index) else 'dir'
        menu = self.makeMenu(type)
        
        menu.exec_(self.view.mapToGlobal(pos))
            
    def onKeyPress(self, event):
        key = event.key()
        modifiers = event.modifiers()

        # Enter or Space -> open file
        if key in (Qt.Key_Return, Qt.Key_Space):
            if modifiers & Qt.ShiftModifier:
                self.openInNewTab()
            else:
                self.askOpenFile()

        elif key == Qt.Key_H:
            self.view.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Left, Qt.NoModifier))
        elif key == Qt.Key_L:
            self.view.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Right, Qt.NoModifier))
        elif key == Qt.Key_J:
            steps = 5 if modifiers & Qt.ShiftModifier else 1
            for _ in range(steps):
                self.view.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Down, Qt.NoModifier))
        elif key == Qt.Key_K:
            steps = 5 if modifiers & Qt.ShiftModifier else 1
            for _ in range(steps):
                self.view.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Up, Qt.NoModifier))
        # g / Shift+G navigation
        elif key == Qt.Key_G:
            if modifiers & Qt.ShiftModifier:
                self.view.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_End, Qt.NoModifier))
            else:
                self.view.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Home, Qt.NoModifier))

        elif key == Qt.Key_W:
            if modifiers & Qt.ControlModifier:
                self.main_view.closeTab()

        elif (key == Qt.Key_Tab and modifiers & Qt.ControlModifier) or \
            (key == Qt.Key_Backtab and modifiers & Qt.ControlModifier):

            tabs = self.main_view.graphic_tabs
            n = tabs.count()
            if n == 0:
                return

            i = tabs.currentIndex()

            if key == Qt.Key_Backtab:
                tabs.setCurrentIndex((i - 1) % n)
            else:
                tabs.setCurrentIndex((i + 1) % n)
        else:
            QTreeView.keyPressEvent(self.view, event)

    def onItemChanged(self, current, previous):
        index = self.view.currentIndex()
        type = 'file' if not self.model.isDir(index) else 'dir'
        if type == "file":
            path = self.model.filePath(current)
            pass

    ### ACTIONS ###

    def askOpenFile(self, index=None):
        if not index:
            index = self.view.currentIndex()
        path = self.model.filePath(index)
        if not self.model.isDir(index):
            self.sig_askOpenFile.emit(path)
    
    def changePath(self, path):
        if not os.path.exists(path):
            self.main_view.write('Path does not exist: '+path)
            return
        self.model.setRootPath(path)
        self.view.setRootIndex(self.model.index(path))
        print('Path changed to:', path)

    def openInTE(self):
        # try to open in text editor
        index = self.view.currentIndex()
        path = self.model.filePath(index)
        try:
            process = QProcess()
            process.startDetached('notepad.exe', [path])
        except:
            self.main_view.write('Could not open in text editor: '+path)

    def openInNewTab(self):
        self.new_tab_asked = True
        self.askOpenFile()
    
    def goUpDir(self):
        path = self.model.filePath(self.view.rootIndex())
        path = os.path.dirname(path)
        self.changePath(path)

    def openDir(self):
        index = self.view.currentIndex()
        path = self.model.filePath(index)
        self.changePath(path)
        
    def copyPath(self):
        index = self.view.currentIndex()
        path = self.model.filePath(index)
        self.clipboard.setText(path)
    
    def refresh(self):
        path = self.model.filePath(self.view.rootIndex())
        self.model.setRootPath('')
        self.model.setRootPath(path)
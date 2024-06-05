from PyQt5.QtWidgets import QWidget, QFileSystemModel, QTreeView, QMenu
from PyQt5.QtCore import Qt, QProcess
import os

class FileTreeWidget(QWidget):
    
        def __init__(self, parent):
            super().__init__()
            self.parent = parent
            
            self.model = QFileSystemModel()
            self.view = QTreeView()
            self.view.setModel(self.model)
            
            # arrange columns
            self.view.setColumnHidden(2, True) # hide type
            self.view.setColumnWidth(0, 300) # resize name
            
            # right click menu
            self.view.setContextMenuPolicy(Qt.CustomContextMenu)
            self.view.customContextMenuRequested.connect(self.showContextMenu)    
            


            self.view.doubleClicked.connect(self.readfile)
           
        def makeMenu(self, type):
            menu = QMenu()
            menu.addAction('Copy path', self.copyPath)
            #menu.addAction('Open in file explorer', self.openInFE)
            file_action = [('Open in notepad', self.openInTE), ('Read file', self.readfile)]
            dir_action = [('Open', self.openDir)]
            for action in file_action if type=='file' else dir_action:
                menu.addAction(action[0], action[1])
            menu.addSeparator()
            menu.addAction('Go up a dir', self.goUpDir)
            expand_all_action = [('Expand all', self.view.expandAll), ('Collapse all', self.view.collapseAll)]
            for action in expand_all_action:
                menu.addAction(action[0], action[1])
            return menu

        def showContextMenu(self, pos):
            index = self.view.indexAt(pos)
            if not index.isValid():
                return
            # check if file or dir
            type = 'file' if not self.model.isDir(index) else 'dir'
            menu = self.makeMenu(type)
            
            menu.exec_(self.view.mapToGlobal(pos))
            
        # ACTIONS

        def readfile(self, index=None):
            if not index:
                index = self.view.currentIndex()
            path = self.model.filePath(index)
            if not self.model.isDir(index):
                self.parent.openFile(path)

        def openInTE(self):
            # try to open in text editor
            index = self.view.currentIndex()
            path = self.model.filePath(index)
            try:
                process = QProcess()
                process.startDetached('notepad.exe', [path])
            except:
                self.parent.write('Could not open in text editor: '+path)

        def goUpDir(self):
            path = self.model.filePath(self.view.rootIndex())
            path = os.path.dirname(path)
            self.parent.changePath(path)

        def openDir(self):
            index = self.view.currentIndex()
            path = self.model.filePath(index)
            self.parent.changePath(path)
            
        def copyPath(self):
            index = self.view.currentIndex()
            path = self.model.filePath(index)
            self.parent.cb.setText(path)
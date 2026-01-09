from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QSplitter, QWidget, QTabWidget, QTabBar
from PyQt5.QtWidgets import QToolBar, QAction, QMenu
from PyQt5.QtCore import Qt, pyqtSignal
import pyqtgraph as pg

from views.MPLView import MPLView
from widgets.MPLTraceWidget import MPLTraceWidget
from views.FilterTreeView import FilterTreeView
from views.SettingTreeView import SettingTreeView
from views.SweepTreeView import SweepTreeView
from views.FileTreeView import FileTreeView

from widgets.CustomQWidgets import CustomTabWidget

from src.ReadfileData import ReadfileData

import numpy as np
import os


class MainView(QMainWindow):
    """
    Gère les différentes vues
    """

    def __init__(self, hlog="to_remove"):
        super().__init__()
        self.hlog = hlog
        self.setWindowTitle('hlog')
        self.resize(1000, 600)
        icon = pg.QtGui.QIcon('./resources/icon.png')
        self.setWindowIcon(icon)
        
        self.block_update = False
        self.current_plot_dict_rfdata = None

        ## extra windows
        # TODO: remove `self` dependence
        self.trace_window = MPLTraceWidget(self)
        
        ## MAIN LAYOUT
        self.file_tree = FileTreeView(self)
        self.graphic_tabs = CustomTabWidget(self)
        self.graphic_tabs.tabCloseRequested.connect(self.closeTab)

        # Splitter: (FILES, TABS)
        self.v_splitter = QSplitter()
        self.v_splitter.addWidget(self.file_tree.view)
        self.v_splitter.addWidget(self.graphic_tabs)
        self.setCentralWidget(self.v_splitter)
        self.v_splitter.setSizes([300, 500])
        ##

    def newTab(self, name:str):
        """ Build tab layout
        return: sweep_tree, filter_tree, setting_tree, graph
        
        """
        # LAYOUT
        graph = MPLView(self)
        # --
        sweep_tree = SweepTreeView()
        filter_tree = FilterTreeView()
        setting_tree = SettingTreeView()
        # bottom (sweep, [analyse, graph settings])
        setting_tabs = QTabWidget()
        setting_tabs.addTab(filter_tree.tree, 'Analyse')
        #setting_tabs.addTab(setting_tree.tree, 'Graph')

        bottom_splitter = QSplitter()
        bottom_splitter.addWidget(sweep_tree.tree)
        bottom_splitter.addWidget(setting_tabs)
        bottom_splitter.setSizes([200, 1])

        # main splitter
        layout = QSplitter(2)
        layout.addWidget(graph)
        layout.addWidget(bottom_splitter)
        layout.setSizes([250, 100])

        # saving trees for easy retrieve
        layout.sweep_tree = sweep_tree
        layout.filter_tree = filter_tree
        layout.setting_tree = setting_tree
        layout.graph = graph

        # add the tab
        self.graphic_tabs.addTab(layout, name)
        self.graphic_tabs.setCurrentWidget(layout)

        return sweep_tree, filter_tree, setting_tree, graph

    def currentTab(self, name):
        layout = self.graphic_tabs.currentWidget()
        if not layout:
            return self.newTab(name)

        sweep_tree  = layout.sweep_tree
        filter_tree = layout.filter_tree
        setting_tree = layout.setting_tree
        graph = layout.graph
        return sweep_tree, filter_tree, setting_tree, graph

    def closeTab(self, index=None):
        if not index:
            index = self.graphic_tabs.currentIndex()
        self.graphic_tabs.removeTab(index)

    def write(self, text):
        print(text)
        self.statusBar().showMessage(text)

    def onFileOpened(self, rfdata, new_tab_asked:bool):

        fn = {True:self.newTab, False:self.currentTab}[new_tab_asked]
        sweep_tree, filter_tree, setting_tree, graph = fn(name=rfdata.filename)

        self.block_update = True
        # Tell the views about the new rfdata:
        sweep_tree.onNewReadFileData(rfdata)
        filter_tree.onNewReadFileData(rfdata)
        graph.onNewReadFileData(rfdata)
        #setting_tree.onNewReadFileData(rfdata)
        
        # Connect signals
        update_this_graph = lambda **kwargs: self.prepare_and_send_plot_dict(rfdata, filter_tree, sweep_tree, graph, **kwargs)
        filter_tree.parameters.sigTreeStateChanged.disconnect()
        sweep_tree.parameters.sigTreeStateChanged.disconnect()
        
        filter_tree.parameters.sigTreeStateChanged.connect(update_this_graph)
        sweep_tree.parameters.sigTreeStateChanged.connect(update_this_graph)
        
        
        self.block_update = False
        update_this_graph()


    def prepare_and_send_plot_dict(self,
        rfdata:ReadfileData, 
        filter_tree:FilterTreeView, 
        sweep_tree:SweepTreeView, 
        graph:MPLView,
    ):
        """ Prepare a new `plot_dict` and send to MPLView """
        if self.block_update: return
        self.block_update = True

        #print("updataing")

        d = rfdata.data_dict
        transpose_checked = filter_tree.transposeChecked()
        x_title, y_title = sweep_tree.get_xy_titles(transpose=transpose_checked)

        if d["sweep_dim"] == 1:

            x_data = rfdata.get_data(x_title)
            y_data = rfdata.get_data(y_title)
            y_data, y_mod_title = filter_tree.applyOnData(y_data, y_title)

            plot_dict = {
                "x_title": x_title,
                "y_title": y_mod_title,
                "x_data": rfdata.get_data(x_title),
                "y_data": y_data,
                "grid": True
            }
            graph.plot1D(plot_dict)

        elif d["sweep_dim"] == 2:
            out_title = sweep_tree.get_z_title()
            alternate = sweep_tree.alternate_checked()
            
            img = rfdata.get_data(out_title, alternate=alternate,
            transpose=transpose_checked)
            img, out_mod_title = filter_tree.applyOnData(img, out_title)

            plot_dict = {
                "img": img,
                "x_title": x_title,
                "y_title": y_title,
                "z_title": out_mod_title,
                "cmap": filter_tree.getCmap(),
                "extent": rfdata.get_extent(transpose=transpose_checked),
                "grid": True,
                #"z_scale": {False:"linear", True:"log"}[filter_tree.zLogChecked()]
            }
            graph.plot2D(plot_dict)

        self.block_update = False


    # TRACE WINDOW
    def _findIndexOfClosestToTarget(self, target, array):
        # find the closest point in the array to the target
        index = np.argmin(np.abs(array - target))
        return index

    def showTrace(self, click_x=None, click_y=None):
        # 2 in 1 function
        # show the trace window if no arguments
        # if click_x and click_y are not None, display the trace for the clicked position
        self.trace_window.show()
        if click_x is None or click_y is None:
            self.trace_window.raise_()
            # force the trace window to be on top
            self.trace_window.activateWindow()
            return
        if self.displayed_data is None:
            return
        
        color = self.trace_window.getColor()

        if self.displayed_data['dim'] == 1:
            x_ax = self.displayed_data['data'][0]
            x_ax = x_ax[~np.isnan(x_ax)] # remove nans
            x_index_clicked = self._findIndexOfClosestToTarget(click_x, x_ax)
            self.trace_window.plotHorizontalTrace(*self.displayed_data['data'])
        
        elif self.displayed_data['dim'] == 2:
            # gen linspace for x axis from the extent
            x_start, x_stop, y_start, y_stop = self.displayed_data['data'][1]
            x_start, x_stop, y_start, y_stop = min(x_start, x_stop), max(x_start, x_stop), min(y_start, y_stop), max(y_start, y_stop)
            x_ax = np.linspace(x_start, x_stop, self.displayed_data['data'][0].shape[1])
            y_ax = np.linspace(y_start, y_stop, self.displayed_data['data'][0].shape[0])
            x_index_clicked = self._findIndexOfClosestToTarget(click_x, x_ax)
            y_index_clicked = self._findIndexOfClosestToTarget(click_y, y_ax)
            self.current_graph().onNewTrace(x_ax[x_index_clicked], y_ax[y_index_clicked], color=color)
            vert_trace = self.displayed_data['data'][0][:, x_index_clicked]
            hor_trace = self.displayed_data['data'][0][y_index_clicked]
            self.trace_window.plotVerticalTrace(y_ax, vert_trace, color)
            self.trace_window.plotHorizontalTrace(x_ax, hor_trace, color)
            
    def clearTraces(self):
        self.trace_window.clear()
        self.current_graph().clearCrosses()
        self.current_graph().canvas.draw()

    ### DROP

    def dropEvent(self, e):
        file_urls = [url.toLocalFile() for url in e.mimeData().urls()]
        if len(file_urls) > 1:
            self.write('I\'m sorry but one file at a time please...\n Or you can drop your folder to open it.')
            return
        if os.path.isdir(file_urls[0]):
            self.file_tree.changePath(file_urls[0])
        else:
            self.file_tree.sig_askOpenFile.emit(file_urls[0])
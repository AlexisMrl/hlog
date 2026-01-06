from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QSplitter, QWidget, QTabWidget
from PyQt5.QtWidgets import QToolBar, QAction, QMenu
from PyQt5.QtCore import Qt, pyqtSignal
import pyqtgraph as pg

from widgets.MPLWidget import MPLWidget
from widgets.MPLTraceWidget import MPLTraceWidget
from views.FilterTreeView import FilterTreeView
from views.SettingTreeView import SettingTreeView
from views.SweepTreeView import SweepTreeView
from views.FileTreeView import FileTreeView

from src.ReadfileData import ReadfileData


from scipy.ndimage import gaussian_filter1d, gaussian_filter
import numpy as np


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

        ## extra windows
        # TODO: remove `self` dependence
        self.trace_window = MPLTraceWidget(self)
        
        ## MAIN LAYOUT
        self.file_tree = FileTreeView(self)
        self.graphic_tabs = QTabWidget()
        self.graphic_tabs.setTabsClosable(True)
        self.graphic_tabs.tabCloseRequested.connect(self.closeTab)

        # Splitter: (FILES, TABS)
        self.v_splitter = QSplitter()
        self.v_splitter.addWidget(self.file_tree.view)
        self.v_splitter.addWidget(self.graphic_tabs)
        self.setCentralWidget(self.v_splitter)
        self.v_splitter.setSizes([300, 500])

    def newTab(self, name:str):
        """ Build tab layout
        return: sweep_tree, filter_tree, setting_tree
        
        """
        # LAYOUT
        graph = MPLWidget(self)
        # --
        sweep_tree = SweepTreeView()
        filter_tree= FilterTreeView()
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

        self.graphic_tabs.addTab(layout, name)
        self.graphic_tabs.setCurrentWidget(layout)

        return sweep_tree, filter_tree, setting_tree

    def closeTab(self, index):
        print("DEBUG: closing tab "+str(index))
        self.graphic_tabs.removeTab(index)

    def write(self, text):
        print(text)
        self.statusBar().showMessage(text)


    #####

    def current_graph(self, force_new:bool):
        graph = self.graphic_tabs.currentWidget()
        if not graph:
            return self.newGraph() if force_new else None
        return graph


    def onFileOpened(self, rfdata):

        sweep_tree, filter_tree, setting_tree = self.newTab(name=rfdata.filename)

        ## Send a new graph signal
        self.block_update = True
        #self.sig_newReadFileData.emit(rfdata)
        sweep_tree.onNewReadFileData(rfdata)
        filter_tree.onNewReadFileData(rfdata)
        #self.filter_tree.new_rfdata(rfdata)
        #self.setting_tree.new_rfdata(rfdata)
        self.block_update = False
        print("hiii")
        return
        
        # connect to new plot
        update_plot = lambda *args: self.update_plot(rfdata, graph)
        self.filter_tree.parameters.sigTreeStateChanged.connect(update_plot)
        self.setting_tree.parameters.sigTreeStateChanged.connect(update_plot)
        self.sweep_tree.parameters.sigTreeStateChanged.connect(update_plot)

        update_plot()#, data_changed=True, file_changed=True)


    def update_plot(self, rfdata, graphic):#, data_changed=False, file_changed=False, new_tab=False):
        # called on file open or when a parameter is changed
        if self.block_update: return

        self.block_update = True

        # reset traces
        self.traces = []
        
        # # Polar/Cartesian conversion
        # conversion_type = self.filters.param('Polar/Cartesian', 'type').value()
        # if conversion_type != 'No conversion':
        #     param_1, param_2 = self.filters.param('Polar/Cartesian').children()[1:]
        #     if conversion_type == 'Polar to Cart':
        #         param_1.setName('r')
        #         param_2.setName('theta')
        #         rfdata.genXYData(param_1.value(), param_2.value())
        #     elif conversion_type == 'Cart to Polar':
        #         param_1.setName('x')
        #         param_2.setName('y')
        #         rfdata.genPolarData(param_1.value(), param_2.value())
        # else:
        #     rfdata.clearComputedData()
        # self._updateOutTitles()
        #self.mplkw.param('YLabel').setValue(y_title)
        #self.mplkw.param('XLabel').setDefault(x_title)
        #self.mplkw.param('YLabel').setDefault(y_title)

        x_title, y_title = self.sweep_tree.get_xy_titles()

        if rfdata.data_dict['sweep_dim'] == 1:
            x_data = rfdata.get_data(x_title)
            y_data = rfdata.get_data(y_title)
            y_data = self.filter_tree.apply_on(y_data)
            keywords_for_plot = self.setting_tree.get_kw(dim=1).to_dict()

            graphic.display_plot(x_data, y_data, plot_kwargs=keywords_for_plot)#, is_new_data=data_changed, is_new_file=file_changed)

        elif rfdata.data_dict['sweep_dim'] == 2:
            out_title = self.sweep_tree.get_z_title()
            alternate = self.sweep_tree.alternate_checked()
            #transpose = self.sweep_tree.transpose_checked()

            #cbar_min = self.filters.param('Colorbar', 'min').value()
            #cbar_max = self.filters.param('Colorbar', 'max').value()
            
            img = rfdata.get_data(out_title, alternate=alternate)
            img = self.filter_tree.apply_on(img)

            extent = rfdata.get_extent()
        
            keywords_for_plot = self.setting_tree.get_kw(dim=2).to_dict()
            graphic.display_image(img, extent, plot_kwargs=keywords_for_plot)#, is_new_data=data_changed, is_new_file=file_changed, cbar_min_max=(cbar_min, cbar_max))

        self.block_update = False

    def _updateOutTitles(self):
        # update the out titles in the filter tree, keeping the current value selected
        # usefull to dynamically add new out titles (polar/cartesian)
        rfdata = self.hlog.current_data
        out_titles = rfdata.data_dict['out']['titles']
        computed_out_titles = rfdata.data_dict['computed_out']['titles']
        if rfdata.data_dict['sweep_dim'] == 1:
            current_x, current_y = self.params.param('Out', 'x').value(), self.params.param('Out', 'y').value()
            self.params.param('Out', 'x').setLimits(out_titles + computed_out_titles)
            self.params.param('Out', 'y').setLimits(out_titles + computed_out_titles)
            if current_x in out_titles + computed_out_titles:
                self.params.param('Out', 'x').setValue(current_x)
            if current_y in out_titles + computed_out_titles:
                self.params.param('Out', 'y').setValue(current_y)
        elif rfdata.data_dict['sweep_dim'] == 2:
            current_z = self.params.param('Out', 'z').value()
            self.params.param('Out', 'z').setLimits(out_titles + computed_out_titles)
            if current_z in out_titles + computed_out_titles:
                self.params.param('Out', 'z').setValue(current_z)
    
    
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

from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QSplitter, QWidget, QTabWidget
from PyQt5.QtWidgets import QToolBar, QAction, QMenu
from PyQt5.QtCore import Qt
import pyqtgraph as pg

from widgets.MPLWidget import MPLWidget
from widgets.MPLTraceWidget import MPLTraceWidget
from widgets.FilterTreeWidget import FilterTreeWidget
from widgets.SettingTreeWidget import SettingTreeWidget
from widgets.SweepTreeWidget import SweepTreeWidget


from scipy.ndimage import gaussian_filter1d, gaussian_filter
import numpy as np


class MainView(QMainWindow):

    def __init__(self, controller, tree_view):
        super().__init__()
        self.controller = controller
        self.setWindowTitle('hlog')
        self.resize(1000, 600)
        icon = pg.QtGui.QIcon('./resources/icon.png')
        self.setWindowIcon(icon)
        
        self.block_update = False

        # extra windows
        # TODO: remove `self` dependence
        self.trace_window = MPLTraceWidget(self)
        
        # main layout
        # trees
        self.sweep_tree = SweepTreeWidget()
        self.filter_tree= FilterTreeWidget()
        self.setting_tree = SettingTreeWidget()
        # graph tab:
        self.graphic_tabs = QTabWidget()
        self.graphic_tabs.setTabsClosable(True)
        self.graphic_tabs.tabCloseRequested.connect(self.on_graph_close)

        # left splitter (tree_view, param_tree)
        self.h_splitter_left = QSplitter(2)
        self.h_splitter_left.addWidget(tree_view)
        self.h_splitter_left.addWidget(self.sweep_tree.tree)
        self.h_splitter_left.setSizes([300, 50])

        # right splitter (graphics, setting_tabs)
        self.setting_tabs = QTabWidget()
        self.setting_tabs.addTab(self.filter_tree.tree, 'Analysis')
        self.setting_tabs.addTab(self.setting_tree.tree, 'Graph settings')
        self.h_splitter_right = QSplitter(2)
        self.h_splitter_right.addWidget(self.graphic_tabs)
        self.h_splitter_right.addWidget(self.setting_tabs)

        # Main splitter with (left, right)
        self.v_splitter = QSplitter()
        self.v_splitter.addWidget(self.h_splitter_left)
        self.v_splitter.addWidget(self.h_splitter_right)
        self.setCentralWidget(self.v_splitter)
        self.v_splitter.setSizes([300, 500])
        
        # variables
        self.displayed_data = None # store the data displayed in the plot
        # {dim: 1, data: (x, y)} or {dim: 2, data: (img, (x_start, x_stop, y_start, y_stop))}

    def closeEvent(self, event):
        self.controller.close()

    def new_graph(self, closable=True):
        graphic = MPLWidget(self)
        self.graphic_tabs.addTab(graphic, "graph")
        self.graphic_tabs.setCurrentWidget(graphic)
        return graphic
    
    def current_graph(self):
        graph = self.graphic_tabs.currentWidget()
        if not graph: return self.new_graph()
        return graph
    
    def on_graph_close(self, index):
        self.graphic_tabs.removeTab(index)

    def updatePlot(self, rfdata, data_changed=False, file_changed=False, new_tab=False):
        # called on file open or when a parameter is changed
        if self.block_update: return

        graphic = self.new_graph() if new_tab else self.graphic_tabs.currentWidget()
        self.graphic_tabs.setTabText(self.graphic_tabs.indexOf(graphic), rfdata.filename)

        self.block_update = True
        
        # reset variables
        self.displayed_data = None
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
        x_title, y_title = self.sweep_tree.get_xy_titles()
        #self.mplkw.param('YLabel').setValue(y_title)
        #self.mplkw.param('XLabel').setDefault(x_title)
        #self.mplkw.param('YLabel').setDefault(y_title)
        
        #filter_title = self.filter_tree.parameters.param('Filter', 'Type').value()
        #sigma = self.filter_tree.parameters.param('Filter', 'Sigma').value()
        #order = self.filter_tree.parameters.param('Filter', 'Order').value()
        print(x_title, y_title)
        if rfdata.data_dict['sweep_dim'] == 1:
            x_data = rfdata.get_data(x_title)
            y_data = rfdata.get_data(y_title)
            #y_data = self.filter_fn(filter_title)(y_data, sigma, order)
            #plot_kwargs = self.mplkw.toDict(dim=1)
            graphic.displayPlot(x_data, y_data)#, plot_kwargs=plot_kwargs, is_new_data=data_changed, is_new_file=file_changed)
            self.displayed_data = {'dim': 1, 'data': (x_data, y_data)}

        elif rfdata.data_dict['sweep_dim'] == 2:
            out_title = self.sweep_tree.get_z_title()
            alternate = self.sweep_tree.is_alternate()
            transposed = self.sweep_tree.is_transposed()
            #self.mplkw.param('ZLabel').setValue(out_title)
            #self.mplkw.param('ZLabel').setDefault(out_title)


            img = rfdata.get_data(out_title, alternate=alternate, transpose=transposed)
            #img = self.filter_fn(filter_title)(img, sigma, order)
            #if self.filters.param('Colorbar', 'log').value():
            #    img = np.log10(np.absolute(img))

            #cbar_min = self.filters.param('Colorbar', 'min').value()
            #cbar_max = self.filters.param('Colorbar', 'max').value()
            
            x_start, x_stop, x_nbpts, x_step = rfdata.data_dict['x']['range']
            y_start, y_stop, y_nbpts, y_step = rfdata.data_dict['y']['range']
            extent = (min(x_start, x_stop)-abs(x_step)/2, max(x_start, x_stop)+abs(x_step)/2,
                      min(y_start, y_stop)-abs(y_step)/2, max(y_start, y_stop)+abs(y_step)/2)
            # extent = (x_start, x_stop, y_start, y_stop)
            if transposed: extent = (extent[2], extent[3], extent[0], extent[1])
            if any([np.isnan(e) for e in extent]):
                extent = None
        
            #plot_kwargs = self.mplkw.toDict(dim=2)

            graphic.displayImage(img, extent)#, plot_kwargs=plot_kwargs, is_new_data=data_changed, is_new_file=file_changed, cbar_min_max=(cbar_min, cbar_max))
            self.displayed_data = {'dim': 2, 'data': (img, (x_start, x_stop, y_start, y_stop))}

        self.block_update = False

    def _updateOutTitles(self):
        # update the out titles in the filter tree, keeping the current value selected
        # usefull to dynamically add new out titles (polar/cartesian)
        rfdata = self.controller.current_data
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
    
    def on_file_opened(self, rfdata):
        print(rfdata)
        self.update_views(rfdata)

    def update_views(self, rfdata):  
        self.block_update = True
        self.sweep_tree.new_rfdata(rfdata)
        self.filter_tree.new_rfdata(rfdata)
        self.setting_tree.new_rfdata(rfdata)
        self.block_update = False

        self.updatePlot(rfdata, data_changed=True, file_changed=True)

    
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

    ## UTILS

    def filter_fn(self, str_arg):
        if str_arg == 'No filter':
            return lambda data, simga, order: data
        elif str_arg == 'dy/dx':
            return lambda data, sigma, order: gaussian_filter1d(data, sigma=sigma, order=order, axis=0)
        elif str_arg == 'dz/dy':
            return lambda data, sigma, order: gaussian_filter1d(data, sigma=sigma, order=order, axis=0)
        elif str_arg == 'dz/dx':
            return lambda data, sigma, order: gaussian_filter1d(data, sigma=sigma, order=order, axis=1)
        elif str_arg == 'Gaussian filter':
            return lambda data, sigma, order: gaussian_filter(data, sigma=sigma, order=order, mode='nearest')
    

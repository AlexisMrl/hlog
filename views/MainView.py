from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QSplitter, QWidget, QTabWidget
from PyQt5.QtWidgets import QToolBar, QAction, QMenu
from PyQt5.QtCore import Qt
import pyqtgraph as pg

from widgets.MPLWidget import MPLWidget
from widgets.MPLTraceWidget import MPLTraceWidget


from scipy.ndimage import gaussian_filter1d, gaussian_filter
import numpy as np


class MainView(QMainWindow):

    def __init__(self, controller, tree_view):
        super().__init__()
        self.controller = controller
        self.setWindowTitle('hlog')
        self.resize(1000, 600)
        self.block_update = False

        # ICON
        icon = pg.QtGui.QIcon('./resources/icon.png')
        self.setWindowIcon(icon)
        
        # TRACE WINDOW
        self.trace_window = MPLTraceWidget(self)
        
        # MAIN LAYOUT
        self._makeParamTreeWidget()
        self._makeFilterTreeWidget()
        self._makeSettingsTreeWidget()
        self.graphic = MPLWidget(self)

        # Left splitter with (tree_view, param_tree)
        self.h_splitter_left = QSplitter(2)
        self.h_splitter_left.addWidget(tree_view)
        self.h_splitter_left.addWidget(self.param_tree)
        self.h_splitter_left.setSizes([300, 50])

        # Right splitter with (graphic, tabs)
        self.tabs = QTabWidget()
        self.tabs.addTab(self.filter_tree, 'Analysis')
        self.tabs.addTab(self.mplkw_tree, 'Graph settings')
        self.h_splitter_right = QSplitter(2)
        self.h_splitter_right.addWidget(self.graphic)
        self.h_splitter_right.addWidget(self.tabs)

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

    def _makeParamTreeWidget(self):
        children = [
            {'name': 'Sweep', 'type': 'group', 'children': [
                {'name': 'dev1', 'type': 'group', 'children': []},
                {'name': 'dev2', 'type': 'group', 'children': []},
                {'name': 'alternate', 'type': 'bool', 'value': False},
                {'name': 'Transopse', 'type': 'bool', 'value': False},
                {'name': 'wait_before (s)', 'type': 'str', 'value': '[0.02, 0.02]', 'readonly': True},
                ]},
            {'name': 'Out', 'type': 'group', 'children': [
                {'name': 'x', 'type': 'list', 'values': []},
                {'name': 'y', 'type': 'list', 'values': []},
                {'name': 'z', 'type': 'list', 'values': []}
            ]},
            {'name': 'Header', 'type': 'group', 'children': [
                {'name': 'config', 'type': 'text', 'value': '', 'readonly': True},
                {'name': 'comments', 'type': 'text', 'value': '', 'readonly': True},
                ], 'expanded': False},
        ] # these are just placeholders, they are filled/rewritten in onFileOpened
        self.params = pg.parametertree.Parameter.create(name='params', type='group', children=children)
        self.param_tree = pg.parametertree.ParameterTree(showHeader=True)
        self.param_tree.setParameters(self.params, showTop=False)

        def onParamChange(param, changes):
            self.updatePlot()
        self.params.sigTreeStateChanged.connect(onParamChange)
        
        self.param_tree.header().setSectionResizeMode(0)
        self.param_tree.setColumnWidth(0, 130)
    
    def _makeFilterTreeWidget(self):
    
        self.d1_filters = ['No filter', 'dy/dx']  # filters possible for 1d data
        self.d2_filters = ['No filter', 'dz/dx', 'dz/dy', 'Gaussian filter'] # filters possible for 2d data
        children = [
            {'name': 'Filter', 'type': 'group', 'children': [
                {'name': 'Type', 'type': 'list', 'values': self.d2_filters, 'default': 'No filter'},
                {'name': 'Sigma', 'type': 'float', 'value': 1, 'limits': (1, None)},
                {'name': 'Order', 'type': 'int', 'value': 1, 'limits': (0, None)},
            ]},
            {'name': 'Colorbar', 'type': 'group', 'children': [
                {'name': 'min', 'type': 'slider', 'value': 0, 'limits':(0, 1), 'step': 0.001, 'default': 0},
                {'name': 'max', 'type': 'slider', 'value': 1, 'limits':(0, 1), 'step': 0.001, 'default': 1},
                {'name': 'log', 'type': 'bool', 'value': False}
            ]},
            {'name': 'Polar/Cartesian', 'type': 'group', 'children': [
                {'name': 'type', 'type': 'list', 'value': ['No conversion', 'Polar to Cart', 'Cart to Polar']},
                {'name': 'r', 'type': 'list', 'value': []},
                {'name': 'theta', 'type': 'list', 'value': []}
            ]},
        ]
        self.filters = pg.parametertree.Parameter.create(name='filters', type='group', children=children)
        self.filter_tree = pg.parametertree.ParameterTree(showHeader=False)
        self.filter_tree.setParameters(self.filters, showTop=False)
        
        def onFilterChange(param, changes): # called when something changes in the filter tree
            self.updatePlot()
            #print('filter change:', param, changes)
        self.filters.sigTreeStateChanged.connect(onFilterChange)

        self.filter_tree.header().setSectionResizeMode(0)
        self.filter_tree.setColumnWidth(0, 130)

    def _makeSettingsTreeWidget(self):
        children=[
            {'name': 'Title', 'type': 'str', 'value': ''},
            {'name': 'XLabel', 'type': 'str', 'value': ''},
            {'name': 'YLabel', 'type': 'str', 'value': ''},
            {'name': 'ZLabel', 'type': 'str', 'value': '', 'dim':2},
            {'name': 'Color', 'type': 'list', 'values': ['tab:blue', 'tab:orange', 'tab:green', 'tab:red',
                                                         'b', 'g', 'r', 'c', 'm', 'y', 'k'], 'default': 'tab:blue', 'dim':1},
            {'name': 'Cmap', 'type': 'list', 'values': ['viridis', 'RdBu_r'], 'default': 'viridis', 'dim':2},
            {'name': 'LineStyle', 'type': 'list', 'values': ['-', '--', '-.', ':', 'None'], 'default': '-', 'dim':1},
            {'name': 'LineWidth', 'type': 'float', 'value': 2, 'limits': (1, 10), 'default': 2, 'dim':1},
            {'name': 'Marker', 'type': 'list', 'values': ['o', 's', '^', 'v', '<', '>', 'x', '+', '*'], 'default': 'o', 'dim':1},
            {'name': 'MarkerSize', 'type': 'float', 'value': 5, 'limits': (0, 20), 'default': 5, 'dim':1},
            {'name': 'Grid', 'type': 'bool', 'value': True, 'dim':1},
            {'name': 'XScale', 'type': 'list', 'values': ['linear', 'log'], 'default': 'linear', 'dim':1},
            {'name': 'YScale', 'type': 'list', 'values': ['linear', 'log'], 'default': 'linear', 'dim':1},
        ]
        self.mplkw = pg.parametertree.Parameter.create(name='settings', type='group', children=children)
        self.mplkw_tree = pg.parametertree.ParameterTree(showHeader=False)
        self.mplkw_tree.setParameters(self.mplkw, showTop=False)
        
        def onParamChange(param, changes): # called when something changes in the settings tree
            #data_changed = changes[0][0].opts.get('changes_data', True)
            self.updatePlot()
        self.mplkw.sigTreeStateChanged.connect(onParamChange)
    
        def toDict(dim=2):
            # return a dictionary with all the settings to be passed to the plot function
            dic = {}
            for child in self.mplkw.children():
                if 'dim' in child.opts and child.opts['dim'] != dim:
                    continue
                dic[child.name().lower()] = child.value()
            return dic

        self.mplkw.toDict = toDict
        
        self.mplkw_tree.header().setSectionResizeMode(0)
        self.mplkw_tree.setColumnWidth(0, 130)

    
    def updatePlot(self, data_changed=False, file_changed=False):
        # called on file open or when a parameter is changed
        if self.block_update: return

        rfdata = self.controller.current_data
        if rfdata is None: return

        self.block_update = True
        
        # reset variables
        self.displayed_data = None
        self.traces = []
        
        # Polar/Cartesian conversion
        conversion_type = self.filters.param('Polar/Cartesian', 'type').value()
        if conversion_type != 'No conversion':
            param_1, param_2 = self.filters.param('Polar/Cartesian').children()[1:]
            if conversion_type == 'Polar to Cart':
                param_1.setName('r')
                param_2.setName('theta')
                rfdata.genXYData(param_1.value(), param_2.value())
            elif conversion_type == 'Cart to Polar':
                param_1.setName('x')
                param_2.setName('y')
                rfdata.genPolarData(param_1.value(), param_2.value())
        else:
            rfdata.clearComputedData()
        self._updateOutTitles()

        x_title = self.params.param('Out', 'x').value()
        y_title = self.params.param('Out', 'y').value()
        transposed = self.params.param('Sweep', 'Transpose image').value()
        if transposed:
            x_title, y_title = y_title, x_title
        self.mplkw.param('XLabel').setValue(x_title)
        self.mplkw.param('YLabel').setValue(y_title)
        self.mplkw.param('XLabel').setDefault(x_title)
        self.mplkw.param('YLabel').setDefault(y_title)
        
        filter_title = self.filters.param('Filter', 'Type').value()
        sigma = self.filters.param('Filter', 'Sigma').value()
        order = self.filters.param('Filter', 'Order').value()

        if rfdata.data_dict['sweep_dim'] == 1:
            x_data = rfdata.getData(x_title, transpose=transposed)
            y_data = rfdata.getData(y_title, transpose=transposed)
            y_data = self.filter_fn(filter_title)(y_data, sigma, order)
            plot_kwargs = self.mplkw.toDict(dim=1)
            self.graphic.displayPlot(x_data, y_data, plot_kwargs=plot_kwargs, is_new_data=data_changed, is_new_file=file_changed)
            self.displayed_data = {'dim': 1, 'data': (x_data, y_data)}

        elif rfdata.data_dict['sweep_dim'] == 2:
            out_title = self.params.param('Out', 'z').value()
            self.mplkw.param('ZLabel').setValue(out_title)
            self.mplkw.param('ZLabel').setDefault(out_title)

            alternate = self.params.param('Sweep', 'alternate').value()

            img = rfdata.getData(out_title, alternate=alternate, transpose=transposed)
            img = self.filter_fn(filter_title)(img, sigma, order)
            if self.filters.param('Colorbar', 'log').value():
                img = np.log10(np.absolute(img))

            cbar_min = self.filters.param('Colorbar', 'min').value()
            cbar_max = self.filters.param('Colorbar', 'max').value()
            
            x_start, x_stop, x_nbpts, x_step = rfdata.data_dict['x']['range']
            y_start, y_stop, y_nbpts, y_step = rfdata.data_dict['y']['range']
            extent = (min(x_start, x_stop)-abs(x_step)/2, max(x_start, x_stop)+abs(x_step)/2,
                      min(y_start, y_stop)-abs(y_step)/2, max(y_start, y_stop)+abs(y_step)/2)
            # extent = (x_start, x_stop, y_start, y_stop)
            if transposed: extent = (extent[2], extent[3], extent[0], extent[1])
            if any([np.isnan(e) for e in extent]):
                extent = None
        
            plot_kwargs = self.mplkw.toDict(dim=2)

            self.graphic.displayImage(img, extent, plot_kwargs=plot_kwargs, is_new_data=data_changed, is_new_file=file_changed, cbar_min_max=(cbar_min, cbar_max))
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
    
    def onFileOpened(self, rfdata):
        # 1 block the update
        # 2 clear the trees
        # 3 fill all the param trees with the data
        self.block_update = True

        self.params.param('Out').clearChildren()
        self.params.param('Sweep').clearChildren()
        self.filters.param('Filter', 'Type').clearChildren()
        
        out_titles = rfdata.data_dict['out']['titles']
        
        if rfdata.data_dict['sweep_dim'] == 1:
            x_title, y_title = out_titles[:2]
            x_ax = {'name': 'x', 'type': 'list', 'values': out_titles, 'default': x_title}
            y_ax = {'name': 'y', 'type': 'list', 'values': out_titles, 'default': y_title}
            self.params.param('Out').addChildren([x_ax, y_ax])
            self.params.param('Out', 'x').setValue(rfdata.titles[0])
            self.params.param('Out', 'y').setValue(rfdata.titles[1])
            
            x_range = rfdata.data_dict['x']['range']
            x_sweep = {'name': x_title, 'type': 'group', 'children': [
                {'name': 'range', 'type': 'str', 'value': self.rangeToString(x_range), 'readonly': True}]}
            self.params.param('Sweep').addChildren([x_sweep])
            
            self.filters.param('Filter', 'Type').setLimits(self.d1_filters)
            self.filters.param('Filter', 'Type').setValue('No filter')

        elif rfdata.data_dict['sweep_dim'] == 2:
            x_title, y_title = rfdata.data_dict['x']['title'], rfdata.data_dict['y']['title']
            x = {'name': 'x', 'type': 'str', 'value': x_title, 'readonly': True, 'visible': False}
            y = {'name': 'y', 'type': 'str', 'value': y_title, 'readonly': True, 'visible': False}
            z = {'name': 'z', 'type': 'list', 'values': out_titles, 'default': out_titles[0]}
            self.params.param('Out').addChildren([x, y, z])
            self.params.param('Out', 'z').setValue(rfdata.titles[2])

            x_range, y_range = rfdata.data_dict['x']['range'], rfdata.data_dict['y']['range']
            x_sweep = {'name': x_title, 'type': 'group', 'children': [
                {'name': 'range', 'type': 'str', 'value': self.rangeToString(x_range), 'readonly': True}]}
            y_sweep = {'name': y_title, 'type': 'group', 'children': [
                {'name': 'range', 'type': 'str', 'value': self.rangeToString(y_range), 'readonly': True}]}
            self.params.param('Sweep').addChildren([x_sweep, y_sweep])
            
            self.filters.param('Filter', 'Type').setLimits(self.d2_filters)
            self.filters.param('Filter', 'Type').setValue('No filter')

            self.mplkw.param('ZLabel').setValue(out_titles[0])

        # logs
        self.params.param('Header', 'config').setValue(str(rfdata.data_dict['config']))
        self.params.param('Header', 'comments').setValue(str(rfdata.data_dict['comments']))
        alternate = {'name': 'alternate', 'type': 'bool', 'value': rfdata.data_dict['alternate']}
        #wait_before = {'name': 'wait_before', 'type': 'str', 'value': str(rfdata.data_dict['beforewait']), 'readonly': True},
        #self.params.param('Sweep').addChildren([alternate, wait_before])
        self.params.param('Sweep').addChildren([alternate])
        transpose = {'name': 'Transpose image', 'type': 'bool', 'value': False}
        self.params.param('Sweep').addChildren([transpose])
        
        # Polar/Cartesian
        polar_cart = self.filters.param('Polar/Cartesian')
        item_list = ['No conversion', 'Polar to Cart', 'Cart to Polar']
        self.filters.param('Polar/Cartesian', 'type').setLimits(item_list) 
        self.filters.param('Polar/Cartesian', 'type').setDefault(item_list[0])
        polar_cart.children()[1].setLimits(out_titles)
        polar_cart.children()[1].setValue(out_titles[0])
        polar_cart.children()[1].setDefault(out_titles[0])
        polar_cart.children()[2].setLimits(out_titles)
        polar_cart.children()[2].setValue(out_titles[1])
        polar_cart.children()[2].setDefault(out_titles[1])


        self.mplkw.param('Title').setValue(rfdata.filename)
        self.mplkw.param('Title').setDefault(rfdata.filename)
        self.mplkw.param('XLabel').setValue(x_title)
        self.mplkw.param('XLabel').setDefault(x_title)
        self.mplkw.param('YLabel').setValue(y_title)
        self.mplkw.param('YLabel').setDefault(y_title)
        

        self.block_update = False
        self.updatePlot(data_changed=True, file_changed=True)

    
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
            self.graphic.onNewTrace(x_ax[x_index_clicked], y_ax[y_index_clicked], color=color)
            vert_trace = self.displayed_data['data'][0][:, x_index_clicked]
            hor_trace = self.displayed_data['data'][0][y_index_clicked]
            self.trace_window.plotVerticalTrace(y_ax, vert_trace, color)
            self.trace_window.plotHorizontalTrace(x_ax, hor_trace, color)
            
    def clearTraces(self):
        self.trace_window.clear()
        self.graphic.clearCrosses()
        self.graphic.canvas.draw()

    ## UTILS
    def rangeToString(self, ranges):
        return '[{:.3g}, {:.3g}], npts: {}, step: {:.3g}'.format(*ranges)

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
    

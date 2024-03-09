from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QSplitter, QWidget, QTabWidget
from PyQt5.QtCore import Qt
import pyqtgraph as pg

from widgets.DisplayWidget import DisplayWidget
from widgets.MPLWidget import MPLWidget

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
        
        # MAIN LAYOUT
        self._makeParamTreeWidget()
        self._makeFilterTreeWidget()
        self._makeSettingsTreeWidget()
        self.graphic = MPLWidget(self)

        self.left_widget = QWidget()
        self.left_layout = QVBoxLayout()
        self.left_layout.addWidget(tree_view)
        self.left_layout.addWidget(self.param_tree)
        self.left_widget.setLayout(self.left_layout)
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self.filter_tree, 'Analysis')
        self.tabs.addTab(self.mplkw_tree, 'Graph settings')

        self.h_splitter = QSplitter(2)
        self.h_splitter.addWidget(self.graphic)
        self.h_splitter.addWidget(self.tabs)

        self.v_splitter = QSplitter()
        self.v_splitter.addWidget(self.left_widget)
        self.v_splitter.addWidget(self.h_splitter)
        self.setCentralWidget(self.v_splitter)
        self.v_splitter.setSizes([300, 500])
    

    def _makeParamTreeWidget(self):
        children = [
            {'name': 'Sweep', 'type': 'group', 'children': [
                {'name': 'dev1', 'type': 'group', 'children': []},
                {'name': 'dev2', 'type': 'group', 'children': []},
                ]},
            {'name': 'Out', 'type': 'group', 'children': [
                {'name': 'x', 'type': 'list', 'values': []},
                {'name': 'y', 'type': 'list', 'values': []},
                {'name': 'z', 'type': 'list', 'values': []}
            ]},
            {'name': 'Header', 'type': 'group', 'children': [
                {'name': 'config', 'type': 'text', 'value': '', 'readonly': True},
                {'name': 'comments', 'type': 'text', 'value': '', 'readonly': True, 'expanded': False},
                ]},
        ]
        self.params = pg.parametertree.Parameter.create(name='params', type='group', children=children)
        self.param_tree = pg.parametertree.ParameterTree(showHeader=True)
        self.param_tree.setParameters(self.params, showTop=False)

        def onParamChange(param, changes):
            #print('param change:', param, changes)
            name = changes[0][0].name()
            value = changes[0][2]
            if name in ['x', 'y', 'z']:
                kw_name = {'x': 'XLabel', 'y': 'YLabel', 'z': 'ZLabel'}[name]
                self.mplkw.param(kw_name).setValue(value)
                self.mplkw.param(kw_name).setDefault(value)
            self.updatePlot()
        self.params.sigTreeStateChanged.connect(onParamChange)
        
        self.param_tree.header().setSectionResizeMode(0)
        self.param_tree.setColumnWidth(0, 130)
    
    def _makeFilterTreeWidget(self):
    
        self.d1_filters = ['No filter', 'dy/dx']  # 1d_filters
        self.d2_filters = ['No filter', 'dy/dx', 'dx/dy', 'Gaussian filter'] # 2d_filters
        children = [
            {'name': 'Filter', 'type': 'group', 'children': [
                {'name': 'Type', 'type': 'list', 'values': self.d2_filters, 'default': 'No filter'},
                {'name': 'Sigma', 'type': 'float', 'value': 1, 'limits': (1, None)},
                {'name': 'Order', 'type': 'int', 'value': 1, 'limits': (0, None)},
            ]},
            {'name': 'Colorbar', 'type': 'group', 'children': [
                {'name': 'min', 'type': 'slider', 'value': 0, 'limits':(0, 1), 'step': 0.001, 'default': 0},
                {'name': 'max', 'type': 'slider', 'value': 1, 'limits':(0, 1), 'step': 0.001, 'default': 1},
            ]}
        ]
        self.filters = pg.parametertree.Parameter.create(name='filters', type='group', children=children)
        self.filter_tree = pg.parametertree.ParameterTree(showHeader=False)
        self.filter_tree.setParameters(self.filters, showTop=False)
        
        def onFilterChange(param, changes):
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
        
        def onParamChange(param, changes):
            self.updatePlot()
        self.mplkw.sigTreeStateChanged.connect(onParamChange)
    
        def toDict(dim=2):
            dic = {}
            for child in self.mplkw.children():
                if 'dim' in child.opts and child.opts['dim'] != dim:
                    continue
                dic[child.name().lower()] = child.value()
            return dic

        self.mplkw.toDict = toDict
        
        self.mplkw_tree.header().setSectionResizeMode(0)
        self.mplkw_tree.setColumnWidth(0, 130)

    
    def updatePlot(self):
        if self.block_update: return
        rfdata = self.controller.current_data
        if rfdata is None: return

        self.block_update = True


        x_title = self.params.param('Out', 'x').value()
        y_title = self.params.param('Out', 'y').value()
        
        filter_title = self.filters.param('Filter', 'Type').value()
        sigma = self.filters.param('Filter', 'Sigma').value()
        order = self.filters.param('Filter', 'Order').value()

        if rfdata.data_dict['sweep_dim'] == 1:
            x_data = rfdata.getData(x_title)
            y_data = rfdata.getData(y_title)
            y_data = self.filter_fn(filter_title)(y_data, sigma, order)
            plot_kwargs = self.mplkw.toDict(dim=1)
            self.graphic.displayPlot(x_data, y_data, plot_kwargs=plot_kwargs)

        elif rfdata.data_dict['sweep_dim'] == 2:
            out_title = self.params.param('Out', 'z').value()
            img = rfdata.getData(out_title)
            img = self.filter_fn(filter_title)(img, sigma, order)
            
            x_range = rfdata.data_dict['x']['range']
            y_range = rfdata.data_dict['y']['range']
            extent = (x_range[0], x_range[1], y_range[0], y_range[1])
            if any([np.isnan(e) for e in extent]):
                extent = None
        
            plot_kwargs = self.mplkw.toDict(dim=2)
            plot_kwargs['cbar_factor_min'] = self.filters.param('Colorbar', 'min').value()
            plot_kwargs['cbar_factor_max'] = self.filters.param('Colorbar', 'max').value()

            self.graphic.displayImage(img, extent, plot_kwargs=plot_kwargs)
        
        self.block_update = False

    
    def onFileOpened(self, rfdata):
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

        self.mplkw.param('Title').setValue(rfdata.filename)
        self.mplkw.param('Title').setDefault(rfdata.filename)
        self.mplkw.param('XLabel').setValue(x_title)
        self.mplkw.param('XLabel').setDefault(x_title)
        self.mplkw.param('YLabel').setValue(y_title)
        self.mplkw.param('YLabel').setDefault(y_title)
        

        self.block_update = False
        self.updatePlot()



    
    ## UTILS
    def rangeToString(self, ranges):
        return '[{:.3g}, {:.3g}], npts: {}, step: {:.3g}'.format(*ranges)

    def filter_fn(self, str_arg):
        if str_arg == 'No filter':
            return lambda data, simga, order: data
        elif str_arg == 'dx/dy':
            return lambda data, sigma, order: gaussian_filter1d(data, sigma=sigma, order=order, axis=1)
        elif str_arg == 'dy/dx':
            return lambda data, sigma, order: gaussian_filter1d(data, sigma=sigma, order=order, axis=0)
        elif str_arg == 'Gaussian filter':
            return lambda data, sigma, order: gaussian_filter(data, sigma=sigma, order=order, mode='nearest')
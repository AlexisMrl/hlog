from PyQt5.QtWidgets import QWidget
import os
import pyqtgraph as pg

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
class SettingTreeWidget(QWidget):
    
    def __init__(self):
        super().__init__()

        self.parameters = pg.parametertree.Parameter.create(name='settings', type='group', children=children)
        self.tree = pg.parametertree.ParameterTree(showHeader=False)
        self.tree.setParameters(self.parameters, showTop=False)
        
        def onParamChange(param, changes): # called when something changes in the settings tree
            #data_changed = changes[0][0].opts.get('changes_data', True)
            #print("a setting has changed")
            pass
            #self.updatePlot()
        self.parameters.sigTreeStateChanged.connect(onParamChange)
    
            
        self.tree.header().setSectionResizeMode(0)
        self.tree.setColumnWidth(0, 130)

    def new_rfdata(self, rfdata):

        p = self.parameters
        data_dict = rfdata.data_dict
        out_titles = data_dict['out']['titles']
    
        if rfdata.data_dict['sweep_dim'] == 1:
            x_title, y_title = out_titles[:2]
        elif rfdata.data_dict['sweep_dim'] == 2:
            x_title, y_title = rfdata.data_dict['x']['title'], rfdata.data_dict['y']['title']
            p.param('ZLabel').setValue(out_titles[0])

        p.param('Title').setValue(rfdata.filename)
        p.param('Title').setDefault(rfdata.filename)
        p.param('XLabel').setValue(x_title)
        p.param('XLabel').setDefault(x_title)
        p.param('YLabel').setValue(y_title)
        p.param('YLabel').setDefault(y_title)
        


    def to_dict(self, dim=2):
        # return a dictionary with all the settings to be passed to the plot function
        dic = {}
        for child in self.mplkw.children():
            if 'dim' in child.opts and child.opts['dim'] != dim:
                continue
            dic[child.name().lower()] = child.value()
        return dic
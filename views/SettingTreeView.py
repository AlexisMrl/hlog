from PyQt5.QtWidgets import QWidget
import os
import pyqtgraph as pg

from dataclasses import dataclass, asdict

@dataclass
class Kw1d:
    title: str = ""
    xlabel: str = ""
    ylabel: str = ""
    color: str = "tab:blue"
    linestyle: str = "-"
    linewidth: float = 2.0
    marker: str = "o"
    markersize: float = 5.0
    grid: bool = True
    xscale: str = "linear"
    yscale: str = "linear"
    
    def to_dict(self):
        return asdict(self)


@dataclass
class Kw2d:
    title: str = ""
    xlabel: str = ""
    ylabel: str = ""
    zlabel: str = ""
    cmap: str = "viridis"

    def to_dict(self):
        return asdict(self)

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


class SettingTreeView:
    
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
        self.dim = dim = rfdata.data_dict['sweep_dim']
        if dim == 1:
            # TODO: remove 2dim parameters
            x_title, y_title = out_titles[:2]
        elif dim == 2:
            # TODO: remove 1dim parameters
            x_title, y_title = rfdata.data_dict['x']['title'], rfdata.data_dict['y']['title']
            p.param('ZLabel').setValue(out_titles[0])
            #self.mplkw.param('ZLabel').setValue(out_title)
            #self.mplkw.param('ZLabel').setDefault(out_title)

        p.param('Title').setValue(rfdata.filename)
        p.param('Title').setDefault(rfdata.filename)
        p.param('XLabel').setValue(x_title)
        p.param('XLabel').setDefault(x_title)
        p.param('YLabel').setValue(y_title)
        p.param('YLabel').setDefault(y_title)

        

    def get_kw(self, dim=1):
        data = {}

        for child in self.parameters.children():
            name = child.name().lower()
            value = child.value()

            opt_dim = child.opts.get("dim", None)
            if opt_dim is not None and opt_dim != dim:
                continue
            data[name] = value

        cls = {1:Kw1d, 2:Kw2d}[dim]
        kw = cls(**{k: v for k, v in data.items() if k in cls.__annotations__})
        return kw
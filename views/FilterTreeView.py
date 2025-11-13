from PyQt5.QtWidgets import QWidget
import os
import pyqtgraph as pg

from scipy.ndimage import gaussian_filter1d, gaussian_filter
import numpy as np


d1_filters = ['No filter', 'dy/dx']  # filters possible for 1d data
d2_filters = ['No filter', 'dz/dx', 'dz/dy', 'Gaussian filter'] # filters possible for 2d data
children = [
    {'name': 'Filter', 'type': 'group', 'children': [
        {'name': 'Type', 'type': 'list', 'values': d2_filters, 'default': 'No filter'},
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
class FilterTreeView:
    
    def __init__(self):
        super().__init__()

        self.parameters = pg.parametertree.Parameter.create(name='filters', type='group', children=children)
        self.tree = pg.parametertree.ParameterTree(showHeader=False)
        self.tree.setParameters(self.parameters, showTop=False)
        
        def onFilterChange(param, changes): # called when something changes in the filter tree
            #self.updatePlot()
            print('filter change:', param, changes)
            #pass
        self.parameters.sigTreeStateChanged.connect(onFilterChange)

        self.tree.header().setSectionResizeMode(0)
        self.tree.setColumnWidth(0, 130)


    def new_rfdata(self, rfdata):

        p = self.parameters
        data_dict = rfdata.data_dict
        out_titles = data_dict['out']['titles']

        p.param('Filter', 'Type').clearChildren()
        
        if rfdata.data_dict['sweep_dim'] == 1:
            # TODO: remove 2dim parameters
            p.param('Filter', 'Type').setLimits(d1_filters)
            p.param('Filter', 'Type').setValue('No filter')
        elif rfdata.data_dict['sweep_dim'] == 2:
            # TODO: remove 1dim parameters
            p.param('Filter', 'Type').setLimits(d2_filters)
            p.param('Filter', 'Type').setValue('No filter')

        
        # Polar/Cartesian
        polar_cart = p.param('Polar/Cartesian')
        item_list = ['No conversion', 'Polar to Cart', 'Cart to Polar']
        p.param('Polar/Cartesian', 'type').setLimits(item_list) 
        p.param('Polar/Cartesian', 'type').setDefault(item_list[0])
        polar_cart.children()[1].setLimits(out_titles)
        polar_cart.children()[1].setValue(out_titles[0])
        polar_cart.children()[1].setDefault(out_titles[0])
        polar_cart.children()[2].setLimits(out_titles)
        polar_cart.children()[2].setValue(out_titles[1])
        polar_cart.children()[2].setDefault(out_titles[1])


    def apply_on(self, data):
        p = self.parameters
        fn = filter_fn(p.param('Filter', 'Type').value())
        sigma = p.param('Filter', 'Sigma').value()
        order = p.param('Filter', 'Order').value()
        
        if p.param('Colorbar', 'log').value():
            #img = np.log10(np.absolute(img))
            print("log not implemented")


        return fn(data, sigma, order)



def filter_fn(str_arg):
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


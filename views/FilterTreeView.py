from PyQt5.QtWidgets import QWidget
import os
import pyqtgraph as pg

from scipy.ndimage import gaussian_filter1d, gaussian_filter
import numpy as np
from src.ReadfileData import ReadfileData


d1_filters = ['No filter', 'dy/dx']  # filters possible for 1d data
d2_filters = ['No filter', 'dz/dx', 'dz/dy', 'Gaussian filter'] # filters possible for 2d data
children = [
    {'name': 'auto update', 'type': 'bool', 'value': False},
    {'name': 'Filter', 'type': 'group', 'children': [
        {'name': 'Transpose', 'type': 'bool', 'value': False},

        {'name': 'Type', 'type': 'list', 'values': d2_filters, 'default': 'No filter'},
        {'name': 'Sigma', 'type': 'float', 'value': 1, 'limits': (1, None)},
        {'name': 'Order', 'type': 'int', 'value': 1, 'limits': (0, None)},
    ]},
    {'name': '2d sweep', 'type': 'group', 'children': [
        #{'name': 'min', 'type': 'slider', 'value': 0, 'limits':(0, 1), 'step': 0.001, 'default': 0},
        #{'name': 'max', 'type': 'slider', 'value': 1, 'limits':(0, 1), 'step': 0.001, 'default': 1},
        {'name': 'cmap', 'type': 'list', 'values': ['viridis', 'RdBu_r', 'twilight', 'plasma', 'inferno', 'magma', 'cividis'], 'default': 'viridis'},
        {'name': 'z log', 'type': 'bool', 'value': False},
        #{'name': 'Deinterlace', 'type': 'bool', 'value': False},
        
    ]},
    {'name': 'Plot', 'type': 'group', 'children': [
        {'name': 'bins', 'type': 'int', 'value': 101},
        {'name': 'histogram flatten', 'type': 'action'},
    ]},
    #{'name': '1d sweep', 'type': 'group', 'children': [
    #    {'name': 'x log', 'type': 'bool', 'value': False},
    #    {'name': 'y log', 'type': 'bool', 'value': False},
    #    #{'name': 'Deinterlace', 'type': 'bool', 'value': False},
        
    #]},
    #{'name': 'Polar/Cartesian', 'type': 'group', 'children': [
    #    {'name': 'type', 'type': 'list', 'value': ['No conversion', 'Polar to Cart', 'Cart to Polar']},
    #    {'name': 'r', 'type': 'list', 'value': []},
    #    {'name': 'theta', 'type': 'list', 'value': []}
    #]},
]
class FilterTreeView:
    
    def __init__(self, fn_new_computed_rfdata=lambda rfdata: 0):
        super().__init__()
        self.fn_new_computed_rfdata = fn_new_computed_rfdata
        self.parameters = pg.parametertree.Parameter.create(name='filters', type='group', children=children)
        self.tree = pg.parametertree.ParameterTree(showHeader=False)
        self.tree.setParameters(self.parameters, showTop=False)

        self.displayed_dim = 0


        def onFilterChange(param, changes): # called when something changes in the filter tree
            #print('filter change:', param, changes)
            p = self.parameters
            change = changes[0][0]
            # print(changes)

                        
        self.parameters.sigTreeStateChanged.connect(onFilterChange)

        self.tree.header().setSectionResizeMode(0)
        self.tree.setColumnWidth(0, 130)


    def onNewReadFileData(self, rfdata):

        p = self.parameters
        data_dict = rfdata.data_dict
        out_titles = data_dict['out']['titles']

        p.param('Filter', 'Type').clearChildren()
        
        if rfdata.data_dict['sweep_dim'] == 1:
            p.param('Filter', 'Type').setLimits(d1_filters)
            p.param('Filter', 'Type').setValue('No filter')
            #p.param('1d sweep').show()
            p.param('2d sweep').hide()
            self.displayed_dim = 1
        elif rfdata.data_dict['sweep_dim'] == 2:
            p.param('Filter', 'Type').setLimits(d2_filters)
            p.param('Filter', 'Type').setValue('No filter')
            #p.param('1d sweep').hide()
            p.param('2d sweep').show()
            self.displayed_dim = 2

        p.param('Plot', 'histogram flatten').sigActivated.connect(lambda: self.makeHistogramFlatten(rfdata))
        p.param("auto update").setValue(False)
        
        # Polar/Cartesian
        """
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
        """

    def transposeChecked(self):
        p = self.parameters
        return p.param('Filter', 'Transpose').value()
    
    def zLogChecked(self):
        p = self.parameters
        return p.param('2d sweep', 'z log').value()

    def autoUpdateChecked(self):
        p = self.parameters
        return p.param('auto update').value()
    
    def getCmap(self):
        return self.parameters.param('2d sweep', 'cmap').value()

    def applyOnData(self, data, data_label:str):
        p = self.parameters
        filt = p.param('Filter', 'Type').value()
        fn = filter_fn(filt)
        sigma = p.param('Filter', 'Sigma').value()
        order = p.param('Filter', 'Order').value()
        
        if p.param('2d sweep', 'z log').value():
            if data.ndim == 2:
                data = np.log10(np.absolute(data))
                data_label = f"log {data_label}"

        new_label = f"{filt} {data_label}" if filt!= "No filter" else data_label
        new_data = fn(data, sigma, order)
        self.last_data_and_label = new_data, new_label
        return new_data, new_label


    def makeHistogramFlatten(self, rfdata_reference):
        plot_dict = rfdata_reference.plot_dict

        bins = self.parameters.param('Plot', 'bins').value()
        if self.displayed_dim == 1:
            arr = plot_dict.get("y_data")
        elif self.displayed_dim == 2:
            print(plot_dict)
            arr = plot_dict.get("img")
            arr = arr[~np.isnan(arr)]
        hist, bins = np.histogram(arr.flatten(), bins=bins)
        bins_c = (bins[:-1] + bins[1:]) / 2
        bins_c_title = plot_dict.get("y_title")+" bins"
        rfdata = ReadfileData.from_computed_array_1d(
            out_datas = [bins_c, hist],
            out_titles = [bins_c_title, "count"],
            rfdata_original=rfdata_reference
        )
        self.fn_new_computed_rfdata(rfdata)


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


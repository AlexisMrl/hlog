from PyQt5.QtWidgets import QWidget
import os
import pyqtgraph as pg

children = [
    {'name': 'Sweep', 'type': 'group', 'children': [
        {'name': 'dev1', 'type': 'group', 'children': []},
        {'name': 'dev2', 'type': 'group', 'children': []},
        {'name': 'alternate', 'type': 'bool', 'value': False},
        {'name': 'Transpose', 'type': 'bool', 'value': False},
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


class SweepTreeView:
    
    def __init__(self):
        super().__init__()
    
        self.parameters = pg.parametertree.Parameter.create(name='params', type='group', children=children)
        self.tree = pg.parametertree.ParameterTree(showHeader=True)
        self.tree.setParameters(self.parameters, showTop=False)

        def onParamChange(param, changes):
            #print('a param has changed')
            pass
            #self.updatePlot()
        self.parameters.sigTreeStateChanged.connect(onParamChange)
        
        self.tree.header().setSectionResizeMode(0)
        self.tree.setColumnWidth(0, 130)
    
    def new_rfdata(self, rfdata):
        p = self.parameters
        p.param('Out').clearChildren()
        p.param('Sweep').clearChildren()
        
        data_dict = rfdata.data_dict
        out_titles = data_dict['out']['titles']
        
        if data_dict['sweep_dim'] == 1:
            x_title, y_title = out_titles[:2]
            x_ax = {'name': 'x', 'type': 'list', 'values': out_titles, 'default': x_title}
            y_ax = {'name': 'y', 'type': 'list', 'values': out_titles, 'default': y_title}
            p.param('Out').addChildren([x_ax, y_ax])
            p.param('Out', 'x').setValue(out_titles[0])
            p.param('Out', 'y').setValue(out_titles[1])
            
            x_range = data_dict['x']['range']
            x_sweep = {'name': x_title, 'type': 'group', 'children': [
                {'name': 'range', 'type': 'str', 'value': range_to_string(x_range), 'readonly': True}]}
            p.param('Sweep').addChildren([x_sweep])

        elif data_dict['sweep_dim'] == 2:
            x_title, y_title = rfdata.data_dict['x']['title'], rfdata.data_dict['y']['title']
            x = {'name': 'x', 'type': 'str', 'value': x_title, 'readonly': True, 'visible': False}
            y = {'name': 'y', 'type': 'str', 'value': y_title, 'readonly': True, 'visible': False}
            z = {'name': 'z', 'type': 'list', 'values': out_titles, 'default': out_titles[0]}
            p.param('Out').addChildren([x, y, z])
            p.param('Out', 'z').setValue(out_titles[0])

            x_range, y_range = rfdata.data_dict['x']['range'], rfdata.data_dict['y']['range']
            x_sweep = {'name': x_title, 'type': 'group', 'children': [
                {'name': 'range', 'type': 'str', 'value': range_to_string(x_range), 'readonly': True}]}
            y_sweep = {'name': y_title, 'type': 'group', 'children': [
                {'name': 'range', 'type': 'str', 'value': range_to_string(y_range), 'readonly': True}]}
            p.param('Sweep').addChildren([x_sweep, y_sweep])

            alternate = {'name': 'alternate', 'type': 'bool', 'value': data_dict['alternate']}
            p.param('Sweep').addChildren([alternate])



        # logs
        p.param('Header', 'config').setValue(str(data_dict['config']))
        p.param('Header', 'comments').setValue(str(data_dict['comments']))
        #wait_before = {'name': 'wait_before', 'type': 'str', 'value': str(rfdata.data_dict['beforewait']), 'readonly': True},
        #self.params.param('Sweep').addChildren([alternate, wait_before])
        
        #transpose = {'name': 'Transpose', 'type': 'bool', 'value': False}
        #p.param('Sweep').addChildren([transpose])
        
    def get_xy_titles(self):
        p = self.parameters
        x_title = p.param('Out', 'x').value()
        y_title = p.param('Out', 'y').value()
        if self.transpose_checked():
            x_title, y_title = y_title, x_title
        return x_title, y_title
    
    def get_z_title(self):
        return self.parameters.param('Out', 'z').value()

    def alternate_checked(self):
        return self.parameters.param('Sweep', 'alternate').value()
    
    def transpose_checked(self):
        return False
        #return self.parameters.param('Sweep', 'Transpose').value()

def range_to_string(ranges):
    return '[{:.3g}, {:.3g}], npts: {}, step: {:.3g}'.format(*ranges)

import pyHegel.commands as c
import os, sys
import numpy as np

class ReadfileData:

    def __init__(self, filepath):
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        self.data = []
        self.titles = []
        self.headers = []
        self.data_dict = {'x': {'range': [-1,1,6,0.2], 'title': 'random_x', 'data': np.zeros((11,6))},
                          'y': {'range': [0,2,11,0.1], 'title': 'random_y', 'data': np.zeros((11,6))},
                          'out': {'titles': ['out1', 'out2'], 'data': [np.random.rand(11,6), np.random.rand(11,6)]},
                          'computed_out': {'titles': [], 'data': []}, # for computed data (r, deg, x, y)
                          'alternate': False,
                          'beforewait': True,
                          'sweep_dim': 2,
                          #'hl_logs': {'dev1': 0.1, 'dev2': 0.2},
                          #'ph_logs': ['#dev1', '#dev2']
                          'config': [],
                          'comments': []
                          }
        self.x_index, self.y_index = 0, 1 # default values for swept columns in a 2d sweep


    def _build1DDataDict(self):
        # in one dimension, we use the x and out keys
        x_data = self.data[0]
        self.data_dict['x']['data'] = x_data
        self.data_dict['x']['title'] = self.titles[0]
        self.data_dict['x']['range'] = self._findSweepRange1D(x_data)

        self.data_dict['out']['titles'] = []
        self.data_dict['out']['data'] = []
        rev_data = True if self.data_dict['x']['range'][3] < 0 else False
        for i, title in enumerate(self.titles):
            self.data_dict['out']['titles'].append(title)
            data = self.data[i][::-1] if rev_data else self.data[i]
            self.data_dict['out']['data'].append(data)

    def _detectXYIndex(self):
        # manually detect if the first two columns are actually the same value:
        # ex: field_scale, field_raw 
        if self.titles[0].endswith('scale') and self.titles[1].endswith('raw'):
            return 0, 2
        return 0, 1

    def _build2dDataDict(self):
        self.x_index, self.y_index = self._detectXYIndex()
        x, y = self.x_index, self.y_index
        data_x, data_y = self.data[x], self.data[y]
        self.data_dict['x']['data'] = data_x
        self.data_dict['y']['data'] = data_y
        # check if titles are the same:
        if self.titles[x] == self.titles[y]:
            self.titles[x] = self.titles[y] + '_'
        self.data_dict['x']['title'] = self.titles[x]
        self.data_dict['y']['title'] = self.titles[y]
        self._findSweepRange2D(self.headers)
        self.data_dict['alternate'] = False if np.array_equal(data_y[0], data_y[1]) else True

        self.data_dict['out']['titles'] = []
        self.data_dict['out']['data'] = []
        rev_x = True if self.data_dict['x']['range'][3] < 0 else False
        rev_y = True if self.data_dict['y']['range'][3] < 0 else False
        for i, title in enumerate(self.titles[y+1:]):
            self.data_dict['out']['titles'].append(title)
            data = self.data[i+1+y] # we start at index y+1
            data = data[::-1] if rev_x else data
            data = data[:,::-1] if rev_y else data
            #print(rev_x, rev_y)
            self.data_dict['out']['data'].append(data)
            
    def _findSweepRange1D(self, array):
        # try to find the ranges the sweep array
        start, stop, nbpts, step = np.nan, np.nan, len(array), np.nan
        if array[0] != np.nan:
            start = array[0]
            if not np.isnan(array[-1]):
                stop = array[-1]
                step = (stop - start) / (nbpts - 1)
            elif not np.isnan(array[1]):
                step = array[1] - array[0]
                stop = start + step * (nbpts - 1)
        return [start, stop, nbpts, step]
        
    def _findSweepRange2D(self, headers):
        # try to find the ranges of the 2d sweep
        # for multi sweep, it is not well written in the headers
        # so we have to estimate it from the data
        # 1.1 for Y: try to find start/stop in the header
        array_y = self.data[1][0]
        start_y, stop_y, nbpts_y, step_y = np.nan, np.nan, len(array_y), np.nan
        line_options = headers[-3]
        if 'sweep' not in line_options:
            return
        options = line_options.split(',')
        for option in options:
            if 'start' in option:
                try: start_y = float(option.split(' ')[-1])
                except: pass
            elif 'stop' in option:
                try: stop_y = float(option.split(' ')[-1])
                except: pass
        if not np.isnan(start_y) or not np.isnan(stop_y):
            step_y = (stop_y - start_y) / (nbpts_y - 1)

        # 1.2 for X try to deduce start/stop from the data
        array_x = self.data[0][:,0]
        range_x = self._findSweepRange1D(array_x)
            
        self.data_dict['x']['range'] = range_x
        self.data_dict['y']['range'] = [start_y, stop_y, nbpts_y, step_y]

    def _findHLLogValues(self, headers):
        logs = {} # {dev_name: value, ... }
        for line in headers:
            if not line.startswith('#com ...:='): continue
            try:
                dev_name = line.split(' ')[2]
                dev_name = dev_name[:-1]
                value = line.split(' ')[-1]
                value = value.replace('\n', '')
                logs[dev_name] = value
            except:
                pass
        return logs
    
    def _findConfigAndComments(self, headers):
        comments = []
        config = []
        for line in headers:
            if line.startswith('#comment:=') or line.startswith('#com ...:='):
                comments.append(line[10:])
            else:
                config.append(line)
        return config, comments

    def _findBeforeWait(self, headers):
        sweep_multi_option = headers[-3]
        # "#sweep_multi_options:= {..., 'beforewait': [0.02, 0.02], ... };\n"
        # or "#sweep_multi_options:= {..., 'beforewait': [0.02], ... };\n"
        beforewait = []
        try:
            beforewait = sweep_multi_option.split('beforewait\': [')[1].split(']')[0]
            beforewait = beforewait.split(',')
            for i, bw in enumerate(beforewait):
                beforewait[i] = float(bw)
        except:
            beforewait = np.nan
        return beforewait




    def readfile(self):
        try:
            self.data, self.titles, self.headers = c.readfile(self.filepath, getheaders=True, multi_sweep='force')
        except:
            try:
                self.data, self.titles, self.headers = c.readfile(self.filepath, getheaders=True, multi_sweep=False)
            except Exception as e:
                raise e


        if self.data[0].ndim == 1:
            self.data_dict['sweep_dim'] = 1
            self._build1DDataDict()
        elif self.data[0].ndim == 2:
            self.data_dict['sweep_dim'] = 2
            self._build2dDataDict()

        self.data_dict['beforewait'] = self._findBeforeWait(self.headers)
        config, comment = self._findConfigAndComments(self.headers)
        self.data_dict['config'] = config
        self.data_dict['comments'] = comment

            
    def getData(self, title, alternate=False):
        # get the data array corresponding to the title
        # search in the out titles and data
        if title in self.data_dict['out']['titles']:
            i = self.data_dict['out']['titles'].index(title)
            data_cp = self.data_dict['out']['data'][i].copy()
        # search in the computed_out titles and data
        elif title in self.data_dict['computed_out']['titles']:
            i = self.data_dict['computed_out']['titles'].index(title)
            data_cp = self.data_dict['computed_out']['data'][i].copy()
        # alternate data if needed
        if self.data_dict['sweep_dim'] == 2:
            if alternate:
                # flip odd rows
                data_cp[1::2] = data_cp[1::2, ::-1]
        # transpose by default
        return data_cp.T



    # -- POLAR/CARTESIAN CONVERSION --

    def clearComputedData(self):
        self.data_dict['computed_out']['titles'] = []
        self.data_dict['computed_out']['data'] = []
    
    def genXYData(self, r_title, deg_title, alternate=False):
        # from the r aneg titles, gen new out titles and data arrays for x and y
        r_data = self.getData(r_title, alternate=alternate)
        deg_data = self.getData(deg_title, alternate=alternate)
        x_data = r_data * np.cos(np.radians(deg_data))
        y_data = r_data * np.sin(np.radians(deg_data))

        self.clearComputedData()
        self.data_dict['computed_out']['titles'].append(r_title + '_X')
        self.data_dict['computed_out']['titles'].append(deg_title + '_Y')
        self.data_dict['computed_out']['data'].append(x_data)
        self.data_dict['computed_out']['data'].append(y_data)

    def genPolarData(self, x_title, y_title, alternate=False):
        # from the x and y titles, gen new out titles and data arrays for r and deg
        x_data = self.getData(x_title, alternate=alternate)
        y_data = self.getData(y_title, alternate=alternate)
        r_data = np.sqrt(x_data**2 + y_data**2)
        deg_data = np.arctan2(y_data, x_data)
        deg_data = np.degrees(deg_data)
        
        self.clearComputedData()
        self.data_dict['computed_out']['titles'].append(x_title + '_R')
        self.data_dict['computed_out']['titles'].append(y_title + '_DEG')
        self.data_dict['computed_out']['data'].append(r_data)
        self.data_dict['computed_out']['data'].append(deg_data)


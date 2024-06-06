from matplotlib.widgets import AxesWidget
import matplotlib.lines as lines

import numpy as np
from PyQt5.QtCore import Qt


# blitted line:
class ResizableLine():
    
    def __init__(self, parent):
        self.parent = parent
        
        self.line = lines.Line2D([0,0], [0.3,0.4], picker=5)
        self.parent.ax.add_line(self.line)
        
        self.parent.figure.canvas.mpl_connect('pick_event', self.onPick)
    
    def onPick(self, event):
        thisline = event.artist
        xdata = thisline.get_xdata()
        ydata = thisline.get_ydata()
        print('line picked:', xdata, ydata)

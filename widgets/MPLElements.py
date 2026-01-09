from matplotlib.widgets import AxesWidget
import matplotlib.lines as lines

import numpy as np
from PyQt5.QtCore import Qt

class ResizableLine():
    
    def __init__(self, parent, visible=True, color='black'):
        self.parent = parent
        self.action_button = None
        
        self.follow_mouse = False
        self.active_point = 0
        
        self.line = lines.Line2D([0,0], [0.3,0.4], picker=5, color=color)
        self.parent.ax.add_line(self.line)
        
        self.line.set_visible(visible)
        self.visible = visible

    
    def setPosition(self, x0, y0, x1, y1):
        self.line.set_xdata([x0, x1])
        self.line.set_ydata([y0, y1])

    def toggleActive(self):
        self.line.set_visible(not self.line.get_visible())
        self.visible = self.line.get_visible()
        self.parent.canvas.draw()
    
    def onPick(self, event):
        thisline = event.artist
        xdata = thisline.get_xdata()
        ydata = thisline.get_ydata()
        # find the point that is closest to the click
        clickx = event.mouseevent.xdata
        clicky = event.mouseevent.ydata
        if clickx is None or clicky is None:
            return
        if abs(clickx - xdata[0]) < abs(clickx - xdata[1]):
            self.active_point = 0
        else:
            self.active_point = 1
        self.follow_mouse = True
        self.parent.cursor.visible = False
        self.parent.canvas.mpl_connect('motion_notify_event', self.onMotion)
        self.parent.canvas.mpl_connect('button_release_event', self.onRelease)

    def onMotion(self, event):
        if not self.follow_mouse: return
        if event.xdata is None or event.ydata is None:
            return
        xdata = self.line.get_xdata()
        ydata = self.line.get_ydata()
        if self.active_point == 0:
            xdata[0] = event.xdata
            ydata[0] = event.ydata
        else:
            xdata[1] = event.xdata
            ydata[1] = event.ydata
        self.line.set_xdata(xdata)
        self.line.set_ydata(ydata)
        
        # set text
        self.action_button.setText(self.makeText(xdata[0], ydata[0], xdata[1], ydata[1]))

        self.parent.canvas.draw()
    
    def onRelease(self, event):
        self.follow_mouse = False
        self.parent.cursor.visible = True
        self.parent.canvas.mpl_disconnect(self.onMotion)
        self.parent.canvas.mpl_disconnect(self.onRelease)
    
    def makeText(self, x0, y0, x1, y1):
        # <color>Line: \n slope: <slope> \n deltaX: <deltaX> \n deltaY: <deltaY>
        dx = x1 - x0
        dy = y1 - y0
        slope = np.inf if dx == 0 else dy / dx
        return f'Line: slope: {slope:.3g} \n deltaX: {dx:.3g} deltaY: {dy:.3g}'



class Markers():
    def __init__(self, parent, orientation='v', visible=True, color='green'):
        self.parent = parent
        self.action_button = None

        self.orientation = orientation
        self.visible = False
        
        self.follow_mouse = False
        self.active_line = 0
        
        if orientation == 'v':
            self.line1 = self.parent.ax.axvline(0, color=color, picker=5)
            self.line2 = self.parent.ax.axvline(1, color=color, picker=5)
        elif orientation == 'h':
            self.line1 = self.parent.ax.axhline(0, color=color, picker=5)
            self.line2 = self.parent.ax.axhline(1, color=color, picker=5)
        self.lines = [self.line1, self.line2]
        
        self.line1.set_visible(visible)
        self.line2.set_visible(visible)
    
    def setPosition(self, coord_l1, coord_l2): # x or y depending on orientation
        #print('coord_l1:', coord_l1, 'coord_l2:', coord_l2)
        if self.orientation == 'v':
            self.line1.set_xdata([coord_l1, coord_l1])
            self.line2.set_xdata([coord_l2, coord_l2])
        elif self.orientation == 'h':
            self.line1.set_ydata([coord_l1, coord_l1])
            self.line2.set_ydata([coord_l2, coord_l2])

    def toggleActive(self):
        self.line1.set_visible(not self.line1.get_visible())
        self.line2.set_visible(not self.line2.get_visible())
        self.visible = self.line1.get_visible()
        #print('position:', self.line1.get_xdata(), self.line1.get_ydata())
        self.parent.canvas.draw()
    
    def onPick(self, event):
        line = event.artist
        if line == self.line1: self.active_line = 0
        elif line == self.line2: self.active_line = 1
        xdata = line.get_xdata()
        ydata = line.get_ydata()
        # find the point that is closest to the click
        self.follow_mouse = True
        self.parent.cursor.visible = False
        self.parent.canvas.mpl_connect('motion_notify_event', self.onMotion)
        self.parent.canvas.mpl_connect('button_release_event', self.onRelease)
    
    def onMotion(self, event):
        if not self.follow_mouse: return
        if event.xdata is None or event.ydata is None:
            return
        non_active_line = 1 if self.active_line == 0 else 0
        if self.orientation == 'v':
            self.lines[self.active_line].set_xdata([event.xdata, event.xdata])
            text = self.makeText(event.xdata, self.lines[non_active_line].get_xdata()[0])
        elif self.orientation == 'h':
            self.lines[self.active_line].set_ydata([event.ydata, event.ydata])
            text = self.makeText(event.ydata, self.lines[non_active_line].get_ydata()[0])
        
        # set text
        self.action_button.setText(text)

        self.parent.canvas.draw()
    
    def onRelease(self, event):
        self.follow_mouse = False
        self.parent.cursor.visible = True
        self.parent.canvas.mpl_disconnect(self.onMotion)
        self.parent.canvas.mpl_disconnect(self.onRelease)
        
    def makeText(self, coord_l1, coord_l2):
        delta = abs(coord_l1 - coord_l2)
        label = { 'v': 'VMarks deltaX:', 'h': 'HMarks deltaY:' }
        return f'{label[self.orientation]} {delta:.3g}'
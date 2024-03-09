# -*- coding: utf-8 -*-
"""
Created on Wed Nov 11 10:39:32 2020

@author: devj2901
"""
from matplotlib.widgets import AxesWidget
import matplotlib.lines as lines
import numpy as np
from PyQt5.QtCore import Qt

class HorizontalCursor(AxesWidget):
    def __init__(self, ax, label, y1, y2, color = 'limegreen'):

        AxesWidget.__init__(self, ax)

        self.line1 = self.ax.axhline(y = y1, visible=False, markersize=6, color=color)
        self.line2 = self.ax.axhline(y = y2, visible=False, markersize=6, color=color)

        self.Dy = abs(y1-y2)
        self.dy = abs(y1-y2)/70
        self.label = label
        
        self.connect_event('button_press_event', self.click)
        self.connect_event('button_release_event', self.click)
        self.connect_event('motion_notify_event', self.update)

        self.dragging_1 = False
        self.dragging_2 = False
        self.visible = False

    def click(self, event):
        if event.name == 'button_press_event' and event.inaxes == self.ax and self.visible:
            if abs(event.ydata-self.line1.get_ydata()[0])<self.dy:
                self.dragging_1 = True
            elif abs(event.ydata-self.line2.get_ydata()[0])<self.dy:
                self.dragging_2 = True
            event.canvas.grab_mouse(self.ax)

        if event.name == 'button_release_event' or event.inaxes != self.ax:
            self.dragging_1 = False
            self.dragging_2 = False
            event.canvas.release_mouse(self.ax)

    def update(self, event):
        if self.dragging_1:
            self.line1.set_ydata([event.ydata, event.ydata])
        elif self.dragging_2:
            self.line2.set_ydata([event.ydata, event.ydata])
        else:
            return
        self.Dy = abs(self.line1.get_ydata()[0]-self.line2.get_ydata()[0])
        self.ax.figure.canvas.draw()
        self.setLabel()

    def reinitialize_Ax(self, color = 'limegreen'):
        y1 = self.line1.get_ydata()[0]
        y2 = self.line2.get_ydata()[0]
        self.line1 = self.ax.axvline(y = y1, visible=False, markersize=6, color=color)
        self.line2 = self.ax.axvline(y = y2, visible=False, markersize=6, color=color)

    def setLabel(self):
        if self.visible:
            s = str('Δ')+'y = {Dy:.3e}'.format(Dy=self.Dy)
            self.label.setText(s)
        else:
            self.label.setText('')
            
    def getY(self):
        y1 = self.line1.get_ydata()[0]
        y2 = self.line2.get_ydata()[0]
        return y1, y2
            
    def checkBox_visible(self):
        """
        When click on checkbox, lines are set to visible or not
        """
        if self.checkBox.checkState() == Qt.Checked: self.setVisible(True)
        else: self.setVisible(False)
        self.ax.figure.canvas.draw()
        
    def setVisible(self, boo):
        self.line1.set_visible(boo)
        self.line2.set_visible(boo)
        self.visible = boo
        self.setLabel()


class VerticalCursor(AxesWidget):
    def __init__(self, ax, label, checkBox, x1, x2, color = 'limegreen'):

        AxesWidget.__init__(self, ax)
        
        self.line1 = self.ax.axvline(x = x1, visible=False, markersize=6, color=color)
        self.line2 = self.ax.axvline(x = x2, visible=False, markersize=6, color=color)
 
        self.Dx = abs(x1-x2)
        self.dx = abs(x1-x2)/70
        self.label = label
        self.checkBox = checkBox
        
        self.checkBox.stateChanged.connect(self.checkBox_visible)
        self.connect_event('button_press_event', self.click)
        self.connect_event('button_release_event', self.click)
        self.connect_event('motion_notify_event', self.update)

        self.dragging_1 = False
        self.dragging_2 = False
        self.visible = False

    def click(self, event):
        if event.name == 'button_press_event' and event.inaxes == self.ax and self.visible:
            if abs(event.xdata-self.line1.get_xdata()[0])<self.dx:
                self.dragging_1 = True
            elif abs(event.xdata-self.line2.get_xdata()[0])<self.dx:
                self.dragging_2 = True
            event.canvas.grab_mouse(self.ax)

        if event.name == 'button_release_event' or event.inaxes != self.ax:
            self.dragging_1 = False
            self.dragging_2 = False
            event.canvas.release_mouse(self.ax)

    def update(self, event):
        if event.inaxes is self.ax:
            if self.dragging_1:
                self.line1.set_xdata([event.xdata, event.xdata])
            elif self.dragging_2:
                self.line2.set_xdata([event.xdata, event.xdata])
            self.Dx = abs(self.line1.get_xdata()[0]-self.line2.get_xdata()[0])
            self.ax.figure.canvas.draw()
            self.setLabel()

    def reinitialize_Ax(self, color = 'limegreen'):
        x1 = self.line1.get_xdata()[0]
        x2 = self.line2.get_xdata()[0]
        self.line1 = self.ax.axvline(x = x1, visible=False, markersize=6, color=color)
        self.line2 = self.ax.axvline(x = x2, visible=False, markersize=6, color=color)

    def setLabel(self):
        if self.visible:
            s = str('Δ')+'x = {Dx: .3e}'.format(Dx=self.Dx)
            self.label.setText(s)
        else:
            self.label.setText('')
            
    def getX(self):
        x1 = self.line1.get_xdata()[0]
        x2 = self.line2.get_xdata()[0]
        return x1, x2
            
    def checkBox_visible(self):
        if self.checkBox.checkState() == Qt.Checked: self.setVisible(True)
        else: self.setVisible(False)
        self.ax.figure.canvas.draw()

    def setVisible(self, boo):
        self.line1.set_visible(boo)
        self.line2.set_visible(boo)
        self.visible = boo
        self.setLabel()
        
class ResizableLine(AxesWidget):
    def __init__(self, ax, x1, y1, x2, y2, color='black'):
        AxesWidget.__init__(self, ax)
        
        self.line = lines.Line2D([x1,x2],[y1,y2], visible=False, lw=1, ls='--', color=color)
        self.ax.add_artist(self.line)
        
        self.dx = abs(x1-x2)/70
        self.dy = abs(y1-y2)/70
        self.label = None
        
        self.connect_event('button_press_event', self.click)
        self.connect_event('button_release_event', self.click)
        self.connect_event('motion_notify_event', self.update)
        
        self.dragEnd_1 = False
        self.dragEnd_2 = False
        self.visible = False
        self.pente = 0
    
    def onEnd_1(self, event):
        return abs(event.ydata-self.line.get_ydata()[0])<self.dy and \
                abs(event.xdata-self.line.get_xdata()[0])<self.dx
    def onEnd_2(self, event):
        return abs(event.ydata-self.line.get_ydata()[1])<self.dy and \
                abs(event.xdata-self.line.get_xdata()[1])<self.dx
    def onLine(self, event):
        x1, y1 = self.line.get_xdata()[0], self.line.get_ydata()[0]
        x2, y2 = self.line.get_xdata()[1], self.line.get_ydata()[1]
        x0, y0 = event.xdata, event.ydata
        # check if mouse is on the line
        return abs((y2-y1)*x0 - (x2-x1)*y0 + x2*y1 - y2*x1) < 0.01*np.sqrt((y2-y1)**2+(x2-x1)**2)
        
    def click(self, event):
        if not self.visible or event.inaxes is not self.ax:
            return
        if event.name == 'button_press_event':
            if self.onEnd_1(event): self.dragEnd_1 = True
            elif self.onEnd_2(event): self.dragEnd_2 = True
            #event.canvas.grab_mouse(self.ax)

        elif event.name == 'button_release_event':
            self.dragEnd_1 = False
            self.dragEnd_2 = False
            #event.canvas.release_mouse(self.ax)
            
    def update(self, event):
        if event.inaxes is not self.ax: return
        if not self.dragEnd_1 and not self.dragEnd_2:
            return

        if self.dragEnd_1: 
            self.line.set_data([event.xdata, self.line.get_xdata()[1]], [event.ydata, self.line.get_ydata()[1]])
        elif self.dragEnd_2:
            self.line.set_data([self.line.get_xdata()[0], event.xdata], [self.line.get_ydata()[0], event.ydata])
        self.ax.figure.canvas.draw()
        self.pente = (self.line.get_ydata()[1]-self.line.get_ydata()[0])/(self.line.get_xdata()[1]-self.line.get_xdata()[0])
        self.setLabel()
    
    def setLabel(self):
        if self.visible:
            s = '{p:.3e}'.format(p=self.pente)
            self.label.setText('Slope line: ' + s)
        else:
            self.label.setText('Slope line')
        
    def setVisible(self, boo):
        self.line.set_visible(boo)
        self.visible = boo
        self.setLabel()
    
    def toggleVisible(self):
        self.setVisible(not self.visible)
        self.ax.figure.canvas.draw()
    
    def setData(self, xdata, ydata):
        self.line.set_data(xdata, ydata)
        self.dx = abs(xdata[0]-xdata[1])/80
        self.dy = abs(ydata[0]-ydata[1])/80


class Crosshair(AxesWidget):
    def __init__(self, ax, color='black'):
        AxesWidget.__init__(self, ax)
        
        self.hline = lines.Line2D([0, 1], [0, 0], visible=False, lw=1, ls='--', color=color)
        self.vline = lines.Line2D([0, 0], [0, 1], visible=False, lw=1, ls='--', color=color)
        self.ax.add_artist(self.hline)
        self.ax.add_artist(self.vline)
        
        self.connect_event('motion_notify_event', self.mouse_move)
        self.visible = False
    
    def mouse_move(self, event):
        if event.inaxes is self.ax:
            if self.visible:
                self.hline.set_ydata([event.ydata, event.ydata])
                self.vline.set_xdata([event.xdata, event.xdata])
                self.hline.set_xdata([self.ax.get_xlim()[0], self.ax.get_xlim()[1]])
                self.vline.set_ydata([self.ax.get_ylim()[0], self.ax.get_ylim()[1]])
                self.ax.figure.canvas.draw()
    
    def toggleVisible(self):
        self.hline.set_visible(not self.visible)
        self.vline.set_visible(not self.visible)
        self.visible = not self.visible
        self.ax.figure.canvas.draw()

import sys, os
import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QAction
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib import colors

from matplotlib.widgets import Cursor
from widgets.MPLElements import ResizableLine, Markers

class MPLWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.setAcceptDrops(True)


        # Create a Matplotlib FigureCanvas and set up the layout
        self.figure = Figure()
        self.ax = self.figure.add_subplot(111)
        self.ax.autoscale(enable=False)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        
        self.actionTrace = QAction('Traces', self)
        self.actionTrace.setCheckable(True)
        self.actionPan = self.toolbar.actions()[4]
        self.actionZoom = self.toolbar.actions()[5]
        self.toolbar.insertAction(self.toolbar.actions()[6], self.actionTrace)
        self.actionZoom.toggled.connect(lambda boo: self.actionModeChanged(boo, 'ZOOM'))
        self.actionPan.toggled.connect(lambda boo: self.actionModeChanged(boo, 'PAN'))
        self.actionTrace.toggled.connect(lambda boo: self.actionModeChanged(boo, 'TRACE'))
        self._changing_mode = False # use to block signal
        
        self.toolbar.addSeparator()
        self.trace_action = self.toolbar.addAction('Trace window', self.traceActionClicked)
        self.trace_crosses = []

        # slope line copied from TraitementQuantique, 
        # TODO: do better, not redrawing the whole figure, if possible
        #self.line1 = ResizableLine(self.ax, 0, 0, 1, 1, name='line1')
        #self.line1.label = self.toolbar.addAction('line 1', self.line1.toggleVisible)
        #self.line2 = ResizableLine(self.ax, 0, 0, 1, 1, name='line2', color='green')
        #self.line2.label = self.toolbar.addAction('line 2', self.line2.toggleVisible)
        #self.line3 = ResizableLine(self.ax, 0, 0, 1, 1, name='line3', color='purple')
        #self.line3.label = self.toolbar.addAction('line 3', self.line3.toggleVisible)
        
        # crosshair
        #self.crosshair = Crosshair(self.ax)
        #self.action_crosshair = self.toolbar.addAction('Crosshair', self.crosshair.toggleVisible)


        self.line = None # line plot
        self.im = None # image
        self.bar = None # colorbar
        
        # cursor
        self.cursor = Cursor(self.ax, useblit=True, color='black', linewidth=1)
        def toggleCursor(boo):
            self.cursor.visible = not self.cursor.visible
        self.toggleCursor = toggleCursor
        
        # resizable line
        self.toolbar.addSeparator()
        self.resizable_line = ResizableLine(self, visible=False)
        self.line1_action = self.toolbar.addAction('Line', self.resizable_line.toggleActive)
        self.line1_action.setCheckable(True)
        self.resizable_line.action_button = self.line1_action
        
        # markers
        self.vmarkers = Markers(self, 'v', visible=False)
        self.hmarkers = Markers(self, 'h', visible=False)
        self.vmarkers_action = self.toolbar.addAction('VMarks', self.vmarkers.toggleActive)
        self.hmarkers_action = self.toolbar.addAction('HMarks', self.hmarkers.toggleActive)
        self.vmarkers_action.setCheckable(True)
        self.hmarkers_action.setCheckable(True)
        self.vmarkers.action_button = self.vmarkers_action
        self.hmarkers.action_button = self.hmarkers_action

        
        self.home_coords = (0, 1, 0, 1)
        self.home_cbar = (0, 1)
        # we redefine the home button behavior
        home = self.toolbar.actions()[0]
        home.disconnect()
        def onHomeTrig(boo):
            self.ax.set_xlim(self.home_coords[0], self.home_coords[1])
            self.ax.set_ylim(self.home_coords[2], self.home_coords[3])
            if self.bar:
                self.im.set_clim(*self.home_cbar)
            self.canvas.draw()
        home.triggered.connect(onHomeTrig)
        
        self.canvas.mpl_connect('button_press_event', self.onMouseClick)
        self.canvas.mpl_connect('pick_event', self.onPick)

    
    # HANDLING EVENTS
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls(): e.accept()
        else: e.ignore()
    
    def dropEvent(self, e):
        file_urls = [url.toLocalFile() for url in e.mimeData().urls()]
        if len(file_urls) > 1:
            self.write('I\'m sorry but one file at a time please...\n Or you can drop your folder to open it.')
            return
        if os.path.isdir(file_urls[0]):
            self.parent.controller.changePath(file_urls[0])
        else:
            self.parent.controller.openFile(file_urls[0])
            
    def actionModeChanged(self, boo, clicked=''):
        if self._changing_mode: return
        if clicked == 'ZOOM' or clicked == 'PAN':
            self._changing_mode = True
            self.actionTrace.setChecked(False)
            self.toggleCursor(False)
            self._changing_mode = False
        elif clicked == 'TRACE':
            self._changing_mode = True
            if self.actionPan.isChecked(): self.toolbar.pan()
            if self.actionZoom.isChecked(): self.toolbar.zoom()
            self.toggleCursor(True)
            self._changing_mode = False

    def onMouseClick(self, event):
        if event.inaxes != self.ax: return
        #print('click', event.xdata, event.ydata)
        if event.button == 1:
            if self.actionTrace.isChecked():
                self.parent.showTrace(event.xdata, event.ydata)
    
    def onPick(self, event):
        artist = event.artist
        if artist == self.resizable_line.line and self.resizable_line.visible:
            self.resizable_line.onPick(event)
        if artist in self.vmarkers.lines and self.vmarkers.visible:
            self.vmarkers.onPick(event)
        if artist in self.hmarkers.lines and self.hmarkers.visible:
            self.hmarkers.onPick(event)

    def traceActionClicked(self):
        self.parent.showTrace()
    def onNewTrace(self, x, y, color='black'):
        # add a cross to the graph
        self.trace_crosses.append(self.ax.plot(x, y, 'x', color=color)[0])
        self.canvas.draw()
    def clearCrosses(self):
        for cross in self.trace_crosses:
            cross.remove()
        self.trace_crosses = []
    # END OF HANDLING EVENTS
    

    def removeAll(self):
        if self.bar:
            self.bar.remove()
            self.bar = None
        if self.im:
            self.im.remove()
            self.im = None
        if self.line:
            self.line.remove()
            self.line = None
    
    def afterDisplay(self):
        #self.figure.tight_layout()
        # redraw trace crosses
        for cross in self.trace_crosses: self.ax.add_artist(cross)
        self.ax.add_artist(self.vmarkers.line1); self.ax.add_artist(self.vmarkers.line2)
        self.ax.add_artist(self.hmarkers.line1); self.ax.add_artist(self.hmarkers.line2)
        self.ax.add_artist(self.resizable_line.line)
        self.canvas.draw()
        print('end of afterDisplay')

    def displayImage(self, image_data, extent, plot_kwargs={}, is_new_data=False, is_new_file=False, cbar_min_max=(0,1)):
        self.removeAll()
        if is_new_file:
            self.clearCrosses()
            self.ax.cla()

        # titles
        title = plot_kwargs.pop('title', '')
        x_title = plot_kwargs.pop('xlabel', '')
        y_title = plot_kwargs.pop('ylabel', '')
        zlabel = plot_kwargs.pop('zlabel', '')
        self.ax.set_title(title)
        self.ax.set_xlabel(x_title)
        self.ax.set_ylabel(y_title)

        # plotting
        self.im = self.ax.imshow(image_data, origin='lower', aspect='auto', interpolation='nearest',
                                 extent=extent, **plot_kwargs)
        self.bar = self.figure.colorbar(self.im, ax=self.ax, label=zlabel)

        # colorbar limits
        data_min, data_max = np.nanmin(image_data), np.nanmax(image_data)
        self.im.set_clim(data_min+(data_max-data_min)*cbar_min_max[0], data_min+(data_max-data_min)*cbar_min_max[1])
        
        self.home_coords = self.ax.get_xlim() + self.ax.get_ylim()
        self.home_cbar = self.im.get_clim()
        
        if is_new_data:
            # set the line shorter than the image extent
            x0, x1, y0, y1 = extent
            x_padding = 0.1*(x1-x0)
            y_padding = 0.1*(y1-y0)
            self.resizable_line.setPosition(x0+x_padding, y0+y_padding, x1-x_padding, y1-y_padding)
            self.vmarkers.setPosition(x0+x_padding, x1-x_padding)
            self.hmarkers.setPosition(y0+y_padding, y1-y_padding)

        
        self.afterDisplay()

    def displayPlot(self, x_data, y_data, plot_kwargs={}, is_new_data=False, is_new_file=False):
        if is_new_file:
            self.clearCrosses()
            self.ax.cla()

        title = plot_kwargs.pop('title', '')
        x_title = plot_kwargs.pop('xlabel', '')
        y_title = plot_kwargs.pop('ylabel', '')
        self.ax.set_title(title)
        self.ax.set_xlabel(x_title)
        self.ax.set_ylabel(y_title)

        self.ax.grid(plot_kwargs.pop('grid', True))
        self.ax.set_yscale(plot_kwargs.pop('yscale', 'linear'))
        self.ax.set_xscale(plot_kwargs.pop('xscale', 'linear'))

        self.removeAll()
        self.line = self.ax.plot(x_data, y_data, **plot_kwargs)[0]
        
        # redefine home coord
        x_padding = 0.1*(np.nanmax(x_data)-np.nanmin(x_data))
        y_padding = 0.1*(np.nanmax(y_data)-np.nanmin(y_data))
        self.home_coords = (np.nanmin(x_data)-x_padding, np.nanmax(x_data)+x_padding, np.nanmin(y_data)-y_padding, np.nanmax(y_data)+y_padding)
        
        if is_new_data:
            x0, x1 = self.ax.get_xlim()
            y0, y1 = self.ax.get_ylim()
            x_padding = 0.1*(x1-x0)
            y_padding = 0.1*(y1-y0)
            self.resizable_line.setPosition(x0+x_padding, y0+y_padding, x1-x_padding, y1-y_padding)
            self.vmarkers.setPosition(x0+x_padding, x1-x_padding)
            self.hmarkers.setPosition(y0+y_padding, y1-y_padding)
        
        self.afterDisplay()
    
    def write(self, text):
        self.removeAll()
        self.ax.clear()
        loading_label = self.ax.text(0.5, 0.5, text, ha="center", va="center", fontsize=12, color="gray")
        self.canvas.draw()

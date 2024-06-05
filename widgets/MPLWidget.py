import sys, os
import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib import colors

from src.Cursors import ResizableLine, Crosshair

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
        
        self.toolbar.addSeparator()
        # slope line copied from TraitementQuantique, 
        # TODO: do better, not redrawing the whole figure, if possible
        self.line1 = ResizableLine(self.ax, 0, 0, 1, 1, name='line1')
        self.line1.label = self.toolbar.addAction('line 1', self.line1.toggleVisible)
        self.line2 = ResizableLine(self.ax, 0, 0, 1, 1, name='line2', color='green')
        self.line2.label = self.toolbar.addAction('line 2', self.line2.toggleVisible)
        self.line3 = ResizableLine(self.ax, 0, 0, 1, 1, name='line3', color='purple')
        self.line3.label = self.toolbar.addAction('line 3', self.line3.toggleVisible)
        
        # crosshair
        self.crosshair = Crosshair(self.ax)
        self.action_crosshair = self.toolbar.addAction('Crosshair', self.crosshair.toggleVisible)


        self.line = None # line
        self.im = None # image
        self.bar = None # colorbar
        
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
    
    # DROPPING THINGS:
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
    # END OF DROPPING THINGS
    
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
        self.canvas.draw()
        print('end of afterDisplay')

    def displayImage(self, image_data, extent, plot_kwargs={}, is_new_data=True):
        self.removeAll()
        if is_new_data:
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
        self.im.set_clim(np.nanmin(image_data), np.nanmax(image_data))
        
        self.home_coords = self.ax.get_xlim() + self.ax.get_ylim()
        self.home_cbar = self.im.get_clim()
        
        self.afterDisplay()

    def displayPlot(self, x_data, y_data, plot_kwargs={}, is_new_data=True):
        if is_new_data:
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
        
        self.home_coords = self.ax.get_xlim() + self.ax.get_ylim()
        
        self.afterDisplay()
    
    def write(self, text):
        self.removeAll()
        self.ax.clear()
        loading_label = self.ax.text(0.5, 0.5, text, ha="center", va="center", fontsize=12, color="gray")
        self.canvas.draw()

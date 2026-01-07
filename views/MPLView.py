import sys, os
import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QAction, QToolBar
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib import colors

from matplotlib.widgets import Cursor
from widgets.MPLElements import ResizableLine, Markers
from widgets.MPLToolbar import MPLToolbar

class MPLView(QWidget):

    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent

        self.figure = Figure()
        self.ax = self.figure.add_subplot(111)
        self.ax.autoscale(enable=True)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        
        # resizable line and markers
        self.resizable_line = ResizableLine(self, visible=False)
        self.vmarkers = Markers(self, 'v', visible=False)
        self.hmarkers = Markers(self, 'h', visible=False)
        # init toolbars:
        MPLToolbar(self)

        self.line = None # line plot
        self.im = None # image
        self.bar = None # colorbar
        self.text = None # text
        self.last_extent = (0,0,0,0)
        self.last_im_min_max = (0,0,0,0)
        self.last_im_clim = (0,0)

        # cursor / crosshair
        self.cursor = Cursor(self.ax, useblit=True, color='black', linewidth=1)
        self.setCursor = lambda boo: setattr(self.cursor, 'visible', boo)
        self.setCursor(False)

        self.canvas.mpl_connect('pick_event', self.onPick)
        self.canvas.mpl_connect('button_press_event', self.onMouseClick)

        self.last_plot_dict = {}

    def init1D(self):
        """ make a line for setData later """
        self.line = self.ax.plot(0, 0)[0]

    def plot1D(self, plot_dict):
        d = plot_dict

        self.plot_fns = {
            "x_title": self.ax.set_xlabel,
            "y_title": self.ax.set_ylabel,
            "x_or_y_data": self.line.set_data,
            "grid": lambda visible: self.ax.grid(visible=visible)
        }
        print(plot_dict)

        # set_data if x or y data has changed
        if (not np.array_equal(x_data, self.last_plot_dict.pop("x_data", None))) or \
            (not np.array_equal(y_data, self.last_plot_dict.pop("y_data", None))):
            self.plot_fns["x_or_y_data"](x_data, y_data)
            self.ax.relim()
            self.ax.autoscale_view()
            self.canvas.draw_idle()

        for key, val in plot_dict.items():
            # if val is different from before, exec the function
            if val != self.last_plot_dict.get(key, None):
                fn = self.plot_fns[key]
                fn(val)

    def plot1D_old(self,
            x_data,
            y_data,
            grid=False,
            is_first_time=True,
            plot_kwargs={},
        ):
        # CLEAR
        self.ax.clear()
        # PLOT
        self.ax.set_title(plot_kwargs.pop('title', ''))
        self.ax.set_xlabel(plot_kwargs.pop('xlabel', ''))
        self.ax.set_ylabel(plot_kwargs.pop('ylabel', ''))
        if grid:
            self.ax.grid()
        self.line = self.ax.plot(x_data, y_data)[0]
        # DRAW objects if lims changes
        self.ax.add_artist(self.resizable_line.line)
        self.ax.add_artist(self.vmarkers.line1); self.ax.add_artist(self.vmarkers.line2)
        self.ax.add_artist(self.hmarkers.line1); self.ax.add_artist(self.hmarkers.line2)
        extent = (np.min(x_data), np.max(x_data), np.min(y_data), np.max(y_data))
        if extent != self.last_extent:
            self.resizable_line.setPosition(
                np.min(x_data), np.min(y_data), 
                np.max(x_data), np.max(y_data))
            self.hmarkers.setPosition(np.min(y_data), np.max(y_data))
            self.vmarkers.setPosition(np.min(x_data), np.max(x_data))
            self.extent = extent

        self.canvas.draw_idle()
        if is_first_time:
            self.figure.tight_layout()
    
    def plot2D(self,
        image_data,
        extent,
        grid=False,
        is_first_time=False,
        keep_ax_lims=False,
        keep_cb_lims=False,
        plot_kwargs={},
    ):
        # CLEAR
        if self.bar:
            self.bar.remove()
            self.bar = None
        if self.im:
            last_ax_xlim, last_ax_ylim = self.ax.get_xlim(), self.ax.get_ylim()
            last_im_clim = self.im.get_clim()
        self.ax.clear()
        # PLOT
        self.ax.set_title(plot_kwargs.pop('title', ''))
        self.ax.set_xlabel(plot_kwargs.pop('xlabel', ''))
        self.ax.set_ylabel(plot_kwargs.pop('ylabel', ''))
        zlabel = plot_kwargs.pop('zlabel', '')
        if grid:
            self.ax.grid(color='#DDDDDD', linestyle='--', linewidth=0.8, alpha=0.3)

        # PLOT
        self.im = self.ax.imshow(
            image_data,
            origin='lower', 
            aspect='auto', 
            interpolation='nearest',
            extent=extent,
            **plot_kwargs
        )
        self.bar = self.figure.colorbar(self.im, ax=self.ax, label=zlabel)

        if keep_ax_lims and not is_first_time:
            self.ax.set_xlim(last_ax_xlim)
            self.ax.set_ylim(last_ax_ylim)
        if keep_cb_lims and not is_first_time:
            print("cb kept")
            self.im.set_clim(last_im_clim)

        # DRAW objects if extent changed
        self.ax.add_artist(self.resizable_line.line)
        self.ax.add_artist(self.vmarkers.line1); self.ax.add_artist(self.vmarkers.line2)
        self.ax.add_artist(self.hmarkers.line1); self.ax.add_artist(self.hmarkers.line2)
        if extent != self.last_extent:
            x0, x1, y0, y1 = extent
            self.resizable_line.setPosition(x0, y0, x1, y1)
            self.vmarkers.setPosition(x0, x1)
            self.hmarkers.setPosition(y0, y1)
            self.last_extent = extent


        self.canvas.draw_idle()
        if is_first_time: self.figure.tight_layout()


    # HANDLING EVENTS

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
    

    def remove_graph_elements(self):
        if self.bar:
            self.bar.remove()
            self.bar = None
        if self.im:
            self.im.remove()
            self.im = None
        if self.line:
            self.line.remove()
            self.line = None
        self.ax.clear()

    def write(self, text):
        self.remove_graph_elements()
        self.text = self.ax.text(0.5, 0.5, text, ha="center", va="center", fontsize=12, color="gray")
        self.canvas.draw()

def set_1d_ax_lim(ax, x_data, y_data, padding_factor=0.05):
    x_padding = padding_factor*(np.nanmax(x_data)-np.nanmin(x_data))
    y_padding = padding_factor*(np.nanmax(y_data)-np.nanmin(y_data))
    ax.set_xlim(np.nanmin(x_data)-x_padding, np.nanmax(x_data)+x_padding)
    ax.set_ylim(np.nanmin(y_data)-y_padding, np.nanmax(y_data)+y_padding)

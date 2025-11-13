
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.widgets import Cursor
from widgets.MPLElements import ResizableLine, Markers
import pyqtgraph as pg

# widget displayed when the user clicks on a point
# 2 plot displayed: the vertical and horizontal slice of the data
# TODO: clear on keypress

class MPLTraceWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent

        self.setWindowTitle('traces')
        icon = pg.QtGui.QIcon('./resources/icon.png')
        self.setWindowIcon(icon)
        
        # window height, width
        self.resize(800, 400)
        
        self.figure = Figure()
        self.axH = self.figure.add_subplot(121)
        self.axV = self.figure.add_subplot(122)

        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.clear_action = self.toolbar.addAction('Clear', self.parent.clearTraces)

        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        
        self.plotkw = {'marker': 'o', 'linestyle': '-', 'markersize': 3, 'linewidth': 1}

        self.color = ['royalblue','orange','forestgreen','red','darkviolet', 'peru', 'hotpink', 'lightslategray', 'olive', 'darkturquoise']
        self.color_index = -1
        
        self.checkboxes = []
        
        #self.cursorV = Cursor(self.axV, useblit=True, color='black', linewidth=1)
        #self.cursorH = Cursor(self.axH, useblit=True, color='black', linewidth=1)
        #self.resizable_lineV = ResizableLine(self, visible=False)
        #self.resizable_lineH = ResizableLine(self, visible=False)


        self.clear() # init plots
        
    def clear(self):
        self.axV.clear()
        self.axH.clear()
        self.axV.set_title('Vertical slice')
        self.axH.set_title('Horizontal slice')
        self.axV.set_xlabel('y')
        self.axH.set_ylabel('z')
        self.axH.set_xlabel('x')
        self.axV.grid(); self.axH.grid()
        self.color_index = -1
        self.canvas.draw()
    
    def getColor(self):
        self.color_index += 1
        return self.color[self.color_index % len(self.color)]
    
    def plotHorizontalTrace(self, x, y, color='tab:blue'):
        self.axH.plot(x, y, color, **self.plotkw)
        self.canvas.draw()
    
    def plotVerticalTrace(self, x, y, color='tab:blue'):
        self.axV.plot(x, y, color, **self.plotkw)
        self.canvas.draw()
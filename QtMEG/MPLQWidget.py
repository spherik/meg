from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

import numpy as np
################################################################################
# The QWidget containing the plot.
class MPLQWidget(FigureCanvas):
    def __init__(self, parent=None):

        # layout = QtGui.QVBoxLayout(self)
        # layout.setContentsMargins(0,0,0,0)
        # layout.setSpacing(0)
        # generate the plot
        self.fig = Figure( dpi=72, facecolor=(1,1,1), edgecolor=(0,0,0))
        FigureCanvas.__init__(self, self.fig)
        self.axes = self.fig.add_subplot(111)
        self.axes.plot([0,1])
        # generate the canvas to display the plot


        # If you want to debug, beware that you need to remove the Qt
        # input hook.
        #QtCore.pyqtRemoveInputHook()
        #import pdb ; pdb.set_trace()
        #QtCore.pyqtRestoreInputHook()

        # The edit_traits call will generate the widget to embed.
        # self.ui = self.visualization.edit_traits(parent=self,
        #                                          kind='subpanel').control
        #layout.addWidget(self.canvas)
        #self.ui.setParent(self)

        #cid = fig.canvas.mpl_connect('button_press_event', self.onclick)



    def SetSignals(self, signals, time_index = 0):
        self.axes.clear()
        self.axes.plot(signals+ np.arange(signals.shape[1]-1,-1,-1)*signals.max())
        #print(len(self.axes.lines))
        #self.axes.plot(np.zeros(signals.shape) + np.arange(signals.shape[1]-1,-1,-1),'--',color='gray');
        self.axes.axvline(x=time_index, color="k")
        self.time_mark_line = self.axes.lines[-1]
        #self.axes.set_xlim([0, 10])
        #self.axes.set_ylim([0, 100])

        self.draw()

    def SetTimeIndex(self, time_index = 0):
        #self.axes.lines = self.axes.lines[0:len(self.axes.lines)-1]
        #self.axes.axvline(x=time_index, color="k")
        self.time_mark_line.set_xdata(time_index)
        self.draw()

    # def mousePressEvent(self, event):
    #     print(event)
    #     print(self.fig.get_picker())
    #     #self.fig.canvas.
    def onclick(self,event):
        print(event)
        # print('%s click: button=%d, x=%d, y=%d, xdata=%f, ydata=%f' %
        #       ('double' if event.dblclick else 'single', event.button,
        #        event.x, event.y, event.xdata, event.ydata))

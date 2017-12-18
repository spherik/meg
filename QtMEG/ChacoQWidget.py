# First, and before importing any Enthought packages, set the ETS_TOOLKIT
# environment variable to qt4, to tell Traits that we will use Qt.
import os
os.environ['ETS_TOOLKIT'] = 'qt4'
# By default, the PySide binding will be used. If you want the PyQt bindings
# to be used, you need to set the QT_API environment variable to 'pyqt'
#os.environ['QT_API'] = 'pyqt'

# To be able to use PySide or PyQt4 and not run in conflicts with traits,
# we need to import QtGui and QtCore from pyface.qt
from pyface.qt import QtGui, QtCore
# Alternatively, you can bypass this line, but you need to make sure that
# the following lines are executed before the import of PyQT:
#   import sip
#   sip.setapi('QString', 2)

from traits.api import HasTraits, Instance, on_trait_change, Range
from traits.trait_numeric import Array
from traitsui.api import View, Item, VSplit,HGroup

from chaco.api import ArrayPlotData, Plot
from chaco.tools.api import PanTool, ZoomTool, LineInspector
from chaco.api import PlotLabel, DataRange1D, create_line_plot, LinePlot,ArrayDataSource,LinearMapper,PlotAxis
from chaco.multi_array_data_source import MultiArrayDataSource
from chaco.multi_line_plot import MultiLinePlot
from enable.api import ComponentEditor

import numpy as np
from scipy.special import jn


class DataModel(HasTraits):
    """This is the data to be plotted in the demo."""

    # The x values of the data (1D numpy array).
    x_index = Array()

    # The channel numbers (1D numpy array).
    y_index = Array()

    # The data.  The shape of this 2D array must be (y_index.size, x_index.size)
    data = Array()

################################################################################
#The actual visualization
class Visualization(HasTraits):

    # Data models
    dipole_data_model = Instance(DataModel)
    signals_data_model = Instance(DataModel)

    # Renderers
    # dipole_renderer = Instance(LinePlot)
    signals_renderer = Instance(MultiLinePlot)

    # Plots
    dipole_plot = Instance(LinePlot)
    signals_plot = Instance(Plot)


    def _signals_renderer_default(self):
        print('_signals_renderer_default')
        """Create the default MultiLinePlot instance."""

        xs = ArrayDataSource(self.signals_data_model.x_index, sort_order='ascending')
        xrange = DataRange1D()
        xrange.add(xs)

        ys = ArrayDataSource(self.signals_data_model.y_index, sort_order='ascending')
        yrange = DataRange1D()
        yrange.add(ys)

        # The data source for the MultiLinePlot.
        ds = MultiArrayDataSource(data=self.signals_data_model.data)

        multi_line_plot_renderer = \
            MultiLinePlot(
                index = xs,
                yindex = ys,
                index_mapper = LinearMapper(range=xrange),
                value_mapper = LinearMapper(range=yrange),
                value=ds,
                global_max = self.signals_data_model.data.max(),
                global_min = self.signals_data_model.data.min(),
                fast_clip = False)

        # Add pan tool
        multi_line_plot_renderer.tools.append(PanTool(multi_line_plot_renderer, restrict_to_data = True))

        # Add zoom tool
        multi_line_plot_renderer.overlays.append(ZoomTool(multi_line_plot_renderer, tool_mode="range", always_on=False,
                                                            x_max_zoom_factor = 20.0, y_max_zoom_factor = 20.0,
                                                            x_min_zoom_factor = 1.0, y_min_zoom_factor = 1.0,
                                                            zoom_to_mouse = True))
        #multi_line_plot_renderer.overlays.append(LineInspector(multi_line_plot_renderer, axis="index",write_metadata=True,is_listener=True))
        # multi_line_plot_renderer.overlays.append(LineInspector(multi_line_plot_renderer, axis='value',
        #                                         write_metadata=True,
        #                                         is_listener=True))
        multi_line_plot_renderer.overlays.append(LineInspector(multi_line_plot_renderer, axis="index",
                                                write_metadata=True,
                                                is_listener=True))
        return multi_line_plot_renderer

    # def _dipole_renderer_default(self):
    #     print("_dipole_renderer_default")
    #     xs = ArrayDataSource(self.dipole_data_model.x_index, sort_order='ascending')
    #     xrange = DataRange1D()
    #     xrange.add(xs)
    #     xm = LinearMapper(range = xrange)
    #
    #     ys = ArrayDataSource(self.dipole_data_model.data, sort_order='ascending')
    #     yrange = DataRange1D()
    #     yrange.add(ys)
    #     ym = LinearMapper(range=yrange)
    #
    #     #pd = ArrayPlotData(index = self.dipole_data_model.x_index)
    #     pd = ArrayDataSource(data = self.dipole_data_model.data)
    #     #pd.set_data("y", self.dipole_data_model.data)
    #
    #     line_plot_renderer = LinePlot(index = xs,
    #                                   value=pd,
    #                                   index_mapper = LinearMapper(range=xrange),
    #                                   value_mapper = LinearMapper(range=yrange),
    #                                   global_max = self.dipole_data_model.data.max(),
    #                                   global_min = self.dipole_data_model.data.min(),
    #                                   fast_clip = False)
    #     return line_plot_renderer


    def _signals_plot_default(self):
        print('_signals_plot_default')
        """Create the Plot instance."""

        plot = Plot()

        plot.add(self.signals_renderer)

        x_axis = PlotAxis(component=plot,
                            mapper=self.signals_renderer.index_mapper,
                            orientation='bottom')
        # y_axis = PlotAxis(component=plot,
        #                     mapper=self.signals_renderer.value_mapper,
        #                     orientation='left')
        plot.overlays.extend([x_axis])

        plot.origin_axis_visible = False
        plot.padding_top = 0
        plot.padding_left = 0
        plot.padding_right = 0
        plot.padding_bottom = 50
        plot.border_visible = False
        plot.bgcolor = "white"
        plot.use_downsampling = True
        return plot

    def _dipole_plot_default(self):
        print('_dipole_plot_default')
        """Create the Plot instance."""


        #pd = ArrayPlotData(index = self.dipole_data_model.x_index)
        #pd.set_data("y", self.dipole_data_model.data)

        plot = create_line_plot((self.dipole_data_model.x_index, self.dipole_data_model.data),color='black')
        #plot.add(self.dipole_renderer)
        #plot.plot(("index", "y"))

        x_axis = PlotAxis(component=plot,
                            mapper=plot.index_mapper,
                            orientation='bottom')
        # # y_axis = PlotAxis(component=plot,
        # #                     mapper=self.signals_renderer.value_mapper,
        # #                     orientation='left')
        plot.overlays.extend([x_axis])
        plot.index = self.signals_renderer.index
        plot.overlays.append(LineInspector(plot, write_metadata=True,
                                  is_listener=True))
        # plot.overlays.append(LineInspector(plot, axis="value",
        #                           is_listener=True))

        plot.origin_axis_visible = False
        plot.padding_top = 0
        plot.padding_left = 0
        plot.padding_right = 0
        plot.padding_bottom = 50
        plot.border_visible = False
        plot.bgcolor = "white"
        plot.use_downsampling = True
        return plot

    def _signals_data_model_changed(self, old, new):
        print('model_changed')

        xs = ArrayDataSource(self.signals_data_model.x_index, sort_order='ascending')
        xrange = DataRange1D()
        xrange.add(xs)

        ys = ArrayDataSource(self.signals_data_model.y_index, sort_order='ascending')
        yrange = DataRange1D()
        yrange.add(ys)

        # The data source for the MultiLinePlot.
        print('ds')
        ds = MultiArrayDataSource(data=self.signals_data_model.data)

        self.signals_renderer.set(index = xs, yindex = ys,
                                #index_mapper = LinearMapper(range=xrange), value_mapper = LinearMapper(range=yrange),
                                value=ds,
                                global_max = self.signals_data_model.data.max(),
                                global_min = self.signals_data_model.data.min())
        self.signals_renderer.index_mapper.range = xrange
        self.signals_renderer.value_mapper.range = yrange
        self.signals_renderer.request_redraw()

    def _dipole_data_model_changed(self, old, new):
        print('dipole_data_model_changed')
        #self.dipole_plot.index_range = self.signals_renderer.index_range
        #self.dipole_plot.index = self.signals_renderer.index
        print(dir(self.dipole_data_model.x_index))
        xs = ArrayDataSource(self.dipole_data_model.x_index, sort_order='ascending')
        xrange = DataRange1D()
        xrange.add(xs)

        self.dipole_plot.index.set_data(self.dipole_data_model.x_index)
        self.dipole_plot.value.set_data(self.dipole_data_model.data)

        self.dipole_plot.index_mapper.range = xrange

        self.dipole_plot.request_redraw()

    # def _time_default(self):
    #     numpoints = 1000.0
    #     low = -5
    #     high = 15
    #     time = np.arange(low, high, (high-low)/numpoints).tolist()
    #     return time
    #
    # def _dipole_signal_default(self):
    #     signal = jn(10, self.time)
    #     return signal
    #
    # def _signals_default(self):
    #     numpoints = 1000
    #     signals = [] #np.zeros((10, numpoints))
    #     for i in range(10):
    #         signals.append(jn(i, self.time))
    #     return signals
    #
    # def _dipole_plot_default(self):
    #     plot = create_line_plot((self.time, self.dipole_signal), color = 'black')
    #     plot.origin_axis_visible = False
    #     plot.origin = "top left"
    #     plot.border_visible = False
    #     plot.bgcolor = "white"
    #     return plot
    #
    # def _plots_container_default(self):
    #     container = VPlotContainer()
    #     # Plot some bessel functions
    #     value_range = None
    #     for i in range(10):
    #         plot = create_line_plot((self.time,self.signals[i,:]), width=2.0)#color=tuple(COLOR_PALETTE[i]), width=2.0)
    #         plot.origin_axis_visible = False
    #         plot.origin = "top left"
    #         plot.border_visible = False
    #         plot.bgcolor = "white"
    #         if value_range is None:
    #             value_range = plot.value_mapper.range
    #         else:
    #             plot.value_range = value_range
    #             value_range.add(plot.value)
    #         # if i%2 == 1:
    #         #     plot.line_style = "dash"
    #         container.add(plot)
    #     return container
    #
    # def _signals_changed(self, old, new):
    #     #self.signals.values = new
    #     print("_signals_changed")
    #     print(dir(self.plots_container))
    #
    # def _dipole_signal_changed(self, old, new):
    #     #self.signals.values = new
    #     print("_signals_changed")
    #     self.dipole_plot.set(y_values = new)
    #     self.dipole_plot.draw()
    #     #print(dir(self.dipole_plot))
    # #     self.dipole_plot.
    #
    # def zoom_in(self, zoom_factor = 1.0):
    #     print('zoom')
    #     #for i,s in enumerate(self.plots_container):
    #         #self.plots_container.

    # @on_trait_change('scene.activated')
    # def update_plot(self):
    #     # This function is called when the view is opened. We don't
    #     # populate the scene when the view is not yet open, as some
    #     # VTK features require a GLContext.
    #
    #     # We can do normal mlab calls on the embedded scene.
    #     self.scene.mlab.test_points3d()

    # Drives multi_line_plot_renderer.normalized_amplitude
    amplitude = Range(0.0, 3.0, value=1.0)

    # Drives multi_line_plot_renderer.offset
    offset = Range(-1.0, 1.0, value=0)

    # Drives multi_line_plot_renderer.scaler
    scale = Range(0.0,2.0, value = 1.0)

    #-----------------------------------------------------------------------
    # Trait change handlers
    #-----------------------------------------------------------------------

    def _amplitude_changed(self, amp):
        self.signals_renderer.normalized_amplitude = amp

    def _offset_changed(self, off):
        self.signals_renderer.offset = off
        # FIXME:  The change does not trigger a redraw.  Force a redraw by
        # faking an amplitude change.
        self.signals_renderer._amplitude_changed()

    def _scale_changed(self, sca):
        self.signals_renderer.scale = sca
        self.signals_renderer._amplitude_changed()

    # the layout of the dialog screated
    view = View(VSplit(
                Item('dipole_plot',editor=ComponentEditor(), show_label=False, height = 75),
                Item('signals_plot',editor=ComponentEditor(), show_label=False)),
                #HGroup(
                    Item('amplitude'),
                    Item('offset'),
                    Item('scale'),
#                    springy=True,
                #),
                width=500, height=500,
                resizable=True)



################################################################################
# The QWidget containing the visualization, this is pure PyQt4 code.
class ChacoQWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        layout = QtGui.QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)


        # Sample rate.
        fs = 500
        # Total time.
        T = 10.0
        num_samples = fs * T
        t = np.arange(num_samples) / fs

        channels = np.arange(12)
        # Frequencies of the sine functions in each channel.
        freqs = 3*(channels[:,None] + 1)
        y = np.sin(freqs * t)

        # Create an instance of DataModel.  This is the data to
        # be plotted with a MultiLinePlot.
        signals = DataModel(x_index=t, y_index=channels, data=y)
        dipole_signal = DataModel(x_index = t, y_index = [0] ,data = y[0,:].T)
        # Create the demo class, and show it.
        self.visualization = Visualization(signals_data_model=signals, dipole_data_model = dipole_signal)

        # If you want to debug, beware that you need to remove the Qt
        # input hook.
        #QtCore.pyqtRemoveInputHook()
        #import pdb ; pdb.set_trace()
        #QtCore.pyqtRestoreInputHook()

        # The edit_traits call will generate the widget to embed.
        self.ui = self.visualization.edit_traits(parent=self,
                                                 kind='subpanel').control
        layout.addWidget(self.ui)
        self.ui.setParent(self)

    def SetSignals(self, time, signals, time_index = 0):
        print('SetSignals')
        print(time.shape)
        print(np.arange(signals.shape[0])).shape
        print(signals.shape)
        data = DataModel(x_index = time, y_index = np.arange(signals.shape[0]), data = signals)

        self.visualization.set(signals_data_model = data)
        #self.visualization.set_signals()

    def SetDipoleSignal(self, time, dipole_signal):
        data = DataModel(x_index = time, y_index = [0], data = dipole_signal)

        self.visualization.set(dipole_data_model = data)

    def SetTimeIndex(self, index):
        print('SetTimeIndex')

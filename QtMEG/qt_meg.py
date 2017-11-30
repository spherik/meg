#!/Users/spherik/anaconda3/envs/mayavi_env/bin/python
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

from traits.api import HasTraits, Instance, on_trait_change
from traitsui.api import View, Item
from mayavi.core.api import Engine
from mayavi.core.ui.api import MayaviScene, MlabSceneModel, \
        SceneEditor
from tvtk.pyface.api import Scene
import matplotlib
matplotlib.use('Qt4Agg')

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import scipy.io as sio
import numpy as np
################################################################################
#The actual visualization
class Visualization(HasTraits):
    engine1 = Instance(Engine, args=())
    scene = Instance(MlabSceneModel, ())

    def _scene1_default(self):
        " The default initializer for 'scene1' "
        self.engine1.start()
        scene1 = MlabSceneModel(engine=self.engine1)
        return scene1

    # @on_trait_change('scene.activated')
    # def update_plot(self):
    #     # This function is called when the view is opened. We don't
    #     # populate the scene when the view is not yet open, as some
    #     # VTK features require a GLContext.
    #
    #     # We can do normal mlab calls on the embedded scene.
    #     self.scene.mlab.test_points3d()

    # the layout of the dialog screated
    view = View(Item('scene', editor=SceneEditor(scene_class=Scene),
                     show_label=False),
                resizable=True # We need this to resize with the parent widget
                )

################################################################################
# The QWidget containing the plot.
class MPLQWidget(FigureCanvas):
    def __init__(self, parent=None):

        # layout = QtGui.QVBoxLayout(self)
        # layout.setContentsMargins(0,0,0,0)
        # layout.setSpacing(0)
        # generate the plot
        fig = Figure( dpi=72, facecolor=(1,1,1), edgecolor=(0,0,0))
        ax = fig.add_subplot(111)
        ax.plot([0,1])
        # generate the canvas to display the plot
        FigureCanvas.__init__(self, fig)

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


################################################################################
# The QWidget containing the visualization, this is pure PyQt4 code.
class MayaviQWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        layout = QtGui.QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)
        self.visualization = Visualization()

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

    def SetPoints(self,x = None, y = None, z = None, scalars = None):
        #self.visualization.scene.clf()
        if not hasattr(self, 'virtual_sensors_3D'):
            self.virtual_sensors_3D = self.visualization.scene.mlab.points3d(x,y,z,scalars)
            self.virtual_sensors_3D.glyph.glyph.scale_mode = 'data_scaling_off'
            self.virtual_sensors_3D.glyph.scale_mode = 'data_scaling_off'
            self.virtual_sensors_3D.glyph.glyph.scale_factor = 0.003
            self.visualization.scene.reset_zoom()
        else:
            self.visualization.scene.disable_render = True
            self.virtual_sensors_3D.mlab_source.reset(x = x, y = y,z = z,scalars = scalars)
            self.virtual_sensors_3D.mlab_source.set(x = x, y = y,z = z,scalars = scalars)
            self.visualization.scene.disable_render = False



    def SetScalarsRange(self, min_value = 0.0, max_value = 1.0):
        # Setup lut
        self.virtual_sensors_3D.module_manager.scalar_lut_manager.use_default_range = False
        self.virtual_sensors_3D.module_manager.scalar_lut_manager.lut._vtk_obj.SetTableRange(min_value, max_value)
        self.virtual_sensors_3D.module_manager.scalar_lut_manager.lut_mode = 'magma'

    def ToggleScalarBarVisibility(self, visible):
        self.virtual_sensors_3D.module_manager.scalar_lut_manager.show_scalar_bar = True
        self.virtual_sensors_3D.module_manager.scalar_lut_manager.show_legend = True

    def SetScalars(self,scalars = None):
        self.visualization.scene.disable_render = True
        self.virtual_sensors_3D.mlab_source.set(scalars = scalars)
        self.visualization.scene.disable_render = False

################################################################################
# The QMainWindow
class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self._BuildLayout()
        self._BuildMenu()

    def _OpenMatFile(self):
        title = "Select mat file"
        filename = QtGui.QFileDialog.getOpenFileName(self,
						title,
						os.path.expanduser("~"),
						"Mat files (*.mat)")

        if filename:
            mat_data = sio.loadmat(filename)

            self.virtual_sensor_positions = mat_data['posVs']
            self.time = mat_data['time']
            self.virtual_sensors_signals = mat_data.get('signalproj').T
            self.correl = mat_data['correl']

            print(self.virtual_sensors_signals.shape)

            self.time_slider.setRange(0, self.time.shape[1])
            self.time_slider.setSingleStep(1)
            self.time_slider.setTickInterval(10)
            self.time_slider.setTickPosition(QtGui.QSlider.TicksBelow)

            self.correl_slider.setRange(0, self.correl.shape[1])
            self.correl_slider.setSingleStep(1)
            self.correl_slider.setTickInterval(10)
            self.correl_slider.setTickPosition(QtGui.QSlider.TicksBelow)

            self.time_slider.valueChanged.connect(self._TimeChanged)
            self.correl_slider.valueChanged.connect(self._CorrelChanged)

            self._BuildScene()
            self._BuildPlot()

            # print(self.time.shape)

    def _BuildLayout(self):
        container = QtGui.QWidget()
        container.setWindowTitle("Embedding Mayavi in a PyQt4 Application")
        # define a "complex" layout to test the behaviour
        layout = QtGui.QVBoxLayout(container) #QGridLayout(container)

        # Plot and scene
        self.mpl_widget = MPLQWidget(self)
        self.mayavi_widget = MayaviQWidget(self)

        visualization_layout = QtGui.QSplitter(container)
        visualization_layout.addWidget(self.mpl_widget)
        visualization_layout.addWidget(self.mayavi_widget)
        layout.addWidget(visualization_layout)

        # Controls
        self.time_slider = QtGui.QSlider(self)
        self.time_slider.setOrientation(QtCore.Qt.Horizontal)
        self.time_slider.setRange(0,1000)
        self.time_slider.setValue(0)

        self.correl_slider = QtGui.QSlider(self)
        self.correl_slider.setOrientation(QtCore.Qt.Horizontal)
        self.correl_slider.setRange(0,1000)
        self.correl_slider.setValue(0)

        controls_layout = QtGui.QVBoxLayout(container)
        controls_layout.addWidget(self.time_slider)
        controls_layout.addWidget(self.correl_slider)
        layout.addLayout(controls_layout)

        #layout.addWidget(mayavi_widget, 1, 1)
        container.show()
        self.setCentralWidget(container)

    def _BuildMenu(self):
        bar = self.menuBar()

        # File menu
        file = bar.addMenu("File")
        open = QtGui.QAction("Open",self,triggered=self._OpenMatFile)
        open.setShortcut("Ctrl+O")
        file.addAction(open)

    def _BuildScene(self):
        selected_correl_value = self.correl.min()
        self.selected_ids = np.ravel_multi_index(np.where(self.correl>=selected_correl_value), self.correl.shape)
        # print(self.virtual_sensors_signals[self.time_slider.value(),self.selected_ids].shape)
        self.mayavi_widget.SetPoints(self.virtual_sensor_positions[:,0],
                                     self.virtual_sensor_positions[:,1],
                                     self.virtual_sensor_positions[:,2],
                                     self.virtual_sensors_signals[self.time_slider.value(),self.selected_ids])

        self.mayavi_widget.SetScalarsRange(self.virtual_sensors_signals.min(),self.virtual_sensors_signals.max())
        self.mayavi_widget.ToggleScalarBarVisibility(True)

    def _BuildPlot(self):
        print('Build plot')

    def _TimeChanged(self, value):
        # print(self.selected_ids.shape)
        # print(value)
        # print(self.virtual_sensors_signals[value,self.selected_ids].shape)
        self.mayavi_widget.SetScalars(self.virtual_sensors_signals[value,self.selected_ids])
        print('---------------')
    def _CorrelChanged(self, value):
        selected_correl_value = self.correl.min()+((self.correl.max()-self.correl.min())*float(value)/(self.correl.shape[1]-1))
        self.selected_ids = np.ravel_multi_index(np.where(self.correl>=selected_correl_value), self.correl.shape)
        # print(self.selected_ids.shape)
        # print(self.virtual_sensors_signals[self.time_slider.value(),self.selected_ids].shape)
        self.mayavi_widget.SetPoints(self.virtual_sensor_positions[self.selected_ids,0],
                                     self.virtual_sensor_positions[self.selected_ids,1],
                                     self.virtual_sensor_positions[self.selected_ids,2],
                                     self.virtual_sensors_signals[self.time_slider.value(),self.selected_ids])
        # print('-------------------')
if __name__ == "__main__":
    # Don't create a new QApplication, it would unhook the Events
    # set by Traits on the existing QApplication. Simply use the
    # '.instance()' method to retrieve the existing one.
    app = QtGui.QApplication.instance()

    window = MainWindow()

    window.show()

    # Start the main event loop.
    app.exec_()

#!/Users/spherik/anaconda3/envs/mayavi_env/bin/python

# Mostrar dipSignal a part (mes amunt)
# Checkbox normalitzar senyals x = x-min/max-min
# menu toogle visualize per ocultar dipol - done
# mostrar correl_slider i time_slider
# Veure el num de dipols mostrats (despres de filtrar per correlacio)


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

import matplotlib
matplotlib.use('Qt4Agg')

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import scipy.io as sio
import numpy as np

from MPLQWidget import MPLQWidget
from MayaviQWidget import MayaviQWidget
from ChacoQWidget import ChacoQWidget
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
            # Anatomy meshes
            self.cortex_vertices = mat_data['cortex_vertices']
            self.cortex_triangles = mat_data['cortex_triangles']-1
            self.head_vertices = mat_data['head_vertices']
            self.head_triangles = mat_data['head_triangles']-1

            # Simulated signal
            self.virtual_sensor_positions = mat_data['posVS']
            self.time = mat_data['time'][0,:]
            self.virtual_sensors_signals = mat_data['signalproj']
            self.correl = np.abs(mat_data['correl'])

            # Dipole
            self.dipole_position = mat_data['origDipolePos'][0]
            self.dipole_momentum = mat_data['origDipoleMom'][0]/np.linalg.norm(mat_data['origDipoleMom'][0])
            self.dipole_signal = mat_data['dipSignal'][0]

            print(self.dipole_position)
            print(self.dipole_momentum)
            print(self.virtual_sensors_signals.shape)

            self.time_slider.setRange(0, self.time.shape[0])
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

    def _BuildLayout(self):
        container = QtGui.QWidget()
        container.setWindowTitle("Brain signal visualizer")
        # define a "complex" layout to test the behaviour
        layout = QtGui.QVBoxLayout(container) #QGridLayout(container)

        # Plot and scene
        #scroll = QtGui.QScrollArea(self)
        self.plot_widget = QtGui.QWidget()
        self.mpl_widget = ChacoQWidget(self)

        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.mpl_widget)  # the chaco canvas
        self.plot_widget.setLayout(vbox)

        self.mayavi_widget = MayaviQWidget(self)

        visualization_layout = QtGui.QSplitter(container)
        visualization_layout.addWidget(self.plot_widget)
        visualization_layout.addWidget(self.mayavi_widget)
        layout.addWidget(visualization_layout)

        # Controls
        self.time_slider = QtGui.QSlider(self)
        self.time_slider.setOrientation(QtCore.Qt.Horizontal)
        self.time_slider.setRange(0,1000)
        self.time_slider.setValue(0)
        self.time_slider.setEnabled(False)

        self.time_text = QtGui.QLineEdit()
        self.time_text.setText('0')
        self.time_text.editingFinished.connect(self._TimeTextChanged)
        self.time_text.setEnabled(False)

        self.correl_slider = QtGui.QSlider(self)
        self.correl_slider.setOrientation(QtCore.Qt.Horizontal)
        self.correl_slider.setRange(0,1000)
        self.correl_slider.setValue(0)

        self.correl_text = QtGui.QLineEdit()
        self.correl_text.setText('0')
        self.correl_text.editingFinished.connect(self._CorrelTextChanged)
        self.correl_text.setEnabled(False)

        controls_layout = QtGui.QGridLayout(container)
        controls_layout.addWidget(self.time_slider,0,0)
        controls_layout.addWidget(self.time_text,0,1)
        controls_layout.addWidget(self.correl_slider,1,0)
        controls_layout.addWidget(self.correl_text,1,1)
        layout.addLayout(controls_layout)
        controls_layout.activate()
        self.correl_text.resize(self.correl_text.sizeHint())
        self.time_text.resize(self.time_text.sizeHint())
        #layout.addWidget(mayavi_widget, 1, 1)

        container.show()
        self.setCentralWidget(container)

    def _BuildMenu(self):
        bar = self.menuBar()

        # File menu
        file_menu = bar.addMenu('File')

        open_action = QtGui.QAction('Open',self,triggered = self._OpenMatFile)
        open_action.setShortcut('Ctrl+O')
        file_menu.addAction(open_action)

        # Visualization menuBar
        visualization_menu = bar.addMenu('Visualization')

        self.head_visual_action = QtGui.QAction('Head', self, triggered = self._ToggleHeadVisibility)
        self.head_visual_action.setCheckable(True)
        self.head_visual_action.setChecked(True)
        self.head_visual_action.setEnabled(False)
        visualization_menu.addAction(self.head_visual_action)

        self.cortex_visual_action = QtGui.QAction('Cortex', self, triggered = self._ToggleCortexVisibility)
        self.cortex_visual_action.setCheckable(True)
        self.cortex_visual_action.setChecked(True)
        self.cortex_visual_action.setEnabled(False)
        visualization_menu.addAction(self.cortex_visual_action)

        self.dipole_visual_action = QtGui.QAction('Dipole',self, triggered = self._ToggleDipoleVisibility)
        self.dipole_visual_action.setCheckable(True)
        self.dipole_visual_action.setChecked(True)
        self.dipole_visual_action.setEnabled(False)
        visualization_menu.addAction(self.dipole_visual_action)

    def _BuildScene(self):
        selected_correl_value = self.correl.min()
        self.selected_ids = np.ravel_multi_index(np.where(self.correl>=selected_correl_value), self.correl.shape)
        self.mayavi_widget.SetPoints(self.virtual_sensor_positions[:,0],
                                     self.virtual_sensor_positions[:,1],
                                     self.virtual_sensor_positions[:,2],
                                     self.virtual_sensors_signals[self.time_slider.value()-1,self.selected_ids])

        self.mayavi_widget.SetScalarsRange(self.virtual_sensors_signals.min(),self.virtual_sensors_signals.max())
        self.mayavi_widget.ToggleScalarBarVisibility(True)

        self.mayavi_widget.AddCortex(self.cortex_vertices, self.cortex_triangles)
        self.mayavi_widget.AddHead(self.head_vertices, self.head_triangles)

        self.mayavi_widget.AddDipole(self.dipole_position, self.dipole_momentum)

    def _BuildPlot(self):
        self.mpl_widget.SetDipoleSignal(self.time,self.dipole_signal)
        self.mpl_widget.SetSignals(self.time, self.virtual_sensors_signals[self.selected_ids,:], self.time_slider.value()-1)

    def _TimeChanged(self, value):
        self.mayavi_widget.SetScalars(self.virtual_sensors_signals[self.selected_ids,value])
        self.mpl_widget.SetTimeIndex(value)
        self.time_text.setText(str(value))

    def _CorrelChanged(self, value):
        selected_correl_value = self.correl.min()+((self.correl.max()-self.correl.min())*float(value)/(self.correl.shape[1]-1))
        self.selected_ids = np.ravel_multi_index(np.where(self.correl>=selected_correl_value), self.correl.shape)

        # Update 3D scene
        self.mayavi_widget.SetPoints(self.virtual_sensor_positions[self.selected_ids,0],
                                     self.virtual_sensor_positions[self.selected_ids,1],
                                     self.virtual_sensor_positions[self.selected_ids,2],
                                     self.virtual_sensors_signals[self.selected_ids,self.time_slider.value()-1])
        # Update signal Plot
        self.mpl_widget.SetSignals(self.time,self.virtual_sensors_signals[self.selected_ids,:],time_index = self.time_slider.value()-1)

        self.correl_text.setText(str(value))

    def _TimeTextChanged(self):
        value = int(self.time_text.text())
        self.time_slider.setValue(value)
        self.mayavi_widget.SetScalars(self.virtual_sensors_signals[self.selected_ids,value])
        self.mpl_widget.SetTimeIndex(value)

    def _CorrelTextChanged(self):
        value = int(self.correl_text.text())
        self.correl_slider.setValue(value)

        selected_correl_value = self.correl.min()+((self.correl.max()-self.correl.min())*float(value)/(self.correl.shape[1]-1))
        self.selected_ids = np.ravel_multi_index(np.where(self.correl>=selected_correl_value), self.correl.shape)

        # Update 3D scene
        self.mayavi_widget.SetPoints(self.virtual_sensor_positions[self.selected_ids,0],
                                     self.virtual_sensor_positions[self.selected_ids,1],
                                     self.virtual_sensor_positions[self.selected_ids,2],
                                     self.virtual_sensors_signals[self.selected_ids,self.time_slider.value()-1])
        # Update signal Plot
        self.mpl_widget.SetSignals(self.virtual_sensors_signals[self.selected_ids,:], time_index = self.time_slider.value()-1)

    def _ToggleHeadVisibility(self, is_checked):
        self.mayavi_widget.ToggleHeadVisibility(is_checked)

    def _ToggleCortexVisibility(self, is_checked):
        self.mayavi_widget.ToggleCortexVisibility(is_checked)

    def _ToggleDipoleVisibility(self, is_checked):
        self.mayavi_widget.ToggleDipoleVisibility(is_checked)

if __name__ == "__main__":
    # Don't create a new QApplication, it would unhook the Events
    # set by Traits on the existing QApplication. Simply use the
    # '.instance()' method to retrieve the existing one.
    app = QtGui.QApplication.instance()

    window = MainWindow()

    window.show()

    # Start the main event loop.
    app.exec_()

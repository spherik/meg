#!/Users/spherik/anaconda3/envs/mayavi_env/bin/python
## #!/usr/bin/python
# -*- coding: utf-8 -*-

from traits.api import Instance
from traitsui.qt4.editor import Editor
from traitsui.qt4.basic_editor_factory import BasicEditorFactory

from traits.api import HasTraits, Int, Float, on_trait_change,Range, Array
from traitsui.api import View, Item, HSplit

from mayavi.core.api import Engine
from mayavi.core.ui.api import MayaviScene, MlabSceneModel, \
            SceneEditor

import matplotlib
# We want matplotlib to use a QT backend
matplotlib.use('Qt4Agg')
# matplotlib.interactive(True)  # Not sure it's necessary
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

import numpy as np
import scipy.io as sio

class _MPLFigureEditor(Editor):

   scrollable  = True

   def init(self, parent):
       self.control = self._create_canvas(parent)
       #self.nav_toolbar = NavigationToolbar(self.control, self.value)
       self.set_tooltip()

   def update_editor(self):
       pass

   def _create_canvas(self, parent):
       """ Create the MPL canvas. """
       # matplotlib commands to create a canvas
       mpl_canvas = FigureCanvas(self.value)
       return mpl_canvas

class MPLFigureEditor(BasicEditorFactory):

   klass = _MPLFigureEditor


class MEGVisualizator(HasTraits):

    # Plot figure
    mpl_figure = Instance(Figure, ())
    n = Int(11)
    a = Float(0.5)
    selected_time = Range(0,100,50)
    selected_correl = Range(0,100,0)

    # The first engine. As default arguments (an empty tuple) are given,
    # traits initializes it.
    engine1 = Instance(Engine, args=())
    scene1 = Instance(MlabSceneModel)

    def _scene1_default(self):
        " The default initializer for 'scene1' "
        self.engine1.start()
        scene1 = MlabSceneModel(engine=self.engine1)
        return scene1


    view = View(HSplit(
                        Item('mpl_figure', editor=MPLFigureEditor(),show_label=False,resizable=True),
                        Item('scene1', editor=SceneEditor(scene_class=MayaviScene),width=480, height=480,show_label=False),
                        ),
                Item('selected_time'),
                Item('selected_correl'),
                resizable=True)

    def __init__(self):
        super(MEGVisualizator, self).__init__()
        self.load_data('0006_1-all.mat')


    def load_data(self, filename):
        mat_data = sio.loadmat(filename)

        self.virtual_sensor_positions = mat_data['posVs']
        self.time = mat_data['time']
        self.virtual_sensors_signals = mat_data.get('signalproj').T
        self.correl = mat_data['correl']
        self.generate_scene()
        self.generate_plot()

        print(self.virtual_sensors_signals.shape)

    def onMouseMovePlot():
        print("mouse move")

    def generate_plot(self):
        n = self.virtual_sensors_signals

        len_signals = self.virtual_sensors_signals.shape[1]-1
        time_index = int(len_signals*self.selected_time/100.0)

        self.axes = self.mpl_figure.add_subplot(111)
        self.axes.plot(self.virtual_sensors_signals+ 80*np.arange(self.virtual_sensors_signals.shape[1]-1,-1,-1))
        self.axes.plot(np.zeros(self.virtual_sensors_signals.shape) + 80*np.arange(self.virtual_sensors_signals.shape[1]-1,-1,-1),'--',color='gray');
        self.axes.axvline(x=time_index, color="k")

    def generate_scene(self):
        self.virtual_sensors_3D = self.scene1.mlab.points3d(self.virtual_sensor_positions[:,0],self.virtual_sensor_positions[:,1],self.virtual_sensor_positions[:,2],
                                   self.virtual_sensors_signals[0,:], mode = 'sphere')
        #self.virtual_sensors_3D.glyph.color_mode = 'color_by_scalar'
        self.virtual_sensors_3D.glyph.glyph.scale_mode = 'data_scaling_off'
        self.virtual_sensors_3D.glyph.scale_mode = 'data_scaling_off'
        self.virtual_sensors_3D.glyph.glyph.scale_factor = 0.003

        # Setup lut
        #self.virtual_sensors_3D.module_manager.scalar_lut_manager.show_scalar_bar = True
        #self.virtual_sensors_3D.module_manager.scalar_lut_manager.show_legend = True
        self.virtual_sensors_3D.module_manager.scalar_lut_manager.use_default_range = False
        self.virtual_sensors_3D.module_manager.scalar_lut_manager.lut._vtk_obj.SetTableRange(self.virtual_sensors_signals.min(),
                                                                                             self.virtual_sensors_signals.max())
        self.virtual_sensors_3D.module_manager.scalar_lut_manager.lut_mode = 'magma'

        #sb = self.scene1.mlab.scalarbar(self.virtual_sensors_3D)
        print(self.virtual_sensors_signals.min(),self.virtual_sensors_signals.max())
        # self.scene1.mlab.axes(self.virtual_sensors_3D)


    @on_trait_change('selected_correl')
    def update_selected_correlation(self):
        print('update_selected_correlation')
        # Get correlation value
        selected_correl_value = self.correl.min()+(self.correl.max()-self.correl.min())*(self.selected_correl/100.0)
        selected_ids = np.ravel_multi_index(np.where(self.correl>selected_correl_value), self.correl.shape)

        # Get time value
        len_signals = self.virtual_sensors_signals.shape[1]-1
        time_index = int(len_signals*self.selected_time/100.0)

        #
        selected_positions = self.virtual_sensor_positions[selected_ids,:]
        selected_signals = self.virtual_sensors_signals[:,selected_ids]
        print(selected_positions.shape)
        print(selected_signals.shape)

        # Update 3D scene
        self.scene1.disable_render = True
        #self.virtual_sensors_3D.mlab_source.reset()
        self.virtual_sensors_3D.mlab_source.reset(x = selected_positions[:,0], y = selected_positions[:,1], z = selected_positions[:,2],
                                                    scalars=selected_signals[time_index,:])
        self.virtual_sensors_3D.mlab_source.set(x = selected_positions[:,0], y = selected_positions[:,1], z = selected_positions[:,2],
                                                    scalars=selected_signals[time_index,:])
        self.scene1.disable_render = False
        self.scene1.scene.do_render = True
        # Update plot
        self.axes.cla()
        self.axes.plot(selected_signals+ 80*np.arange(selected_signals.shape[1]-1,-1,-1))
        self.axes.plot(np.zeros(selected_signals.shape) + 80*np.arange(selected_signals.shape[1]-1,-1,-1),'--',color='gray');
        self.axes.axvline(x=time_index, color="k")
        self.mpl_figure.canvas.draw()


    @on_trait_change('selected_time')
    def update_selected_time(self):
        print('update_selected_time')
        # Update signal plot
        # Get correlation value
        selected_correl_value = self.correl.min()+(self.correl.max()-self.correl.min())*(self.selected_correl/100.0)
        selected_ids = np.ravel_multi_index(np.where(self.correl>selected_correl_value), self.correl.shape)

        # Get time value
        len_signals = self.virtual_sensors_signals.shape[1]-1
        time_index = int(len_signals*self.selected_time/100.0)

        #
        selected_signals = self.virtual_sensors_signals[:,selected_ids]

        # Update signals plot
        axes = self.mpl_figure.axes[0]
        axes.lines = axes.lines[0:len(axes.lines)-1]    # Remove last line (the one added in the last event)
        axes.axvline(x=time_index, color="k")
        canvas = self.mpl_figure.canvas
        if canvas is not None:
            canvas.draw()

        # Update 3D scene
        self.scene1.disable_render = True
        self.virtual_sensors_3D.mlab_source.set(scalars=selected_signals[time_index])
        self.scene1.disable_render = False
        self.scene1.scene.do_render = True


if __name__ == "__main__":
   # Create a window to demo the editor
   t = MEGVisualizator()
   t.configure_traits()

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
    view = View(Item('scene', editor=SceneEditor(scene_class=MayaviScene), # Scene
                     show_label=False),
                resizable=True # We need this to resize with the parent widget
                )

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


    def AddHead(self, vertices, triangles):
        self.head_mesh = self.visualization.scene.mlab.triangular_mesh(vertices[:,0],vertices[:,1],vertices[:,2],
                                                                        triangles, opacity = 0.4)
        self.head_mesh.actor.mapper.scalar_visibility = False
        self.head_mesh.actor.property.frontface_culling = True
        self.head_mesh.actor.property.color = (0.95, 0.75, 0.5)
        self.visualization.scene.reset_zoom()

    def AddCortex(self, vertices, triangles):
        self.cortex_mesh = self.visualization.scene.mlab.triangular_mesh(vertices[:,0],vertices[:,1],vertices[:,2],
                                                                        triangles, opacity = 0.2)
        self.cortex_mesh.actor.mapper.scalar_visibility = False
        self.cortex_mesh.actor.property.frontface_culling = True
        self.visualization.scene.reset_zoom()

    def ToggleCortexVisibility(self, is_visible):
        self.cortex_mesh.actor.visible = is_visible

    def ToggleHeadVisibility(self, is_visible):
        self.head_mesh.actor.visible = is_visible

    def AddDipole(self, position, momentum):
        self.dipole_momentum_sphere = self.visualization.scene.mlab.points3d(position[0], position[1], position[2])
        self.dipole_momentum_sphere.actor.property.color = (0.0, 1.0, 0.0)
        self.dipole_momentum_sphere.glyph.glyph.scale_factor = 0.008

        self.dipole_momentum_arrow = self.visualization.scene.mlab.quiver3d(position[0], position[1], position[2], momentum[0], momentum[1], momentum[2])
        self.dipole_momentum_arrow.glyph.color_mode = 'no_coloring'
        self.dipole_momentum_arrow.actor.property.color = (0.0, 1.0, 0.0)
        self.dipole_momentum_arrow.glyph.glyph_source.glyph_source = self.dipole_momentum_arrow.glyph.glyph_source.glyph_dict['arrow_source']
        self.dipole_momentum_arrow.glyph.glyph.scale_factor = 0.04
        self.visualization.scene.reset_zoom()
        
    def ToggleDipoleVisibility(self, is_visible):
        self.dipole_momentum_sphere.actor.visible = is_visible
        self.dipole_momentum_arrow.actor.visible = is_visible

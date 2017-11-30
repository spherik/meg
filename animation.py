#!/usr/local/bin/python3
from mayavi import mlab
from tvtk.tools import visual
import scipy.io as sio
import numpy as np

# Create a figure
f = mlab.figure(size=(500,500))
# Tell visual to use this as the viewer.
visual.set_viewer(f)

# Load data
mat_data = sio.loadmat('0006_1-all.mat')
print(mat_data.keys())

virtual_sensor_positions = mat_data['posVs']
time = mat_data.get('time')
virtual_sensors_signals = mat_data.get('signalproj')
print(virtual_sensors_signals.shape)

bbox = [virtual_sensor_positions[:,0].min(),virtual_sensor_positions[:,0].max(),
       virtual_sensor_positions[:,1].min(),virtual_sensor_positions[:,1].max(),
       virtual_sensor_positions[:,2].min(),virtual_sensor_positions[:,2].max()]

virtual_sensors_3D = mlab.points3d(virtual_sensor_positions[:,0],virtual_sensor_positions[:,1],virtual_sensor_positions[:,2],
                                   virtual_sensors_signals[:,0],
                                   #extent=bbox,
                                   figure=f)
virtual_sensors_3D.glyph.color_mode = 'color_by_scalar'
#virtual_sensors_3D.glyph.glyph.scale_mode = 'data_scaling_off'
#virtual_sensors_3D.glyph.scale_mode = 'data_scaling_off'
#virtual_sensors_3D.glyph.glyph.scale_factor = 0.01
#sb = mlab.scalarbar(virtual_sensors_3D)

mlab.axes(virtual_sensors_3D)
f.scene.reset_zoom()


ms = virtual_sensors_3D.mlab_source
@mlab.show
@mlab.animate(delay=250)
def anim():
    """Animate the b1 box."""
    frame = 0
    while 1:
        frame = frame + 1
        if frame == virtual_sensors_signals.shape[1]:
            frame = 0
        ms.set(scalars=virtual_sensors_signals[:,frame])
        yield

# Run the animation.
anim()

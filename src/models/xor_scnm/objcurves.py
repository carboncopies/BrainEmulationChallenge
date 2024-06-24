# Blender Python API script used to convert OBJ lines into curves
# to give them material with color.
# In Blender 4.0, OBJ lines already appear to be loaded as curves.
# Either that, or all the objects imported were still selected
# when conversion was carried out.

import bpy

bpy.ops.wm.obj_import(filepath='/home/randalk/Desktop/test.obj')


first_axon = bpy.data.objects["axon0"]

first_axon.select_set(True)
bpy.context.view_layer.objects.active = first_axon

bpy.ops.object.convert(target='CURVE')

first_axon.data.bevel_depth = 0.1

bpy.ops.wm.save_as_mainfile(filepath='test.blend')

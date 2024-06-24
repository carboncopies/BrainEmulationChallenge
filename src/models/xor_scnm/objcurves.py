# Blender Python API script used to convert OBJ lines into curves
# to give them material with color.

import bpy

bpy.ops.wm.obj_import(filepath='/home/randalk/Desktop/test.obj')


first_axon = bpy.data.objects["axon0"]

first_axon.select_set(True)
bpy.context.view_layer.objects.active = first_axon

bpy.ops.object.convert(target='CURVE')

bpy.ops.wm.save_as_mainfile(filepath='test.blend')

# Blender Python API script used to convert OBJ lines into curves
# to give them material with color.
# In Blender 4.0, OBJ lines already appear to be loaded as curves.
# Either that, or all the objects imported were still selected
# when conversion was carried out.

import bpy
import json

def get_object_info()->tuple:
	# Obtain necessary information about the OBJ file to properly
	# run the conversion through Blender.
	with open('obj_data.json', 'r') as f:
		obj_data = json.load(f)

	filepath = obj_data['obj_path']
	axons_list = obj_data['axons']
	dendrites_list = obj_data['dendrites']
	somas_list = obj_data['somas']
	blendpath = obj_data['blend_path']
	return filepath, axons_list, dendrites_list, somas_list, blendpath

def get_blender_objects(names_list:list)->list:
	blender_objects = []
	for name in names_list:
		blender_objects.append( bpy.data.objects[name] )
	return blender_objects

def set_bevel_depths(objects_list:list, depth:float):
	for curve_object in objects_list:
		curve_object.data.bevel_depth = depth

def delete_default_cube():
	# Delete the default Cube object
	# 1. Deselect all
	bpy.ops.object.select_all(action='DESELECT')
	# 3. Select the Cube
	bpy.data.objects['Cube'].select_set(True)
	# 4. Delete it    
	bpy.ops.object.delete()

filepath, axons_list, dendrites_list, somas_list, blendpath = get_object_info()

# Note: After importing, all objects are automatically selected
# so that converting to curves converts all of the lines to
# curves without having to select them individually to do so.
bpy.ops.wm.obj_import(filepath=filepath)

# Convert all selected to curves
bpy.ops.object.convert(target='CURVE')

axon_objects = get_blender_objects(axons_list)
dendtite_objects = get_blender_objects(dendrites_list)
soma_objects = get_blender_objects(somas_list)

set_bevel_depths(axon_objects, 0.1)
set_bevel_depths(dendite_objects, 0.1)

delete_default_cube()

bpy.ops.wm.save_as_mainfile(filepath=blendpath)

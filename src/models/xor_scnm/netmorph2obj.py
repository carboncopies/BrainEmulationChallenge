#!/usr/bin/env python3
# netmoprh2obj.py
# Randal A. Koene, 20240621
#
# A simple script to convert Netmorph output to a Wavefront OBJ file
# for viewing in Blender.

scriptversion='0.0.1'

import numpy as np
from datetime import datetime
from time import sleep
import json

from netmorph2nes import netmorph_to_somas_segments_synapses

obj_path = 'test.obj'
blend_path = 'test.blend'

import argparse
Parser = argparse.ArgumentParser(description="Netmorph to Wavefront OBJ file")
Parser.add_argument("-NmSource", default='../../../../../src/nnmodels/netmorph/examples/nesvbp/nesvbp_202406151142', help="Netmorph source files trunk")
Args = Parser.parse_args()

print('Collecting segments from Netmorph output files...')

somas, segments, synapses = netmorph_to_somas_segments_synapses(Args.NmSource)

print('Got %d somas, %d segments and %d synapses. Converting each to shape and compartment (this may take a while)...' % (len(somas), len(segments), len(synapses)))

# First, let's just make some cubes in OBJ format, one for each soma

CUBE_HEADER = '''# netmorph_output.obj
#

'''

CUBE_TOP = '''o soma%s
mtllib cube.mtl
'''

DENDRITES_TOP = '''o dendrites%s
'''

AXON_TOP = '''o axon%s
'''

FACES = '''
vn 0.000000 0.000000 1.000000
vn 0.000000 1.000000 0.000000
vn 0.000000 0.000000 -1.000000
vn 0.000000 -1.000000 0.000000
vn 1.000000 0.000000 0.000000
vn -1.000000 0.000000 0.000000
'''

SIMPLE_CUBE_FACES = '''
vn 0.000000 -1.000000 0.000000
vn 0.000000 1.000000 0.000000
vn 1.000000 0.000000 0.000000
vn -0.000000 0.000000 1.000000
vn -1.000000 -0.000000 -0.000000
vn 0.000000 0.000000 -1.000000
'''

CUBE_EXTRAS = '''
usemtl cube
s off
'''

face_lines = [
    [(0,0), (1,0), (2,0), (3,0)],
    [(4,1), (7,1), (6,1), (5,1)],
    [(0,2), (4,2), (5,2), (1,2)],
    [(1,3), (5,3), (6,3), (2,3)],
    [(2,4), (6,4), (7,4), (3,4)],
    [(4,5), (0,5), (3,5), (7,5)],
]

# f 2/1/1 3/2/1 4/3/1
# f 8/1/2 7/4/2 6/5/2
# f 5/6/3 6/7/3 2/8/3
# f 6/8/4 7/5/4 3/4/4
# f 3/9/5 7/10/5 8/11/5
# f 1/12/6 4/13/6 8/11/6
# f 1/4/1 2/1/1 4/3/1
# f 5/14/2 8/1/2 6/5/2
# f 1/12/3 5/6/3 2/8/3
# f 2/12/4 6/8/4 3/4/4
# f 4/13/5 3/9/5 8/11/5
# f 5/6/6 1/12/6 8/11/6

pyramid_face_lines = [
    [3, 0, 1],
    [2, 3, 1],
    [4, 1, 0],
    [3, 4, 0],
    [2, 4, 3],
    [4, 2, 1],
]

simple_cube_lines = [
    [ 1.0, -1.0, -1.0 ],
    [ 1.0, -1.0, 1.0 ],
    [ -1.0, -1.0, 1.0 ],
    [ -1.0, -1.0, -1.0 ],
    [ 1.0, 1.0, -1.0 ],
    [ 1.0, 1.0, 1.0 ],
    [ -1.0, 1.0, 1.0 ],
    [ -1.0, 1.0, -1.0 ],
]

two_sided_cube_faces = [
    [1, 2, 3],
    [7, 6, 5],
    [4, 5, 1],
    [5, 6, 2],
    [2, 6, 7],
    [0, 3, 7],
    [0, 1, 3],
    [4, 7, 5],
    [0, 4, 1],
    [1, 5, 2],
    [3, 2, 7],
    [4, 0, 7],
]

soma_obj_names = []
axon_obj_names = []
dendrite_obj_names = []

def add_neuron_neurites(neuron_label:str, neurite_type:str, segments:list, vertex_start:int, center:np.array)->tuple:
    neurite_segments = ''
    for segment in segments:
        if segment.data.somaneuron_label == neuron_label and segment.data.fiberstructure_type==neurite_type:
            v1 = segment.start
            v1 = np.array([v1.x, v1.y, v1.z]) - center
            v2 = segment.end
            v2 = np.array([v2.x, v2.y, v2.z]) - center
            neurite_segments += 'v %.3f %.3f %.3f 1.0 0.0 0.0\n' % (v1[0], v1[1], v1[2])
            neurite_segments += 'v %.3f %.3f %.3f 1.0 0.0 0.0\n' % (v2[0], v2[1], v2[2])
            neurite_segments += 'l %d %d\n' % (vertex_start, vertex_start+1)

            vertex_start += 2
    return vertex_start, neurite_segments

def add_simple_cube(obj_name:str, vertex_start:int, face_start:int, radius:float, location:np.array, center:np.array)->tuple:
    cube_data = obj_name+'\n'

    vertices = []
    for simple_cube_line in simple_cube_lines:
        vertices.append( np.array(simple_cube_line)*radius + location - center )

    for v in vertices:
        cube_data += 'v %.3f %.3f %.3f\n' % (v[0], v[1], v[2])

    faces = ''
    for i in range(len(two_sided_cube_faces)):
        faceline = 'f '
        for j in range(3):
            faceline += str(vertex_start+two_sided_cube_faces[i][j])+' '
        faces += faceline+'\n'
    cube_data += faces

    vertex_start += len(vertices)
    face_start += len(two_sided_cube_faces)

    return vertex_start, face_start, cube_data

def add_soma_cube(cube_num: int, vertex_start:int, face_start:int, soma, center:np.array)->tuple:
    cube_data = CUBE_TOP % str(cube_num)

    v1 = np.array(soma.point()) + np.array([-soma.radius, -soma.radius, soma.radius]) - center
    v2 = np.array(soma.point()) + np.array([soma.radius, -soma.radius, soma.radius]) - center
    v3 = np.array(soma.point()) + np.array([-soma.radius, soma.radius, soma.radius]) - center
    v4 = np.array(soma.point()) + np.array([soma.radius, soma.radius, soma.radius]) - center
    v5 = np.array(soma.point()) + np.array([-soma.radius, soma.radius, -soma.radius]) - center
    v6 = np.array(soma.point()) + np.array([soma.radius, soma.radius, -soma.radius]) - center
    v7 = np.array(soma.point()) + np.array([-soma.radius, -soma.radius, -soma.radius]) - center
    v8 = np.array(soma.point()) + np.array([soma.radius, -soma.radius, -soma.radius]) - center

    vertices = ( v1, v2, v3, v4, v5, v6, v7, v8 )

    for v in vertices:
        cube_data += 'v %.3f %.3f %.3f\n' % (v[0], v[1], v[2])

    faces = ''
    for i in range(6):
        faceline = 'f '
        for j in range(4):
            faceline += str(vertex_start+face_lines[i][j][0])+'//'+str(face_start+face_lines[i][j][1])+' '
        faces += faceline+'\n'
    cube_data += faces

    vertex_start += 8
    face_start += 6

    return vertex_start, face_start, cube_data

def add_soma_pyramid(cube_num: int, vertex_start:int, face_start:int, soma, center:np.array)->tuple:
    pyramid_data = CUBE_TOP % str(cube_num)

    v1 = np.array([0.0, 0.0, 0.0])*2.0*soma.radius + np.array(soma.point()) + np.array([-soma.radius, -soma.radius, -soma.radius]) - center
    v2 = np.array([1.0, 0.0, 0.0])*2.0*soma.radius + np.array(soma.point()) + np.array([-soma.radius, -soma.radius, -soma.radius]) - center
    v3 = np.array([1.0, 1.0, 0.0])*2.0*soma.radius + np.array(soma.point()) + np.array([-soma.radius, -soma.radius, -soma.radius]) - center
    v4 = np.array([0.0, 1.0, 0.0])*2.0*soma.radius + np.array(soma.point()) + np.array([-soma.radius, -soma.radius, -soma.radius]) - center
    v5 = np.array([0.5, 0.5, 1.6])*2.0*soma.radius + np.array(soma.point()) + np.array([-soma.radius, -soma.radius, -soma.radius]) - center

    vertices = ( v1, v2, v3, v4, v5 )

    for v in vertices:
        pyramid_data += 'v %.3f %.3f %.3f\n' % (v[0], v[1], v[2])

    pyramid_data += FACES

    pyramid_data += CUBE_EXTRAS

    faces = ''
    for i in range(6):
        faceline = 'f '
        for j in range(3):
            faceline += str(vertex_start+pyramid_face_lines[i][j])+' '
        faces += faceline+'\n'
    pyramid_data += faces

    vertex_start += 5
    face_start += 6

    return vertex_start, face_start, pyramid_data

def make_Wavefront_OBJ(somas:list, segments:list, center:np.array)->str:

    obj_data = CUBE_HEADER

    cube_num = 0
    face_start = 1
    vertex_start = 1
    for soma in somas:
        soma_obj_names.append('soma'+str(cube_num))

        #vertex_start, face_start, soma_data = add_soma_cube(cube_num, vertex_start, face_start, soma, center)

        vertex_start, face_start, soma_data = add_soma_pyramid(cube_num, vertex_start, face_start, soma, center)

        obj_data += soma_data

        axon_obj_names.append('axon'+str(cube_num))
        obj_data += AXON_TOP % str(cube_num)
        vertex_start, neurite_segments = add_neuron_neurites(soma.label, 'axon', segments, vertex_start, center)
        obj_data += '\n' + neurite_segments

        dendrite_obj_names.append('dendrites'+str(cube_num))
        obj_data += DENDRITES_TOP % str(cube_num)
        vertex_start, neurite_segments = add_neuron_neurites(soma.label, 'dendrite', segments, vertex_start, center)
        obj_data += '\n' + neurite_segments

        cube_num += 1


    for synapse in synapses:
        receptor_loc = np.array(synapse.postsyn_receptor_point())
        spine_loc = np.array(synapse.presyn_spine_point())

        synapse_size = np.linalg.norm(receptor_loc - spine_loc)

        vertex_start, face_start, synapse_data = add_simple_cube('synapse'+str(synapse.idx), vertex_start, face_start, synapse_size/2.0, receptor_loc, center)

        obj_data += '\n' + synapse_data

    return obj_data

def find_center_of_mass(somas:list)->np.array:
    center = np.array([0.0,0.0,0.0])
    for soma in somas:
        center += np.array(soma.point())
    center = center/float(len(somas))
    return center

center = find_center_of_mass(somas)
obj_data = make_Wavefront_OBJ(somas, segments, center)

blender_obj_data = {
    'obj_path': obj_path,
    'axons': axon_obj_names,
    'dendrites': dendrite_obj_names,
    'somas': soma_obj_names,
    'blend_path': blend_path,
}

with open('obj_data.json', 'w') as f:
    json.dump(blender_obj_data, f)

with open('test.obj', 'w') as f:
    f.write(obj_data)

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

CUBE_TOP = '''o cube%s
mtllib cube.mtl
'''

FACES = '''
vn 0.000000 0.000000 1.000000
vn 0.000000 1.000000 0.000000
vn 0.000000 0.000000 -1.000000
vn 0.000000 -1.000000 0.000000
vn 1.000000 0.000000 0.000000
vn -1.000000 0.000000 0.000000
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

obj_data = CUBE_HEADER

cube_num = 0
face_start = 1
vertex_start = 1
for soma in somas:
    cube_data = CUBE_TOP % str(cube_num)

    v1 = np.array(soma.point()) + np.array([-soma.radius, -soma.radius, soma.radius])
    v2 = np.array(soma.point()) + np.array([soma.radius, -soma.radius, soma.radius])
    v3 = np.array(soma.point()) + np.array([-soma.radius, soma.radius, soma.radius])
    v4 = np.array(soma.point()) + np.array([soma.radius, soma.radius, soma.radius])
    v5 = np.array(soma.point()) + np.array([-soma.radius, soma.radius, -soma.radius])
    v6 = np.array(soma.point()) + np.array([soma.radius, soma.radius, -soma.radius])
    v7 = np.array(soma.point()) + np.array([-soma.radius, -soma.radius, -soma.radius])
    v8 = np.array(soma.point()) + np.array([soma.radius, -soma.radius, -soma.radius])

    vertices = ( v1, v2, v3, v4, v5, v6, v7, v8 )

    for v in vertices:
        cube_data += 'v %.3f %.3f %.3f\n' % (v[0], v[1], v[2])

    cube_data += FACES

    cube_data += CUBE_EXTRAS

    faces = ''
    for i in range(6):
        faceline = 'f '
        for j in range(4):
            faceline += str(vertex_start+face_lines[i][j][0])+'//'+str(face_start+face_lines[i][j][1])+' '
        faces += faceline+'\n'
    cube_data += faces

    obj_data += cube_data

    cube_num += 1
    vertex_start += 8
    face_start += 6

obj_data += '\n'

for segment in segments:
    v1 = segment.start
    v2 = segment.end
    obj_data += 'v %.3f %.3f %.3f\n' % (v1[0], v1[1], v1[2])
    obj_data += 'v %.3f %.3f %.3f\n' % (v2[0], v2[1], v2[2])
    obj_data += 'l %d %d' % (vertex_start, vertex_start+1)

    vertex_start += 2

with open('test.obj', 'w') as f:
    f.write(obj_data)

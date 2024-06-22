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

CUBE_TOP = '''o cube
mtllib cube.mtl
'''

CUBE_EXTRAS = '''
vt 0.000000 0.000000
vt 1.000000 0.000000
vt 0.000000 1.000000
vt 1.000000 1.000000

vn 0.000000 0.000000 1.000000
vn 0.000000 1.000000 0.000000
vn 0.000000 0.000000 -1.000000
vn 0.000000 -1.000000 0.000000
vn 1.000000 0.000000 0.000000
vn -1.000000 0.000000 0.000000

g cube
usemtl cube
s 1
f 1/1/1 2/2/1 3/3/1
f 3/3/1 2/2/1 4/4/1
s 2
f 3/1/2 4/2/2 5/3/2
f 5/3/2 4/2/2 6/4/2
s 3
f 5/4/3 6/3/3 7/2/3
f 7/2/3 6/3/3 8/1/3
s 4
f 7/1/4 8/2/4 1/3/4
f 1/3/4 8/2/4 2/4/4
s 5
f 2/1/5 8/2/5 4/3/5
f 4/3/5 8/2/5 6/4/5
s 6
f 7/1/6 1/2/6 5/3/6
f 5/3/6 1/2/6 3/4/6
'''

obj_data = CUBE_HEADER

for soma in somas:
    cube_data = CUBE_TOP

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

    cube_data += CUBE_EXTRAS

    obj_data += cube_data

with open('test.obj', 'w') as f:
    f.write(obj_data)

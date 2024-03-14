#!/usr/bin/env python3
# xor_sc_groundtruth.py
# Randal A. Koene, 20240311

'''
The XOR SimpleCompartmental example uses branching axons in a representation of a
meaningful logic circuit to produce expected functional output.

This file implements an in-silico fully known ground-truth system.
In this example file, we do this with a minimum of Python complexity,
keeping the script as flat as possible and maximizing immediate use of NES calls.

VBP process step 00: groundtruth
WBE topic-level XI: sample preparation / preservation (in-silico)
'''

scriptversion='0.0.1'

import numpy as np
from datetime import datetime
from time import sleep

import vbpcommon
from BrainGenix.BG_API import BG_API_Setup
from NES_interfaces.KGTRecords import plot_recorded


import argparse
Parser = argparse.ArgumentParser(description="vbp script")
Parser.add_argument("-Local", action='store_true', help="Run on local NES server")
Parser.add_argument("-Remote", action='store_true', help="Run on remote NES server")
Args = Parser.parse_args()

#default:
api_is_local=True
if Args.Remote:
    api_is_local=False
if Args.Local:
    api_is_local=True

randomseed = 12345
np.random.seed(randomseed)
runtime_ms = 500.0
savefolder = 'output/'+str(datetime.now()).replace(":", "_")
figspecs = {
    'figsize': (6,6),
    'linewidth': 0.5,
    'figext': 'pdf',
}

# 1. Init NES connection

bg_api = BG_API_Setup(user='Admonishing', passwd='Instruction')
if api_is_local:
    bg_api.set_local()
    print('Running locally.')
else:
    print('Running remotely.')
if not bg_api.BGNES_QuickStart(scriptversion, versionmustmatch=False, verbose=False):
    print('BG NES Interface access failed.')
    exit(1)

# 2. Init simulation

sys_name='xor_sc'
bg_api.BGNES_simulation_create(name=sys_name, seed=randomseed)

# 3. Define ground-truth model

INITTEXT1='''
1. Defining an XOR logic circuit composed of SimpleCompartmental
   principal neurons and interneurons. The network and its
   connectivity are specified explicitly.

   The steps we take:
   a. Define shapes for the neurons and place each specifically.
   b. Define shapes for the connections and place them.
   c. Create compartments.
   d. Create principal neurons.
   e. Create interneurons.
   f. Create receptors for active connections.
   g. Save the resulting neuronal circuit.

   Circuit:

   P_in0 (-45,-45) -----------------------+ // note that P_A0 has been removed
                |                         |
                +----> I_A0 (-15,-15) --> P_B0 (15,-15) --+
                                                          P_out (45, 0)
                +----> I_A1 (-15, 15) --> P_B1 (15, 15) --+
                |                         |
   P_in1 (-45, 45) --> P_A1 (-15, 45) ----+

   Distances of 30 um are typical between somas in cortex.
'''

print(INITTEXT1)

### Soma sizes

principal_soma_radius_um = 7.0                 # A typical radius for the soma of a human cortical pyramidal neuron 5-25 um.
interneuron_soma_radius_um = 3.0               # A typical radius for the soma of a human cortical interneuron 2.5-15 um.

### Axon and Dendrite start and end sizes

end0_radius_um = 0.75 # Typical radius at the axon hillock of a pyramidal neuron in human cortex.
end1_radius_um = 0.3  # Typical radius of distal axon segments of pyramidal neurons in human cortex.

### Relevant 3D points (as numpy arrays) for the build. See image ...

neuron_build_data = {}
connection_build_data = {}

# Soma points
points_3D_np = {
    'P_in0_pos': np.array([-45,-45, 0]),
    'P_in1_pos': np.array([-45, 45, 0]),
    'I_A0_pos': np.array([-15,-15, 0]),
    'I_A1_pos': np.array([-15, 15, 0]),
    'P_B0_pos': np.array([ 15,-45, 0]),
    'P_B1_pos': np.array([ 15, 45, 0]),
    'P_out_pos': np.array([ 45,  0, 0]),
}

# Receptor: points
points_3D_np['Pin0_IA0_rec'] = points_3D_np['I_A0_pos'] + np.array([-10, -5, 0])
points_3D_np['Pin1_IA1_rec'] = points_3D_np['I_A1_pos'] + np.array([-10, +5, 0])
points_3D_np['Pin0_PB0_rec'] = points_3D_np['P_B0_pos'] + np.array([-10, -5, 0])
points_3D_np['Pin1_PB1_rec'] = points_3D_np['P_B1_pos'] + np.array([-10, +5, 0])
points_3D_np['IA0_PB1_rec'] = points_3D_np['P_B1_pos'] + np.array([-13, -5, 0])
points_3D_np['IA1_PB0_rec'] = points_3D_np['P_B1_pos'] + np.array([-13, +5, 0])
points_3D_np['PB0_Pout_rec'] = points_3D_np['P_out_pos'] + np.array([-15, -5, 0])
points_3D_np['PB1_Pout_rec'] = points_3D_np['P_out_pos'] + np.array([-15, +5, 0])
# Receptor: shapes and type
connection_build_data['Pin0_IA0_rec'] = {
    'pre': 'P_in0',
    'post': 'I_A0',
    'shape': ( 'box',
        list(points_3D_np['Pin0_IA0_rec']),
        [0.1, 0.1, 0.1],
        [0.0, 0.0, 0.0],),
    'type': 'AMPA',
    'weight': 1.2,
}
connection_build_data['Pin1_IA1_rec'] = {
    'pre': 'P_in1',
    'post': 'I_A1',
    'shape': ( 'box',
        list(points_3D_np['Pin1_IA1_rec']),
        [0.1, 0.1, 0.1],
        [0.0, 0.0, 0.0],),
    'type': 'AMPA',
    'weight': 1.2,
}
connection_build_data['Pin0_PB0_rec'] = {
    'pre': 'P_in0',
    'post': 'P_B0',
    'shape': ( 'box',
        list(points_3D_np['Pin0_PB0_rec']),
        [0.1, 0.1, 0.1],
        [0.0, 0.0, 0.0],),
    'type': 'AMPA',
    'weight': 0.9,
}
connection_build_data['Pin1_PB1_rec'] = {
    'pre': 'P_in1',
    'post': 'P_B1',
    'shape': ( 'box',
        list(points_3D_np['Pin1_PB1_rec']),
        [0.1, 0.1, 0.1],
        [0.0, 0.0, 0.0],),
    'type': 'AMPA',
    'weight': 0.9,
}
connection_build_data['IA0_PB1_rec'] = {
    'pre': 'I_A0',
    'post': 'P_B1',
    'shape': ( 'box',
        list(points_3D_np['IA0_PB1_rec']),
        [0.1, 0.1, 0.1],
        [0.0, 0.0, 0.0],),
    'type': 'GABA',
    'weight': 1.2,
}
connection_build_data['IA1_PB0_rec'] = {
    'pre': 'I_A1',
    'post': 'P_B0',
    'shape': ( 'box',
        list(points_3D_np['IA1_PB0_rec']),
        [0.1, 0.1, 0.1],
        [0.0, 0.0, 0.0],),
    'type': 'GABA',
    'weight': 1.2,
}
connection_build_data['PB0_Pout_rec'] = {
    'pre': 'P_B0',
    'post': 'P_out',
    'shape': ( 'box',
        list(points_3D_np['PB0_Pout_rec']),
        [0.1, 0.1, 0.1],
        [0.0, 0.0, 0.0],),
    'type': 'AMPA',
    'weight': 1.0,
}
connection_build_data['PB1_Pout_rec'] = {
    'pre': 'P_B1',
    'post': 'P_out',
    'shape': ( 'box',
        list(points_3D_np['PB1_Pout_rec']),
        [0.1, 0.1, 0.1],
        [0.0, 0.0, 0.0],),
    'type': 'AMPA',
    'weight': 1.0,
}

### 3.1 Define shapes for the neurons and place each specifically.

# Pin0: soma: sphere
neuron_build_data['P_in0'] = {}
neuron_build_data['P_in0']['soma'] = {}
neuron_build_data['P_in0']['soma']['shapes'] = []
neuron_build_data['P_in0']['soma']['shapes'][0] = ( 'sphere',
    list(points_3D_np['P_in0_pos']) + [ principal_soma_radius_um ],)
# Pin0: dendrites: points
points_3D_np['Pin0_den0_s'] = points_3D_np['P_in0_pos'] + np.array([-principal_soma_radius_um, 0, 0])
points_3D_np['Pin0_den1_s'] = points_3D_np['Pin0_den0_s']
points_3D_np['Pin0_den0_e'] = points_3D_np['P_in0_pos'] + np.array([-10, -10, 0])
points_3D_np['Pin0_den1_e'] = points_3D_np['P_in0_pos'] + np.array([-10, +10, 0])
# Pin0: dendrites: cylinders
neuron_build_data['P_in0']['dendrites'] = {}
neuron_build_data['P_in0']['dendrites']['shapes'] = []
neuron_build_data['P_in0']['dendrites']['shapes'][0] = ( 'cylinder',
        list(points_3D_np['Pin0_den0_s']) + [ end0_radius_um ],
        list(points_3D_np['Pin0_den0_e']) + [ end1_radius_um ],)
neuron_build_data['P_in0']['dendrites']['shapes'][1] = ( 'cylinder',
        list(points_3D_np['Pin0_den1_s']) + [ end0_radius_um ],
        list(points_3D_np['Pin0_den1_e']) + [ end1_radius_um ],)
# Pin0: axon: points
points_3D_np['Pin0_ax0_s'] = points_3D_np['P_in0_pos'] + np.array([+principal_soma_radius_um, 0, 0])
points_3D_np['Pin0_ax0_e'] = points_3D_np['Pin0_ax0_s'] + np.array([+5, 0, 0])
points_3D_np['Pin0_ax0_0_s'] = points_3D_np['Pin0_ax0_e']
points_3D_np['Pin0_ax0_0_e'] = points_3D_np['Pin0_ax0_0_s'] + 1.3*( points_3D_np['Pin0_PB0_rec'] - points_3D_np['Pin0_ax0_0_s'] )
points_3D_np['Pin0_ax0_1_s'] = points_3D_np['Pin0_ax0_e']
points_3D_np['Pin0_ax0_1_e'] = points_3D_np['Pin0_ax0_1_s'] + 1.3*( points_3D_np['Pin0_IA0_rec'] - points_3D_np['Pin0_ax0_1_s'] )
# Pin0: axon: cylinders
neuron_build_data['P_in0']['axons'] = {}
neuron_build_data['P_in0']['axons']['shapes'] = []
neuron_build_data['P_in0']['axons']['shapes'][0] = ( 'cylinder',
        list(points_3D_np['Pin0_ax0_s']) + [ end0_radius_um ],
        list(points_3D_np['Pin0_ax0_e']) + [ end1_radius_um ],)
neuron_build_data['P_in0']['axons']['shapes'][1] = ( 'cylinder',
        list(points_3D_np['Pin0_ax0_0_s']) + [ end1_radius_um ],
        list(points_3D_np['Pin0_ax0_0_e']) + [ end1_radius_um ],)
neuron_build_data['P_in0']['axons']['shapes'][2] = ( 'cylinder',
        list(points_3D_np['Pin0_ax0_1_s']) + [ end1_radius_um ],
        list(points_3D_np['Pin0_ax0_1_e']) + [ end1_radius_um ],)
# Update receptor data
connection_build_data['Pin0_PB0_rec']['from_idx'] = 1 # Pin0_ax0_0_e
connection_build_data['Pin0_IA0_rec']['from_idx'] = 2 # Pin0_ax0_1_e

# Pin1: soma: sphere
neuron_build_data['P_in1'] = {}
neuron_build_data['P_in1']['soma'] = {}
neuron_build_data['P_in1']['soma']['shapes'] = []
neuron_build_data['P_in1']['soma']['shapes'][0] = ( 'sphere',
    list(points_3D_np['P_in1_pos']) + [ principal_soma_radius_um ],)
# Pin1: dendrites: points
points_3D_np['Pin1_den0_s'] = points_3D_np['P_in1_pos'] + np.array([-principal_soma_radius_um, 0, 0])
points_3D_np['Pin1_den1_s'] = points_3D_np['Pin1_den0_s']
points_3D_np['Pin1_den0_e'] = points_3D_np['P_in1_pos'] + np.array([-10, -10, 0])
points_3D_np['Pin1_den1_e'] = points_3D_np['P_in1_pos'] + np.array([-10, +10, 0])
# Pin1: dendrites: cylinders
neuron_build_data['P_in1']['dendrites'] = {}
neuron_build_data['P_in1']['dendrites']['shapes'] = []
neuron_build_data['P_in1']['dendrites']['shapes'][0] = ( 'cylinder',
        list(points_3D_np['Pin1_den0_s']) + [ end0_radius_um ],
        list(points_3D_np['Pin1_den0_e']) + [ end1_radius_um ],)
neuron_build_data['P_in1']['dendrites']['shapes'][1] = ( 'cylinder',
        list(points_3D_np['Pin1_den1_s']) + [ end0_radius_um ],
        list(points_3D_np['Pin1_den1_e']) + [ end1_radius_um ],)
# Pin1: axon: points
points_3D_np['Pin1_ax0_s'] = points_3D_np['P_in1_pos'] + np.array([+principal_soma_radius_um, 0, 0])
points_3D_np['Pin1_ax0_e'] = points_3D_np['Pin1_ax0_s'] + np.array([+5, 0, 0])
points_3D_np['Pin1_ax0_0_s'] = points_3D_np['Pin1_ax0_e']
points_3D_np['Pin1_ax0_0_e'] = points_3D_np['Pin1_ax0_0_s'] + 1.3*( points_3D_np['Pin1_PB1_rec'] - points_3D_np['Pin1_ax0_0_s'] )
points_3D_np['Pin1_ax0_1_s'] = points_3D_np['Pin1_ax0_e']
points_3D_np['Pin1_ax0_1_e'] = points_3D_np['Pin1_ax0_1_s'] + 1.3*( points_3D_np['Pin1_IA1_rec'] - points_3D_np['Pin1_ax0_1_s'] )
# Pin1: axon: cylinders
neuron_build_data['P_in1']['axons'] = {}
neuron_build_data['P_in1']['axons']['shapes'] = []
neuron_build_data['P_in1']['axons']['shapes'][0] = ( 'cylinder',
        list(points_3D_np['Pin1_ax0_s']) + [ end0_radius_um ],
        list(points_3D_np['Pin1_ax0_e']) + [ end1_radius_um ],)
neuron_build_data['P_in1']['axons']['shapes'][1] = ( 'cylinder',
        list(points_3D_np['Pin1_ax0_0_s']) + [ end1_radius_um ],
        list(points_3D_np['Pin1_ax0_0_e']) + [ end1_radius_um ],)
neuron_build_data['P_in1']['axons']['shapes'][2] = ( 'cylinder',
        list(points_3D_np['Pin1_ax0_1_s']) + [ end1_radius_um ],
        list(points_3D_np['Pin1_ax0_1_e']) + [ end1_radius_um ],)
# Update receptor data
connection_build_data['Pin1_PB1_rec']['from_idx'] = 1 # Pin1_ax0_0_e
connection_build_data['Pin1_IA1_rec']['from_idx'] = 2 # Pin1_ax0_1_e

# IA0: soma: sphere
neuron_build_data['I_A0'] = {}
neuron_build_data['I_A0']['soma'] = {}
neuron_build_data['I_A0']['soma']['shapes'] = []
neuron_build_data['I_A0']['soma']['shapes'][0] = ( 'sphere',
    list(points_3D_np['I_A0_pos']) + [ interneuron_soma_radius_um ],)
# IA0: dendrites: points
points_3D_np['IA0_den0_s'] = points_3D_np['I_A0_pos'] + np.array([-interneuron_soma_radius_um, 0, 0])
points_3D_np['IA0_den1_s'] = points_3D_np['IA0_den0_s']
points_3D_np['IA0_den0_e'] = points_3D_np['IA0_den0_s'] + 1.3*( points_3D_np['Pin0_IA0_rec'] - points_3D_np['IA0_den0_s'] )
points_3D_np['IA0_den1_e'] = points_3D_np['I_A0_pos'] + np.array([-10, +10, 0])
# IA0: dendrites: cylinders
neuron_build_data['I_A0']['dendrites'] = {}
neuron_build_data['I_A0']['dendrites']['shapes'] = []
neuron_build_data['I_A0']['dendrites']['shapes'][0] = ( 'cylinder',
        list(points_3D_np['IA0_den0_s']) + [ end0_radius_um ],
        list(points_3D_np['IA0_den0_e']) + [ end1_radius_um ],)
neuron_build_data['I_A0']['dendrites']['shapes'][1] = ( 'cylinder',
        list(points_3D_np['IA0_den1_s']) + [ end0_radius_um ],
        list(points_3D_np['IA0_den1_e']) + [ end1_radius_um ],)
# Update receptor data
connection_build_data['Pin0_IA0_rec']['to_idx'] = 0 # IA0_den0_e
# IA0: axon: points
points_3D_np['IA0_ax0_s'] = points_3D_np['I_A0_pos'] + np.array([+interneuron_soma_radius_um, 0, 0])
points_3D_np['IA0_ax0_e'] = points_3D_np['IA0_ax0_s'] + np.array([+5, 0, 0])
points_3D_np['IA0_ax0_0_s'] = points_3D_np['IA0_ax0_e']
points_3D_np['IA0_ax0_0_e'] = points_3D_np['IA0_ax0_0_s'] + 1.17*( points_3D_np['IA0_PB1_rec'] - points_3D_np['IA0_ax0_0_s'] )
# IA0: axon: cylinders
neuron_build_data['I_A0']['axons'] = {}
neuron_build_data['I_A0']['axons']['shapes'] = []
neuron_build_data['I_A0']['axons']['shapes'][0] = ( 'cylinder',
        list(points_3D_np['IA0_ax0_s']) + [ end0_radius_um ],
        list(points_3D_np['IA0_ax0_e']) + [ end1_radius_um ],)
neuron_build_data['I_A0']['axons']['shapes'][1] = ( 'cylinder',
        list(points_3D_np['IA0_ax0_0_s']) + [ end1_radius_um ],
        list(points_3D_np['IA0_ax0_0_e']) + [ end1_radius_um ],)
# Update receptor data
connection_build_data['IA0_PB1_rec']['from_idx'] = 1 # IA0_ax0_0_e

# IA1: soma: sphere
neuron_build_data['I_A1'] = {}
neuron_build_data['I_A1']['soma'] = {}
neuron_build_data['I_A1']['soma']['shapes'] = []
neuron_build_data['I_A1']['soma']['shapes'][0] = ( 'sphere',
    list(points_3D_np['I_A1_pos']) + [ interneuron_soma_radius_um ],)
# IA1: dendrites: points
points_3D_np['IA1_den0_s'] = points_3D_np['I_A1_pos'] + np.array([-interneuron_soma_radius_um, 0, 0])
points_3D_np['IA1_den1_s'] = points_3D_np['IA1_den0_s']
points_3D_np['IA1_den0_e'] = points_3D_np['IA1_den1_s'] + 1.3*( points_3D_np['Pin1_IA1_rec'] - points_3D_np['IA1_den1_s'] )
points_3D_np['IA1_den1_e'] = points_3D_np['I_A1_pos'] + np.array([-10, -10, 0])
# IA1: dendrites: cylinders
neuron_build_data['I_A1']['dendrites'] = {}
neuron_build_data['I_A1']['dendrites']['shapes'] = []
neuron_build_data['I_A1']['dendrites']['shapes'][0] = ( 'cylinder',
        list(points_3D_np['IA1_den0_s']) + [ end0_radius_um ],
        list(points_3D_np['IA1_den0_e']) + [ end1_radius_um ],)
neuron_build_data['I_A1']['dendrites']['shapes'][1] = ( 'cylinder',
        list(points_3D_np['IA1_den1_s']) + [ end0_radius_um ],
        list(points_3D_np['IA1_den1_e']) + [ end1_radius_um ],)
# Update receptor data
connection_build_data['Pin1_IA1_rec']['to_idx'] = 0 # IA1_den0_e
# IA1: axon: points
points_3D_np['IA1_ax0_s'] = points_3D_np['I_A1_pos'] + np.array([+interneuron_soma_radius_um, 0, 0])
points_3D_np['IA1_ax0_e'] = points_3D_np['IA1_ax0_s'] + np.array([+5, 0, 0])
points_3D_np['IA1_ax0_0_s'] = points_3D_np['IA1_ax0_e']
points_3D_np['IA1_ax0_0_e'] = points_3D_np['IA1_ax0_0_s'] + 1.17*( points_3D_np['IA1_PB0_rec'] - points_3D_np['IA1_ax0_0_s'] )
# IA1: axon: cylinders
neuron_build_data['I_A1']['axons'] = {}
neuron_build_data['I_A1']['axons']['shapes'] = []
neuron_build_data['I_A1']['axons']['shapes'][0] = ( 'cylinder',
        list(points_3D_np['IA1_ax0_s']) + [ end0_radius_um ],
        list(points_3D_np['IA1_ax0_e']) + [ end1_radius_um ],)
neuron_build_data['I_A1']['axons']['shapes'][1] = ( 'cylinder',
        list(points_3D_np['IA1_ax0_0_s']) + [ end1_radius_um ],
        list(points_3D_np['IA1_ax0_0_e']) + [ end1_radius_um ],)
# Update receptor data
connection_build_data['IA1_PB0_rec']['from_idx'] = 1 # IA1_ax0_0_e

# PB0: soma: sphere
neuron_build_data['P_B0'] = {}
neuron_build_data['P_B0']['soma'] = {}
neuron_build_data['P_B0']['soma']['shapes'] = []
neuron_build_data['P_B0']['soma']['shapes'][0] = ( 'sphere',
    list(points_3D_np['P_B0_pos']) + [ principal_soma_radius_um ],)
# PB0: dendrites: points
points_3D_np['PB0_den0_s'] = points_3D_np['P_B0_pos'] + np.array([-principal_soma_radius_um, 0, 0])
points_3D_np['PB0_den1_s'] = points_3D_np['PB0_den0_s']
points_3D_np['PB0_den0_e'] = points_3D_np['PB0_den0_s'] + 1.3*( points_3D_np['Pin0_PB0_rec'] - points_3D_np['PB0_den0_s'] )
points_3D_np['PB0_den1_e'] = points_3D_np['PB0_den1_s'] + 1.3*( points_3D_np['IA1_PB0_rec'] - points_3D_np['PB0_den1_s'] )
# PB0: dendrites: cylinders
neuron_build_data['P_B0']['dendrites'] = {}
neuron_build_data['P_B0']['dendrites']['shapes'] = []
neuron_build_data['P_B0']['dendrites']['shapes'][0] = ( 'cylinder',
        list(points_3D_np['PB0_den0_s']) + [ end0_radius_um ],
        list(points_3D_np['PB0_den0_e']) + [ end1_radius_um ],)
neuron_build_data['P_B0']['dendrites']['shapes'][1] = ( 'cylinder',
        list(points_3D_np['PB0_den1_s']) + [ end0_radius_um ],
        list(points_3D_np['PB0_den1_e']) + [ end1_radius_um ],)
# Update receptor data
connection_build_data['Pin0_PB0_rec']['to_idx'] = 0 # PB0_den0_e
connection_build_data['IA1_PB0_rec']['to_idx'] = 1 # PB0_den1_e
# PB0: axon: points
points_3D_np['PB0_ax0_s'] = points_3D_np['P_B0_pos'] + np.array([+principal_soma_radius_um, 0, 0])
points_3D_np['PB0_ax0_e'] = points_3D_np['PB0_ax0_s'] + np.array([+5, 0, 0])
points_3D_np['PB0_ax0_0_s'] = points_3D_np['PB0_ax0_e']
points_3D_np['PB0_ax0_0_e'] = points_3D_np['PB0_ax0_0_s'] + 1.17*( points_3D_np['PB0_Pout_rec'] - points_3D_np['PB0_ax0_0_s'] )
# PB0: axon: cylinders
neuron_build_data['P_B0']['axons'] = {}
neuron_build_data['P_B0']['axons']['shapes'] = []
neuron_build_data['P_B0']['axons']['shapes'][0] = ( 'cylinder',
        list(points_3D_np['PB0_ax0_s']) + [ end0_radius_um ],
        list(points_3D_np['PB0_ax0_e']) + [ end1_radius_um ],)
neuron_build_data['P_B0']['axons']['shapes'][1] = ( 'cylinder',
        list(points_3D_np['PB0_ax0_0_s']) + [ end1_radius_um ],
        list(points_3D_np['PB0_ax0_0_e']) + [ end1_radius_um ],)
# Update receptor data
connection_build_data['PB0_Pout_rec']['from_idx'] = 1 # PB0_ax0_0_e

# PB1: soma: sphere
neuron_build_data['P_B1'] = {}
neuron_build_data['P_B1']['soma'] = {}
neuron_build_data['P_B1']['soma']['shapes'] = []
neuron_build_data['P_B1']['soma']['shapes'][0] = ( 'sphere',
    list(points_3D_np['P_B1_pos']) + [ principal_soma_radius_um ],)
# PB1: dendrites: points
points_3D_np['PB1_den0_s'] = points_3D_np['P_B1_pos'] + np.array([-principal_soma_radius_um, 0, 0])
points_3D_np['PB1_den1_s'] = points_3D_np['PB1_den0_s']
points_3D_np['PB1_den0_e'] = points_3D_np['PB1_den0_s'] + 1.3*( points_3D_np['Pin1_PB1_rec'] - points_3D_np['PB1_den0_s'] )
points_3D_np['PB1_den1_e'] = points_3D_np['PB1_den1_s'] + 1.3*( points_3D_np['IA0_PB1_rec'] - points_3D_np['PB1_den1_s'] )
# PB1: dendrites: cylinders
neuron_build_data['P_B1']['dendrites'] = {}
neuron_build_data['P_B1']['dendrites']['shapes'] = []
neuron_build_data['P_B1']['dendrites']['shapes'][0] = ( 'cylinder',
        list(points_3D_np['PB1_den0_s']) + [ end0_radius_um ],
        list(points_3D_np['PB1_den0_e']) + [ end1_radius_um ],)
neuron_build_data['P_B1']['dendrites']['shapes'][1] = ( 'cylinder',
        list(points_3D_np['PB1_den1_s']) + [ end0_radius_um ],
        list(points_3D_np['PB1_den1_e']) + [ end1_radius_um ],)
# Update receptor data
connection_build_data['Pin1_PB1_rec']['to_idx'] = 0 # PB1_den0_e
connection_build_data['IA0_PB1_rec']['to_idx'] = 1 # PB1_den1_e
# PB1: axon: points
points_3D_np['PB1_ax0_s'] = points_3D_np['P_B1_pos'] + np.array([+principal_soma_radius_um, 0, 0])
points_3D_np['PB1_ax0_e'] = points_3D_np['PB1_ax0_s'] + np.array([+5, 0, 0])
points_3D_np['PB1_ax0_0_s'] = points_3D_np['PB1_ax0_e']
points_3D_np['PB1_ax0_0_e'] = points_3D_np['PB1_ax0_0_s'] + 1.17*( points_3D_np['PB1_Pout_rec'] - points_3D_np['PB1_ax0_0_s'] )
# PB1: axon: cylinders
neuron_build_data['P_B1']['axons'] = {}
neuron_build_data['P_B1']['axons']['shapes'] = []
neuron_build_data['P_B1']['axons']['shapes'][0] = ( 'cylinder',
        list(points_3D_np['PB1_ax0_s']) + [ end0_radius_um ],
        list(points_3D_np['PB1_ax0_e']) + [ end1_radius_um ],)
neuron_build_data['P_B1']['axons']['shapes'][1] = ( 'cylinder',
        list(points_3D_np['PB1_ax0_0_s']) + [ end1_radius_um ],
        list(points_3D_np['PB1_ax0_0_e']) + [ end1_radius_um ],)
# Update receptor data
connection_build_data['PB1_Pout_rec']['from_idx'] = 1 # PB1_ax0_0_e

# Pout: soma: sphere
neuron_build_data['P_out'] = {}
neuron_build_data['P_out']['soma'] = {}
neuron_build_data['P_out']['soma']['shapes'] = []
neuron_build_data['P_out']['soma']['shapes'][0] = ( 'sphere',
    list(points_3D_np['P_out_pos']) + [ principal_soma_radius_um ],)
# Pout: dendrites: points
points_3D_np['Pout_den0_s'] = points_3D_np['P_out_pos'] + np.array([-principal_soma_radius_um, 0, 0])
points_3D_np['Pout_den1_s'] = points_3D_np['Pout_den0_s']
points_3D_np['Pout_den0_e'] = points_3D_np['Pout_den0_s'] + 1.3*( points_3D_np['PB0_Pout_rec'] - points_3D_np['Pout_den0_s'] )
points_3D_np['Pout_den1_e'] = points_3D_np['Pout_den1_s'] + 1.3*( points_3D_np['PB1_Pout_rec'] - points_3D_np['Pout_den1_s'] )
# Pout: dendrites: cylinders
neuron_build_data['P_out']['dendrites'] = {}
neuron_build_data['P_out']['dendrites']['shapes'] = []
neuron_build_data['P_out']['dendrites']['shapes'][0] = ( 'cylinder',
        list(points_3D_np['Pout_den0_s']) + [ end0_radius_um ],
        list(points_3D_np['Pout_den0_e']) + [ end1_radius_um ],)
neuron_build_data['P_out']['dendrites']['shapes'][1] = ( 'cylinder',
        list(points_3D_np['Pout_den1_s']) + [ end0_radius_um ],
        list(points_3D_np['Pout_den1_e']) + [ end1_radius_um ],)
# Update receptor data
connection_build_data['PB0_Pout_rec']['to_idx'] = 0 # Pout_den0_e
connection_build_data['PB1_Pout_rec']['to_idx'] = 1 # Pout_den1_e
# Pout: axon: points
points_3D_np['Pout_ax0_s'] = points_3D_np['P_out_pos'] + np.array([+principal_soma_radius_um, 0, 0])
points_3D_np['Pout_ax0_e'] = points_3D_np['Pout_ax0_s'] + np.array([+5, 0, 0])
# Pout: axon: cylinders
neuron_build_data['P_out']['axons'] = {}
neuron_build_data['P_out']['axons']['shapes'] = []
neuron_build_data['P_out']['axons']['shapes'][0] = ( 'cylinder',
        list(points_3D_np['Pout_ax0_s']) + [ end0_radius_um ],
        list(points_3D_np['Pout_ax0_e']) + [ end1_radius_um ],)

### 3.2 Create SC shapes and compartments.

neuron_names = list(neuron_build_data.keys())

def make_shape(shape_data:list):
    shape_type = shape_data[0]
    if shape_type == 'sphere':
        return bg_api.BGNES_sphere_create(
            radius_um=shape_data[1][3],
            center_um=shape_data[1][0:3]),)
    elif shape_type == 'cylinder':
        return bg_api.BGNES_cylinder_create(
            Point1Radius_um=shape_data[1][3],
            Point1Position_um=shape_data[1][0:3],
            Point2Radius_um=shape_data[2][3],
            Point2Position_um=shape_data[2][0:3],)
    elif shape_type == 'box':
        return bg_api.BGNES_box_create(
            CenterPosition_um=shape_data[1],
            Dimensions_um=shape_data[2],
            Rotation_rad=shape_data[3],)

neuron_Vm_mV = -60.0
neuron_Vrest_mV = -60.0
neuron_Vact_mV = -50.0
neuron_Vahp_mV = -20.0
neuron_tau_AHP_ms = 30.0

for n in neuron_names:

    for morph in ['soma', 'dendrites', 'axons']:

        neuron_build_data[n][morph]['shape_refs'] = []       # *** Actually, we probably only need to store the IDs
        neuron_build_data[n][morph]['compartment_refs'] = [] # *** Actually, we probably only need to store the IDs
        for s in neuron_build_data[n][morph]['shapes']:
            shape_ref = make_shape(s)
            compartment_ref = bg_api.BGNES_SC_compartment_create(
                ShapeID=shape_ref.ID,
                MembranePotential_mV=neuron_Vm_mV,
                RestingPotential_mV=neuron_Vrest_mV,
                SpikeThreshold_mV=neuron_Vact_mV,
                DecayTime_ms=neuron_tau_AHP_ms,
                AfterHyperpolarizationAmplitude_mV=neuron_Vahp_mV,)
            neuron_build_data[n][morph]['shape_refs'].append(shape_ref)
            neuron_build_data[n][morph]['compartment_refs'].append(compartment_ref)

# Update receptor data with actual compartment IDs
for connection_data in connection_build_data:
    pre_n = connection_data['pre']
    from_idx = connection_data['from_idx']
    post_n = connection_data['post']
    to_idx = connection_data['to_idx']
    connection_data['from_ID'] = neuron_build_data[pre_n]['axons']['compartment_refs'][from_idx].ID
    connection_data['to_ID'] = neuron_build_data[post_n]['dendrites']['compartment_refs'][to_idx].ID

### 3.3 Create neurons.

neuron_tau_PSPr = 5.0
neuron_tau_PSPd = 25.0
neuron_IPSP = 870.0 # nA
#neuron_tau_spont_mean_stdev_ms = (0, 0) # 0 means no spontaneous activity
#neuron_t_spont_next = -1

# *** CHECK: If we need to slow down P_B0 and P_B1 PSP rise time
#            then we need to explicitly specify neuron_tau_PSPr
#            for each neuron in the neuron_build_data.
#            The longer rise time would receive and added +200 ms.

def neuron_builder(neuron_name:str):
    SomaIDs = [ compartment.ID for compartment in neuron_build_data[neuron_name]['soma']['compartment_refs'] ]
    DendriteIDs = [ compartment.ID for compartment in neuron_build_data[neuron_name]['dendrites']['compartment_refs'] ]
    AxonIDs = [ compartment.ID for compartment in neuron_build_data[neuron_name]['axons']['compartment_refs'] ]
    return bg_api.BGNES_SC_neuron_create(
        SomaIDs=SomaIDs,
        DendriteIDs=DendriteIDs,
        AxonIDs=AxonIDs,
        MembranePotential_mV=neuron_Vm_mV,
        RestingPotential_mV=neuron_Vrest_mV,
        SpikeThreshold_mV=neuron_Vact_mV,
        DecayTime_ms=neuron_tau_AHP_ms,
        AfterHyperpolarizationAmplitude_mV=neuron_Vahp_mV,
        PostsynapticPotentialRiseTime_ms=neuron_tau_PSPr,
        PostsynapticPotentialDecayTime_ms=neuron_tau_PSPd,
        PostsynapticPotentialAmplitude_nA=neuron_IPSP,
    )

cells = {}
for n in neuron_names:
    neuron_ref = neuron_builder(n)
    cells[n] = neuron_ref

### 3.4 Create receptors for active connections.

AMPA_conductance = 40.0 #60 # nS
GABA_conductance = -40.0 # nS

#receptor_functionals = []
#receptor_morphologies = []
for connection_data in connection_build_data:
    # Set the total conductance through receptors at synapses at this connection:
    if connection_data['type'] == 'AMPA':
        conductance = AMPA_conductance
    else:
        conductance = GABA_conductance
    receptor_conductance = conductance / connection_data['weight'] # Divided by weight to avoid counter-intuitive weight interpretation.
    print("Setting up '%s' receptor for connection from %s to %s." % (connection_data['type'], connection_data['pre'], connection_data['post']))

    # Build receptor form:
    print('Receptor loction: '+str(connection_data['shape'][1]))
    receptor_box = make_shape(connection_data['shape'])
    #receptor_morphologies.append(receptor_box)

    # Build receptor function:
    from_compartment_id = from_axon.ID
    to_compartment_id = to_cell.SomaID
    receptor = bg_api.BGNES_BS_receptor_create(
        SourceCompartmentID=connection_data['from_ID'],
        DestinationCompartmentID=connection_data['to_ID'],
        Conductance_nS=receptor_conductance,
        TimeConstantRise_ms=neuron_tau_PSPr,
        TimeConstantDecay_ms=neuron_tau_PSPd,
        ReceptorMorphology=receptor_box.ID,
    )
    #receptor_functionals.append( (receptor, connection_data['post']) )

# 3.7 Save the ground-truth system.

response = bg_api.BGNES_save()
print('Saved simulation: '+str(response))

with open(".SimulationHandle", "w") as f:
    print(f"Saving simulation handle '{response[0]['SavedSimName']}' to '.SimulationHandle'")
    f.write(response[0]['SavedSimName'])


STIMTEXT1='''
Dynamic activity:

God's eye direct access to every aspect of the in-silico
ground-truth system includes the ability to specifically
cause a somatic action potential at any time.

We use this to test the XOR logic by running the input
spiking sequences:

  0 0 = (no spikes for the first 100 ms)
  1 0 = (100.0, P_in0)
  0 1 = (200.0, P_in1)
  1 1 = (300.0, P_in0), (300.0, P_in1)
'''

# 4. Init experiment

print(STIMTEXT1)
t_soma_fire_ms = [
    (100.0, cells['P_in0'].ID),
    (200.0, cells['P_in1'].ID),
    (300.0, cells['P_in0'].ID),
    (300.0, cells['P_in1'].ID),
]
print('Directed somatic firing: '+str(t_soma_fire_ms))

response = bg_api.BGNES_set_specific_AP_times(
    TimeNeuronPairs=t_soma_fire_ms,
)

# 5. Run experiment

print('\nRunning experiment for %.1f milliseconds...\n' % runtime_ms)

# 5.1 Set record-all

t_max_ms=-1 # record forever
bg_api.BGNES_simulation_recordall(t_max_ms)

# 5.2 Run for specified simulation time

if not bg_api.BGNES_simulation_runfor_and_await_outcome(runtime_ms):
    exit(1)

# 5.3 Retrieve recordings and plot

def find_cell_with_id(id:int)->str:
    for n in cells.keys():
        if cells[n].ID == id:
            return n
    return ''

recording_dict = bg_api.BGNES_get_recording()
if isinstance(recording_dict, dict):
    if "StatusCode" in recording_dict:
        if recording_dict["StatusCode"] != 0:
            print('Retrieving recording failed: StatusCode = '+str(recording_dict["StatusCode"]))
        else:
            if "Recording" not in recording_dict:
                print('Missing "Recording" key.')
            else:
                if recording_dict["Recording"] is None:
                    print('Recording is empty.')
                else:
                    print('Keys in record: '+str(list(recording_dict["Recording"].keys())))

                    print('Neurons for which output was recorded: '+str(list(recording_dict["Recording"]['neurons'].keys())))

                    #print('The arrangement of neurons in the plot at %s will be:' % savefolder)
                    sorted_neuron_names = [ '?' for n in range(len(cells))]
                    for neuron_idstr in recording_dict["Recording"]['neurons'].keys():
                        neuron_name = find_cell_with_id(int(neuron_idstr))
                        sorted_neuron_names[int(neuron_idstr)] = neuron_name
                        #print(neuron_idstr+' --> '+find_cell_with_id(int(neuron_idstr)))

                    plot_recorded(
                        savefolder=savefolder,
                        data=recording_dict["Recording"],
                        figspecs=figspecs,
                        cell_titles=sorted_neuron_names)

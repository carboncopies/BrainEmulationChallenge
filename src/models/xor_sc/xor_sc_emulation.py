#!/usr/bin/env python3
# xor_sc_emulation.py
# Randal A. Koene, 20240325

'''
The XOR SimpleCompartmental example uses branching axons in a representation of a
meaningful logic circuit to produce expected functional output.

This file implements a demonstration of an emulation specification, i.e. a
neural circuit reconstruction submitted to the challenge.

Here, we do not show the steps taken by the challenge participant to interpret
the acquisition data stack and to derive from that the circuit architecture and
parameter values.
We show the step where the participant submits the resulting circuit, which is
implemented in the VBP/NES environment for validation.
For demonstration purposes, we create this implementation in the same manner as
the ground-truth system, with a few changes to simulate reconstruction errors.

VBP process step 03: emulation
WBE topic-level ??: 
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

def event_occurs(prob:float)->bool:
    return np.random.rand() <= prob

prob_missed_receptor = 0.3

#default:
api_is_local=True
if Args.Remote:
    api_is_local=False
if Args.Local:
    api_is_local=True

randomseed = 12345
np.random.seed(randomseed)
runtime_ms = 500.0
savefolder = 'output/'+str(datetime.now()).replace(":", "_")+'-emulation'
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

sys_name='em_xor_sc'
bg_api.BGNES_simulation_create(name=sys_name, seed=randomseed)

# 3. Define ground-truth model

INITTEXT1=r'''
1. After analyzing the data stack obtained from the WBE challange,
   we derived a system architecture from the identified connectome
   and we set up parameter values according to our system identifiction
   and translation method. Here is the model implementation of the
   resulting circuit reconstruction.

   The steps we take:
   a. Define shapes for the neurons and place each specifically.
   b. Define shapes for the connections and place them.
   c. Create compartments.
   d. Create principal neurons.
   e. Create interneurons.
   f. Create receptors for active connections.
   g. Save the resulting neuronal circuit.

   Circuit:

        +------------>P_out (0, -45)<------------+
        |                                        |
        |                                        |
   P_B0 (-45,-15)<----------+  +--------->P_B1 (45, -15)
        |                    \/                  |
        |                    /\                  |
        |     I_A0 (-15, 15)   I_A1 (15, 15)     |
        |      /                           \     |
        |     /                             \    |
   P_in0 (-45, 45)                         P_in1(45, 45)

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
    'P_in0_pos': np.array([-45, 45, 0]),
    'P_in1_pos': np.array([ 45, 45, 0]),
    'I_A0_pos' : np.array([-15, 15, 5]),
    'I_A1_pos' : np.array([ 15, 15,-5]),
    'P_B0_pos' : np.array([-45,-15, 0]),
    'P_B1_pos' : np.array([ 45,-15, 0]),
    'P_out_pos': np.array([ 0, -45, 0]),
}

# Receptor: points
points_3D_np['Pin0_IA0_rec'] = points_3D_np['I_A0_pos'] + np.array([-10, -5, 0])
points_3D_np['Pin1_IA1_rec'] = points_3D_np['I_A1_pos'] + np.array([-10, +5, 0])
points_3D_np['Pin0_PB0_rec'] = points_3D_np['P_B0_pos'] + np.array([-10, -5, 0])
points_3D_np['Pin1_PB1_rec'] = points_3D_np['P_B1_pos'] + np.array([-10, +5, 0])
points_3D_np['IA0_PB1_rec'] = points_3D_np['P_B1_pos'] + np.array([-13, -5, 0])
points_3D_np['IA1_PB0_rec'] = points_3D_np['P_B0_pos'] + np.array([-13, +5, 0])
points_3D_np['PB0_Pout_rec'] = points_3D_np['P_out_pos'] + np.array([-15, -5, 0])
points_3D_np['PB1_Pout_rec'] = points_3D_np['P_out_pos'] + np.array([-15, +5, 0])
# Receptor: shapes and type
def set_connection_data(connection:str, pre:str, post:str, _type:str, weight:float):
    connection_build_data[connection] = {
        'pre': pre,
        'post': post,
        'shape': ( 'box',
            points_3D_np[connection].tolist(),
            [0.1, 0.1, 0.1],
            [0.0, 0.0, 0.0],),
        'type': _type,
        'weight': weight,
    }

set_connection_data('Pin0_IA0_rec', 'P_in0', 'I_A0', 'AMPA', 1.2)
set_connection_data('Pin1_IA1_rec', 'P_in1', 'I_A1', 'AMPA', 1.2)
set_connection_data('Pin0_PB0_rec', 'P_in0', 'P_B0', 'AMPA', 0.9)
set_connection_data('Pin1_PB1_rec', 'P_in1', 'P_B1', 'AMPA', 0.9)
set_connection_data('IA0_PB1_rec', 'I_A0', 'P_B1', 'GABA', 1.2)
set_connection_data('IA1_PB0_rec', 'I_A1', 'P_B0', 'GABA', 1.2)
set_connection_data('PB0_Pout_rec', 'P_B0', 'P_out', 'AMPA', 1.0)
set_connection_data('PB1_Pout_rec', 'P_B1', 'P_out', 'AMPA', 1.0)

### 3.1 Define shapes for the neurons and place each specifically.

def set_neuron_soma(neuron:str, center:str, radius_um:float):
    neuron_build_data[neuron] = {}
    neuron_build_data[neuron]['soma'] = {}
    neuron_build_data[neuron]['soma']['shapes'] = []
    neuron_build_data[neuron]['soma']['shapes'].append( ( 'sphere',
        points_3D_np[center].tolist() + [ radius_um ],) )

def dendrite_root_start_np(center:str, radius_um:float):
    return points_3D_np[center] + np.array([-radius_um, 0, 0])

def axon_root_start_np(center:str, radius_um:float):
    return points_3D_np[center] + np.array([+radius_um, 0, 0])

def axon_root_end_np(startpoint:str):
    return points_3D_np[startpoint] + np.array([+5, 0, 0])

def set_neuron_dendrite_branch(neuron:str, startpoint:str, startradius_um:float, endpoint:str, endradius_um:float):
    if 'dendrites' not in neuron_build_data[neuron]:
        neuron_build_data[neuron]['dendrites'] = {}
    if 'shapes' not in neuron_build_data[neuron]['dendrites']:
        neuron_build_data[neuron]['dendrites']['shapes'] = []
    neuron_build_data[neuron]['dendrites']['shapes'].append( ( 'cylinder',
        points_3D_np[startpoint].tolist() + [ startradius_um ],
        points_3D_np[endpoint].tolist() + [ endradius_um ],) )

def set_neuron_axon_branch(neuron:str, startpoint:str, startradius_um:float, endpoint:str, endradius_um:float):
    if 'axons' not in neuron_build_data[neuron]:
        neuron_build_data[neuron]['axons'] = {}
    if 'shapes' not in neuron_build_data[neuron]['axons']:
        neuron_build_data[neuron]['axons']['shapes'] = []
    neuron_build_data[neuron]['axons']['shapes'].append( ( 'cylinder',
        points_3D_np[startpoint].tolist() + [ startradius_um ],
        points_3D_np[endpoint].tolist() + [ endradius_um ],) )

def branch_intersect_receptor_np(startpoint:str, receptorpoint:str, lengthmul:float):
    return points_3D_np[startpoint] + lengthmul*( points_3D_np[receptorpoint] - points_3D_np[startpoint] )

def dendrite_branch_deflected_np(startpoint:str, y_deflect:float):
    return points_3D_np[startpoint] + np.array([-10, y_deflect, 0])

def dendrite_point_np(data):
    op = data[0]
    if op == 'root':
        return dendrite_root_start_np(data[1], data[2])
    elif op == 'deflected':
        return dendrite_branch_deflected_np(data[1], data[2])
    elif op == 'intersect':
        return branch_intersect_receptor_np(data[1], data[2], data[3])
    else:
        raise Exception('Unknown dendrite_point_np op: '+str(op))

def set_dendrite_branch_points_np(startpoint:str, startdata, endpoint:str, enddata):
    points_3D_np[startpoint] = dendrite_point_np(startdata)
    points_3D_np[endpoint] = dendrite_point_np(enddata)

def axon_point_np(data):
    op = data[0]
    if op == 'root':
        return axon_root_start_np(data[1], data[2])
    elif op == 'rootend':
        return axon_root_end_np(data[1])
    elif op == 'copy':
        return points_3D_np[data[1]]
    elif op == 'intersect':
        return branch_intersect_receptor_np(data[1], data[2], data[3])
    else:
        raise Exception('Unknown axon_point_np op: '+str(op))

def set_axon_branch_points_np(startpoint:str, startdata, endpoint:str, enddata):
    points_3D_np[startpoint] = axon_point_np(startdata)
    points_3D_np[endpoint] = axon_point_np(enddata)

# Pin0: soma: sphere
set_neuron_soma('P_in0', 'P_in0_pos', principal_soma_radius_um)
# Pin0: dendrites: points
set_dendrite_branch_points_np('Pin0_den0_s', ['root', 'P_in0_pos', principal_soma_radius_um], 'Pin0_den0_e', ['deflected', 'Pin0_den0_s', -10])
set_dendrite_branch_points_np('Pin0_den1_s', ['root', 'P_in0_pos', principal_soma_radius_um], 'Pin0_den1_e', ['deflected', 'Pin0_den1_s', 10])
# Pin0: dendrites: cylinders
set_neuron_dendrite_branch('P_in0', 'Pin0_den0_s', end0_radius_um, 'Pin0_den0_e', end1_radius_um)
set_neuron_dendrite_branch('P_in0', 'Pin0_den1_s', end0_radius_um, 'Pin0_den1_e', end1_radius_um)
# Pin0: axon: points
set_axon_branch_points_np('Pin0_ax0_s', ['root', 'P_in0_pos', principal_soma_radius_um], 'Pin0_ax0_e', ['rootend', 'Pin0_ax0_s'])
set_axon_branch_points_np('Pin0_ax0_0_s', ['copy', 'Pin0_ax0_e'], 'Pin0_ax0_0_e', ['intersect', 'Pin0_ax0_0_s', 'Pin0_PB0_rec', 1.3])
set_axon_branch_points_np('Pin0_ax0_1_s', ['copy', 'Pin0_ax0_e'], 'Pin0_ax0_1_e', ['intersect', 'Pin0_ax0_1_s', 'Pin0_IA0_rec', 1.3])
# Pin0: axon: cylinders
set_neuron_axon_branch('P_in0', 'Pin0_ax0_s', end0_radius_um, 'Pin0_ax0_e', end1_radius_um)
set_neuron_axon_branch('P_in0', 'Pin0_ax0_0_s', end1_radius_um, 'Pin0_ax0_0_e', end1_radius_um)
set_neuron_axon_branch('P_in0', 'Pin0_ax0_1_s', end1_radius_um, 'Pin0_ax0_1_e', end1_radius_um)
# Update receptor data
connection_build_data['Pin0_PB0_rec']['from_idx'] = 1 # Pin0_ax0_0_e
connection_build_data['Pin0_IA0_rec']['from_idx'] = 2 # Pin0_ax0_1_e

# Pin1: soma: sphere
set_neuron_soma('P_in1', 'P_in1_pos', principal_soma_radius_um)
# Pin1: dendrites: points
set_dendrite_branch_points_np('Pin1_den0_s', ['root', 'P_in1_pos', principal_soma_radius_um], 'Pin1_den0_e', ['deflected', 'Pin1_den0_s', -10])
set_dendrite_branch_points_np('Pin1_den1_s', ['root', 'P_in1_pos', principal_soma_radius_um], 'Pin1_den1_e', ['deflected', 'Pin1_den1_s', +10])
# Pin1: dendrites: cylinders
set_neuron_dendrite_branch('P_in1', 'Pin1_den0_s', end0_radius_um, 'Pin1_den0_e', end1_radius_um)
set_neuron_dendrite_branch('P_in1', 'Pin1_den1_s', end0_radius_um, 'Pin1_den1_e', end1_radius_um)
# Pin1: axon: points
set_axon_branch_points_np('Pin1_ax0_s', ['root', 'P_in1_pos', principal_soma_radius_um], 'Pin1_ax0_e', ['rootend', 'Pin1_ax0_s'])
set_axon_branch_points_np('Pin1_ax0_0_s', ['copy', 'Pin1_ax0_e'], 'Pin1_ax0_0_e', ['intersect', 'Pin1_ax0_0_s', 'Pin1_PB1_rec', 1.3])
set_axon_branch_points_np('Pin1_ax0_1_s', ['copy', 'Pin1_ax0_e'], 'Pin1_ax0_1_e', ['intersect', 'Pin1_ax0_1_s', 'Pin1_IA1_rec', 1.3])
# Pin1: axon: cylinders
set_neuron_axon_branch('P_in1', 'Pin1_ax0_s', end0_radius_um, 'Pin1_ax0_e', end1_radius_um)
set_neuron_axon_branch('P_in1', 'Pin1_ax0_0_s', end1_radius_um, 'Pin1_ax0_0_e', end1_radius_um)
set_neuron_axon_branch('P_in1', 'Pin1_ax0_1_s', end1_radius_um, 'Pin1_ax0_1_e', end1_radius_um)
# Update receptor data
connection_build_data['Pin1_PB1_rec']['from_idx'] = 1 # Pin1_ax0_0_e
connection_build_data['Pin1_IA1_rec']['from_idx'] = 2 # Pin1_ax0_1_e

# IA0: soma: sphere
set_neuron_soma('I_A0', 'I_A0_pos', interneuron_soma_radius_um)
# IA0: dendrites: points
set_dendrite_branch_points_np('IA0_den0_s', ['root', 'I_A0_pos', interneuron_soma_radius_um], 'IA0_den0_e', ['intersect', 'IA0_den0_s', 'Pin0_IA0_rec', 1.3])
set_dendrite_branch_points_np('IA0_den1_s', ['root', 'I_A0_pos', interneuron_soma_radius_um], 'IA0_den1_e', ['deflected', 'IA0_den1_s', +10])
# IA0: dendrites: cylinders
set_neuron_dendrite_branch('I_A0', 'IA0_den0_s', end0_radius_um, 'IA0_den0_e', end1_radius_um)
set_neuron_dendrite_branch('I_A0', 'IA0_den1_s', end0_radius_um, 'IA0_den1_e', end1_radius_um)
# Update receptor data
connection_build_data['Pin0_IA0_rec']['to_idx'] = 0 # IA0_den0_e
# IA0: axon: points
set_axon_branch_points_np('IA0_ax0_s', ['root', 'I_A0_pos', interneuron_soma_radius_um], 'IA0_ax0_e', ['rootend', 'IA0_ax0_s'])
set_axon_branch_points_np('IA0_ax0_0_s', ['copy', 'IA0_ax0_e'], 'IA0_ax0_0_e', ['intersect', 'IA0_ax0_0_s', 'IA0_PB1_rec', 1.1])
# IA0: axon: cylinders
set_neuron_axon_branch('I_A0', 'IA0_ax0_s', end0_radius_um, 'IA0_ax0_e', end1_radius_um)
set_neuron_axon_branch('I_A0', 'IA0_ax0_0_s', end1_radius_um, 'IA0_ax0_0_e', end1_radius_um)
# Update receptor data
connection_build_data['IA0_PB1_rec']['from_idx'] = 1 # IA0_ax0_0_e

# IA1: soma: sphere
set_neuron_soma('I_A1', 'I_A1_pos', interneuron_soma_radius_um)
# IA1: dendrites: points
set_dendrite_branch_points_np('IA1_den0_s', ['root', 'I_A1_pos', interneuron_soma_radius_um], 'IA1_den0_e', ['intersect', 'IA1_den0_s', 'Pin1_IA1_rec', 1.3])
set_dendrite_branch_points_np('IA1_den1_s', ['root', 'I_A1_pos', interneuron_soma_radius_um], 'IA1_den1_e', ['deflected', 'IA1_den1_s', -10])
# IA1: dendrites: cylinders
set_neuron_dendrite_branch('I_A1', 'IA1_den0_s', end0_radius_um, 'IA1_den0_e', end1_radius_um)
set_neuron_dendrite_branch('I_A1', 'IA1_den1_s', end0_radius_um, 'IA1_den1_e', end1_radius_um)
# Update receptor data
connection_build_data['Pin1_IA1_rec']['to_idx'] = 0 # IA1_den0_e
# IA1: axon: points
set_axon_branch_points_np('IA1_ax0_s', ['root', 'I_A1_pos', interneuron_soma_radius_um], 'IA1_ax0_e', ['rootend', 'IA1_ax0_s'])
set_axon_branch_points_np('IA1_ax0_0_s', ['copy', 'IA1_ax0_e'], 'IA1_ax0_0_e', ['intersect', 'IA1_ax0_0_s', 'IA1_PB0_rec', 1.1])
# IA1: axon: cylinders
set_neuron_axon_branch('I_A1', 'IA1_ax0_s', end0_radius_um, 'IA1_ax0_e', end1_radius_um)
set_neuron_axon_branch('I_A1', 'IA1_ax0_0_s', end1_radius_um, 'IA1_ax0_0_e', end1_radius_um)
# Update receptor data
connection_build_data['IA1_PB0_rec']['from_idx'] = 1 # IA1_ax0_0_e

# PB0: soma: sphere
set_neuron_soma('P_B0', 'P_B0_pos', principal_soma_radius_um)
# PB0: dendrites: points
set_dendrite_branch_points_np('PB0_den0_s', ['root', 'P_B0_pos', principal_soma_radius_um], 'PB0_den0_e', ['intersect', 'PB0_den0_s', 'Pin0_PB0_rec', 1.3])
set_dendrite_branch_points_np('PB0_den1_s', ['root', 'P_B0_pos', principal_soma_radius_um], 'PB0_den1_e', ['intersect', 'PB0_den1_s', 'IA1_PB0_rec', 1.3])
# PB0: dendrites: cylinders
set_neuron_dendrite_branch('P_B0', 'PB0_den0_s', end0_radius_um, 'PB0_den0_e', end1_radius_um)
set_neuron_dendrite_branch('P_B0', 'PB0_den1_s', end0_radius_um, 'PB0_den1_e', end1_radius_um)
# Update receptor data
connection_build_data['Pin0_PB0_rec']['to_idx'] = 0 # PB0_den0_e
connection_build_data['IA1_PB0_rec']['to_idx'] = 1 # PB0_den1_e
# PB0: axon: points
set_axon_branch_points_np('PB0_ax0_s', ['root', 'P_B0_pos', principal_soma_radius_um], 'PB0_ax0_e', ['rootend', 'PB0_ax0_s'])
set_axon_branch_points_np('PB0_ax0_0_s', ['copy', 'PB0_ax0_e'], 'PB0_ax0_0_e', ['intersect', 'PB0_ax0_0_s', 'PB0_Pout_rec', 1.1])
# PB0: axon: cylinders
set_neuron_axon_branch('P_B0', 'PB0_ax0_s', end0_radius_um, 'PB0_ax0_e', end1_radius_um)
set_neuron_axon_branch('P_B0', 'PB0_ax0_0_s', end1_radius_um, 'PB0_ax0_0_e', end1_radius_um)
# Update receptor data
connection_build_data['PB0_Pout_rec']['from_idx'] = 1 # PB0_ax0_0_e

# PB1: soma: sphere
set_neuron_soma('P_B1', 'P_B1_pos', principal_soma_radius_um)
# PB1: dendrites: points
set_dendrite_branch_points_np('PB1_den0_s', ['root', 'P_B1_pos', principal_soma_radius_um], 'PB1_den0_e', ['intersect', 'PB1_den0_s', 'Pin1_PB1_rec', 1.3])
set_dendrite_branch_points_np('PB1_den1_s', ['root', 'P_B1_pos', principal_soma_radius_um], 'PB1_den1_e', ['intersect', 'PB1_den1_s', 'IA0_PB1_rec', 1.3])
# PB1: dendrites: cylinders
set_neuron_dendrite_branch('P_B1', 'PB1_den0_s', end0_radius_um, 'PB1_den0_e', end1_radius_um)
set_neuron_dendrite_branch('P_B1', 'PB1_den1_s', end0_radius_um, 'PB1_den1_e', end1_radius_um)
# Update receptor data
connection_build_data['Pin1_PB1_rec']['to_idx'] = 0 # PB1_den0_e
connection_build_data['IA0_PB1_rec']['to_idx'] = 1 # PB1_den1_e
# PB1: axon: points
set_axon_branch_points_np('PB1_ax0_s', ['root', 'P_B1_pos', principal_soma_radius_um], 'PB1_ax0_e', ['rootend', 'PB1_ax0_s'])
set_axon_branch_points_np('PB1_ax0_0_s', ['copy', 'PB1_ax0_e'], 'PB1_ax0_0_e', ['intersect', 'PB1_ax0_0_s', 'PB1_Pout_rec', 1.1])
# PB1: axon: cylinders
set_neuron_axon_branch('P_B1', 'PB1_ax0_s', end0_radius_um, 'PB1_ax0_e', end1_radius_um)
set_neuron_axon_branch('P_B1', 'PB1_ax0_0_s', end1_radius_um, 'PB1_ax0_0_e', end1_radius_um)
# Update receptor data
connection_build_data['PB1_Pout_rec']['from_idx'] = 1 # PB1_ax0_0_e

# Pout: soma: sphere
set_neuron_soma('P_out', 'P_out_pos', principal_soma_radius_um)
# Pout: dendrites: points
set_dendrite_branch_points_np('Pout_den0_s', ['root', 'P_out_pos', principal_soma_radius_um], 'Pout_den0_e', ['intersect', 'Pout_den0_s', 'PB0_Pout_rec', 1.3])
set_dendrite_branch_points_np('Pout_den1_s', ['root', 'P_out_pos', principal_soma_radius_um], 'Pout_den1_e', ['intersect', 'Pout_den1_s', 'PB1_Pout_rec', 1.3])
# Pout: dendrites: cylinders
set_neuron_dendrite_branch('P_out', 'Pout_den0_s', end0_radius_um, 'Pout_den0_e', end1_radius_um)
set_neuron_dendrite_branch('P_out', 'Pout_den1_s', end0_radius_um, 'Pout_den1_e', end1_radius_um)
# Update receptor data
connection_build_data['PB0_Pout_rec']['to_idx'] = 0 # Pout_den0_e
connection_build_data['PB1_Pout_rec']['to_idx'] = 1 # Pout_den1_e
# Pout: axon: points
set_axon_branch_points_np('Pout_ax0_s', ['root', 'P_out_pos', principal_soma_radius_um], 'Pout_ax0_e', ['rootend', 'Pout_ax0_s'])
# Pout: axon: cylinders
set_neuron_axon_branch('P_out', 'Pout_ax0_s', end0_radius_um, 'Pout_ax0_e', end1_radius_um)

### 3.2 Create SC shapes and compartments.
print('Creating shapes and compartments...')

neuron_names = list(neuron_build_data.keys())

def make_shape(shape_data:list):
    shape_type = shape_data[0]
    if shape_type == 'sphere':
        return bg_api.BGNES_sphere_create(
            radius_um=shape_data[1][3],
            center_um=shape_data[1][0:3],)
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
for connection_data in connection_build_data.values():
    pre_n = connection_data['pre']
    from_idx = connection_data['from_idx']
    post_n = connection_data['post']
    to_idx = connection_data['to_idx']
    connection_data['from_ID'] = neuron_build_data[pre_n]['axons']['compartment_refs'][from_idx].ID
    connection_data['to_ID'] = neuron_build_data[post_n]['dendrites']['compartment_refs'][to_idx].ID

### 3.3 Create neurons.

print('Making neurons...')

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

print('Making receptors...')

AMPA_conductance = 40.0 #60 # nS
GABA_conductance = -40.0 # nS

#receptor_functionals = []
#receptor_morphologies = []
for connection_data in connection_build_data.values():
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

    if event_occurs(prob_missed_receptor):
        print('MISSED RECEPTOR')
    else:
        # Build receptor function:
        receptor = bg_api.BGNES_BS_receptor_create(
            SourceCompartmentID=connection_data['from_ID'],
            DestinationCompartmentID=connection_data['to_ID'],
            Conductance_nS=receptor_conductance,
            TimeConstantRise_ms=neuron_tau_PSPr,
            TimeConstantDecay_ms=neuron_tau_PSPd,
            ReceptorMorphology=receptor_box.ID,
        )
        #receptor_functionals.append( (receptor, connection_data['post']) )

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

# 4.1 Save the ground-truth system.
#     Saving this after setting up specific stimulation so that it is included
#     when loading in following scripts.

response = bg_api.BGNES_save()
print('Saved simulation: '+str(response))

with open(".EmulationHandle", "w") as f:
    print(f"Saving emulation handle '{response[0]['SavedSimName']}' to '.SimulationHandle'")
    f.write(response[0]['SavedSimName'])


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

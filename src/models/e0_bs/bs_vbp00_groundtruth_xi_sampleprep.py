#!/usr/bin/env python3
# bs_vbp00_groundtruth_xi_sampleprep.py
# Randal A. Koene, 20240202

'''
The ball-and-stick example is intended to provide the simplest in-silico case with the smallest
number of variables to address while still demonstrating the full process and dependencies
chain for whole brain emulation.

This file implements an in-silico fully known ground-truth system.
In this example file, we do this with a minimum of Python complexity,
keeping the script as flat as possible and maximizing immediate use of NES calls.

The idea here is to get this to achieve the same result as the Python prototype
but try not to constrain the implementation by basing it hard on the prototype
implementation. The method has the following steps:

1) Express all the steps taken in the prototype as flat as possible, following
   just 1 set of options for the prototype (e.g. only unirand distribution).
2) Ensure that all of the NES interfaces and functions exist for that flat
   version to work.
3) Consider parts that should be easier or more flexible for the user (e.g.
   just ask for 20 neurons instead of specifying each, or, being able to
   choose unirand or aligned layout).
4) Consider which of those parts should be build right into NES and which
   into the Python support libraries.
5) Build the first into NES.
6) Build the second into the NES_interfaces modules.

VBP process step 00: groundtruth
WBE topic-level XI: sample preparation / preservation (in-silico)
'''

scriptversion='0.0.1'

import numpy as np
from datetime import datetime
from time import sleep

import vbpcommon
#import common.glb as glb
from BrainGenix.BG_API import BG_API_Setup
from NES_interfaces.KGTRecords import plot_recorded


import argparse
Parser = argparse.ArgumentParser(description="vbp script")
Parser.add_argument("-Remote", action='store_true', help="Render remotely or on localhost")
Args = Parser.parse_args()


api_is_local=Args.Remote

randomseed = 12345
np.random.seed(randomseed)
num_nodes=20
circuit_distribution='unirand'
runtime_ms = 500.0
savefolder = '/tmp/vbp_'+str(datetime.now()).replace(":", "_")
figspecs = {
    'figsize': (6,6),
    'linewidth': 0.5,
    'figext': 'pdf',
}

# 1. Init NES connection

bg_api = BG_API_Setup(user='Admonishing', passwd='Instruction')
if api_is_local:
    bg_api.set_local()
if not bg_api.BGNES_QuickStart(scriptversion, versionmustmatch=False, verbose=False):
    print('BG NES Interface access failed.')
    exit(1)

# 2. Init simulation

sys_name='e0_bs'
bg_api.BGNES_simulation_create(name=sys_name, seed=randomseed)

# 3. Define ground-truth model

INITTEXT1='''
1. Defining a %s-neuron system:
   a. Scale: The number of principal nodes.
   b. Functional: The type of network arrangment
      (aligned ball-and-stick).
   c. Physical: A specific volume (a box region).
   Defaults are applied to other parameters.
'''

print(INITTEXT1 % str(num_nodes))

# 3.1 Add either a uniform random or aligned circuit

circuit_id='BS NC'
circuit_num_cells=num_nodes

# 3.2 That circuit has the function and a box is the shape
#     of a brain region:

box_center = [0,0,0]
box_dims = [20.0, 20.0, 2.0]
box_rot = [0,0,0]
box = bg_api.BGNES_box_create(
            CenterPosition_um=box_center,
            Dimensions_um=box_dims,
            Rotation_rad=box_rot)

region_id='BS'
region_content=circuit_id
region_shape=box.ID

# 3.3 Init cells within circuit:

if circuit_distribution != 'unirand':
    print('Distribution %s not implemented.' % circuit_distribution)
    exit(1)

# 3.3.1 Find uniform random distributed soma positions that do not overlap:

soma_radius_um = 0.5
dist_threshold = 4*soma_radius_um*soma_radius_um

somas = []
soma_positions = []
for n in range(circuit_num_cells):
    need_position = True
    while need_position:
        xyz = np.random.uniform(-0.5, 0.5, 3)
        xyz = xyz*np.array(box_dims) + np.array(box_center)
        # 2. Check it isn't too close to other neurons already placed.
        need_position = False
        for soma_pos in soma_positions:
            v = xyz - soma_pos
            d_squared = v.dot(v)
            if d_squared <= dist_threshold:
                need_position = True
                break
    soma_positions.append(xyz)
    soma = bg_api.BGNES_sphere_create(
                radius_um=soma_radius_um,
                center_um=xyz,)
    somas.append(soma)

# 3.3.2 Create axons and direct them to neighboring cells:

end0_radius_um = 0.1
end1_radius_um = 0.1

# TODO: We don't need the axon_ends list if we remember end0 and end0
#       in Cylinder creation in pyBrainGenixClient.

axons = []
axon_ends = []
axons_to = -1*np.ones(circuit_num_cells, dtype=int)
max_dist_squared = max(box_dims)**2
for n in range(circuit_num_cells):
    min_dist_squared = max_dist_squared
    # Find nearest cell:
    nearest = -1
    for i in range(len(soma_positions)):
        if i != n:
            if axons_to[i] != n: # Avoid tiny loops.
                v = soma_positions[n] - soma_positions[i]
                d_squared = v.dot(v)
                if d_squared < min_dist_squared:
                    min_dist_squared = d_squared
                    nearest = i
    axons_to[n] = nearest
    #print('This one is %s and nearest is %s.' % (str(n), str(nearest)))
    dv_axon = soma_positions[nearest] - soma_positions[n]
    mag = np.sqrt(dv_axon.dot(dv_axon))
    if mag == 0:
        exit(1)
    dv_axon = (1/mag)*dv_axon
    end0 = soma_positions[n] + (soma_radius_um*dv_axon)
    end1 = soma_positions[nearest] - (soma_radius_um*dv_axon)
    axon_ends.append( (end0, end1) )

    axon = bg_api.BGNES_cylinder_create(
                Point1Radius_um=end0_radius_um,
                Point1Position_um=end0,
                Point2Radius_um=end1_radius_um,
                Point2Position_um=end1,)
    axons.append(axon)

# 3.3.3 Create compartments for somas:

neuron_Vm_mV = -60.0
neuron_Vrest_mV = -60.0
neuron_Vact_mV = -50.0
neuron_Vahp_mV = -20.0
neuron_tau_AHP_ms = 30.0

soma_compartments = []
for soma in somas:
    compartment = bg_api.BGNES_BS_compartment_create(
                    ShapeID=soma.ID,
                    MembranePotential_mV=neuron_Vm_mV,
                    RestingPotential_mV=neuron_Vrest_mV,
                    SpikeThreshold_mV=neuron_Vact_mV,
                    DecayTime_ms=neuron_tau_AHP_ms,
                    AfterHyperpolarizationAmplitude_mV=neuron_Vahp_mV,)
    soma_compartments.append(compartment)

# 3.3.4 Create compartments for axons:

axon_compartments = []
for axon in axons:
    compartment = bg_api.BGNES_BS_compartment_create(
                    ShapeID=axon.ID,
                    MembranePotential_mV=neuron_Vm_mV,
                    RestingPotential_mV=neuron_Vrest_mV,
                    SpikeThreshold_mV=neuron_Vact_mV,
                    DecayTime_ms=neuron_tau_AHP_ms,
                    AfterHyperpolarizationAmplitude_mV=neuron_Vahp_mV,)
    axon_compartments.append(compartment)

# 3.3.5 Create neurons:

# Current at typical single AMPA receptor is in pA range.
# Multiple receptors or in specific conditions can get up to nA (or even uA) range.
# In hippocampus, estimates are that a single synapse can have 50-100 active
# AMPA receptors. In hippocampus, through the typical number of receptors and
# one or more synapses, typical AMPA current is several hundres pA or into the
# low nA range.
# In hippocampus, transmission from one neuron to another can involve a few to
# several hundred synapses.
# A single AMPA receptor channel has a conductance in the range of 9-10 pS.
#
# Example: Currents through AMPA receptors from a medial temporal lobe neuron
# to a hippocampal neuron.
#
#   Number of synapses involved = 80
#   Number of active receptors per synapse = 75
#   Average conductance of a single receptor channel = 10 pS
#   Average potential difference across cell boundary = (-)55 mV
#   Typical current across the connection = (-)55 * 10^-3 * 80*75*10 * 10^-12 A
#     = 3300000 * 10^-15 A = (-)3.3 * 10^-9 A = (-)3.3 nA
#
#   Rewritten to represent magnitudes for the whole connection between the
#   two neurons (i = v * g):
#   (-)3.3 nA = (-)55 mV * 60 nS
#
#   The double exponential PSP response model represents the accumulation of
#   charge over time and its gradual decay, causing a difference in the
#   membrane potential. For the example current and conductance given, the
#   firing threshold should be reached after a brief rise-time at the
#   hippocampal neuron. That's a change in the membrane potential of about
#   10 mV. To represent that level of change at the peak of the double
#   exponential ( -exp(-tDiff / tauRise) + exp(-tDiff / tauDecay) ), with
#   a current of about 3.3 nA and conductance of about 60 nS, we need
#   a constant weight scaling factor (using v = i*r = i/g):
#     10 mV = w_scaling * (3.3 nA / 60 nS) * peak_doubleexp
#   The peak of the double exponential is around 0.69
#     w_scaling = 10*10^-3 * 60 / (3.3 * 0.69) = 0.264
#   Combining this with the 3.3 nA gives a I_PSP_nA constant of about 0.87 nA.
#   And for mV, 870 nA:
#     10 mV = (870 nA / 60 nS) * peak_doubleexp

neuron_tau_PSPr = 5.0
neuron_tau_PSPd = 25.0
neuron_IPSP = 870.0 # nA
#neuron_tau_spont_mean_stdev_ms = (0, 0) # 0 means no spontaneous activity
#neuron_t_spont_next = -1

cells = {}
for n in range(circuit_num_cells):
    cell_id = str(n)
    cell = bg_api.BGNES_BS_neuron_create(
        Soma=soma_compartments[n].ID, 
        Axon=axon_compartments[n].ID,
        MembranePotential_mV=neuron_Vm_mV,
        RestingPotential_mV=neuron_Vrest_mV,
        SpikeThreshold_mV=neuron_Vact_mV,
        DecayTime_ms=neuron_tau_AHP_ms,
        AfterHyperpolarizationAmplitude_mV=neuron_Vahp_mV,
        PostsynapticPotentialRiseTime_ms=neuron_tau_PSPr,
        PostsynapticPotentialDecayTime_ms=neuron_tau_PSPd,
        PostsynapticPotentialAmplitude_nA=neuron_IPSP,
    )
    cells[cell_id] = cell

# 3.4 (Optionally) visualize the system

# glb.bg_api.Some_sort_of_call()

# 3.5 Set up an instant binary connection from cell 0 to cell 1

AMPA_conductance = 40.0 #60 # nS
weight = 1.0 # binary

connection_pattern_set = [
    ( 0, 1 ), # From cell 0 to cell 1.
    ( 1, 2 ),
    ( 2, 3 ),
    ( 3, 4 ),
    ( 5, 6 ),
    ( 6, 0 ),
    ( 15, 0 ),
    ( 15, 3 ),
] 
receptor_functionals = []
receptor_morphologies = []
for pattern in connection_pattern_set:
    print("Setting up a 'binary' connection from %s to %s." % pattern)

    # Find the neurons:
    from_cell = cells[str(pattern[0])]
    to_cell = cells[str(pattern[1])]

    # Find the compartments:
    from_compartment_id = from_cell.AxonID
    to_compartment_id = to_cell.SomaID
    receptor_location = axon_ends[pattern[1]][1]
    print('Receptor loction: '+str(receptor_location))

    # Set the total conductance through receptors at synapses at this connection:
    receptor_conductance = weight * AMPA_conductance

    # Build receptor form:
    receptor_box = bg_api.BGNES_box_create(
            CenterPosition_um=receptor_location,
            Dimensions_um=[0.1,0.1,0.1],
            Rotation_rad=[0,0,0],)
    receptor_morphologies.append(receptor_box)

    # Build receptor function:
    receptor = bg_api.BGNES_BS_receptor_create(
        SourceCompartmentID=from_compartment_id,
        DestinationCompartmentID=to_compartment_id,
        Conductance_nS=receptor_conductance,
        TimeConstantRise_ms=neuron_tau_PSPr,
        TimeConstantDecay_ms=neuron_tau_PSPd,
        ReceptorMorphology=receptor_box.ID,
        #ReceptorLocation_um=tuple(receptor_location),
    )
    receptor_functionals.append( (receptor, to_cell) )

# 3.6 (Optionally) visualize the system with the connection

# glb.bg_api.Some_sort_of_call()

# 3.7 Save the ground-truth system

response = bg_api.BGNES_save()
print('Saved simulation: '+str(response))

with open(".SimulationHandle", "w") as f:
    print(f"Saving simulation handle '{response[0]['SavedSimName']}' to '.SimulationHandle'")
    f.write(response[0]['SavedSimName'])


STIMTEXT1='''
Dynamic activity:
The imagined nature of the 2-neuron ball-and-stick circuit
provides no differentiation of dendritic input sources to
the neurons. Activity is elicited exclusively by generating
potential at or near a soma to the point where a cell fires
and action potential is propagated.

God's eye direct access to every aspect of the in-silico
ground-truth system includes the ability to specifically
cause a somatic action potential at any time.
'''

# 4. Init experiment

print(STIMTEXT1)
t_soma_fire_ms = [
    (100.0, 0),
    (150.0, 5),
    (200.0, 10),
    (250.0, 15),
    (300.0, 18),
    (350.0, 13),
    (400.0, 8),
    (450.0, 3),
]
print('Directed somatic firing: '+str(t_soma_fire_ms))

response = bg_api.BGNES_set_specific_AP_times(
        TimeNeuronPairs=t_soma_fire_ms,
    )

# # 4.1 Convert to stims-by-patch-clamp-DAC

# DAC_stims = {}
# for stim in t_soma_fire_ms:
#     t, cell_id = stim
#     if cell_id not in DAC_stims:
#         DAC_stims[cell_id] = {
#             'stims': [],
#             'patch_clamp': None,
#         }
#     DAC_stims[cell_id]['stims'].append(t)

# # 4.2 Create DACs for direct stimulation

# for cell_id in DAC_stims:
#     patch_clamp = glb.bg_api.BGNES_DAC_create(
#         DestinationCompartmentID=cells[cell_id].SomaID,
#         ClampLocation_um=[0,0,0],
#     )
#     DAC_stims[cell_id]['patch_clamp'] = patch_clamp

# # 4.3 Init DAC voltage transitions according to stim lists

# for cell_id in DAC_stims:
#     DAC_settings = [ (0, neuron_Vrest_mV) ]
#     for t_stim in DAC_stims[cell_id]['stims']:
#         DAC_settings.append( (t_stim, neuron_Vact_mV+10.0 ) )
#         DAC_settings.append( (t_stim+5.0, neuron_Vrest_mV ) )
#     print('At DAC on cell %s, DAC control commands: %s' % (str(cell_id), str(DAC_settings)))
#     glb.bg_api.BGNES_DAC_set_output_list(
#         TargetDAC=DAC_stims[cell_id]['patch_clamp'].ID,
#         DACControlPairs=DAC_settings,)

# 5. Run experiment

print('\nRunning experiment for %.1f milliseconds...\n' % runtime_ms)

# 5.1 Set record-all

t_max_ms=-1 # record forever
bg_api.BGNES_simulation_recordall(t_max_ms)

# 5.2 Run for specified simulation time

if not bg_api.BGNES_simulation_runfor_and_await_outcome(runtime_ms):
    exit(1)

# 5.3 Retrieve recordings and plot

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

                    plot_recorded(
                        savefolder=savefolder,
                        data=recording_dict["Recording"],
                        figspecs=figspecs,)

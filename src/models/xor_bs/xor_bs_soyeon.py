#!/usr/bin/env python3
# xor_bs_groundtruth.py
# Randal A. Koene, 20240306

'''
The XOR ball-and-stick example uses extremely simple neuron representations in a
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
# savefolder = '/tmp/vbp_'+str(datetime.now()).replace(":", "_")
savefolder = '/home/skim/output/output'+str(datetime.now()).replace(":", "_")
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

sys_name='xor_bs'
bg_api.BGNES_simulation_create(name=sys_name, seed=randomseed)

# 3. Define ground-truth model

INITTEXT1='''
1. Defining an XOR logic circuit composed of ball-and-stick
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

    P_inA (-45, -45)----------------------+
                    |                     |
                    +-> IA (-15, -15) --> P_out (15, -15)
                    |                     |
    P_inB (-45, 45)-----------------------+

   Distances of 30 um are typical between somas in cortex.
'''

print(INITTEXT1)

# 3.1 Define shapes for the neurons and place each specifically.

principal_soma_radius_um = 10.0                # A typical radius for the soma of a human cortical pyramidal neuron 5-25 um.
interneuron_soma_radius_um = 5.0               # A typical radius for the soma of a human cortical interneuron 2.5-15 um.

P_inA_pos = [-45, -45, 0]
P_inB_pos = [-45, 45, 0]
IA_pos = [-15, -15, 0]
P_out_pos = [15, -15, 0]

soma_positions_and_radius = {
    'P_inA': ( P_inA_pos, principal_soma_radius_um ),
    'P_inB': ( P_inB_pos, principal_soma_radius_um ),
    'IA': ( IA_pos, principal_soma_radius_um ),
    'P_out': ( P_out_pos, interneuron_soma_radius_um ),
}

neuron_names = list(soma_positions_and_radius.keys())

somas = {}
for n in neuron_names:
    soma = bg_api.BGNES_sphere_create(
                radius_um=soma_positions_and_radius[n][1],
                center_um=soma_positions_and_radius[n][0],)
    somas[n] = soma

# 3.2 Define shapes for the connections and place them

end0_radius_um = 0.75 # Typical radius at the axon hillock of a pyramidal neuron in human cortex.
end1_radius_um = 0.3  # Typical radius of distal axon segments of pyramidal neurons in human cortex.

axon_ends = {}

# Pin0_PA0_start = list(np.array(P_in0_pos) + np.array([principal_soma_radius_um, 0, 0]))
# Pin0_PA0_end   = list(np.array(P_A0_pos) + np.array([-principal_soma_radius_um, 0, 0]))
# axon_ends['P_in0_P_A0'] = (Pin0_PA0_start, Pin0_PA0_end)

# Pin1_PA1_start = list(np.array(P_in1_pos) + np.array([principal_soma_radius_um, 0, 0]))
# Pin1_PA1_end   = list(np.array(P_A1_pos) + np.array([-principal_soma_radius_um, 0, 0]))
# axon_ends['P_in1_P_A1'] = (Pin1_PA1_start, Pin1_PA1_end)

# Pin0_IA0_start = list(0.5*(np.array(P_in0_pos) + np.array(P_A0_pos)) )
# Pin0_IA0_end   = list(np.array(I_A0_pos) + np.array([-interneuron_soma_radius_um, 0, 0]))
# axon_ends['P_in0_I_A0'] = (Pin0_IA0_start, Pin0_IA0_end)

# Pin1_IA1_start = list(0.5*(np.array(P_in1_pos) + np.array(P_A1_pos)) )
# Pin1_IA1_end   = list(np.array(I_A1_pos) + np.array([-interneuron_soma_radius_um, 0, 0]))
# axon_ends['P_in1_I_A1'] = (Pin1_IA1_start, Pin1_IA1_end)

# PA0_PB0_start  = list(np.array(P_A0_pos) + np.array([principal_soma_radius_um, 0, 0]))
# PA0_PB0_end    = list(np.array(P_B0_pos) + np.array([-principal_soma_radius_um, 0, 0]))
# axon_ends['P_A0_P_B0'] = (PA0_PB0_start, PA0_PB0_end)

# PA1_PB1_start  = list(np.array(P_A1_pos) + np.array([principal_soma_radius_um, 0, 0]))
# PA1_PB1_end    = list(np.array(P_B1_pos) + np.array([-principal_soma_radius_um, 0, 0]))
# axon_ends['P_A1_P_B1'] = (PA1_PB1_start, PA1_PB1_end)

# IA0_PB1_start  = list(np.array(I_A0_pos) + np.array([interneuron_soma_radius_um, 0, 0]))
# IA0_PB1_end    = list(np.array(P_B1_pos) + np.array([-principal_soma_radius_um, 0, 0]))
# axon_ends['I_A0_P_B1'] = (IA0_PB1_start, IA0_PB1_end)

# IA1_PB0_start  = list(np.array(I_A1_pos) + np.array([interneuron_soma_radius_um, 0, 0]))
# IA1_PB0_end    = list(np.array(P_B0_pos) + np.array([-principal_soma_radius_um, 0, 0]))
# axon_ends['I_A1_P_B0'] = (IA1_PB0_start, IA1_PB0_end)

# PB0_Pout_start = list(np.array(P_B0_pos) + np.array([principal_soma_radius_um, 0, 0]))
# PB0_Pout_end   = list(np.array(P_out_pos) + np.array([-principal_soma_radius_um, 0, 0]))
# axon_ends['P_B0_P_out'] = (PB0_Pout_start, PB0_Pout_end)

# PB1_Pout_start = list(np.array(P_B1_pos) + np.array([principal_soma_radius_um, 0, 0]))
# PB1_Pout_end   = list(np.array(P_out_pos) + np.array([-principal_soma_radius_um, 0, 0]))
# axon_ends['P_B1_P_out'] = (PB1_Pout_start, PB1_Pout_end)

# Pout_start = list(np.array(P_out_pos) + np.array([principal_soma_radius_um, 0, 0]))
# Pout_end = list(np.array(P_out_pos) + np.array([30.0, 0, 0]))
# axon_ends['P_out_axon'] = (Pout_start, Pout_end)

# defining start and end positions of axons. 
PinA_Pout_start = list(np.array(P_inA_pos) + np.array([principal_soma_radius_um, 0, 0]))
PinA_Pout_end   = list(np.array(P_out_pos) + np.array([-principal_soma_radius_um, 0, 0]))
axon_ends['P_inA_P_out'] = (PinA_Pout_start, PinA_Pout_end)

PinB_Pout_start = list(np.array(P_inB_pos) + np.array([principal_soma_radius_um, 0, 0]))
PinB_Pout_end   = list(np.array(P_out_pos) + np.array([-principal_soma_radius_um, 0, 0]))
axon_ends['P_inB_P_out'] = (PinB_Pout_start, PinB_Pout_end)

PinA_IA_start = list(np.array(P_inA_pos) + np.array([principal_soma_radius_um, 0, 0]))
PinA_IA_end   = list(np.array(IA_pos) + np.array([-interneuron_soma_radius_um, 0, 0]))
axon_ends['P_inA_IA'] = (PinA_IA_start, PinA_IA_end)

PinB_IA_start = list(np.array(P_inB_pos) + np.array([principal_soma_radius_um, 0, 0]))
PinB_IA_end   = list(np.array(IA_pos) + np.array([-interneuron_soma_radius_um, 0, 0]))
axon_ends['P_inB_IA'] = (PinB_IA_start, PinB_IA_end)

IA_Pout_start = list(np.array(IA_pos) + np.array([interneuron_soma_radius_um, 0, 0]))
IA_Pout_end   = list(np.array(P_out_pos) + np.array([-principal_soma_radius_um, 0, 0]))
axon_ends['IA_P_out'] = (IA_Pout_start, IA_Pout_end)

Pout_start = list(np.array(P_out_pos) + np.array([principal_soma_radius_um, 0, 0]))
Pout_end = list(np.array(P_out_pos) + np.array([30.0, 0, 0]))
axon_ends['P_out_axon'] = (Pout_start, Pout_end)

axon_names = list(axon_ends.keys())

axons = {}
for a in axon_names:
    axon = bg_api.BGNES_cylinder_create(
                Point1Radius_um=end0_radius_um,
                Point1Position_um=axon_ends[a][0],
                Point2Radius_um=end1_radius_um,
                Point2Position_um=axon_ends[a][1],)
    axons[a] = axon

# 3.3 Create compartments.

neuron_Vm_mV = -60.0
neuron_Vrest_mV = -60.0
neuron_Vact_mV = -50.0
neuron_Vahp_mV = -20.0
neuron_tau_AHP_ms = 30.0

soma_compartments = {}
for n in neuron_names:
    compartment = bg_api.BGNES_BS_compartment_create(
                    ShapeID=somas[n].ID,
                    MembranePotential_mV=neuron_Vm_mV,
                    RestingPotential_mV=neuron_Vrest_mV,
                    SpikeThreshold_mV=neuron_Vact_mV,
                    DecayTime_ms=neuron_tau_AHP_ms,
                    AfterHyperpolarizationAmplitude_mV=neuron_Vahp_mV,)
    soma_compartments[n] = compartment

axon_compartments = {}
for a in axon_names:
    compartment = bg_api.BGNES_BS_compartment_create(
                    ShapeID=axons[a].ID,
                    MembranePotential_mV=neuron_Vm_mV,
                    RestingPotential_mV=neuron_Vrest_mV,
                    SpikeThreshold_mV=neuron_Vact_mV,
                    DecayTime_ms=neuron_tau_AHP_ms,
                    AfterHyperpolarizationAmplitude_mV=neuron_Vahp_mV,)
    axon_compartments[a] = compartment

# 3.4 Create principal neurons.

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

def neuron_builder(soma_name:str, axon_name:str):
    return bg_api.BGNES_BS_neuron_create(
        Soma=soma_compartments[soma_name].ID, 
        Axon=axon_compartments[axon_name].ID,
        MembranePotential_mV=neuron_Vm_mV,
        RestingPotential_mV=neuron_Vrest_mV,
        SpikeThreshold_mV=neuron_Vact_mV,
        DecayTime_ms=neuron_tau_AHP_ms,
        AfterHyperpolarizationAmplitude_mV=neuron_Vahp_mV,
        PostsynapticPotentialRiseTime_ms=neuron_tau_PSPr,
        PostsynapticPotentialDecayTime_ms=neuron_tau_PSPd,
        PostsynapticPotentialAmplitude_nA=neuron_IPSP,
    )

# Pin0 = neuron_builder('P_in0', 'P_in0_P_A0') # *** DO WE NEED TO WORRY ABOUT THE SECOND AXON?
# Pin1 = neuron_builder('P_in1', 'P_in1_P_A1') # *** DO WE NEED TO WORRY ABOUT THE SECOND AXON?
# PA0  = neuron_builder('P_A0', 'P_A0_P_B0')
# PA1  = neuron_builder('P_A1', 'P_A1_P_B1')
# PB0  = neuron_builder('P_B0', 'P_B0_P_out')
# PB1  = neuron_builder('P_B1', 'P_B1_P_out')
# Pout = neuron_builder('P_out', 'P_out_axon')

# neuron consists of a soma and an axon. 
# you're simply pairing a soma and an axon to make all connections needed to form a desired circuit.
# but here, you 're only defining one axon (as the "official" axon; typically the longest one) per neuron.
# other axons are established separately through the receptor definition that links axons to somas. 
# when a neuron is "fired", its output branches to all axons it's connected to through when axons were defined.

PinA = neuron_builder('P_inA', 'P_inA_P_out')
PinB = neuron_builder('P_inB', 'P_inB_P_out')
IA = neuron_builder('IA', 'IA_P_out')
Pout = neuron_builder('P_out', 'P_out_axon')

# 3.5 Create interneurons.

# IA0  = neuron_builder('I_A0', 'I_A0_P_B1')
# IA1  = neuron_builder('I_A1', 'I_A1_P_B0')

# cells = {
#     'P_in0': Pin0,
#     'P_in1': Pin1,

#     'P_A0': PA0,
#     'P_A1': PA1,

#     'P_B0': PB0,
#     'P_B1': PB1,

#     'P_out': Pout,

#     'I_A0': IA0,
#     'I_A1': IA1,
# }

# input_neurons = {
#     'P_in0': Pin0,
#     'P_in1': Pin1,
# }
# layerA_neurons = {
#     'P_A0': PA0,
#     'P_A1': PA1,
#     'I_A0': IA0,
#     'I_A1': IA1,
# }
# layerB_neurons = {
#     'P_B0': PB0,
#     'P_B1': PB1,
# }
# output_neurons = {
#     'P_out': Pout,
# }

cells = {
    'P_inA': PinA,
    'P_inB': PinB,
    'IA': IA,
    'P_out': Pout,
}

input_neurons = {
    'P_inA': PinA,
    'P_inB': PinB,
}
LayerA_neurons = {
    'IA': IA,
}
output_neurons = {
    'P_out': Pout,
}

# 3.6 Create receptors for active connections.

AMPA_conductance = 40.0 #60 # nS
GABA_conductance = -40.0 # nS
PinPA_weight  = 1.0 # Greater weight means stronger PSP amplitude.
PinIA_weight  = 1.0
PAPB_weight   = 1.0
IAPB_weight   = 1.0
PBPout_weight = 1.0

# dict key indicates 'from' axon, value[0] indicate 'to' cell soma, value[1] indicates AMPA/GABA
# connection_pattern_set = {
#     'P_in0_P_A0': ( 'P_in0_P_A0', 'P_A0', AMPA_conductance, PinPA_weight),
#     'P_in1_P_A1': ( 'P_in1_P_A1', 'P_A1', AMPA_conductance, PinPA_weight),
#     'P_in0_I_A0': ( 'P_in0_P_A0', 'I_A0', AMPA_conductance, PinIA_weight), # *** FAKING IT FOR FUNCTIONAL REASONS
#     'P_in1_I_A1': ( 'P_in1_P_A1', 'I_A1', AMPA_conductance, PinIA_weight), # *** FAKING IT FOR FUNCTIONAL REASONS

#     'P_A0_P_B0': ( 'P_A0_P_B0', 'P_B0', AMPA_conductance, PAPB_weight),
#     'P_A1_P_B1': ( 'P_A1_P_B1', 'P_B1', AMPA_conductance, PAPB_weight),

#     'I_A0_P_B1': ( 'I_A0_P_B1', 'P_B1', GABA_conductance, IAPB_weight),
#     'I_A1_P_B0': ( 'I_A1_P_B0', 'P_B0', GABA_conductance, IAPB_weight),

#     'P_B0_P_out': ( 'P_B0_P_out', 'P_out', AMPA_conductance, PBPout_weight),
#     'P_B1_P_out': ( 'P_B1_P_out', 'P_out', AMPA_conductance, PBPout_weight),
# }

# defining how neurons should interact with each other. 
# need this for all connections within a circuit (all axons)
connection_pattern_set = {
    'P_inA_P_out': ( 'P_inA_P_out', 'P_out', AMPA_conductance, 1.0),
    'P_inB_P_out': ( 'P_inB_P_out', 'P_out', AMPA_conductance, 1.0),
    'P_inA_IA':    ( 'P_inA_IA', 'IA', AMPA_conductance, 1.0),
    'P_inB_IA':    ( 'P_inB_IA', 'IA', AMPA_conductance, 1.0),
    'IA_P_out':    ( 'IA_P_out', 'P_out', GABA_conductance, 1.0),
}


receptor_functionals = []
receptor_morphologies = []
for connection in connection_pattern_set.keys():

    # skips connections that aren't working... this results in incomplete circuit and inaccurate output. 
    if connection in ['P_inA_IA', 'P_inB_IA']:
        print(f"Skipping connection {connection} due to likely NES restriction.")
        continue

    # Set the total conductance through receptors at synapses at this connection:
    conductance = connection_pattern_set[connection][2]
    if conductance == AMPA_conductance:
        neurotransmitter = 'AMPA'
    else:
        neurotransmitter = 'GABA'
    weight = connection_pattern_set[connection][3]
    receptor_conductance = conductance / weight # Divided by weight to avoid counter-intuitive weight interpretation.
    if receptor_conductance >= 0:
        print("Setting up a 'AMPA' connection for %s." % connection)
    else:
        print("Setting up a 'GABA' connection for %s." % connection)

    # Find the neurons:
    from_axon = axon_compartments[connection_pattern_set[connection][0]]
    to_cell = cells[connection_pattern_set[connection][1]]

    # Find the compartments:
    from_compartment_id = from_axon.ID
    to_compartment_id = to_cell.SomaID
    receptor_location = axon_ends[connection][1]
    print('Receptor loction: '+str(receptor_location))

    

    # Build receptor form:
    receptor_box = bg_api.BGNES_box_create(
            CenterPosition_um=receptor_location,
            Dimensions_um=[0.1,0.1,0.1],
            Rotation_rad=[0,0,0],)
    receptor_morphologies.append(receptor_box)

    # printing receptors before creating them:
    print(f"From ID: {from_compartment_id}, To ID: {to_compartment_id}")


    # Build receptor function:

    print("Attempting to create receptor with config:", {
        'SourceCompartmentID': from_compartment_id,
        'DestinationCompartmentID': to_compartment_id,
        'Neurotransmitter': neurotransmitter,
        'Conductance_nS': receptor_conductance,
        'TimeConstantRise_ms': neuron_tau_PSPr,
        'TimeConstantDecay_ms': neuron_tau_PSPd,
        'ReceptorMorphology': receptor_box.ID,
    })
    receptor = bg_api.BGNES_BS_receptor_create(
        SourceCompartmentID=from_compartment_id,
        DestinationCompartmentID=to_compartment_id,
        Neurotransmitter=neurotransmitter,
        Conductance_nS=receptor_conductance,
        TimeConstantRise_ms=neuron_tau_PSPr,
        TimeConstantDecay_ms=neuron_tau_PSPd,
        ReceptorMorphology=receptor_box.ID,
    )

    receptor_functionals.append( (receptor, to_cell) )

    # if not receptor or 'ReceptorID' not in receptor:
    #     raise RuntimeError(f"Failed to create receptor for {connection}: {receptor}")


# *** ATTEMPTS CREATING RECEPTORS AT MOST 3 TIMES UNTIL GIVING UP
# for connection in connection_pattern_set.keys():
#     conductance = connection_pattern_set[connection][2]
#     weight = connection_pattern_set[connection][3]
#     receptor_conductance = abs(conductance) / weight
#     is_gaba = (connection == 'IA_P_out')
#     neurotransmitter = 1 if is_gaba else 0  # 0=AMPA, 1=GABA

#     from_axon = axon_compartments[connection_pattern_set[connection][0]]
#     to_cell = cells[connection_pattern_set[connection][1]]
    
#     receptor_box = bg_api.BGNES_box_create(
#         CenterPosition_um=axon_ends[connection][1],
#         Dimensions_um=[0.1,0.1,0.1],
#         Rotation_rad=[0,0,0],
#     )

#     for attempt in range(3):  # Try 3 times
#         try:
#             print(f"Attempt {attempt+1} for {connection}")
#             receptor = bg_api.BGNES_BS_receptor_create(
#                 SourceCompartmentID=from_axon.ID,
#                 DestinationCompartmentID=to_cell.SomaID,
#                 Neurotransmitter=neurotransmitter,
#                 Conductance_nS=receptor_conductance,
#                 TimeConstantRise_ms=neuron_tau_PSPr,
#                 TimeConstantDecay_ms=neuron_tau_PSPd,
#                 ReceptorMorphology=receptor_box.ID,
#             )
            
#             if hasattr(receptor, 'ID'):
#                 print(f"Success! Receptor ID: {receptor.ID}")
#                 receptor_functionals.append((receptor, to_cell))
#                 break
                
#         except Exception as e:
#             print(f"Failed attempt {attempt+1}: {str(e)}")
#             if attempt == 2:
#                 print("Giving up on this receptor")
#             time.sleep(0.1)  # Short delay before retry

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
# t_soma_fire_ms = [
#     (100.0, cells['P_in0'].ID),
#     (200.0, cells['P_in1'].ID),
#     (300.0, cells['P_in0'].ID),
#     (300.0, cells['P_in1'].ID),
# ]
t_soma_fire_ms = [
    (100.0, cells['P_inA'].ID),
    (200.0, cells['P_inB'].ID),
    (300.0, cells['P_inA'].ID),
    (300.0, cells['P_inB'].ID),
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

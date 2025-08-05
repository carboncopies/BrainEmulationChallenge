#!/usr/bin/env python3
# full_adder_bs.py
# Soyeon Kim, 20250801

'''
The XOR ball-and-stick example uses extremely simple neuron representations in a
meaningful logic circuit to produce expected functional output.

This file implements an in-silico fully known ground-truth system.
In this example file, we do this with a minimum of Python complexity,
keeping the script as flat as possible and maximizing immediate use of NES calls.

VBP process step 00: groundtruth
WBE topic-level XI: sample preparation / preservation (in-silico)
'''

'''
Full adder circuit:

                   +-----------------------------------------------------------------+
                   |                                                                 |
                   +------------------------------------------+----+                 |
                   |                                          |    |                 |
    Cin (-60,30)---+    +----------------------+            +------+> I_C0 (30,30)---+--> Sum (60,30)
                        |                      |            | |                      
    P_inA (-60,0)-------+--+> I_A0 (-30,0)-----+> P_B0 (0,0)+ | +---> P_C0 (30,0)----+
                        |  |                   |            | | |                    | 
    P_inB (-60,-30)--+-----+-------------------+            +-+-|---> P_C1 (30,-30)--+--> Cout (60,-30)
                     |  |                                       |                      
                     |  +---------------------------------------+                  
                     |                                          |   
                     +------------------------------------------+  

For now, we're looking just at the connections involving P_inA, P_inB, I_A0, and P_B0, that forms 
an XOR gate. 

Just the XOR gate we're looking at:

P_inA -------+-----------+
             |           |
             +-> I_A0 ---+-> P_B0
             |           |
P_inB -------+-----------+

All three signals to P_B0 should preferably arrive at the same time so that P_B0 does not fire when I_A0 fires.
With 


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
runtime_ms = 1000.0
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

sys_name='full_adder_bs'
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

                   +-----------------------------------------------------------------+
                   |                                                                 |
                   +------------------------------------------+----+                 |
                   |                                          |    |                 |
    Cin (-60,30)---+    +----------------------+            +------+> I_C0 (30,30)---+--> Sum (60,30)
                        |                      |            | |                      
    P_inA (-60,0)-------+--+> I_A0 (-30,0)-----+> P_B0 (0,0)+ | +---> P_C0 (30,0)----+
                        |  |                   |            | | |                    | 
    P_inB (-60,-30)--+-----+-------------------+            +-+-|---> P_C1 (30,-30)--+--> Cout (60,-30)
                     |  |                                       |                      
                     |  +---------------------------------------+                  
                     |                                          |   
                     +------------------------------------------+  

   Distances of 30 um are typical between somas in cortex.
'''

print(INITTEXT1)

# 3.1 Define shapes for the neurons and place each specifically.

principal_soma_radius_um = 10.0                # A typical radius for the soma of a human cortical pyramidal neuron 5-25 um.
interneuron_soma_radius_um = 5.0               # A typical radius for the soma of a human cortical interneuron 2.5-15 um.

Cin_pos   = [-60, 30, 0]
P_inA_pos = [-60,  0, 0]
P_inB_pos = [-60,-30, 0]

I_A0_pos =  [-30,  0, 0]

P_B0_pos =  [0, 0, 0]

I_C0_pos =  [30, 30, 0]
P_C0_pos =  [30, 90, 0]
P_C1_pos =  [30,  0, 0]

Sum_pos =   [60, 30, 0]
Cout_pos =  [60,-30, 0]
 

soma_positions_and_radius = {
    'Cin':   ( Cin_pos, principal_soma_radius_um ),
    'P_inA': ( P_inA_pos, principal_soma_radius_um ),
    'P_inB': ( P_inB_pos, principal_soma_radius_um ),

    'I_A0':  ( I_A0_pos, interneuron_soma_radius_um ),

    'P_B0':  ( P_B0_pos, principal_soma_radius_um ),

    'I_C0':  ( I_C0_pos, interneuron_soma_radius_um ),
    'P_C0':  ( P_C0_pos, principal_soma_radius_um ),
    'P_C1':  ( P_C1_pos, principal_soma_radius_um ),
    
    'Sum':   ( Sum_pos, principal_soma_radius_um ),
    'Cout':  ( Cout_pos, principal_soma_radius_um ),
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


# defining start and end positions of axons. 

# to layer A
PinA_IA0_start = list(np.array(P_inA_pos) + np.array([principal_soma_radius_um, 0, 0]))
PinA_IA0_end   = list(np.array(I_A0_pos) + np.array([-interneuron_soma_radius_um, 0, 0]))
axon_ends['PinA_IA0'] = (PinA_IA0_start, PinA_IA0_end)

PinB_IA0_start = list(np.array(P_inB_pos) + np.array([principal_soma_radius_um, 0, 0]))
PinB_IA0_end   = list(np.array(I_A0_pos) + np.array([-interneuron_soma_radius_um, 0, 0]))
axon_ends['PinB_IA0'] = (PinB_IA0_start, PinB_IA0_end)

# to layer B
IA0_PB0_start = list(np.array(I_A0_pos) + np.array([interneuron_soma_radius_um, 0, 0]))
IA0_PB0_end   = list(np.array(P_B0_pos) + np.array([-principal_soma_radius_um, 0, 0]))
axon_ends['IA0_PB0'] = (IA0_PB0_start, IA0_PB0_end)

PinA_PB0_start = list(np.array(P_inA_pos) + np.array([principal_soma_radius_um, 0, 0]))
PinA_PB0_end   = list(np.array(P_B0_pos) + np.array([-principal_soma_radius_um, 0, 0]))
axon_ends['PinA_PB0'] = (PinA_PB0_start, PinA_PB0_end)

PinB_PB0_start = list(np.array(P_inB_pos) + np.array([principal_soma_radius_um, 0, 0]))
PinB_PB0_end   = list(np.array(P_B0_pos) + np.array([-principal_soma_radius_um, 0, 0]))
axon_ends['PinB_PB0'] = (PinB_PB0_start, PinB_PB0_end)

# to layer C
PB0_IC0_start = list(np.array(P_B0_pos) + np.array([principal_soma_radius_um, 0, 0]))
PB0_IC0_end   = list(np.array(I_C0_pos) + np.array([-interneuron_soma_radius_um, 0, 0]))
axon_ends['PB0_IC0'] = (PB0_IC0_start, PB0_IC0_end)

PB0_PC1_start = list(np.array(P_B0_pos) + np.array([principal_soma_radius_um, 0, 0]))
PB0_PC1_end   = list(np.array(P_C1_pos) + np.array([-principal_soma_radius_um, 0, 0]))
axon_ends['PB0_PC1'] = (PB0_PC1_start, PB0_PC1_end)

Cin_IC0_start = list(np.array(Cin_pos) + np.array([principal_soma_radius_um, 0, 0]))
Cin_IC0_end   = list(np.array(I_C0_pos) + np.array([-interneuron_soma_radius_um, 0, 0]))
axon_ends['Cin_IC0'] = (Cin_IC0_start, Cin_IC0_end)

Cin_PC1_start = list(np.array(Cin_pos) + np.array([principal_soma_radius_um, 0, 0]))
Cin_PC1_end   = list(np.array(P_C1_pos) + np.array([-principal_soma_radius_um, 0, 0]))
axon_ends['Cin_PC1'] = (Cin_PC1_start, Cin_PC1_end)

PinA_PC0_start = list(np.array(P_inA_pos) + np.array([principal_soma_radius_um, 0, 0]))
PinA_PC0_end   = list(np.array(P_C0_pos) + np.array([-principal_soma_radius_um, 0, 0]))
axon_ends['PinA_PC0'] = (PinA_PC0_start, PinA_PC0_end)

PinB_PC0_start = list(np.array(P_inB_pos) + np.array([principal_soma_radius_um, 0, 0]))
PinB_PC0_end   = list(np.array(P_C0_pos) + np.array([-principal_soma_radius_um, 0, 0]))
axon_ends['PinB_PC0'] = (PinB_PC0_start, PinB_PC0_end)

# to output layer
IC0_Sum_start = list(np.array(I_C0_pos) + np.array([interneuron_soma_radius_um, 0, 0]))
IC0_Sum_end   = list(np.array(Sum_pos) + np.array([-principal_soma_radius_um, 0, 0]))
axon_ends['IC0_Sum'] = (IC0_Sum_start, IC0_Sum_end)

PC0_Cout_start = list(np.array(P_C0_pos) + np.array([principal_soma_radius_um, 0, 0]))
PC0_Cout_end   = list(np.array(Cout_pos) + np.array([-principal_soma_radius_um, 0, 0]))
axon_ends['PC0_Cout'] = (PC0_Cout_start, PC0_Cout_end)

PC1_Cout_start = list(np.array(P_C1_pos) + np.array([principal_soma_radius_um, 0, 0]))
PC1_Cout_end   = list(np.array(Cout_pos) + np.array([-principal_soma_radius_um, 0, 0]))
axon_ends['PC1_Cout'] = (PC1_Cout_start, PC1_Cout_end)

PB0_Sum_start = list(np.array(P_B0_pos) + np.array([principal_soma_radius_um, 0, 0]))
PB0_Sum_end   = list(np.array(Sum_pos) + np.array([-principal_soma_radius_um, 0, 0]))
axon_ends['PB0_Sum'] = (PB0_Sum_start, PB0_Sum_end)

Cin_Sum_start = list(np.array(Cin_pos) + np.array([principal_soma_radius_um, 0, 0]))
Cin_Sum_end   = list(np.array(Sum_pos) + np.array([-principal_soma_radius_um, 0, 0]))
axon_ends['Cin_Sum'] = (Cin_Sum_start, Cin_Sum_end)

# last layer (as far as my understanding, need this as a soma always requires an axon when using neuron builder)
Sum_start = list(np.array(Sum_pos) + np.array([principal_soma_radius_um, 0, 0]))
Sum_end =   list(np.array(Sum_pos) + np.array([30.0, 0, 0]))
axon_ends['Sum_axon'] = (Sum_start, Sum_end)

Cout_start = list(np.array(Cout_pos) + np.array([principal_soma_radius_um, 0, 0]))
Cout_end =   list(np.array(Cout_pos) + np.array([30.0, 0, 0]))
axon_ends['Cout_axon'] = (Cout_start, Cout_end)

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
    print('Made neuron compartment with ID %d with soma shape ID %d' % (compartment.ID, somas[n].ID))

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
    print('Made axon compartment with ID %d with axon shape ID %d' % (compartment.ID, axons[a].ID))

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

# delay = 200

def neuron_builder(soma_name:str, axon_name:str):
    print('Createing neuron with soma ID %d and axon ID %d' % (soma_compartments[soma_name].ID, axon_compartments[axon_name].ID))
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

def neuron_builder_special(soma_name:str, axon_name:str):
    return bg_api.BGNES_BS_neuron_create(
        Soma=soma_compartments[soma_name].ID, 
        Axon=axon_compartments[axon_name].ID,
        MembranePotential_mV=neuron_Vm_mV,
        RestingPotential_mV=neuron_Vrest_mV,
        SpikeThreshold_mV=neuron_Vact_mV,
        DecayTime_ms=neuron_tau_AHP_ms,
        AfterHyperpolarizationAmplitude_mV=neuron_Vahp_mV,
        PostsynapticPotentialRiseTime_ms=neuron_tau_PSPr + 50,
        PostsynapticPotentialDecayTime_ms=neuron_tau_PSPd + 50,
        PostsynapticPotentialAmplitude_nA=neuron_IPSP,
    )

Cin = neuron_builder('Cin', 'Cin_IC0')
PinA = neuron_builder_special('P_inA', 'PinA_PB0')
PinB = neuron_builder_special('P_inB', 'PinB_PB0')

IA0 = neuron_builder('I_A0', 'IA0_PB0')
# IA0 = neuron_builder_special('I_A0', 'IA0_PB0')

# PB0 = neuron_builder_special('P_B0', 'PB0_IC0')
PB0 = neuron_builder('P_B0', 'PB0_IC0')

IC0 = neuron_builder_special('I_C0', 'IC0_Sum')
PC0 = neuron_builder_special('P_C0', 'PC0_Cout')
PC1 = neuron_builder_special('P_C1', 'PC1_Cout')

Sum = neuron_builder_special('Sum', 'Sum_axon')
Cout = neuron_builder_special('Cout', 'Cout_axon')

# print('Neuron PinA has ID %d' % PinA.ID)
# print('Neuron PinB has ID %d' % PinB.ID)
# print('Neuron IA has ID %d' % IA.ID)
# print('Neuron Pout has ID %d' % Pout.ID)

# 3.5 Create interneurons.

cells = {
    'Cin': Cin,
    'P_inA': PinA,
    'P_inB': PinB,

    'I_A0': IA0,

    'P_B0': PB0,
    
    'I_C0': IC0,
    'P_C0': PC0,
    'P_C1': PC1,

    'Sum': Sum,
    'Cout': Cout,
}

input_neurons = {
    'Cin': Cin,
    'P_inA': PinA,
    'P_inB': PinB,
}
LayerA_neurons = {
    'I_A0': IA0,
}
LayerB_neurons = {
    'P_B0': PB0,
}
LayerC_neurons = {
    'I_C0': IC0,
    'P_C0': PC0,
    'P_C1': PC1,   
}
output_neurons = {
    'Sum': Sum,
    'Cout': Cout,
}

# 3.6 Create receptors for active connections.

AMPA_conductance = 40.0 #60 # nS
GABA_conductance = -40.0 # nS

# normal weights: 
weight = 1.0

# interneurons for XOR logic:
Pin_IA_weight = 0.5 
Pin_PB0_weight = 0.9    
IA0_PB0_weight = 2.0    

# dict key indicates 'from' axon, value[0] indicate 'to' cell soma, value[1] indicates AMPA/GABA
# defining how neurons should interact with each other. 
# need this for all connections within a circuit (all axons)

connection_pattern_set = {
    'Cin_IC0': ( 'Cin_IC0', 'I_C0', AMPA_conductance, weight ),
    'Cin_PC1': ( 'Cin_IC0', 'P_C1', AMPA_conductance, weight ),
    'Cin_Sum': ( 'Cin_IC0', 'Sum', AMPA_conductance, weight ),

    'PinA_IA0': ( 'PinA_PB0', 'I_A0', AMPA_conductance, Pin_IA_weight ),
    'PinA_PB0': ( 'PinA_PB0', 'P_B0', AMPA_conductance, Pin_PB0_weight ),
    'PinA_PC0': ( 'PinA_PB0', 'P_C0', AMPA_conductance, weight ),

    'PinB_IA0': ( 'PinB_PB0', 'I_A0', AMPA_conductance, Pin_IA_weight ),
    'PinB_PB0': ( 'PinB_PB0', 'P_B0', AMPA_conductance, Pin_PB0_weight ),
    'PinB_PC0': ( 'PinB_PB0', 'P_C0', AMPA_conductance, weight ),

    'IA0_PB0': ( 'IA0_PB0', 'P_B0', GABA_conductance, IA0_PB0_weight ),

    'PB0_IC0': ( 'PB0_IC0', 'I_C0', AMPA_conductance, weight ),
    'PB0_PC1': ( 'PB0_IC0', 'P_C1', AMPA_conductance, weight ),
    'PB0_Sum': ( 'PB0_IC0', 'Sum', AMPA_conductance, weight ),

    'IC0_Sum': ( 'IC0_Sum', 'Sum', GABA_conductance, weight ),

    'PC0_Cout': ( 'PC0_Cout', 'Cout', AMPA_conductance, weight ),

    'PC1_Cout': ( 'PC1_Cout', 'Cout', AMPA_conductance, weight ),
}

# *** ORIGINAL CONNECTION MAKING ALGORITHM:
receptor_functionals = []
receptor_morphologies = []
for connection in connection_pattern_set.keys():
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
    print('Created receptor box with ID %d' % receptor_box.ID)

    # Build receptor function:
    print('Creating receptor from ID %d to ID %d with shape %d' % (from_compartment_id, to_compartment_id, receptor_box.ID))
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

print('Completed network model build.')

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
    # full adder test
    # (100.0, cells['Cin'].ID),

    # (200.0, cells['P_inB'].ID),

    # (300.0, cells['P_inB'].ID),
    # (300.0, cells['Cin'].ID),

    # (400.0, cells['P_inA'].ID),

    # (500.0, cells['P_inA'].ID),
    # (500.0, cells['Cin'].ID),

    # (600.0, cells['P_inA'].ID),
    # (600.0, cells['P_inB'].ID),

    # (700.0, cells['P_inA'].ID),
    # (700.0, cells['P_inB'].ID),
    # (700.0, cells['Cin'].ID),

    # xor test
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
print("\n=== RECORDING ANALYSIS ===")

def find_cell_with_id(id:int) -> str:
    """Enhanced cell lookup with debug output"""
    for n in cells.keys():
        if cells[n].ID == id:
            print(f"Found match - ID: {id}, Name: {n}")
            return n
    print(f"Warning: No matching neuron found for ID: {id}")
    return ''

recording_dict = bg_api.BGNES_get_recording()
print("\nRaw recording keys:", list(recording_dict.keys()))

if isinstance(recording_dict, dict):
    if "StatusCode" in recording_dict:
        print(f"API Status Code: {recording_dict['StatusCode']}")
        
    if "Recording" in recording_dict and recording_dict["Recording"] is not None:
        recording = recording_dict["Recording"]
        print("\n=== RECORDING DETAILS ===")
        print("Available data categories:", list(recording.keys()))
        
        if 'neurons' in recording:
            print("\nNeurons with recorded data:")
            recorded_neuron_ids = list(recording['neurons'].keys())
            print("Raw neuron IDs in recording:", recorded_neuron_ids)
            
            # Create mapping of all expected neurons
            print("\nExpected neurons in model:")
            for name, cell in cells.items():
                print(f"Name: {name}, ID: {cell.ID}")
            
            # Check for recorded neurons not in our model
            print("\nNeuron ID analysis:")
            missing_ids = []
            for neuron_idstr in recorded_neuron_ids:
                neuron_id = int(neuron_idstr)
                name = find_cell_with_id(neuron_id)
                if not name:
                    missing_ids.append(neuron_idstr)
            
            if missing_ids:
                print(f"\nWarning: Recording contains data for unknown neuron IDs: {missing_ids}")
            
            # Prepare for plotting
            sorted_neuron_names = []
            for neuron_idstr in recorded_neuron_ids:
                neuron_id = int(neuron_idstr)
                neuron_name = find_cell_with_id(neuron_id)
                if neuron_name:
                    sorted_neuron_names.append(neuron_name)
                else:
                    sorted_neuron_names.append(f"Unknown_{neuron_idstr}")
            
            print("\nFinal neuron mapping for plotting:")
            for i, name in enumerate(sorted_neuron_names):
                print(f"Plot position {i}: {name}")
            
            # Generate plot
            print(f"\nGenerating plot in {savefolder}")
            plot_recorded(
                savefolder=savefolder,
                data=recording,
                figspecs=figspecs,
                cell_titles=sorted_neuron_names
            )
        else:
            print("Error: No neuron data in recording")
    else:
        print("Error: Recording data is missing or empty")
else:
    print("Error: Invalid recording format received")

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

# 3.1 Define shapes for the neurons and place each specifically.

principal_soma_radius_um = 10.0                # A typical radius for the soma of a human cortical pyramidal neuron 5-25 um.
interneuron_soma_radius_um = 5.                # A typical radius for the soma of a human cortical interneuron 2.5-15 um.

P_in0_pos = [-45,-45, 0]
P_in1_pos = [-45, 45, 0]
#P_A0_pos  = [-15,-45, 0]
I_A0_pos  = [-15,-15, 0]
I_A1_pos  = [-15, 15, 0]
#P_A1_pos  = [-15, 45, 0]
P_B0_pos  = [ 15,-15, 0]
P_B1_pos  = [ 15, 15, 0]
P_out_pos = [ 45,  0, 0]

soma_positions_and_radius = {
    'P_in0': ( P_in0_pos, principal_soma_radius_um ),
    'P_in1': ( P_in1_pos, principal_soma_radius_um ),
    #'P_A0': ( P_A0_pos, principal_soma_radius_um ),
    'I_A0': ( I_A0_pos, interneuron_soma_radius_um ),
    'I_A1': ( I_A1_pos, interneuron_soma_radius_um ),
    #'P_A1': ( P_A1_pos, principal_soma_radius_um ),
    'P_B0': ( P_B0_pos, principal_soma_radius_um ),
    'P_B1': ( P_B1_pos, principal_soma_radius_um ),
    'P_out': ( P_out_pos, principal_soma_radius_um ),
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

P_in0_axon_start_np = np.array(P_in0_pos) + np.array([principal_soma_radius_um, 0, 0])
Pin0_PB0_start = list(P_in0_axon_start_np) + [ end0_radius_um ]
P_in0_axon_end_np = np.array(P_B0_pos) + np.array([-principal_soma_radius_um, 0, 0])
Pin0_PB0_end   = list(P_in0_axon_end_np) + [ end1_radius_um ]
axon_ends['P_in0_P_B0'] = (Pin0_PB0_start, Pin0_PB0_end)

Pin1_PB1_start = list(np.array(P_in1_pos) + np.array([principal_soma_radius_um, 0, 0])) + [ end0_radius_um ]
Pin1_PB1_end   = list(np.array(P_B1_pos) + np.array([-principal_soma_radius_um, 0, 0])) + [ end1_radius_um ]
axon_ends['P_in1_P_B1'] = (Pin1_PB1_start, Pin1_PB1_end)

Pin0_PB0_vec_np = P_in0_axon_end_np - P_in0_axon_start_np
Pin0_branch_start_np = P_in0_axon_start_np + 0.25*Pin0_PB0_vec_np

Pin0_IA0_start = list(Pin0_branch_start_np) + [ end1_radius_um ]
Pin0_IA0_end   = list(np.array(I_A0_pos) + np.array([-interneuron_soma_radius_um, 0, 0])) + [ end1_radius_um ]
axon_ends['P_in0_I_A0'] = (Pin0_IA0_start, Pin0_IA0_end)

Pin1_IA1_start = list(np.array(P_in1_pos) + np.array([principal_soma_radius_um, 0, 0]) + 0.25*(np.array(P_B1_pos) + np.array([-principal_soma_radius_um, 0, 0]) - np.array(P_in1_pos) - np.array([-principal_soma_radius_um, 0, 0])) ) + [ end1_radius_um ]
Pin1_IA1_end   = list(np.array(I_A1_pos) + np.array([-interneuron_soma_radius_um, 0, 0])) + [ end1_radius_um ]
axon_ends['P_in1_I_A1'] = (Pin1_IA1_start, Pin1_IA1_end)

# PA0_PB0_start  = list(np.array(P_A0_pos) + np.array([principal_soma_radius_um, 0, 0]))
# PA0_PB0_end    = list(np.array(P_B0_pos) + np.array([-principal_soma_radius_um, 0, 0]))
# axon_ends['P_A0_P_B0'] = (PA0_PB0_start, PA0_PB0_end)

# PA1_PB1_start  = list(np.array(P_A1_pos) + np.array([principal_soma_radius_um, 0, 0]))
# PA1_PB1_end    = list(np.array(P_B1_pos) + np.array([-principal_soma_radius_um, 0, 0]))
# axon_ends['P_A1_P_B1'] = (PA1_PB1_start, PA1_PB1_end)

IA0_PB1_start  = list(np.array(I_A0_pos) + np.array([interneuron_soma_radius_um, 0, 0])) + [ end0_radius_um ]
IA0_PB1_end    = list(np.array(P_B1_pos) + np.array([-principal_soma_radius_um, 0, 0])) + [ end1_radius_um ]
axon_ends['I_A0_P_B1'] = (IA0_PB1_start, IA0_PB1_end)

IA1_PB0_start  = list(np.array(I_A1_pos) + np.array([interneuron_soma_radius_um, 0, 0])) + [ end0_radius_um ]
IA1_PB0_end    = list(np.array(P_B0_pos) + np.array([-principal_soma_radius_um, 0, 0])) + [ end1_radius_um ]
axon_ends['I_A1_P_B0'] = (IA1_PB0_start, IA1_PB0_end)

PB0_Pout_start = list(np.array(P_B0_pos) + np.array([principal_soma_radius_um, 0, 0])) + [ end0_radius_um ]
PB0_Pout_end   = list(np.array(P_out_pos) + np.array([-principal_soma_radius_um, 0, 0])) + [ end1_radius_um ]
axon_ends['P_B0_P_out'] = (PB0_Pout_start, PB0_Pout_end)

PB1_Pout_start = list(np.array(P_B1_pos) + np.array([principal_soma_radius_um, 0, 0])) + [ end0_radius_um ]
PB1_Pout_end   = list(np.array(P_out_pos) + np.array([-principal_soma_radius_um, 0, 0])) + [ end1_radius_um ]
axon_ends['P_B1_P_out'] = (PB1_Pout_start, PB1_Pout_end)

Pout_start = list(np.array(P_out_pos) + np.array([principal_soma_radius_um, 0, 0])) + [ end0_radius_um ]
Pout_end = list(np.array(P_out_pos) + np.array([30.0, 0, 0])) + [ end1_radius_um ]
axon_ends['P_out_axon'] = (Pout_start, Pout_end)

axon_names = list(axon_ends.keys())

axons = {}
for a in axon_names:
    axon = bg_api.BGNES_cylinder_create(
                Point1Radius_um=axon_ends[a][0][3],
                Point1Position_um=axon_ends[a][0][0:3],
                Point2Radius_um=axon_ends[a][1][3],
                Point2Position_um=axon_ends[a][1][0:3],)
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

def neuron_builder_special(soma_name:str, axon_name:str):
    return bg_api.BGNES_BS_neuron_create(
        Soma=soma_compartments[soma_name].ID, 
        Axon=axon_compartments[axon_name].ID,
        MembranePotential_mV=neuron_Vm_mV,
        RestingPotential_mV=neuron_Vrest_mV,
        SpikeThreshold_mV=neuron_Vact_mV,
        DecayTime_ms=neuron_tau_AHP_ms,
        AfterHyperpolarizationAmplitude_mV=neuron_Vahp_mV,
        PostsynapticPotentialRiseTime_ms=neuron_tau_PSPr + 200,
        PostsynapticPotentialDecayTime_ms=neuron_tau_PSPd,
        PostsynapticPotentialAmplitude_nA=neuron_IPSP,
    )

Pin0 = neuron_builder('P_in0', 'P_in0_P_B0') # *** DO WE NEED TO WORRY ABOUT THE SECOND AXON?
Pin1 = neuron_builder('P_in1', 'P_in1_P_B1') # *** DO WE NEED TO WORRY ABOUT THE SECOND AXON?
# PA0  = neuron_builder('P_A0', 'P_A0_P_B0')
# PA1  = neuron_builder('P_A1', 'P_A1_P_B1')
PB0  = neuron_builder_special('P_B0', 'P_B0_P_out')
PB1  = neuron_builder_special('P_B1', 'P_B1_P_out')
Pout = neuron_builder('P_out', 'P_out_axon')

# 3.5 Create interneurons.

IA0  = neuron_builder('I_A0', 'I_A0_P_B1')
IA1  = neuron_builder('I_A1', 'I_A1_P_B0')

cells = {
    'P_in0': Pin0,
    'P_in1': Pin1,

    # 'P_A0': PA0,
    # 'P_A1': PA1,

    'P_B0': PB0,
    'P_B1': PB1,

    'P_out': Pout,

    'I_A0': IA0,
    'I_A1': IA1,
}

input_neurons = {
    'P_in0': Pin0,
    'P_in1': Pin1,
}
layerA_neurons = {
    # 'P_A0': PA0,
    # 'P_A1': PA1,
    'I_A0': IA0,
    'I_A1': IA1,
}
layerB_neurons = {
    'P_B0': PB0,
    'P_B1': PB1,
}
output_neurons = {
    'P_out': Pout,
}

# 3.6 Create receptors for active connections.

AMPA_conductance = 40.0 #60 # nS
GABA_conductance = -40.0 # nS
PinPB_weight  = 0.9 # Greater weight means stronger PSP amplitude.
PinIA_weight  = 1.2
#PAPB_weight   = 1.0
IAPB_weight   = 1.2
PBPout_weight = 1.0

# dict key indicates 'from' axon, value[0] indicate 'to' cell soma, value[1] indicates AMPA/GABA
connection_pattern_set = {
    'P_in0_P_B0': ( 'P_in0_P_B0', 'P_B0', AMPA_conductance, PinPB_weight),
    'P_in1_P_B1': ( 'P_in1_P_B1', 'P_B1', AMPA_conductance, PinPB_weight),
    'P_in0_I_A0': ( 'P_in0_P_B0', 'I_A0', AMPA_conductance, PinIA_weight), # *** FAKING IT FOR FUNCTIONAL REASONS
    'P_in1_I_A1': ( 'P_in1_P_B1', 'I_A1', AMPA_conductance, PinIA_weight), # *** FAKING IT FOR FUNCTIONAL REASONS

    # 'P_A0_P_B0': ( 'P_A0_P_B0', 'P_B0', AMPA_conductance),
    # 'P_A1_P_B1': ( 'P_A1_P_B1', 'P_B1', AMPA_conductance),

    'I_A0_P_B1': ( 'I_A0_P_B1', 'P_B1', GABA_conductance, IAPB_weight),
    'I_A1_P_B0': ( 'I_A1_P_B0', 'P_B0', GABA_conductance, IAPB_weight),

    'P_B0_P_out': ( 'P_B0_P_out', 'P_out', AMPA_conductance, PBPout_weight),
    'P_B1_P_out': ( 'P_B1_P_out', 'P_out', AMPA_conductance,PBPout_weight),
}

receptor_functionals = []
receptor_morphologies = []
for connection in connection_pattern_set.keys():
    # Set the total conductance through receptors at synapses at this connection:
    conductance = connection_pattern_set[connection][2]
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

    # Build receptor function:
    receptor = bg_api.BGNES_BS_receptor_create(
        SourceCompartmentID=from_compartment_id,
        DestinationCompartmentID=to_compartment_id,
        Conductance_nS=receptor_conductance,
        TimeConstantRise_ms=neuron_tau_PSPr,
        TimeConstantDecay_ms=neuron_tau_PSPd,
        ReceptorMorphology=receptor_box.ID,
    )
    receptor_functionals.append( (receptor, to_cell) )

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

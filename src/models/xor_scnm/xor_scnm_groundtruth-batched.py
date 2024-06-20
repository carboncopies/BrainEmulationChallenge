#!/usr/bin/env python3
# xor_scnm_groundtruth.py
# Randal A. Koene, 20240620

# This version attempts to batch as many NES calls as possible to reduce the
# number of interactions needed from front-end to back-end and back.

scriptversion='0.0.1'

import numpy as np
from datetime import datetime
from time import sleep
import json

import vbpcommon
from BrainGenix.BG_API import BG_API_Setup
from NES_interfaces.KGTRecords import plot_recorded
from netmorph2nes import netmorph_to_somas_segments_synapses


import argparse
Parser = argparse.ArgumentParser(description="vbp script")
Parser.add_argument("-Local", action='store_true', help="Run on local NES server")
Parser.add_argument("-Remote", action='store_true', help="Run on remote NES server")
Parser.add_argument("-Address", default="api.braingenix.org", help="Remote server address")
Parser.add_argument("-Port", default=443, help="Remote server port")
Parser.add_argument("-NoHttps", action='store_true', help="Override to use https on remote server")
Parser.add_argument("-NmSource", default='../../../../../src/nnmodels/netmorph/examples/nesvbp/nesvbp_202406151142', help="Netmorph source files trunk")
Args = Parser.parse_args()

#default:
api_is_local=True
if Args.Remote:
    api_is_local=False
if Args.Local:
    api_is_local=True
remote_https=True
if Args.NoHttps:
    remote_https=False

randomseed = 12345
np.random.seed(randomseed)
runtime_ms = 500.0
savefolder = 'output/'+str(datetime.now()).replace(":", "_")+'-groundtruth'
figspecs = {
    'figsize': (6,6),
    'linewidth': 0.5,
    'figext': 'pdf',
}

# 1. Init NES connection

bg_api = BG_API_Setup(user='Admonishing', passwd='Instruction', remote_host=Args.Address, remote_port=Args.Port, remote_https=remote_https)
if api_is_local:
    bg_api.set_local()
    print('Running locally.')
else:
    print('Running remotely.')
if not bg_api.BGNES_QuickStart(scriptversion, versionmustmatch=False, verbose=False):
    print('BG NES Interface access failed.')
    exit(1)

# 2. Init simulation

sys_name='xor_scnm'
bg_api.BGNES_simulation_create(name=sys_name, seed=randomseed)

# 3. Define ground-truth model

print('Collecting segments from Netmorph output files...')

neuron_Vm_mV = -60.0
neuron_Vrest_mV = -60.0
neuron_Vact_mV = -50.0
neuron_Vahp_mV = -20.0
neuron_tau_AHP_ms = 30.0
neuron_tau_PSPr = 5.0
neuron_tau_PSPd = 25.0
neuron_IPSP = 870.0 # nA

somas, segments, synapses = netmorph_to_somas_segments_synapses(Args.NmSource)

print('Got %d somas, %d segments and %d synapses. Converting each to shape and compartment (this may take a while)...' % (len(somas), len(segments), len(synapses)))

neuron_compartments = {}

# 3. a) Collect and batch soma sphere builds

for soma in somas:
    radius = soma.radius
    center = soma.point()
    print("radius %s center %s" % (str(radius), str(center)))

    shape_res = bg_api.BGNES_NES_Common(
        ReqFunc="Simulation/Geometry/Sphere/Create",
        ReqParams={
            "Radius_um": radius,
            "CenterPosX_um": center[0],
            "CenterPosY_um": center[1],
            "CenterPosZ_um": center[2],
            "Name": bg_api.generate_autoname('sphere-'),
            "SimulationID": bg_api.get_SimID(),
        },
        batch_it=True)
    if shape_res != "batched":
        exit(1)

# 3. b) Make the NES call and collect all the sphere IDs

def get_IDs(responses:list, idtype:str)->list:
    IDs = []
    for response in responses:
        if response['StatusCode'] != 0:
            print('ERROR: NES returned a bad status code. Here were the responses: '+str(responses))
            exit(1)
        if idtype in response:
            IDs.append(response[idtype])
    return IDs

shapeIDs = get_shapeIDs(bg_api.BGNES_NESRequest(),'ShapeID')

# 3. c) Collect and batch soma compartment builds

for idx in range(len(somas)):
    compartment_res = bg_api.BGNES_NES_Common(
        ReqFunc="Simulation/Compartments/SC/Create",
        ReqParams={
            "ShapeID": ShapeIDs[idx],
            "MembranePotential_mV": neuron_Vm_mV,
            "SpikeThreshold_mV": neuron_Vact_mV,
            "DecayTime_ms": neuron_tau_AHP_ms,
            "RestingPotential_mV": neuron_Vrest_mV,
            "AfterHyperpolarizationAmplitude_mV": neuron_Vahp_mV,
            "Name": bg_api.generate_autoname('compartment-'),
            "SimulationID": bg_api.get_SimID(),
        },
        batch_it=True)
    if shape_res != "batched":
        exit(1)


# 3. d) Make the NES call and collect all the soma compartment IDs

soma_compartment_IDs = get_shapeIDs(bg_api.BGNES_NESRequest(),'CompartmentID')

for idx in range(len(somas)):
    neuron_label = somas[idx].label

    if neuron_label not in neuron_compartments:
        neuron_compartments[neuron_label] = {
            'dendrite': [],
            'axon': [],
            'soma': [],
        }

    neuron_compartments[neuron_label]['soma'].append(soma_compartment_IDs[idx])

print('Made %d soma compartments belonging to %d neurons.' % (len(somas), len(neuron_compartments)))

exit(0)

comp_label2id = {}

for segment in segments:
    start_point = segment.start.point()
    end_point = segment.end.point()
    start_radius = segment.startradius
    end_radius = segment.endradius
    neuron_label = segment.data.somaneuron_label
    fiberstructure_type = segment.data.fiberstructure_type

    if neuron_label not in neuron_compartments:
        neuron_compartments[neuron_label] = {
            'dendrite': [],
            'axon': [],
            'soma': [],
        }

    shape_ref = bg_api.BGNES_cylinder_create(
        Point1Radius_um=start_radius,
        Point1Position_um=start_point,
        Point2Radius_um=end_radius,
        Point2Position_um=end_point,)

    compartment_ref = bg_api.BGNES_SC_compartment_create(
        ShapeID=shape_ref.ID,
        MembranePotential_mV=neuron_Vm_mV,
        RestingPotential_mV=neuron_Vrest_mV,
        SpikeThreshold_mV=neuron_Vact_mV,
        DecayTime_ms=neuron_tau_AHP_ms,
        AfterHyperpolarizationAmplitude_mV=neuron_Vahp_mV,
        name=str(segment.data.fiberpiece_label),) # *** Note: Not immediately clear if data (from node2) will map to presyn/postsyn compartments.

    neuron_compartments[neuron_label][fiberstructure_type].append(compartment_ref)

    comp_label2id[compartment_ref.Name] = compartment_ref.ID

print('Made %d segment compartments belonging to %d neurons.' % (len(segments), len(neuron_compartments)))

### 3.3 Create neurons.

print('Making neurons...')

cells = {}
for neuron_label in neuron_compartments:
    SomaIDs = [ compartment.ID for compartment in neuron_compartments[neuron_label]['soma'] ]
    DendriteIDs = [ compartment.ID for compartment in neuron_compartments[neuron_label]['dendrite'] ]
    AxonIDs = [ compartment.ID for compartment in neuron_compartments[neuron_label]['axon'] ]
    cells[neuron_label] = bg_api.BGNES_SC_neuron_create(
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
        name=str(neuron_label),
    )

### 3.4 Create receptors for active connections.

print('Making receptors...')

conductances_nS = {
    'AMPAR': 40.0,
    'NMDAR': 60.0,
    'GABAR': -40.0,
}

receptorPSDwidth_um = 0.1
receptorPSDdepth_um = 0.1
receptorPSDlength_um = 0.3

connection_data_weight = 1.0

for synapse in synapses:
    # Set the total conductance through receptors at synapses at this connection:
    conductance = conductances_nS[synapse.type]
    receptor_conductance = conductance / connection_data_weight # Divided by weight to avoid counter-intuitive weight interpretation.
    print("Setting up '%s' receptor for connection from %s to %s." % (synapse.type, synapse.presyn_neuron, synapse.postsyn_neuron))

    psdlength = receptorPSDlength_um * connection_data_weight

    center_position = synapse.postsyn_receptor_point()
    dimensions = [receptorPSDwidth_um, psdlength, receptorPSDdepth_um]
    rotations = [ 0.0, 0.0, 0.0 ]

    # Build receptor form:
    print('Receptor loction: '+str(center_position))
    receptor_box = bg_api.BGNES_box_create(
        CenterPosition_um=center_position,
        Dimensions_um=dimensions,
        Rotation_rad=rotations,)

    # Build receptor function:
    receptor = bg_api.BGNES_BS_receptor_create(
        SourceCompartmentID=comp_label2id[synapse.preaxon_piece],
        DestinationCompartmentID=comp_label2id[synapse.postdendrite_piece],
        Neurotransmitter=synapse.type[:-1],
        Conductance_nS=receptor_conductance,
        TimeConstantRise_ms=neuron_tau_PSPr,
        TimeConstantDecay_ms=neuron_tau_PSPd,
        ReceptorMorphology=receptor_box.ID,
    )

# 3.5 Save the ground-truth system.
#     Saving this after setting up specific stimulation so that it is included
#     when loading in following scripts.

response = bg_api.BGNES_save()
print('Saved simulation: '+str(response))
savedsimname = response[0]['SavedSimName']

with open(".SimulationHandle", "w") as f:
    print(f"Saving simulation handle '{savedsimname}' to '.SimulationHandle'")
    f.write(savedsimname)


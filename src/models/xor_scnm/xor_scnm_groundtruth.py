#!/usr/bin/env python3
# xor_scnm_groundtruth.py
# Randal A. Koene, 20240617

scriptversion='0.0.1'

import numpy as np
from datetime import datetime
from time import sleep
import json

import vbpcommon
from BrainGenix.BG_API import BG_API_Setup
from NES_interfaces.KGTRecords import plot_recorded
from netmorph2nes import netmorph_to_segments


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

segments = netmorph_to_segments(Args.NmSource)

neuron_compartments = {}

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
        AfterHyperpolarizationAmplitude_mV=neuron_Vahp_mV,)

    neuron_compartments[neuron_label][fiberstructure_type].append(compartment_ref)

print('Found %d segments belonging to %d neurons.' % (len(segments), len(neuron_compartments)))

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
    )

### 3.4 Create receptors for active connections.

print('Making receptors...')

AMPA_conductance = 40.0 #60 # nS
GABA_conductance = -40.0 # nS

# 3.5 Save the ground-truth system.
#     Saving this after setting up specific stimulation so that it is included
#     when loading in following scripts.

response = bg_api.BGNES_save()
print('Saved simulation: '+str(response))
savedsimname = response[0]['SavedSimName']


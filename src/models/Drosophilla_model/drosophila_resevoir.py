#!../../../venv/bin/python
# mushroombody_groundtruth_reservoir.py
# Randal A. Koene, 20250620, 20250811
# Edited: retargeted from the autoassociative pattern-embedding
# reservoir to a three-layer expand-converge mushroom-body-style
# architecture (PN -> KC -> MBON), 20260810.
#
# This script is STEP 1 in the creation of realistic
# ground-truth virtual tissue containing an intended
# cognitive function.
#
# The BrainGenix API is used to direct NES to run embedded
# Netmorph on a Netmorph script to grow a three-layer
# expand-converge reservoir:
#   PN  (input, projection neurons)
#   KC  (expansion / pattern separation, Kenyon cells)
#   MBON (convergence, mushroom body output neurons)
#
# CHANGES FROM THE ORIGINAL autoassociative_reservoir.py:
#   - Removed the PATTERNSIZE/CUESIZE/EMBEDMULTIPLE pattern-embedding
#     math and the "In" region override -- those were specific to the
#     old autoassociative-memory architecture and don't apply here.
#   - ARCHITECTURE_MODIFY now overrides the PN / KC / MBON population
#     sizes declared in the .clp modelfile (mushroom_body_reservoir.clp),
#     driven by new -NumPN / -NumKC / -NumMBON arguments, instead of
#     the old In.pyramidal / In.interneuron override.
#   - Default -modelfile changed to mushroom_body_reservoir.clp.
#   - Connectome post-processing (get_prepost_pyramidal_AMPA) is kept
#     but generalized: it now reports PN->KC and KC->MBON AMPA
#     convergence statistics instead of a single pyramidal-pyramidal
#     "target g_peak_sum" retrieval-conductance check, since that
#     check was specific to the old associative-memory design.
#
# For example, call this with the nesvbp-mushroombody script:
#   ./mushroombody_groundtruth_reservoir.py -modelfile nesvbp-mushroombody

scriptversion='0.2.0'

import numpy as np
#from datetime import datetime
from time import sleep
#import json
import base64
import argparse
#import os

import vbpcommon as vbp
from BrainGenix.BG_API import NES

from sys import path
from pathlib import Path
path.insert(0, str(Path(__file__).parent.parent.parent)+'/components')
from NES_interfaces.KGTRecords import plot_weights

# Handle Arguments for Host, Port, etc
Parser = argparse.ArgumentParser(description="BrainGenix-API Simple Python Test Script")
Parser.add_argument("-Host", default="localhost", type=str, help="Host to connect to")
Parser.add_argument("-Port", default=8000, type=int, help="Port number to connect to")
Parser.add_argument("-UseHTTPS", default=False, type=bool, help="Enable or disable HTTPS")
Parser.add_argument("-modelfile", type=str, help="File to read model instructions from")
Parser.add_argument("-modelname", default="mushroombody", type=str, help="Name of neuronal circuit model to save")
Parser.add_argument("-growdays", type=int, help="Number of days Netmorph growth (omit to use the value already in -modelfile)")
Parser.add_argument("-DoOBJ", action='store_true', help="Netmorph should produce OBJ output")
Parser.add_argument("-DoBlend", action='store_true', help="Netmorph should produce Blender output")
Parser.add_argument("-BlendExec", default="/home/rkoene/blender-4.1.1-linux-x64/blender", type=str, help="Path to Blender executable")
Parser.add_argument("-BevelDepth", default=0.1, type=float, help="Blender neurite bevel depth")
Parser.add_argument("-ExpsDB", default="./ExpsDB.json", type=str, help="Path to experiments database JSON file")
Parser.add_argument("-NumPN", default=50, type=int, help="Number of PN (projection neuron / input) cells")
Parser.add_argument("-NumKC", default=2000, type=int, help="Number of KC (Kenyon cell / expansion) cells")
Parser.add_argument("-NumMBON", default=34, type=int, help="Number of MBON (output / convergence) cells")
Parser.add_argument("-Dt", default=1.0, type=float, help="Simulation step size in ms")
Parser.add_argument("-STDP", action="store_true", help="Enable STDP")
Args = Parser.parse_args()

if Args.DoBlend:
    Args.DoOBJ = True

# Initialize data collection for entry in DB file
DBdata = vbp.InitExpDB(
    Args.ExpsDB,
    'reservoir',
    scriptversion,
    _initIN = {
        'modelfile': Args.modelfile,
        'growdays_override': str(Args.growdays),
        'NumPN': str(Args.NumPN),
        'NumKC': str(Args.NumKC),
        'NumMBON': str(Args.NumMBON),
    },
    _initOUT = {
        'modelname': Args.modelname,
    })

# Load Netmorph model file
modelcontent = 'kjhskdjfhkjhs'

if Args.modelfile:
    try:
        with open(Args.modelfile, 'r') as f:
            modelcontent = f.read()
    except Exception as e:
        vbp.ErrorExit(DBdata, 'modelfile error: '+str(e))
else:
    vbp.ErrorExit(DBdata, 'missing modelfile')


# Modify Netmorph model content based on overrides.
# NOTE: these OVERRIDE the PN.pyramidal / KC.bipolar / MBON.pyramidal
# lines already declared in mushroom_body_reservoir.clp, since later
# command declarations replace earlier ones (manual Ch. 3, Table 1).
ARCHITECTURE_MODIFY = '''
PN.pyramidal=%d;
KC.bipolar=%d;
MBON.pyramidal=%d;
'''

NETMORPH_OBJ = '''
outattr_make_full_OBJ=true;
outattr_OBJ_bevdepth_axon=%.1f;
outattr_OBJ_bevdepth_dendrite=%.1f;
'''

NETMORPH_BLEND = '''
outattr_make_full_blend=true;
blender_exec_path=%s;
'''

GROWDAYS = '''
days=%d;
'''

FIGSPECS={
'figsize': (6,6),
'linewidth': 0.5,
'figext': 'pdf',
}

modelcontent += ARCHITECTURE_MODIFY % (Args.NumPN, Args.NumKC, Args.NumMBON)
if Args.DoOBJ:
    modelcontent += NETMORPH_OBJ % (Args.BevelDepth, Args.BevelDepth)
if Args.DoBlend:
    modelcontent += NETMORPH_BLEND % Args.BlendExec
if Args.growdays:
    modelcontent += GROWDAYS % Args.growdays


# Create Client Configuration For Local Simulation
print(" -- Creating Client Configuration For Local Simulation")
ClientCfg = NES.Client.Configuration()
ClientCfg.Mode = NES.Client.Modes.Remote
ClientCfg.Host = Args.Host
ClientCfg.Port = Args.Port
ClientCfg.UseHTTPS = Args.UseHTTPS
ClientCfg.AuthenticationMethod = NES.Client.Authentication.Password
ClientCfg.Username = "Admonishing"
ClientCfg.Password = "Instruction"


# Create Client Instance
print(" -- Creating Client Instance")
try:
    ClientInstance = NES.Client.Client(ClientCfg)
    if not ClientInstance.IsReady():
        vbp.ErrorExit(DBdata, 'NES.Client error: not ready')
except Exception as e:
    vbp.ErrorExit(DBdata, 'NES.Client error: '+str(e))


# Create A New Simulation
print(" -- Creating Simulation")
SimulationCfg = NES.Simulation.Configuration()
SimulationCfg.Name = "Netmorph-"+Args.modelname
SimulationCfg.Seed = 0
try:
    MySim = ClientInstance.CreateSimulation(SimulationCfg)
except:
    vbp.ErrorExit(DBdata, 'NES error: Failed to create simulation')

MySim.SetLIFCAbstractedFunctional(_AbstractedFunctional=True) # needs to be called before building LIFC receptors
MySim.SetLIFCPreciseSpikeTimes(_UsePreciseSpikeTimes=(Args.Dt > 0.2))
MySim.SetSTDP(_DoSTDP=Args.STDP)
print('Options specified')

# Run Netmorph
RunResponse = MySim.Netmorph_RunAndWait(modelcontent, _NeuronClass='LIFC')
if not RunResponse["Success"]:
    vbp.ErrorExit(DBdata, 'NES.Netmorph error: Netmorph reservoir build failed with status response:'+str(RunResponse["NetmorphStatus"]))

vbp.AddOutputToDB(DBdata, 'NetmorphOutputDirectory', str(RunResponse["NetmorphOutputDirectory"]))
print(" -- Netmorph output files directory is "+str(RunResponse["NetmorphOutputDirectory"]))

# Save model at the NES server
try:
    MySim.ModelSave(Args.modelname)
    print(" -- Neuronal Circuit Model saved as "+Args.modelname)
except:
    vbp.ErrorExit(DBdata, 'NES error: Model save failed')

# Retrieve gzipped Blender file if one was requested
if Args.DoBlend:
    try:
        print(" -- Getting Gzipped Blender file to netmorph-net.blend.gz")
        FileBytes = MySim.Netmorph_GetFile('net.obj.blend.gz')
        try:
            blendgzfile = Args.modelname+'-netmorph-net.blend.gz'
            with open(blendgzfile, 'wb') as f:
                f.write(base64.decodebytes(FileBytes))
            vbp.AddOutputToDB(DBdata, 'blendgz', blendgzfile)
        except:
            vbp.ErrorToDB(DBdata, 'File error: Unable to save gzipped Blender file to '+blendgzfile)
    except:
        vbp.ErrorToDB(DBdata, 'NES.Netmorph error: Failed to get gzipped Blender data')

# Update experiments database file with results
vbp.UpdateExpsDB(DBdata)

# Get and plot connectome to have insight into what the reservoir makes available
# For LIFC neurons, this retrieves:
# [ (list with one dict entry per neuron)
#   {
#      "ConnectionTargets": [ (list of all neurons targeted by this neuron per connection) ],
#      "ConnectionTypes": [ (list of corresponding neurotransmitter type per connection) ],
#      "ConnectionWeights": [ (list of corresponding weights per connection) ],
#      "ConnectionGPeakSum": [ (list of max peak conductance per connection) ],
#      "NumReceptors": [ (list of number of actual physical synapses involved per connection) ]
#   }
#   ...
# ]
try:
    connections_dict = MySim.GetConnectome()
except Exception as e:
    vbp.ErrorExit(DBdata, 'NES error: failed to receive model connectome: '+repr(e))


def get_population_indices(connections_dict:dict, num_pn:int, num_kc:int, num_mbon:int)->dict:
    '''
    IMPORTANT ASSUMPTION: this assumes neuron indices in the connectome
    are ordered the same way the regions were declared in the .clp file
    (PN, then KC, then MBON) and that no other populations were added.
    If you uncomment the APL/DAN extensions in the .clp file, or if the
    server orders neurons differently, update these index ranges (or,
    better, pull population membership from Netmorph's .neurons text
    output -- see manual Ch. 11.2.2 -- instead of assuming contiguous
    ranges).
    '''
    pn_idx = list(range(0, num_pn))
    kc_idx = list(range(num_pn, num_pn + num_kc))
    mbon_idx = list(range(num_pn + num_kc, num_pn + num_kc + num_mbon))
    return {'PN': pn_idx, 'KC': kc_idx, 'MBON': mbon_idx}


def get_convergence_stats(connections_dict:dict, pre_idx:list, post_idx:list)->tuple:
    '''
    For a given presynaptic population (pre_idx) and postsynaptic
    population (post_idx), return:
      - indegree: per postsynaptic neuron, how many distinct
        presynaptic neurons in pre_idx connect onto it (AMPA, type==1)
      - gpeaksummatrix: pre x post matrix of summed AMPA peak
        conductance
    '''
    targets = connections_dict['ConnectionTargets']
    types = connections_dict['ConnectionTypes']
    gpeaksum = connections_dict['ConnectionGPeakSum']

    post_set = set(post_idx)
    indegree = {p: 0 for p in post_idx}
    gpeaksummatrix = np.zeros((len(pre_idx), len(post_idx)))
    pre_pos = {n: i for i, n in enumerate(pre_idx)}
    post_pos = {n: i for i, n in enumerate(post_idx)}

    for pre in pre_idx:
        if pre >= len(targets):
            continue
        seen_posts_for_this_pre = set()
        for i in range(len(gpeaksum[pre])):
            if types[pre][i] != 1: # AMPA only
                continue
            post = targets[pre][i]
            if post not in post_set:
                continue
            gpeaksummatrix[pre_pos[pre]][post_pos[post]] += gpeaksum[pre][i]
            if post not in seen_posts_for_this_pre:
                indegree[post] += 1
                seen_posts_for_this_pre.add(post)

    return indegree, gpeaksummatrix


populations = get_population_indices(connections_dict, Args.NumPN, Args.NumKC, Args.NumMBON)

pn_to_kc_indegree, pn_kc_gpeaksum = get_convergence_stats(connections_dict, populations['PN'], populations['KC'])
kc_to_mbon_indegree, kc_mbon_gpeaksum = get_convergence_stats(connections_dict, populations['KC'], populations['MBON'])

pn_to_kc_values = list(pn_to_kc_indegree.values())
kc_to_mbon_values = list(kc_to_mbon_indegree.values())

plot_weights(pn_kc_gpeaksum, 'output', 'mushroom_body_reservoir_PNtoKC', FIGSPECS)
plot_weights(kc_mbon_gpeaksum, 'output', 'mushroom_body_reservoir_KCtoMBON', FIGSPECS)

if len(pn_to_kc_values) > 0:
    print('PN->KC in-degree: mean=%.2f, min=%d, max=%d (target ~7 for pattern separation)' % (
        float(np.mean(pn_to_kc_values)), min(pn_to_kc_values), max(pn_to_kc_values)))
else:
    print('PN->KC in-degree: no KC neurons found -- check population index assumption')

if len(kc_to_mbon_values) > 0:
    print('KC->MBON in-degree: mean=%.2f, min=%d, max=%d (target: dense/near-complete)' % (
        float(np.mean(kc_to_mbon_values)), min(kc_to_mbon_values), max(kc_to_mbon_values)))
else:
    print('KC->MBON in-degree: no MBON neurons found -- check population index assumption')

print(" -- Done.")

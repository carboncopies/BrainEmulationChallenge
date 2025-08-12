#!../../../venv/bin/python
# autoassociative_connectome.py
# Randal A. Koene, 20250620, 20250811

# This script is STEP 2 in the creation of realistic
# ground-truth virtual tissue containing an intended
# cognitive function.
#
# The BrainGenix API is used to load a simulation model with
# previously generated connection reservoirs.
#
# The available connections are analyzed with the aim to tune
# and prune them to the desired functional connectome.

scriptversion='0.1.0'

import numpy as np
#from datetime import datetime
from time import sleep
import json
#import base64
import copy
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
Parser.add_argument("-modelname", default="autoassociative", type=str, help="Name of neuronal circuit model to save")
Parser.add_argument("-DoOBJ", default=False, type=bool, help="Netmorph should produce OBJ output")
Parser.add_argument("-DoBlend", default=False, type=bool, help="Netmorph should produce Blender output")
Parser.add_argument("-BlendExec", default="/home/rkoene/blender-4.1.1-linux-x64/blender", type=str, help="Path to Blender executable")
Parser.add_argument("-BevelDepth", default=0.1, type=float, help="Blender neurite bevel depth")
Parser.add_argument("-ExpsDB", default="./ExpsDB.json", type=str, help="Path to experiments database JSON file")
Parser.add_argument("-Patterns", default=2, type=int, help="Number of patterns to encode and retrieve")
Parser.add_argument("-Dt", default=1.0, type=float, help="Simulation step size in ms")
Parser.add_argument("-STDP", action="store_true", help="Enable STDP")
Parser.add_argument("-T", type=float, help="Simulation time in ms")
Args = Parser.parse_args()

if Args.DoBlend:
    Args.DoOBJ = True

# Initialize data collection for entry in DB file
DBdata = vbp.InitExpDB(
    Args.ExpsDB,
    'connectome',
    scriptversion,
    _initIN = {
        'modelname': Args.modelname,
    },
    _initOUT = {
    })

FIGSPECS={ 'figsize': (6,6), 'linewidth': 0.5, 'figext': 'pdf', }

PATTERNSIZE=8
CUESIZE=4
EMBEDMULTIPLE=2

# The following requisite combined peak conductance available
# between each pre-post pair of pyramidal neurons was derived
# from results in LIFtest.py.
RETRIEVALPEAKCONDUCTANCEATMAXWEIGHT = 27.44
PREPOSTGPEAKSUMTARGET = RETRIEVALPEAKCONDUCTANCEATMAXWEIGHT / CUESIZE


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


# Load previously generated model
try:
    MySim.ModelLoad(Args.modelname)
    print("Loaded neuronal circuit model "+Args.modelname)
    print('')
except:
    vbp.ErrorExit(DBdata, 'NES error: model load failed')


# Get and plot connectome to have insight into what the reservoir makes available
try:
    connections_before_dict = MySim.GetConnectome()
    if not vbp.PlotAndStoreConnections(connections_before_dict, 'output', 'autoassociative_before_weights', FIGSPECS):
        vbp.ErrorToDB(DBdata, 'File error: Failed to store plots of connectivity')
    if not vbp.PlotAndStoreConnections(connections_before_dict, 'output', 'autoassociative_before_conductance', FIGSPECS, usematrix='conductance'):
        vbp.ErrorToDB(DBdata, 'File error: Failed to store plots of connectivity')
    if not vbp.PlotAndStoreConnections(connections_before_dict, 'output', 'autoassociative_before_numreceptors', FIGSPECS, usematrix='numreceptors'):
        vbp.ErrorToDB(DBdata, 'File error: Failed to store plots of connectivity')
except:
    vbp.ErrorExit(DBdata, 'NES error: failed to receive model connectome')

def get_prepost_pyramidal_AMPA(connections_dict:dict)->tuple:
    numneurons = len(connections_dict["ConnectionGPeakSum"])
    # Find pyramidal neurons
    types = connections_dict['ConnectionTypes']
    pyramidal = []
    for pre in range(numneurons):
        for i in range(len(types[pre])):
            if types[pre][i] == 1: # AMPA
                pyramidal.append(pre)
                break
    # Get pyramidal prepost combined AMPA peak conductances
    targets = connections_dict['ConnectionTargets']
    gpeaksummatrix = np.zeros((numneurons, numneurons))
    gpeaksum = connections_dict['ConnectionGPeakSum']
    for pre in pyramidal:
        for i in range(len(gpeaksum[pre])):
            if types[pre][i] == 1: # AMPA
                post = targets[pre][i]
                gpeaksummatrix[pre][post] += gpeaksum[pre][i]
    return pyramidal, gpeaksummatrix

pyramidal, gpeaksummatrix = get_prepost_pyramidal_AMPA(connections_before_dict)
proportiontargetgpeaksum = gpeaksummatrix / PREPOSTGPEAKSUMTARGET
attargetgpeaksum = (gpeaksummatrix >= PREPOSTGPEAKSUMTARGET) # array of True/False
plot_weights(proportiontargetgpeaksum, 'output', 'autoassociative_reservoir_proptarget', FIGSPECS)
print('Number of pre-post pyramidal connections at target g_sum_peak: %d' % int(attargetgpeaksum.sum()))
agp = np.zeros(attargetgpeaksum.shape)
agp[attargetgpeaksum] = 1
plot_weights(agp, 'output', 'autoassociative_reservoir_attargetgpeaksum', FIGSPECS)

# Let's just try training and see what happens
# We'll start with non-overlapping pattern input IDs
patternstims = []
available = pyramidal.copy()
for p in range(Args.Patterns):
    p_stim = []
    for i in range(PATTERNSIZE*EMBEDMULTIPLE):
        n = available.pop(0)
        p_stim.append(n)
    patternstims.append(p_stim)

cuestims = []
for p in range(Args.Patterns):
    c_stim = [ n for n in range(int(len(patternstims[p])//2)) ]
    cuestims.append(c_stim)

# Set stimulation times
    T = 80000
    if Args.T:
        T = int(Args.T)

STIMINTERVAL = 70.0
REPEATSPERBATCH = 4

training_stim = [ i*STIMINTERVAL for i in range(Args.Patterns*REPEATSPERBATCH) ]
batchduration = STIMINTERVAL*Args.Patterns*REPEATSPERBATCH
batchinterval = batchduration + 100
repeatinterval = 2*batchinterval
repeats = int(T // repeatinterval)

timeneuronpairs_list = []
for n in range(len(pyramidal)):
    for r in range(repeats):
        for s in range(len(training_stim)):
            p = s % Args.Patterns
            if n in patternstims[p]:
                timeneuronpairs_list.append( (training_stim[s]+repeatinterval*r, n) )

for n in range(len(pyramidal)):
    for r in range(repeats):
        for s in range(len(training_stim)):
            p = s % Args.Patterns
            if n in cuestims[p]:
                timeneuronpairs_list.append( (training_stim[s]+repeatinterval*r+batchinterval, n)  )

MySim.SetSpecificAPTimes(timeneuronpairs_list)
print('Simulation stimulation specified')

connectome_before_dict = MySim.GetConnectome()
if not vbp.PlotAndStoreConnections(connectome_before_dict, 'output', 'autoassoc_connectome_before', FIGSPECS):
    vbp.ErrorToDB(DBdata, 'File error: Failed to store plots of connectivity')
# if not vbp.PlotAndStoreConnections(connectome_before_dict, 'output', 'autoassoc_connectome_before_conductance', FIGSPECS, usematrix='conductance'):
#     vbp.ErrorToDB(DBdata, 'File error: Failed to store plots of connectivity conductance')

# Run simulation and record membrane potential
MySim.RecordAll(-1)
MySim.RunAndWait(Runtime_ms=T, Dt_ms=Args.Dt, timeout_s=100.0)
print('Functional stimulation completed')

recording_dict = MySim.GetRecording()
print('Recorded data retrieved')
spikes_dict = MySim.GetSpikeTimes()
print('Spike times retrieved')

#with open('output/raw.json', 'w') as f:
#    json.dump(recording_dict, f)
#with open('output/spikes.json', 'w') as f:
#    json.dump(spikes_dict, f)

if not vbp.PlotAndStoreRecordedActivity(recording_dict, 'output', FIGSPECS, spikes_dict):
    vbp.ErrorToDB(DBdata, 'File error: Failed to store plots of recorded activity')
print('Data plot saved as PDF')

connectome_after_dict = MySim.GetConnectome()
if not vbp.PlotAndStoreConnections(connectome_after_dict, 'output', 'autoassoc_connectome_after', FIGSPECS):
    vbp.ErrorToDB(DBdata, 'File error: Failed to store plots of connectivity')
# if not vbp.PlotAndStoreConnections(connectome_after_dict, 'output', 'autoassoc_connectome_after_conductance', FIGSPECS, usematrix='conductance'):
#     vbp.ErrorToDB(DBdata, 'File error: Failed to store plots of connectivity conductance')


# Save tuned model at the NES server
tunedmodelname = Args.modelname+"-tuned"
try:
    MySim.ModelSave(tunedmodelname)
    vbp.AddOutputToDB(DBdata,'modelname', tunedmodelname)
    print("Saved modified model on server as: "+tunedmodelname)
except:
    vbp.ErrorExit(DBdata, 'NES error: Model save failed')

# Update experiments database file with results
vbp.UpdateExpsDB(DBdata)

print(" -- Done.")

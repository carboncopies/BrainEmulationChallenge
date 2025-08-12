#!../../../venv/bin/python
# autoassociative_reservoir.py
# Randal A. Koene, 20250620, 20250811

# This script is STEP 1 in the creation of realistic
# ground-truth virtual tissue containing an intended
# cognitive function.
#
# The BrainGenix API is used to direct NES to run embedded
# Netmorph on Netmorph script to grow a reservoir of
# connections between pyramidal cell and interneuron
# regions.
#
# For example, call this with the nesvbp-xor-res-sep-targets
# script: ./autoassociative_reservoir.py -modelfile nesvbp-autoassociative
#
# The ModelSave API function is called to ensure that the resulting
# NES Simulation model is stored in a rapid binary format on the server.

scriptversion='0.1.0'

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
Parser.add_argument("-modelfile", default="nesvbp-autoassociative", type=str, help="File to read model instructions from")
Parser.add_argument("-modelname", default="autoassociative", type=str, help="Name of neuronal circuit model to save")
Parser.add_argument("-growdays", default=20, type=int, help="Number of days Netmorph growth")
Parser.add_argument("-DoOBJ", default=False, type=bool, help="Netmorph should produce OBJ output")
Parser.add_argument("-DoBlend", default=False, type=bool, help="Netmorph should produce Blender output")
Parser.add_argument("-BlendExec", default="/home/rkoene/blender-4.1.1-linux-x64/blender", type=str, help="Path to Blender executable")
Parser.add_argument("-BevelDepth", default=0.1, type=float, help="Blender neurite bevel depth")
Parser.add_argument("-ExpsDB", default="./ExpsDB.json", type=str, help="Path to experiments database JSON file")
Parser.add_argument("-Patterns", default=2, type=int, help="Number of patterns to encode and retrieve")
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


# Modify Netmorph model content based on overrides
ARCHITECTURE_MODIFY = '''
In.pyramidal=%d;
In.interneurons=%d;
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

FIGSPECS={ 'figsize': (6,6), 'linewidth': 0.5, 'figext': 'pdf', }

PATTERNSIZE=8
CUESIZE=4
EMBEDMULTIPLE=2

# The following requisite combined peak conductance available
# between each pre-post pair of pyramidal neurons was derived
# from results in LIFtest.py.
RETRIEVALPEAKCONDUCTANCEATMAXWEIGHT = 27.44
PREPOSTGPEAKSUMTARGET = RETRIEVALPEAKCONDUCTANCEATMAXWEIGHT / CUESIZE

modelcontent += ARCHITECTURE_MODIFY % (EMBEDMULTIPLE*PATTERNSIZE*Args.Patterns, PATTERNSIZE*Args.Patterns)
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
try:
    connections_before_dict = MySim.GetConnectome()
    if not vbp.PlotAndStoreConnections(connections_before_dict, 'output', 'autoassociative_reservoir_weights', FIGSPECS):
        vbp.ErrorToDB(DBdata, 'File error: Failed to store plots of connectivity weights')
    if not vbp.PlotAndStoreConnections(connections_before_dict, 'output', 'autoassociative_reservoir_numreceptors', FIGSPECS, usematrix='numreceptors'):
        vbp.ErrorToDB(DBdata, 'File error: Failed to store plots of connectivity number of receptors')
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
attargetgpeaksum = (gpeaksummatrix >= PREPOSTGPEAKSUMTARGET)
plot_weights(proportiontargetgpeaksum, 'output', 'autoassociative_reservoir_proptarget', FIGSPECS)
print('Number of pre-post pyramidal connections at target g_sum_peak: %d' % int(attargetgpeaksum.sum()))

print(" -- Done.")

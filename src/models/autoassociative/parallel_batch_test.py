#!../../../venv/bin/python
# parallel_batch_test.py
# Randal A. Koene, 20260407

# This is a test of multiple parallel launches of Netmorph model growth
# via one running NES server.

# Note: We're making a single client connection to the API server here,
#       but we will be making multiple simulations, because each
#       Netmorph run needs to be done in a separate simulation.
#       To keep the ExpsDB.json clean, this also means we need to
#       prepare multiple entries for it, one for each simulation.
#       (You don't need to use ExpsDB.json, it's just a standard
#       we've been using in typical example scripts.)
#
#       The Blender output options were commented out and retrieval
#       of Blender data was removed from the script to keep it
#       simple and focused.
#
#       Output plotting and saving was also left out for the same reason.
#
#       Notice that the specific 'modelname' used in the batchinfo dict
#       is the same as the 'modelname' saved in the corresponding "OUT"
#       section of the entry that will be added to ExpsDB.json. So, you
#       can identify which entry in the database belongs to which sample.
#
#       In this script, saving output to ExpsDB.json is done once for
#       the whole batch at the very end. This is risky, because the
#       script might fail or hang. There are smarter ways to do this.

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
#Parser.add_argument("-DoOBJ", action='store_true', help="Netmorph should produce OBJ output")
#Parser.add_argument("-DoBlend", action='store_true', help="Netmorph should produce Blender output")
#Parser.add_argument("-BlendExec", default="/home/rkoene/blender-4.1.1-linux-x64/blender", type=str, help="Path to Blender executable")
#Parser.add_argument("-BevelDepth", default=0.1, type=float, help="Blender neurite bevel depth")
Parser.add_argument("-ExpsDB", default="./ExpsDB.json", type=str, help="Path to experiments database JSON file")
Parser.add_argument("-Patterns", default=2, type=int, help="Number of patterns to encode and retrieve")
Parser.add_argument("-Dt", default=1.0, type=float, help="Simulation step size in ms")
Parser.add_argument("-STDP", action="store_true", help="Enable STDP")
Args = Parser.parse_args()

# if Args.DoBlend:
#     Args.DoOBJ = True

# FIGSPECS={ 'figsize': (6,6), 'linewidth': 0.5, 'figext': 'pdf', }

PATTERNSIZE=8
CUESIZE=4
EMBEDMULTIPLE=2

# The following requisite combined peak conductance available
# between each pre-post pair of pyramidal neurons was derived
# from results in LIFtest.py.
RETRIEVALPEAKCONDUCTANCEATMAXWEIGHT = 27.44
PREPOSTGPEAKSUMTARGET = RETRIEVALPEAKCONDUCTANCEATMAXWEIGHT / CUESIZE

# Netmorph model content modification templates for use below (based on overrides in command line arguments)
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

# Load Netmorph model file
modelcontent = 'kjhskdjfhkjhs'
if Args.modelfile:
    try:
        with open(Args.modelfile, 'r') as f:
            modelcontent = f.read()
    except Exception as e:
        print('Failed: modelfile error: '+str(e))
        exit(1)
else:
    print('Failed: missing modelfile')
    exit(1)

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
        print('NES.Client error: not ready')
        exit(1)
except Exception as e:
    print('NES.Client error: '+str(e))
    exit(1)

# Some helper functions for dealing with batch sample entries

def runs_incomplete(batchinfo:dict)->bool:
    for netmorphrun in batchinfo.values():
        if netmorphrun['status'] == 'running':
            return True
    return False

def runs_completed(batchinfo:dict)->bool:
    num_completed = 0
    for netmorphrun in batchinfo.values():
        if netmorphrun['status'] == 'completed':
            num_completed += 1
    return num_completed

def runs_failed(batchinfo:dict)->bool:
    num_failed = 0
    for netmorphrun in batchinfo.values():
        if netmorphrun['status'] == 'failed':
            num_failed += 1
    return num_failed

# NOTE:
# Below, I will be running the same Netmorph configuration in multiple
# Netmorph runs in parallel. This is just as a test of how the server
# uses resources and maintains connectivity.
# If you use this script as a template, you'll probably want to set
# up the parameters you want to try on each sample run in either a
# dict (or similar object), or load them from a file.
# E.g. you wouldn't be grabbing growdays from Args.growdays but from
# your dict/list of parameters.
# For each of the simulations being run in parallel, you copy the
# original configuration content and apply the necessary templated
# modifications.

# === Batch prepare

# Todo:
# - Add try-except to detect problem but not crash
# - Replace some ErrorExit()

batchsize = 10
batchinfo = {}

for i in range(batchsize):

    modelname = Args.modelname+'%04d' % i
    batchinfo[i] = {
        "runID": i,             # Some unique identifier of this sample run (e.g. a point in the hypercube of parameter choices)
        "modelname": modelname  # Remember which output model belongs to this run
    }

    # Initialize data collection for entry in DB file
    DBdata = vbp.InitExpDB(
        Args.ExpsDB,
        'reservoir',
        scriptversion,
        _initIN = {
            'modelfile': Args.modelfile,
            'growdays_override': str(Args.growdays), # REPLACE with the growdays of this sample run
        },
        _initOUT = {
            'modelname': modelname,
        })
    batchinfo[i]['DBdata'] = DBdata # DB data unique to this sample run


# === Batch starts

print(" -- Starting batch of Netmorph runs ")
for netmorphrun in batchinfo.values():

    sample_modelcontent = modelcontent # Copy loaded configuration

    sample_modelcontent += ARCHITECTURE_MODIFY % (EMBEDMULTIPLE*PATTERNSIZE*Args.Patterns, PATTERNSIZE*Args.Patterns)
    # if Args.DoOBJ:
    #     sample_modelcontent += NETMORPH_OBJ % (Args.BevelDepth, Args.BevelDepth)
    # if Args.DoBlend:
    #     sample_modelcontent += NETMORPH_BLEND % Args.BlendExec
    if Args.growdays:
        sample_modelcontent += GROWDAYS % Args.growdays

    # *** NOTE: Here, add additional templated modifications of sample_modelcontent as needed!

    # Create A New Simulation
    print("...Creating Simulation")
    SimulationCfg = NES.Simulation.Configuration()
    SimulationCfg.Name = "Netmorph-"+netmorphrun['modelname']
    SimulationCfg.Seed = 0
    try:
        MySim = ClientInstance.CreateSimulation(SimulationCfg)
    except:
        vbp.ErrorToDB(netmorphrun['DBdata'], 'NES error: Failed to create simulation')
        netmorphrun['status'] = 'failed'
        continue # Skipping this sample

    try:
        MySim.SetLIFCAbstractedFunctional(_AbstractedFunctional=True) # needs to be called before building LIFC receptors
        MySim.SetLIFCPreciseSpikeTimes(_UsePreciseSpikeTimes=(Args.Dt > 0.2))
        MySim.SetSTDP(_DoSTDP=Args.STDP)
    except Exception as e:
        vbp.ErrorToDB(netmorphrun['DBdata'], 'NES error: Failed to specify options: %s' % str(e))
        netmorphrun['status'] = 'failed'
        continue # Skipping this sample

    print('...Options specified')

    netmorphrun['SimID'] = MySim.ID
    netmorphrun['Sim'] = MySim

    # Firstly, Setup and Invoke Netmorph
    try:
        NetmorphOutputDirectory, NetmorphErrCode = MySim.Netmorph_Start(sample_modelcontent, _NeuronClass='LIFC')
        if NetmorphErrCode != 0:
            vbp.ErrorToDB(netmorphrun['DBdata'], 'Netmorph error: %s\nNetmorph output dir: %s' % (str(NetmorphErrCode), str(NetmorphOutputDirectory)))
            netmorphrun['status'] = 'failed'
            continue # Skipping this sample

    except Exception as e:
        vbp.ErrorToDB(netmorphrun['DBdata'], 'NES error: Failed to launch Netmorph: %s' % str(e))
        netmorphrun['status'] = 'failed'
        continue # Skipping this sample

    vbp.AddOutputToDB(netmorphrun['DBdata'], 'NetmorphOutputDirectory', str(NetmorphOutputDirectory))
    print('...launched Nemorph run %d' % netmorphrun['runID'])
    netmorphrun['status'] = 'running'


# === Loop check for runs that have completed

while runs_incomplete(batchinfo):

    for netmorphrun in batchinfo.values():
        if netmorphrun['status'] == 'running':

            MySim = netmorphrun['Sim']

            try:
                Percent, NetmorphStatus = MySim.Netmorph_GetStatus()
            except Exception as e:
                print('...failed to retrieve status for sample run %d, continuing (possible momentary comms problem)' % netmorphrun['runID'])
                time.sleep(1.0)
                continue

            if NetmorphStatus == "None":
                netmorphrun['status'] = 'failed'
                print('...a run failed')
            elif NetmorphStatus == "Done":
                netmorphrun['status'] = 'completed'
                try:
                    MySim.ModelSave(netmorphrun['modelname'])
                    print("Saved resulting model as "+netmorphrun['modelname'])
                except:
                    vbp.ErrorToDB(netmorphrun['DBdata'], 'NES error: Model save failed')
                    print('Failed to save completed model')

                print('...a run completed')

    time.sleep(1.0)

print('Runs completed: %d' % runs_completed(batchinfo))
print('Runs failed   : %d' % runs_failed(batchinfo))


# === Update the ExpsDB.json database for all samples in the batch
for netmorphrun in batchinfo.values():
    vbp.UpdateExpsDB(netmorphrun['DBdata'])

print(" -- Done.")

#!../../../venv/bin/python
# gen_autonm_labels.py
# Randal A. Koene, 20260408

# This script merges parallel Netmorph running as per the
# parallel_batch_test.py script and sample space exploration
# and label generation script by Marianna.

scriptversion='0.1.0'

import numpy as np
#from datetime import datetime
from time import sleep
import json
import base64
import argparse
import os
from pathlib import Path
import pandas as pds
import copy
import psutil
import tqdm

import vbpcommon as vbp
from BrainGenix.BG_API import NES

from sys import path
from pathlib import Path
path.insert(0, str(Path(__file__).parent.parent.parent)+'/components')
from NES_interfaces.KGTRecords import plot_weights

def check_connectome(netmorphrun:dict, PREPOSTGPEAKSUMTARGET:float):
    MySim = netmorphrun['Sim']

    # --- Based on the version in autoassociative_connectome_myg.py
    # Get connectome
    try:
        response = MySim.GetAbstractConnectome(Sparse=True)
    except:
        #vbp.ErrorExit(DBdata, 'NES error: failed to receive model connectome')
        print('NES error: failed to receive abstract model connectome')
        return -1, -1
    PrePostNumReceptors = response['PrePostNumReceptors']
    Regions = response['Regions']
    NeuronTypes = response['Types']
    def RegionByNeuronID(NeuronID:int)->str:
        for reg in list(Regions.keys()):
            if NeuronID in Regions[reg]:
                return reg
        return 'unknown'

    PreRegions = {}
    for preidx, postidx, reccnt in PrePostNumReceptors:
        prereg = RegionByNeuronID(preidx)
        postreg = RegionByNeuronID(postidx)
        if prereg not in PreRegions:
            PreRegions[prereg] = {}
        if postreg not in PreRegions[prereg]:
            PreRegions[prereg][postreg] = 1
        else:
            PreRegions[prereg][postreg] += 1

    Neuron2RegionMap = {}
    for reg in Regions:
        for n in Regions[reg]:
            Neuron2RegionMap[n] = reg

    #print("Pre-post neuron to neuron connections (PrePostNumReceptors): "+str(PrePostNumReceptors))
    #print("Regions: "+str(Regions))
    #print("Neuron types: "+str(NeuronTypes))
    #print("Region-to-region connections in resevoirs:")
    #print(PreRegions)
    #print("Neuron to Region map: "+str(Neuron2RegionMap))
    def SetAll(TheList:list, Value:int):
        for i in range(len(TheList)):
            TheList[i][2] = Value

    def SetOneByPost(TheList:list, PostID:int, Value:int):
        for i in range(len(TheList)):
            if TheList[i][1]==PostID:
                TheList[i][2] = Value

    def SetOneByPre(TheList:list, PreID:int, Value:int):
        for i in range(len(TheList)):
            if TheList[i][0]==PreID:
                TheList[i][2] = Value

    def PostIs(TheList:list, PostID:int)->int:
        for i in range(len(TheList)):
            if TheList[i][1]==PostID:
                return TheList[i][2]
        return 0

    def PreIs(TheList:list, PreID:int)->int:
        for i in range(len(TheList)):
            if TheList[i][0]==PreID:
                return TheList[i][2]
        return 0
    Neuron2Neuron = copy.deepcopy(PrePostNumReceptors)
    SetAll(Neuron2Neuron, 1)
    def ActiveInputsTo(NeuronID:int)->list:
        res = []
        for pre, post, active in Neuron2Neuron:
            if active>0 and post==NeuronID:
                res.append(pre)
        return res

    def ActiveOutputsFrom(NeuronID:int)->list:
        res = []
        for pre, post, active in Neuron2Neuron:
            if active>0 and pre==NeuronID:
                res.append(post)
        return res

    def ConnectionsFrom(SourceRegion:str, NeuronID:int)->list:
        res = []
        activeinputs = ActiveInputsTo(NeuronID)
        for pre in activeinputs:
            if Neuron2RegionMap[pre]==SourceRegion:
                res.append(pre)
        return res

    def EliminateByPost(NeuronID:int):
        SetOneByPost(Neuron2Neuron, NeuronID, 0)

    def EliminateByPre(NeuronID:int):
        SetOneByPre(Neuron2Neuron, NeuronID, 0)

    print('Neurons in In population with >0 connections from other In neurons:')
    for n in Regions['In']:
        frompyrmid = ConnectionsFrom('In', n)
        if len(frompyrmid)<1:
            EliminateByPost(n)
        #else:
        #    print('%d: %s' % (n, str(frompyrmid)))
    #print("Neuron to Neuron after eliminating In neurons with <1 connections from In: "+str(Neuron2Neuron))
    print("Number of connections: "+str(len(Neuron2Neuron)))

    def NumActive()->int:
        num = 0
        for pre, post, active in Neuron2Neuron:
            if active>0:
                num += 1
        return num

    def PrintActive()->str:
        active_str = ''
        num = 0
        for pre, post, active in Neuron2Neuron:
            if active>0:
                active_str += '[%s -> %s], ' % (pre, post)
        return active_str

    print("There are %d usable connections on input-to-output paths (out of %d)." % (NumActive(), len(Neuron2Neuron)))
    #print("Neurons to Neuron reachable both from input and from output: "+PrintActive())

    result1 = NumActive()

    # --- Based on the version at the end of autoassociative_reservoir.py
    try:
        connections_before_dict = MySim.GetConnectome()
        # if not vbp.PlotAndStoreConnections(connections_before_dict, 'output', 'autoassociative_reservoir_weights', FIGSPECS):
        #     vbp.ErrorToDB(DBdata, 'File error: Failed to store plots of connectivity weights')
        # if not vbp.PlotAndStoreConnections(connections_before_dict, 'output', 'autoassociative_reservoir_numreceptors', FIGSPECS, usematrix='numreceptors'):
        #     vbp.ErrorToDB(DBdata, 'File error: Failed to store plots of connectivity number of receptors')
    except:
        #vbp.ErrorExit(DBdata, 'NES error: failed to receive model connectome')
        print('NES error: failed to receive model connectome')
        return result1, -1

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
    #plot_weights(proportiontargetgpeaksum, 'output', 'autoassociative_reservoir_proptarget', FIGSPECS)
    print('Number of pre-post pyramidal connections at target g_sum_peak: %d' % int(attargetgpeaksum.sum()))

    result2 = int(attargetgpeaksum.sum())

    return result1, result2


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
#Parser.add_argument("-batchsize", default=10, type=int, help="Number of Netmorph sample runs at once")
Parser.add_argument("-excel", default="NetmorphParOptim/ParameterSpace_700_samples.xlsx", type=str, help="Path to parameter samples Excel file")
Args = Parser.parse_args()

# if Args.DoBlend:
#     Args.DoOBJ = True

# Load samples parameter values from Excel file and keep file name
f = Path(Args.excel).stem
df = pds.read_excel(open(Args.excel,'rb'))
print(df.head(10))
print(df.shape)
cols = df.columns # column identifiers

df['usable_conns']=0

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

PYRAMIDAL_POP='''
In.pyramidal=%d;
'''

INTERNEURON_POP='''
In.interneuron=%d;
'''

MIN_NEURON_SEPARATION='''
In.minneuronseparation=%d;
'''

SHAPE_RADIUS='''
In.shape.radius=%d;
'''

SHAPE_THICKNESS='''
In.shape.thickness=%d;
'''

DM_WEIGHT='''
all_axons.axondm.dm_weight=%.1f;
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

def runs_running(batchinfo:dict)->int:
    num_running = 0
    for netmorphrun in batchinfo.values():
        if netmorphrun['status'] == 'running':
            num_running += 1
    return num_running

def runs_completed(batchinfo:dict)->int:
    num_completed = 0
    for netmorphrun in batchinfo.values():
        if netmorphrun['status'] == 'completed':
            num_completed += 1
    return num_completed

def runs_failed(batchinfo:dict)->int:
    num_failed = 0
    for netmorphrun in batchinfo.values():
        if netmorphrun['status'] == 'failed':
            num_failed += 1
    return num_failed

# Retrieve results data for previously completed samples.
def get_previously_completed()->dict:
    try:
        with open('batchinfo_completed.json', 'r') as f:
            completed_batchinfo_jsonkeys = json.load(f)
        completed_batchinfo = {int(k): v for k, v in completed_batchinfo_jsonkeys.items()}
    except:
        completed_batchinfo = {}
    return completed_batchinfo

def add_completed(netmorphrun:dict):
    completed_batchinfo = get_previously_completed()
    if netmorphrun['runID'] in completed_batchinfo:
        print('Oops - looks like line %d was already marked completed and saved.')
        k = input('Press Enter to overwrite results (or Ctrl+C to exit)')
    completed_batchinfo[netmorphrun['runID']] = {
        "runID": netmorphrun['runID'],
        "modelname": netmorphrun['modelname'],
        "pars": netmorphrun['pars'],
        "status": netmorphrun['status'],
        "usable_conns1": netmorphrun['usable_conns1'],
        "usable_conns2": netmorphrun['usable_conns2'],
    }
    try:
        if os.path.exists('batchinfo_completed.json'):
            os.replace('batchinfo_completed.json', 'batchinfo_completed_backup.json')
        with open('batchinfo_completed.json', 'w') as f:
            json.dump(completed_batchinfo, f)
    except Exception as e:
        print('WARNING: Adding completed data to batchinfo_completed.json failed')

def resources_low()->bool:
    mem = psutil.virtual_memory()
    return (mem.used/mem.total) > 0.9

def prepare_statusbar():
    StatusBar = tqdm.tqdm("Progress", total=1)
    StatusBar.leave = True
    StatusBar.bar_format = "{desc}{percentage:3.0f}%|{bar}| [{elapsed}<{remaining}, {rate_fmt}{postfix}]"
    StatusBar.colour = "green"
    return StatusBar

def update_statusbar(StatusBar, batchinfo:dict):
    grand_total = 0
    grand_percent = 0
    for netmorphrun in batchinfo.values():
        if 'percent' in netmorphrun:
            grand_total += 100
            grand_percent += netmorphrun['percent']
    StatusBar.total = 100
    StatusBar.n = 100.0*grand_percent/grand_total
    StatusBar.refresh()

def close_statusbar(StatusBar, batchinfo:dict):
    update_statusbar(StatusBar, batchinfo)
    StatusBar.close()

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

batchsize = df.shape[0] # Args.batchsize
#batchsize = 4 # just for testing!
batchinfo = get_previously_completed()

if len(batchinfo.keys()) > 0:
    print('Number of samples completed previously: %d' % len(batchinfo.keys()))
    k = input('Press Enter to process remaining %d' % (batchsize - len(batchinfo.keys())))

# Each simulation in the batch corresponds to one line in the Excel sheet.
# Note: The batchinfo["runID"] is identical to the line number in the Excel sheet.
for i in range(batchsize):

    if i in batchinfo:
        print('Run for data line %d already stored as completed' % i)
        continue

    print('Preparing data line %d' % i)
    modelname = Args.modelname+'%04d' % i
    batchinfo[i] = {
        "runID": i,             # Some unique identifier of this sample run (e.g. a point in the hypercube of parameter choices)
        "modelname": modelname  # Remember which output model belongs to this run
    }

    # Get parameters from data frame
    pars = []
    for k in range(len(cols)):
        if k < 6:
            pars.append(int(df.iloc[i][cols[k]])) # explicit type casting since the values are read as floats from the excel file, but we need integers for the parameters in the reservoir script
        else:
            pars.append(float(df.iloc[i][cols[k]]))
    batchinfo[i]['pars'] = pars

    growdays = str(pars[0])

    # Initialize data collection for entry in DB file
    DBdata = vbp.InitExpDB(
        Args.ExpsDB,
        'reservoir',
        scriptversion,
        _initIN = {
            'modelfile': Args.modelfile,
            'growdays_override': growdays,
        },
        _initOUT = {
            'modelname': modelname,
        })
    batchinfo[i]['DBdata'] = DBdata # DB data unique to this sample run

print('Batch prepared.')
k = input('Press Enter to start simulations.')

# === Batch starts
#     Run Reservoir script with Latin Hypercube generated parameters.

print(" -- Starting batch of Netmorph runs ")
for netmorphrun in batchinfo.values():

    if 'status' in netmorphrun: # was already stored as completed
        continue

    pars = netmorphrun['pars']
    print(pars)
    growdays = pars[0]
    pyramidal = pars[1]
    interneuron = pars[2]
    minneuronseparation = pars[3]
    shapeRadius = pars[4]
    shapeThickness = pars[5]
    dmWeight = pars[6]

    sample_modelcontent = modelcontent # Copy loaded configuration

    sample_modelcontent += ARCHITECTURE_MODIFY % (EMBEDMULTIPLE*PATTERNSIZE*Args.Patterns, PATTERNSIZE*Args.Patterns)
    # if Args.DoOBJ:
    #     sample_modelcontent += NETMORPH_OBJ % (Args.BevelDepth, Args.BevelDepth)
    # if Args.DoBlend:
    #     sample_modelcontent += NETMORPH_BLEND % Args.BlendExec
    
    sample_modelcontent += GROWDAYS % growdays
    sample_modelcontent += PYRAMIDAL_POP % pyramidal
    sample_modelcontent += INTERNEURON_POP % interneuron
    sample_modelcontent += MIN_NEURON_SEPARATION % minneuronseparation        
    sample_modelcontent += SHAPE_RADIUS % shapeRadius
    sample_modelcontent += SHAPE_THICKNESS % shapeThickness
    sample_modelcontent += DM_WEIGHT % dmWeight

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


print('Number of Netmorph sample runs running (out of %d): %d' % (batchsize, runs_running(batchinfo)))

# === Loop check for runs that have completed

StatusBar = prepare_statusbar()
while runs_incomplete(batchinfo):

    for netmorphrun in batchinfo.values():
        if netmorphrun['status'] == 'running':

            MySim = netmorphrun['Sim']

            try:
                Percent, NetmorphStatus = MySim.Netmorph_GetStatus()
                netmorphrun['percent'] = Percent
            except Exception as e:
                print('...failed to retrieve status for sample run %d, continuing (possible momentary comms problem)' % netmorphrun['runID'])
                sleep(2.0)
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

                print('...checking connectome')
                result1, result2 = check_connectome(netmorphrun, PREPOSTGPEAKSUMTARGET)

                netmorphrun['usable_conns1'] = result1
                netmorphrun['usable_conns2'] = result2

                add_completed(netmorphrun)

                print('...completed run with ID %s (runs remaining: %d)' % (str(netmorphrun['runID']), runs_running(batchinfo)))

            update_statusbar(StatusBar, batchinfo)
            sleep(2.0)

    if resources_low():
        mem = psutil.virtual_memory()
        usedGB = mem.used/(1024 ** 3)
        totalGB = mem.total/(1024 ** 3)
        print(f'Used {usedGB:.2f} GB of {totalGB:.2f} GB')
        print("Low RAM - let's break here (clear NES and restart script to do remaining)")
        break

close_statusbar(StatusBar, batchinfo)

print('Runs completed: %d' % runs_completed(batchinfo))
print('Runs failed   : %d' % runs_failed(batchinfo))
print('Runs remaining: %d' % runs_running(batchinfo))


# === Update the ExpsDB.json database for all samples in the batch
for netmorphrun in batchinfo.values():
    if 'DBdata' in netmorphrun:
        vbp.UpdateExpsDB(netmorphrun['DBdata'])

# === Update Excel sheet with data from all completed runs
completed_batchinfo = get_previously_completed()
for netmorphrun in completed_batchinfo.values():
    df.loc[netmorphrun['runID'], 'usable_conns'] = netmorphrun['usable_conns1']

path = Path(Args.excel)
labeledpath = str(path.with_suffix(""))+'-labeled.xlsx'
df.to_excel(labeledpath, index=False)

print("Let's compare the results from the two label interpretation methods:")
for netmorphrun in completed_batchinfo.values():
    print('%03d %05d %05d' % (netmorphrun['runID'], netmorphrun['usable_conns1'], netmorphrun['usable_conns2']))

print(" -- Done.")

#!../../../venv/bin/python
# gen_autonm_labels.py
# Randal A. Koene, 20260410

# This script merges parallel Netmorph running as per the
# parallel_batch_test.py script and sample space exploration
# and label generation script by Marianna.

# TODO:
# - figure out modules or functions that can go into PythonClient
#
# E.g. Run this as: ./gen_autonm_labels.py -fitcpus -deleteresident

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

resource_tests = {
    'low_checked': 0,
    'low_checked_failed': 0,
    'launch_checked': 0,
    'launch_checked_failed': 0
}

# Handle Arguments for Host, Port, etc
def get_Args():
    Parser = argparse.ArgumentParser(description="BrainGenix-API Simple Python Test Script")
    Parser.add_argument("-Host", default="localhost", type=str, help="Host to connect to")
    Parser.add_argument("-Port", default=8000, type=int, help="Port number to connect to")
    Parser.add_argument("-UseHTTPS", default=False, type=bool, help="Enable or disable HTTPS")
    Parser.add_argument("-modelfile", default="nesvbp-autoassociative", type=str, help="File to read model instructions from")
    Parser.add_argument("-modelname", default="autoassociative", type=str, help="Stem name of neuronal circuit models to save")
    #Parser.add_argument("-growdays", default=20, type=int, help="Number of days Netmorph growth")
    Parser.add_argument("-ExpsDB", default="./ExpsDB.json", type=str, help="Path to experiments database JSON file")
    Parser.add_argument("-Patterns", default=2, type=int, help="Number of patterns to encode and retrieve (def: 2)")
    Parser.add_argument("-PATTERNSIZE", default=8, type=int, help="Median number of neurons in each pattern (def: 8)")
    Parser.add_argument("-CUESIZE", default=4, type=int, help="Intended minimum cue size to retrieve patterns (def: 4)")
    Parser.add_argument("-EMBEDMULTIPLE", default=2, type=int, help="Multiplier to embed engram neurons in larger population (def: 2)")
    Parser.add_argument("-Dt", default=1.0, type=float, help="Simulation step size in ms")
    Parser.add_argument("-STDP", action="store_true", help="Enable STDP")
    Parser.add_argument("-excel", default="NetmorphParOptim/ParameterSpace_700_samples.xlsx", type=str, help="Path to parameter samples Excel file")
    Parser.add_argument("-fitcpus", action="store_true", help="Fit batches to the number of logical CPUs available")
    Parser.add_argument("-deleteresident", action="store_true", help="Delete completed server-resident simulations to run more samples")
    Parser.add_argument("-batchlimit", default=0, type=int, help="Never run more than this many at once (def: 0, means no limit)")
    Parser.add_argument("-from_sample", default=0, type=int, help="Samples starting at line (def: 0)")
    Parser.add_argument("-to_sample", default=0, type=int, help="Samples up to line (def: 0, meaning all)")
    return Parser.parse_args()

# Load samples parameter values from Excel file, return data frame and column identifiers
def get_sample_data(Args)->tuple:
    df = pds.read_excel(open(Args.excel,'rb'))
    print(df.head(10))
    print(df.shape)
    return df, df.columns

# Load Netmorph model file
def load_Netmorph_configuration(Args)->str:
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
    return modelcontent

# Create Client Configuration For Local Simulation
def connect_client(Args):
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
    return ClientInstance

# Retrieve results data for previously completed samples.
def get_previously_completed()->dict:
    try:
        with open('batchinfo_completed.json', 'r') as f:
            completed_batchinfo_jsonkeys = json.load(f)
        completed_batchinfo = {int(k): v for k, v in completed_batchinfo_jsonkeys.items()}
    except:
        completed_batchinfo = {}
    return completed_batchinfo

# Update results data for completed samples.
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

# Check RAM
def resources_low(ClientInstance)->bool:
    global resource_tests
    try:
        freeRAMbytes = ClientInstance.GetResourceStatus()['RAMfree']
        resource_tests['low_checked'] += 1
    except:
        print('Warning in resources_low(): Failed to retrieve resources data, carrying on')
        print('Response was: '+str(freeRAMbytes))
        resource_tests['low_checked_failed'] += 1
        return False
    toofull = freeRAMbytes < (2*1024*1024*1024)
    mem = psutil.virtual_memory()
    vmpercenttoohigh = (mem.used/mem.total) > 0.9
    return toofull or vmpercenttoohigh

def lauch_resources_low(ClientInstance)->bool:
    global resource_tests
    try:
        freeRAMbytes = ClientInstance.GetResourceStatus()['RAMfree']
        resource_tests['launch_checked'] += 1
    except:
        print('Warning in launch_resources_low(): Failed to retrieve resources data, carrying on')
        print('Response was: '+str(freeRAMbytes))
        resource_tests['launch_checked_failed'] += 1
        return False
    toofull = freeRAMbytes < (2*1024*1024*1024)
    return toofull

# Status bar helper functions
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
    if grand_total <= 0:
        StatusBar.n = 100
    else:
        StatusBar.n = 100.0*grand_percent/grand_total
    StatusBar.refresh()

def close_statusbar(StatusBar, batchinfo:dict):
    update_statusbar(StatusBar, batchinfo)
    StatusBar.close()

# Helper functions for batch runs
def runs_incomplete(batchinfo:dict)->bool:
    for netmorphrun in batchinfo.values():
        if netmorphrun['status'] == 'running':
            return True
    return False

def count_runs_by_status(batchinfo:dict, status:str)->int:
    num = 0
    for netmorphrun in batchinfo.values():
        if netmorphrun['status'] == status:
            num += 1
    return num

def runs_prepped(batchinfo:dict)->int:
    return count_runs_by_status(batchinfo, 'prepped')

def runs_running(batchinfo:dict)->int:
    return count_runs_by_status(batchinfo, 'running')

def runs_completed(batchinfo:dict)->int:
    return count_runs_by_status(batchinfo, 'completed')

def runs_failed(batchinfo:dict)->int:
    return count_runs_by_status(batchinfo, 'failed')

# Usable connections interpretation
# --- Based on the version in autoassociative_connectome_myg.py
def usable_connections_method1(MySim)->int:
    # Get connectome
    try:
        response = MySim.GetAbstractConnectome(Sparse=True)
    except:
        #vbp.ErrorExit(DBdata, 'NES error: failed to receive model connectome')
        print('NES error: failed to receive abstract model connectome')
        return -1
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

    return NumActive()

# --- Based on the version at the end of autoassociative_reservoir.py
def usable_connections_method2(MySim, PREPOSTGPEAKSUMTARGET:float)->int:
    try:
        connections_before_dict = MySim.GetConnectome()
        # if not vbp.PlotAndStoreConnections(connections_before_dict, 'output', 'autoassociative_reservoir_weights', FIGSPECS):
        #     vbp.ErrorToDB(DBdata, 'File error: Failed to store plots of connectivity weights')
        # if not vbp.PlotAndStoreConnections(connections_before_dict, 'output', 'autoassociative_reservoir_numreceptors', FIGSPECS, usematrix='numreceptors'):
        #     vbp.ErrorToDB(DBdata, 'File error: Failed to store plots of connectivity number of receptors')
    except:
        #vbp.ErrorExit(DBdata, 'NES error: failed to receive model connectome')
        print('NES error: failed to receive model connectome')
        return -1

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

    return int(attargetgpeaksum.sum())

def check_connectome(netmorphrun:dict, PREPOSTGPEAKSUMTARGET:float):
    MySim = netmorphrun['Sim']
    result1 = int(usable_connections_method1(MySim))
    result2 = int(usable_connections_method2(MySim, PREPOSTGPEAKSUMTARGET))
    return result1, result2

# Batch prepare batch information and ExpsDB data for those that will be run
def prepare_batch_information(numsamples, Args)->dict:
    if Args.to_sample <= 0:
        to_sample = numsamples
    else:
        to_sample = Args.to_sample

    batchinfo = get_previously_completed()

    if len(batchinfo.keys()) > 0:
        print('Number of samples completed previously: %d' % len(batchinfo.keys()))
        k = input('Press Enter to process remaining %d' % ((to_sample - Args.from_sample) - len(batchinfo.keys())))

    # Each simulation in the batch corresponds to one line in the Excel sheet.
    # Note: The batchinfo["runID"] is identical to the line number in the Excel sheet.
    for i in range(Args.from_sample, to_sample):

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
        batchinfo[i]['status'] = 'prepped'

    return batchinfo


# Modify Netmorph configuration for sample run
def get_sample_modelcontent(modelcontent:str, pars:list, Args)->str:
    print(pars)
    growdays = pars[0]
    pyramidal = pars[1]
    interneuron = pars[2]
    minneuronseparation = pars[3]
    shapeRadius = pars[4]
    shapeThickness = pars[5]
    dmWeight = pars[6]

    sample_modelcontent = modelcontent # Copy loaded configuration

    sample_modelcontent += ARCHITECTURE_MODIFY % (Args.EMBEDMULTIPLE*Args.PATTERNSIZE*Args.Patterns, Args.PATTERNSIZE*Args.Patterns)
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
    return sample_modelcontent

# Run Reservoir script with Latin Hypercube generated parameters.
def start_batch(ClientInstance, batchinfo:dict, batchsize:int, modelcontent:str, Args):
    for netmorphrun in batchinfo.values():

        if netmorphrun['status'] != 'prepped': # was already stored as completed or is running or has failed
            continue

        if runs_running(batchinfo) >= batchsize: # in case batch size is constrained
            return

        if lauch_resources_low(ClientInstance): # enough RAM to add another sample run?
            return

        sample_modelcontent = get_sample_modelcontent(modelcontent, netmorphrun['pars'], Args)

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

        # Start a Netmorph neural morphogenesis simulation
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
        print('...launched Nemorph run with data sample ID %d' % netmorphrun['runID'])
        netmorphrun['status'] = 'running'


# Loop check for runs that have completed
def monitor_batch(ClientInstance, batchinfo:dict, batchsize:int, modelcontent:str, PREPOSTGPEAKSUMTARGET:float, Args):
    global resource_tests
    run_peak_RAM = []
    StatusBar = prepare_statusbar()
    while runs_incomplete(batchinfo):

        for netmorphrun in batchinfo.values():
            if netmorphrun['status'] == 'running':

                MySim = netmorphrun['Sim']

                try:
                    Percent, NetmorphStatus = MySim.Netmorph_GetStatus()
                    netmorphrun['percent'] = Percent
                except Exception as e:
                    print('\n...failed to retrieve status for sample run %d, continuing (possible momentary comms problem)' % netmorphrun['runID'])
                    sleep(2.0)
                    continue

                if NetmorphStatus == "None":
                    netmorphrun['status'] = 'failed'
                    print('...run %d failed' % netmorphrun['runID'])
                elif NetmorphStatus == "Done":
                    netmorphrun['status'] = 'completed'
                    try:
                        MySim.ModelSave(netmorphrun['modelname'])
                        print("Saved resulting model for run %d as %s" % (netmorphrun['runID'], netmorphrun['modelname']))
                    except:
                        vbp.ErrorToDB(netmorphrun['DBdata'], 'NES error: Model save failed')
                        print('Failed to save completed model for run %d' % netmorphrun['runID'])

                    print('...checking connectome for run %d' % netmorphrun['runID'])
                    result1, result2 = check_connectome(netmorphrun, PREPOSTGPEAKSUMTARGET)

                    netmorphrun['usable_conns1'] = result1
                    netmorphrun['usable_conns2'] = result2

                    add_completed(netmorphrun)

                    print('...completed run with ID %s (runs remaining: %d, prepped remaining: %d)' % (str(netmorphrun['runID']), runs_running(batchinfo), runs_prepped(batchinfo)))

                    if Args.deleteresident:
                        mem = psutil.virtual_memory()
                        run_peak_RAM.append(mem.used)
                        MySim.DeleteResidentByID() # This is new!

                    # If we are not running all that were prepped and resources permit then add to running batch
                    if runs_prepped(batchinfo) > 0:
                        start_batch(ClientInstance, batchinfo, batchsize, modelcontent, Args)

                    print('Resource checks: low_checked %d, low_failed %d, launch_checked %d, launch_checked_failed: %d' % ( resource_tests['low_checked'], resource_tests['low_checked_failed'], resource_tests['launch_checked'], resource_tests['launch_checked_failed'] ))

                update_statusbar(StatusBar, batchinfo)
                sleep(2.0)

        if resources_low(ClientInstance):
            mem = psutil.virtual_memory()
            usedGB = mem.used/(1024 ** 3)
            totalGB = mem.total/(1024 ** 3)
            print(f'\nUsed {usedGB:.2f} GB of {totalGB:.2f} GB')
            print("Low RAM - let's break here (clear NES and restart script to do remaining)")
            break

    close_statusbar(StatusBar, batchinfo)
    print('Memory usage: %s' % str(run_peak_RAM))

# Update the ExpsDB.json database for all samples in the batch
def update_experiments_database(batchinfo:dict):
    for netmorphrun in batchinfo.values():
        if 'DBdata' in netmorphrun and netmorphrun['status'] != 'prepped': # only ones that were just run and completed or failed
            vbp.UpdateExpsDB(netmorphrun['DBdata'])

# Save resulting label data for all completed runs to excel file
def write_excel_with_results(df, Args):
    df['usable_conns1']=0 # add column
    df['usable_conns2']=0 # add column
    completed_batchinfo = get_previously_completed()
    for netmorphrun in completed_batchinfo.values():
        df.loc[netmorphrun['runID'], 'usable_conns1'] = netmorphrun['usable_conns1']
        df.loc[netmorphrun['runID'], 'usable_conns2'] = netmorphrun['usable_conns2']

    path = Path(Args.excel)
    labeledpath = str(path.with_suffix(""))+'-labeled.xlsx'
    df.to_excel(labeledpath, index=False)
    print('Results written to: '+labeledpath)
    return completed_batchinfo


# String templates for augmenting Netmorph model configuration content
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

# Constants

# The following requisite combined peak conductance available
# between each pre-post pair of pyramidal neurons was derived
# from results in LIFtest.py.
RETRIEVALPEAKCONDUCTANCEATMAXWEIGHT = 27.44

# FIGSPECS={ 'figsize': (6,6), 'linewidth': 0.5, 'figext': 'pdf', }

# === Start of program steps
if __name__ == '__main__':

    Args = get_Args()

    df, cols = get_sample_data(Args)

    # Find out total conductance that needs to be possible through the combination of
    # all synapses between one Pyr-Pyr pair so that when trained to max weight by STDP
    # that multi-synaptic connection can contribute the proportion of
    # RETRIEVALPEAKCONDUCTANCEATMAXWEIGHT needed to achieve engram retrieval with
    # a cue of at least Args.CUESIZE active neurons.
    PREPOSTGPEAKSUMTARGET = RETRIEVALPEAKCONDUCTANCEATMAXWEIGHT / Args.CUESIZE

    modelcontent = load_Netmorph_configuration(Args)

    ClientInstance = connect_client(Args)

    # Determine total and batch sizes
    logicalCPUs = os.cpu_count()
    numsamples = df.shape[0] # Args.batchsize
    batchsize = numsamples
    if Args.batchlimit > 0:
        batchsize = Args.batchlimit
    elif Args.fitcpus and batchsize > logicalCPUs:
        batchsize = logicalCPUs
    else:
        batchsize = numsamples

    batchinfo = prepare_batch_information(numsamples, Args)
    print('Batch prepared to do %d sample runs out of a total of %d.' % (runs_prepped(batchinfo), numsamples))
    k = input('Press Enter to start simulations.')

    start_batch(ClientInstance, batchinfo, batchsize, modelcontent, Args)
    print('Number of Netmorph sample runs running (out of %d): %d' % (numsamples, runs_running(batchinfo)))

    monitor_batch(ClientInstance, batchinfo, batchsize, modelcontent, PREPOSTGPEAKSUMTARGET, Args)
    print('Number of samples: %d' % numsamples)
    print('Runs completed   : %d' % runs_completed(batchinfo))
    print('Runs failed      : %d' % runs_failed(batchinfo))
    print('Runs remaining   : %d' % (runs_running(batchinfo)+runs_prepped(batchinfo)))

    update_experiments_database(batchinfo)

    completed_batchinfo = write_excel_with_results(df, Args)

    print("Let's compare the results from the two label interpretation methods:")
    sorted_batchinfo = {k: completed_batchinfo[k] for k in sorted(completed_batchinfo)}
    for netmorphrun in sorted_batchinfo.values():
        print('%03d %05d %05d' % (netmorphrun['runID'], netmorphrun['usable_conns1'], netmorphrun['usable_conns2']))

    print(" -- Done.")
    exit(0)

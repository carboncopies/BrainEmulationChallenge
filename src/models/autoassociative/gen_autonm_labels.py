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
from datetime import datetime
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
from BrainGenix.Tools.BatchRun import BatchRun, LoadNetmorphConfiguration, ConnectClient

from sys import path
from pathlib import Path
path.insert(0, str(Path(__file__).parent.parent.parent)+'/components')
from NES_interfaces.KGTRecords import plot_weights

# Handle Arguments for Host, Port, etc
def get_Args():
    Parser = argparse.ArgumentParser(description="BrainGenix-API Simple Python Test Script")
    Parser.add_argument("-Host", default="localhost", type=str, help="Host to connect to")
    Parser.add_argument("-Port", default=8000, type=int, help="Port number to connect to")
    Parser.add_argument("-UseHTTPS", default=False, type=bool, help="Enable or disable HTTPS")
    Parser.add_argument("-modelfile", default="nesvbp-autoassociative", type=str, help="File to read model instructions from")
    Parser.add_argument("-modelname", default="autoassociative", type=str, help="Stem name of neuronal circuit models to save")
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

# Usable connections interpretation
# --- Based on the version in autoassociative_connectome_myg.py
def usable_connections_method1(MySim)->int:
    # Get connectome
    try:
        response = MySim.GetAbstractConnectome(Sparse=True)
    except:
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

    return NumActive()

# --- Based on the version at the end of autoassociative_reservoir.py
def usable_connections_method2(MySim, PREPOSTGPEAKSUMTARGET:float)->int:
    try:
        connections_before_dict = MySim.GetConnectome()
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
    print('Number of pre-post pyramidal connections at target g_sum_peak: %d' % int(attargetgpeaksum.sum()))

    return int(attargetgpeaksum.sum())

# Return 'failed', 'completed' or 'running' and percent done
def evaluate_state_and_check_connectome(netmorphrun:dict, evalcriteriadata:dict)->tuple:
    MySim = netmorphrun['Sim']

    try:
        Percent, NetmorphStatus = MySim.Netmorph_GetStatus()
    except Exception as e:
        print('\n...failed to retrieve status for sample run %d, continuing (possible momentary comms problem)' % netmorphrun['runID'])
        return 'running', Percent

    if NetmorphStatus == "None":
        return 'failed', 100.0
    elif NetmorphStatus == "Done":
        try:
            MySim.ModelSave(netmorphrun['modelname'])
            print("Saved resulting model for run %d as %s" % (netmorphrun['runID'], netmorphrun['modelname']))
        except:
            vbp.ErrorToDB(netmorphrun['DBdata'], 'NES error: Model save failed')
            print('Failed to save completed model for run %d' % netmorphrun['runID'])

        print('...checking connectome for run %d' % netmorphrun['runID'])
        result1 = int(usable_connections_method1(MySim))
        result2 = int(usable_connections_method2(MySim, evalcriteriadata['PREPOSTGPEAKSUMTARGET']))
        netmorphrun['usable_conns1'] = result1
        netmorphrun['usable_conns2'] = result2
        return 'completed', 100.0

    return 'running', Percent

def extraprep(batchinfo:dict, idx:int, extraprepdata:dict)->bool:
    modelname = extraprepdata['modelname']+'%04d' % idx
    batchinfo[idx]['modelname'] = modelname  # Remember which output model belongs to this run

    # Get parameters from data frame
    df = extraprepdata['dataframe']
    cols = extraprepdata['cols']
    pars = []
    for k in range(len(cols)):
        if k < 6:
            pars.append(int(df.iloc[idx][cols[k]])) # explicit type casting since the values are read as floats from the excel file, but we need integers for the parameters in the reservoir script
        else:
            pars.append(float(df.iloc[idx][cols[k]]))
    batchinfo[idx]['pars'] = pars

    growdays = str(pars[0])

    # Initialize data collection for entry in DB file
    DBdata = vbp.InitExpDB(
        extraprepdata['ExpsDB'],
        'reservoir',
        scriptversion,
        _initIN = {
            'modelfile': extraprepdata['modelfile'],
            'growdays_override': growdays,
        },
        _initOUT = {
            'modelname': modelname,
        })
    batchinfo[idx]['DBdata'] = DBdata # DB data unique to this sample run
    return True

def get_sample_modelcontent(launchdata:dict, pars:list)->str:
    print(pars)
    growdays = pars[0]
    pyramidal = pars[1]
    interneuron = pars[2]
    minneuronseparation = pars[3]
    shapeRadius = pars[4]
    shapeThickness = pars[5]
    dmWeight = pars[6]

    sample_modelcontent = launchdata['modelcontent'] # Copy loaded configuration

    sample_modelcontent += ARCHITECTURE_MODIFY % (launchdata['EMBEDMULTIPLE']*launchdata['PATTERNSIZE']*launchdata['Patterns'], launchdata['PATTERNSIZE']*launchdata['Patterns'])
    
    sample_modelcontent += GROWDAYS % growdays
    sample_modelcontent += PYRAMIDAL_POP % pyramidal
    sample_modelcontent += INTERNEURON_POP % interneuron
    sample_modelcontent += MIN_NEURON_SEPARATION % minneuronseparation        
    sample_modelcontent += SHAPE_RADIUS % shapeRadius
    sample_modelcontent += SHAPE_THICKNESS % shapeThickness
    sample_modelcontent += DM_WEIGHT % dmWeight
    return sample_modelcontent


def sample_launch_requests(netmorphrun:dict, launchdata:dict)->bool:
    sample_modelcontent = get_sample_modelcontent(launchdata, netmorphrun['pars'])

    MySim = netmorphrun['Sim']
    try:
        MySim.SetLIFCAbstractedFunctional(_AbstractedFunctional=True) # needs to be called before building LIFC receptors
        MySim.SetLIFCPreciseSpikeTimes(_UsePreciseSpikeTimes=(launchdata['Dt'] > 0.2))
        MySim.SetSTDP(_DoSTDP=launchdata['STDP'])
    except Exception as e:
        vbp.ErrorToDB(netmorphrun['DBdata'], 'NES error: Failed to specify options: %s' % str(e))
        netmorphrun['status'] = 'failed'
        return False

    print('...Options specified')

    # Start a Netmorph neural morphogenesis simulation
    try:
        NetmorphOutputDirectory, NetmorphErrCode = MySim.Netmorph_Start(sample_modelcontent, _NeuronClass='LIFC')
        if NetmorphErrCode != 0:
            vbp.ErrorToDB(netmorphrun['DBdata'], 'Netmorph error: %s\nNetmorph output dir: %s' % (str(NetmorphErrCode), str(NetmorphOutputDirectory)))
            netmorphrun['status'] = 'failed'
            return False

    except Exception as e:
        vbp.ErrorToDB(netmorphrun['DBdata'], 'NES error: Failed to launch Netmorph: %s' % str(e))
        netmorphrun['status'] = 'failed'
        return False

    vbp.AddOutputToDB(netmorphrun['DBdata'], 'NetmorphOutputDirectory', str(NetmorphOutputDirectory))
    print('...launched Nemorph run with data sample ID %d' % netmorphrun['runID'])
    return True

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

# ===== Start of program steps
if __name__ == '__main__':

    # Constants

    # The following requisite combined peak conductance available
    # between each pre-post pair of pyramidal neurons was derived
    # from results in LIFtest.py.
    RETRIEVALPEAKCONDUCTANCEATMAXWEIGHT = 27.44

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

    # List of batch keys to store and retrieve across potential multiple restarts of this script
    BATCHDATAKEYS = [
        "modelname",
        "pars",
        "usable_conns1",
        "usable_conns2",
    ]

    RESOURCESLOWBYTES = 2*1024*1024*1024 # 2GB

    Args = get_Args()

    df, cols = get_sample_data(Args)

    EXTRAPREPDATA = {
        "modelfile": Args.modelfile,
        "modelname": Args.modelname,
        "dataframe": df,
        "cols": cols,
        "ExpsDB": Args.ExpsDB,
    }

    # Find out total conductance that needs to be possible through the combination of
    # all synapses between one Pyr-Pyr pair so that when trained to max weight by STDP
    # that multi-synaptic connection can contribute the proportion of
    # RETRIEVALPEAKCONDUCTANCEATMAXWEIGHT needed to achieve engram retrieval with
    # a cue of at least Args.CUESIZE active neurons.
    PREPOSTGPEAKSUMTARGET = RETRIEVALPEAKCONDUCTANCEATMAXWEIGHT / Args.CUESIZE

    EVALCRITERIADATA = {
        "PREPOSTGPEAKSUMTARGET": PREPOSTGPEAKSUMTARGET,
    }

    modelcontent = LoadNetmorphConfiguration(Args.modelfile)

    LAUNCHDATA = {
        'modelcontent': modelcontent,
        'EMBEDMULTIPLE': Args.EMBEDMULTIPLE,
        'PATTERNSIZE': Args.PATTERNSIZE,
        'Patterns': Args.Patterns,
        'Dt': Args.Dt,
        'STDP': Args.STDP,
    }

    ClientInstance = ConnectClient(Args.Host, Args.Port, Args.UseHTTPS)

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

    batchrun = BatchRun(numsamples, extraprep, EXTRAPREPDATA, Args.from_sample, Args.to_sample)

    batchrun.start_batch(
        ClientInstance,
        'Netmorph-'+Args.modelname,
        batchsize,
        sample_launch_requests,
        LAUNCHDATA,
        RESOURCESLOWBYTES)
    print('Number of Netmorph sample runs running (out of %d): %d' % (numsamples, batchrun.runs_running()))

    batchrun.monitor_batch(
        ClientInstance,
        'Netmorph-'+Args.modelname,
        batchsize,
        evaluate_state_and_check_connectome,
        EVALCRITERIADATA,
        sample_launch_requests,
        LAUNCHDATA,
        BATCHDATAKEYS,
        RESOURCESLOWBYTES,
        Args.deleteresident)
    print('Number of samples: %d' % numsamples)
    print('Runs completed   : %d' % batchrun.runs_completed())
    print('Runs failed      : %d' % batchrun.runs_failed())
    print('Runs remaining   : %d' % (batchrun.runs_running()+batchrun.runs_prepped()))

    update_experiments_database(batchrun.batchinfo)

    completed_batchinfo = write_excel_with_results(df, Args)

    print("Let's compare the results from the two label interpretation methods:")
    sorted_batchinfo = {k: completed_batchinfo[k] for k in sorted(completed_batchinfo)}
    for netmorphrun in sorted_batchinfo.values():
        print('%03d %05d %05d' % (netmorphrun['runID'], netmorphrun['usable_conns1'], netmorphrun['usable_conns2']))

    print(" -- Done.")
    exit(0)

#!../../../venv/bin/python
# gen_autonm_labels.py (mushroom body version)
# Randal A. Koene, 20260410 (autoassociative version)
# Adapted for the PN -> KC -> MBON mushroom-body-style circuit, 20261103.

# Runs a batch of parallel Netmorph reservoir growths, one per row of a
# parameter-samples spreadsheet, scores each resulting connectome, and
# writes the scores back into a labeled copy of the spreadsheet for
# predictive model building.
#
# Differences from src/models/autoassociative/gen_autonm_labels.py:
# - Spreadsheet columns are mapped generically to Netmorph directives.
#   A column named like a directive (e.g. 'KC.pyramidal', 'days') is
#   appended as '<column>=<value>;'. COLUMN_ALIASES maps the few columns
#   whose names differ from the directive (e.g. 'dm.weight'). New
#   columns such as 'PN.pyramidal' or 'MBON.pyramidal' need no code change.
# - Scoring follows usable_connections_method2() in drosophila_resevoir.py:
#   the number of pre-post pairs in a pathway whose summed AMPA peak
#   conductance reaches a threshold. Both the PN->KC and KC->MBON pathways
#   are scored, together with the number of possible pairs in each.
# - Population membership is taken from the Regions reported by NES in the
#   abstract connectome, not assumed from contiguous neuron index ranges.
#
# E.g. Run this as: ./gen_autonm_labels.py -fitcpus -deleteresident
# Smoke test:       ./gen_autonm_labels.py -from_sample 0 -to_sample 4

scriptversion='0.2.0'

import numpy as np
import argparse
import os
from pathlib import Path
import pandas as pds
import random

import vbpcommon as vbp
from BrainGenix.Tools.BatchRun import BatchRun, LoadNetmorphConfiguration

# The combined peak conductance between one pre-post pair at which a
# single presynaptic neuron can drive its postsynaptic target (derived
# in autoassociative/LIFtest.py for LIFC neurons).
SINGLECELLDRIVEGPEAKSUM = 27.44

# Spreadsheet columns whose names differ from the Netmorph directive they set.
COLUMN_ALIASES = {
    'dm.weight': 'all_axons.axondm.dm_weight',
}

# Pathways to score: (label, presynaptic region, postsynaptic region)
PATHWAYS = [
    ('PNKC', 'PN', 'KC'),
    ('KCMBON', 'KC', 'MBON'),
]

# Handle Arguments for Host, Port, etc
# Note that the "rerunfailed" option only operates as expected if used consistently on
# every re-run of the script on the same batch, because it depends on whether "failed"
# is tracked in 'batchinfo_completed.json' or not.
def get_Args():
    Parser = argparse.ArgumentParser(description="BrainGenix-API Batch Run Script (mushroom body)")
    Parser.add_argument("-Host", default="localhost", type=str, help="Host to connect to")
    Parser.add_argument("-Port", default=8000, type=int, help="Port number to connect to")
    Parser.add_argument("-UseHTTPS", default=False, type=bool, help="Enable or disable HTTPS")
    Parser.add_argument("-modelfile", default="nesvbp-mushroombody", type=str, help="File to read model instructions from")
    Parser.add_argument("-modelname", default="mushroombody", type=str, help="Stem name of neuronal circuit models to save")
    Parser.add_argument("-savemodels", action="store_true", help="Save generated sample models (def: False)")
    Parser.add_argument("-ExpsDB", default="./ExpsDB.json", type=str, help="Path to experiments database JSON file")
    Parser.add_argument("-Dt", default=1.0, type=float, help="Simulation step size in ms")
    Parser.add_argument("-STDP", action="store_true", help="Enable STDP")
    Parser.add_argument("-excel", default="NetmorphParOptim/MushroomBody_ParSpace_700_samples.xlsx", type=str, help="Path to parameter samples Excel file")
    Parser.add_argument("-ignorecols", default=[], nargs='*', type=str, help="Spreadsheet columns NOT to apply as Netmorph directives")
    Parser.add_argument("-PNKCInputs", default=7, type=int, help="Number of PN cells meant to drive a KC together (def: 7)")
    Parser.add_argument("-KCMBONInputs", default=1, type=int, help="Number of KC cells meant to drive an MBON together (def: 1)")
    Parser.add_argument("-PNKCGPeakSumTarget", type=float, help="Combined AMPA peak conductance for a PN->KC pair to count as usable (def: %.2f / PNKCInputs)" % SINGLECELLDRIVEGPEAKSUM)
    Parser.add_argument("-KCMBONGPeakSumTarget", type=float, help="Combined AMPA peak conductance for a KC->MBON pair to count as usable (def: %.2f / KCMBONInputs)" % SINGLECELLDRIVEGPEAKSUM)
    Parser.add_argument("-fitcpus", action="store_true", help="Fit batches to the number of logical CPUs available")
    Parser.add_argument("-deleteresident", action="store_true", help="Delete completed server-resident simulations to run more samples")
    Parser.add_argument("-batchlimit", default=0, type=int, help="Never run more than this many at once (def: 0, means no limit)")
    Parser.add_argument("-from_sample", default=0, type=int, help="Samples starting at line (def: 0)")
    Parser.add_argument("-to_sample", default=0, type=int, help="Samples up to line (def: 0, meaning all)")
    Parser.add_argument("-RCIncludeHeap", action="store_true", help="Include slow search of heap in resource check (def: False)")
    Parser.add_argument("-rerunfailed", action="store_true", help="Auto-rerun rather than mark failed samples (def: False)")
    Parser.add_argument("-randomseed", default=20240628, type=int, help="Specify a random seed (def: 20240628, 0: auto-pick)")
    return Parser.parse_args()

# Load samples parameter values from Excel file, return data frame and column identifiers
def get_sample_data(Args)->tuple:
    df = pds.read_excel(open(Args.excel,'rb'))
    print(df.head(10))
    print(df.shape)
    return df, df.columns

# Map spreadsheet columns to Netmorph directive names, skipping ignored ones.
def get_column_directives(cols, ignorecols:list)->dict:
    coldirectives = {}
    for col in cols:
        if col in ignorecols:
            print('Ignoring spreadsheet column "%s".' % col)
            continue
        coldirectives[col] = COLUMN_ALIASES.get(col, col)
    return coldirectives

# Netmorph directive lines that are in effect (not commented out)
def active_directive_lines(modelcontent:str)->list:
    lines = []
    for line in modelcontent.splitlines():
        line = line.split('#', 1)[0].strip()
        if line:
            lines.append(line.replace(' ', ''))
    return lines

# Refuse to run a batch in which a column would set a parameter of a
# direction model label that the model file does not define, since such
# a column would have no effect on the result (or make Netmorph fail).
def check_directive_labels(coldirectives:dict, modelcontent:str):
    active = active_directive_lines(modelcontent)
    problems = []
    for col, directive in coldirectives.items():
        parts = directive.split('.')
        # e.g. all_axons.axondm.dm_weight requires all_axons.dm_label=axondm
        if len(parts) >= 3 and parts[-1].startswith('dm_'):
            prefix, label = parts[0], parts[1]
            if ('%s.dm_label=%s;' % (prefix, label)) not in active:
                problems.append('Column "%s" sets %s, but the model file has no active line "%s.dm_label=%s;".' % (col, directive, prefix, label))
    if problems:
        for p in problems:
            print('ERROR: '+p)
        print('Fix the model file, or exclude the column with -ignorecols.')
        exit(1)

# Format a spreadsheet value as Netmorph expects it.
def directive_value(value)->str:
    v = value.item() if hasattr(value, 'item') else value
    if isinstance(v, float):
        return '%d' % int(v) if v.is_integer() else '%g' % v
    return str(v)

# Determine the region membership of each neuron, as reported by NES.
def get_region_neurons(MySim)->dict:
    global batchrun
    response = 'not returned'
    try:
        response = MySim.GetAbstractConnectome(Sparse=True, Pause_s=0.1)
        batchrun.RTsuccess('getabsconn')
    except Exception as e:
        print('NES error: failed to receive abstract model connectome')
        batchrun.RTfailed('getabsconn_failed', 'Response: %s, Exception: %s' % (str(response), str(e)) )
        return None
    return response['Regions']

# --- From drosophila_resevoir.py
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

# Conductances are sums of fixed per-synapse values in float32, so a pair
# with exactly the target number of synapses can fall a hair below a target
# computed in float64 (e.g. 4*0.98 vs 27.44/7). Compare with a tolerance.
GPEAKSUMRELTOL = 1e-4

# --- From drosophila_resevoir.py (with comparison tolerance)
def usable_connections_method2(gpeaksummatrix:np.ndarray, PREPOSTGPEAKSUMTARGET:float)->int:
    attargetgpeaksum = (gpeaksummatrix >= PREPOSTGPEAKSUMTARGET*(1.0-GPEAKSUMRELTOL))
    return int(attargetgpeaksum.sum())

# Number of postsynaptic neurons that their k strongest presynaptic partners
# together can drive (combined g_sum_peak >= SINGLECELLDRIVEGPEAKSUM).
def drivable_post_neurons(gpeaksummatrix:np.ndarray, k:int)->int:
    if gpeaksummatrix.size == 0:
        return 0
    k = min(k, gpeaksummatrix.shape[0])
    topk = -np.sort(-gpeaksummatrix, axis=0)[:k, :] # strongest k pre per post column
    return int((topk.sum(axis=0) >= SINGLECELLDRIVEGPEAKSUM*(1.0-GPEAKSUMRELTOL)).sum())

# Score every pathway in PATHWAYS. Returns a dict of label values, or None on failure.
def score_pathways(MySim, gpeaksumtargets:dict, pathinputs:dict)->dict:
    global batchrun
    regions = get_region_neurons(MySim)
    if regions is None:
        return None

    connections_dict = 'not returned'
    try:
        connections_dict = MySim.GetConnectome(Pause_s=0.1)
        batchrun.RTsuccess('getconn')
    except Exception as e:
        print('NES error: failed to receive model connectome')
        batchrun.RTfailed('getconn_failed', 'Response: %s, Exception: %s' % (str(connections_dict), str(e)) )
        return None

    labels = {}
    for regname in ['PN', 'KC', 'MBON']:
        labels['n_'+regname] = len(regions.get(regname, []))
    for pathlabel, prereg, postreg in PATHWAYS:
        pre_idx = list(regions.get(prereg, []))
        post_idx = list(regions.get(postreg, []))
        if len(pre_idx) == 0 or len(post_idx) == 0:
            print('WARNING: region %s or %s has no neurons. Regions reported: %s' % (prereg, postreg, str(list(regions.keys()))))
        indegree, gpeaksummatrix = get_convergence_stats(connections_dict, pre_idx, post_idx)
        labels['usable_'+pathlabel] = usable_connections_method2(gpeaksummatrix, gpeaksumtargets[pathlabel])
        labels['pairs_'+pathlabel] = len(pre_idx)*len(post_idx)
        labels['drivable_'+pathlabel] = drivable_post_neurons(gpeaksummatrix, pathinputs[pathlabel])
        print('%s: %d of %d %s neurons drivable by their %d strongest %s inputs' % (
            pathlabel, labels['drivable_'+pathlabel], len(post_idx), postreg, pathinputs[pathlabel], prereg))
        # Diagnostics: how many pairs connect at all, and how strong the strongest is
        connected = gpeaksummatrix[gpeaksummatrix > 0]
        labels['connected_'+pathlabel] = int(connected.size)
        labels['maxg_'+pathlabel] = float(connected.max()) if connected.size > 0 else 0.0
        print('%s: %d usable pairs out of %d (g_sum_peak >= %.2f), %d connected, max g_sum_peak %.2f' % (
            pathlabel, labels['usable_'+pathlabel], labels['pairs_'+pathlabel], gpeaksumtargets[pathlabel],
            labels['connected_'+pathlabel], labels['maxg_'+pathlabel]))
        if connected.size > 0:
            print('%s connected-pair g_sum_peak quantiles (10/50/90/99%%): %s' % (
                pathlabel, str(np.round(np.quantile(connected, [0.1, 0.5, 0.9, 0.99]), 2))))
    return labels

LABELKEYS = ['usable_PNKC', 'usable_KCMBON', 'pairs_PNKC', 'pairs_KCMBON',
             'drivable_PNKC', 'drivable_KCMBON',
             'connected_PNKC', 'connected_KCMBON', 'maxg_PNKC', 'maxg_KCMBON',
             'n_PN', 'n_KC', 'n_MBON']

# Return 'failed', 'completed' or 'running', percent done, check succeeded
def evaluate_state_and_check_connectome(netmorphrun:dict, evalcriteriadata:dict)->tuple:
    global batchrun
    MySim = netmorphrun['Sim']

    Percent = 0
    try:
        Percent, NetmorphStatus = MySim.Netmorph_GetStatus()
        batchrun.RTsuccess('netmorphstatus')
    except Exception as e:
        print('\n...failed to retrieve status for sample run %d, continuing (possible momentary comms problem)' % netmorphrun['runID'])
        batchrun.RTfailed('netmorphstatus_failed', None)
        return 'running', Percent, False

    if NetmorphStatus == "None":
        return 'failed', 100.0, True
    elif NetmorphStatus == "Failed":
        print("Netmorph failed for run %d. Reported errors: %s" % (netmorphrun['runID'], MySim.NetmorphError))
        return 'failed', 100.0, True
    elif NetmorphStatus == "Done":
        check_succeeded = True
        if evalcriteriadata['savemodels']:
            response = 'not returned'
            try:
                response = MySim.ModelSave(netmorphrun['modelname'], Pause_s=0.1)
                print("Saved resulting model for run %d as %s" % (netmorphrun['runID'], netmorphrun['modelname']))
                batchrun.RTsuccess('modelsave')
            except Exception as e:
                vbp.ErrorToDB(netmorphrun['DBdata'], 'NES error: Model save failed')
                print('Failed to save completed model for run %d' % netmorphrun['runID'])
                batchrun.RTfailed('modelsave_failed', 'Response: %s, Exception: %s' % (str(response), str(e)) )
                check_succeeded = False

        print('...checking connectome for run %d' % netmorphrun['runID'])
        labels = score_pathways(MySim, evalcriteriadata['gpeaksumtargets'], evalcriteriadata['pathinputs'])
        if labels is None:
            check_succeeded = False
            labels = {k: -1 for k in LABELKEYS}
        for k in LABELKEYS:
            netmorphrun[k] = labels[k]
        return 'completed', 100.0, check_succeeded

    return 'running', Percent, True

def extra_prep(batchinfo:dict, idx:int, extraprepdata:dict)->bool:
    modelname = extraprepdata['modelname']+'%04d' % idx
    batchinfo[idx]['modelname'] = modelname  # Remember which output model belongs to this run

    # Netmorph directives for this sample, from the spreadsheet row
    df = extraprepdata['dataframe']
    pars = {}
    for col, directive in extraprepdata['coldirectives'].items():
        pars[directive] = directive_value(df.iloc[idx][col])
    batchinfo[idx]['pars'] = pars

    # Initialize data collection for entry in DB file
    DBdata = vbp.InitExpDB(
        extraprepdata['ExpsDB'],
        'reservoir',
        scriptversion,
        _initIN = {
            'modelfile': extraprepdata['modelfile'],
            'sample': str(idx),
            'directives': pars,
        },
        _initOUT = {
            'modelname': modelname,
        })
    batchinfo[idx]['DBdata'] = DBdata # DB data unique to this sample run
    return True

def get_sample_modelcontent(launchdata:dict, pars:dict)->str:
    print(pars)
    # Later directives override earlier ones in Netmorph, so appending
    # replaces the values in the model file.
    sample_modelcontent = launchdata['modelcontent'] + '\n'
    for directive, value in pars.items():
        sample_modelcontent += '%s=%s;\n' % (directive, value)
    sample_modelcontent += 'randomseed=%d;\n' % launchdata['randomseed']
    return sample_modelcontent

def sample_launch_requests(netmorphrun:dict, launchdata:dict)->bool:
    global batchrun
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
    response = 'not returned'
    try:
        response = MySim.Netmorph_Start(sample_modelcontent, _NeuronClass='LIFC')
        NetmorphOutputDirectory, NetmorphErrCode = response
        if NetmorphErrCode != 0:
            vbp.ErrorToDB(netmorphrun['DBdata'], 'Netmorph error: %s\nNetmorph output dir: %s' % (str(NetmorphErrCode), str(NetmorphOutputDirectory)))
            netmorphrun['status'] = 'failed'
            batchrun.RTfailed('launch_failed', 'Response: %s' % str(response) )
            return False

        batchrun.RTsuccess('launch')
    except Exception as e:
        vbp.ErrorToDB(netmorphrun['DBdata'], 'NES error: Failed to launch Netmorph: %s' % str(e))
        netmorphrun['status'] = 'failed'
        batchrun.RTfailed('launch_failed', 'Response: %s, Exception: %s' % (str(response), str(e)) )
        return False

    vbp.AddOutputToDB(netmorphrun['DBdata'], 'NetmorphOutputDirectory', str(NetmorphOutputDirectory))
    print('...launched Netmorph run with data sample ID %d' % netmorphrun['runID'])
    return True

# Update the ExpsDB.json database for all samples in the batch
def update_experiments_database(batchinfo:dict):
    for netmorphrun in batchinfo.values():
        if 'DBdata' in netmorphrun and netmorphrun['status'] != 'prepped': # only ones that were just run and completed or failed
            for k in LABELKEYS:
                if k in netmorphrun:
                    vbp.AddOutputToDB(netmorphrun['DBdata'], k, netmorphrun[k])
            vbp.UpdateExpsDB(netmorphrun['DBdata'])

# Save resulting label data for all completed runs to excel file.
# Note that this retrieves only what was stored in batchinfo_completed.json
# to create the Excel file. Rows not yet run are left empty, failed runs get -1.
def write_excel_with_results(batchrun, df, Args):
    for k in LABELKEYS:
        df[k] = np.nan # add column
    completed_batchinfo = batchrun.get_previously_completed()
    for netmorphrun in completed_batchinfo.values():
        for k in LABELKEYS:
            if netmorphrun['status'] == 'completed':
                df.loc[netmorphrun['runID'], k] = netmorphrun[k]
            else:
                df.loc[netmorphrun['runID'], k] = -1

    path = Path(Args.excel)
    labeledpath = str(path.with_suffix(""))+'-labeled-RS'+str(Args.randomseed)+'.xlsx'
    df.to_excel(labeledpath, index=False)
    print('Results written to: '+labeledpath)
    print('Note that RS%d in the file name specifies the random seed used.' % Args.randomseed)
    return completed_batchinfo

# ===== Start of program steps
if __name__ == '__main__':

    # List of batch keys to store and retrieve across potential multiple restarts of this script
    BATCHDATAKEYS = ["modelname", "pars"] + LABELKEYS

    RESOURCESLOWBYTES = 2*1024*1024*1024 # 2GB

    Args = get_Args()

    if Args.randomseed == 0:
        Args.randomseed = random.randint(1, 99999999)
    print('Random seed is: '+str(Args.randomseed))

    df, cols = get_sample_data(Args)

    modelcontent = LoadNetmorphConfiguration(Args.modelfile)

    coldirectives = get_column_directives(cols, Args.ignorecols)
    print('Spreadsheet columns applied as Netmorph directives:')
    for col, directive in coldirectives.items():
        print('  %s -> %s' % (col, directive))
    check_directive_labels(coldirectives, modelcontent)

    EXTRAPREPDATA = {
        "modelfile": Args.modelfile,
        "modelname": Args.modelname,
        "dataframe": df,
        "coldirectives": coldirectives,
        "ExpsDB": Args.ExpsDB,
    }

    # A pair is usable when it carries its share of the conductance needed
    # to drive the postsynaptic neuron, given how many inputs should do so together.
    pathinputs = {'PNKC': Args.PNKCInputs, 'KCMBON': Args.KCMBONInputs}
    gpeaksumtargets = {
        'PNKC': Args.PNKCGPeakSumTarget if Args.PNKCGPeakSumTarget is not None else SINGLECELLDRIVEGPEAKSUM/Args.PNKCInputs,
        'KCMBON': Args.KCMBONGPeakSumTarget if Args.KCMBONGPeakSumTarget is not None else SINGLECELLDRIVEGPEAKSUM/Args.KCMBONInputs,
    }
    for pathlabel in gpeaksumtargets:
        print('%s: usable pair at g_sum_peak >= %.2f, drivable post neuron with %d inputs' % (pathlabel, gpeaksumtargets[pathlabel], pathinputs[pathlabel]))

    EVALCRITERIADATA = {
        "gpeaksumtargets": gpeaksumtargets,
        "pathinputs": pathinputs,
        "savemodels": Args.savemodels,
    }

    LAUNCHDATA = {
        'modelcontent': modelcontent,
        'Dt': Args.Dt,
        'STDP': Args.STDP,
        'randomseed': Args.randomseed,
    }

    # Determine total and batch sizes
    logicalCPUs = os.cpu_count()
    numsamples = df.shape[0]
    batchsize = numsamples
    if Args.batchlimit > 0:
        batchsize = Args.batchlimit
    elif Args.fitcpus and batchsize > logicalCPUs:
        batchsize = logicalCPUs

    batchrun = BatchRun(
        host=Args.Host,
        port=Args.Port,
        usehttps=Args.UseHTTPS,
        numsamples=numsamples,
        extraprepfunc=extra_prep,
        extraprepdata=EXTRAPREPDATA,
        from_sample=Args.from_sample,
        to_sample=Args.to_sample,
        rerunfailed=Args.rerunfailed)

    # Extra request tracking while testing large batches
    for key in ['getconn', 'getabsconn', 'modelsave', 'launch', 'netmorphstatus']:
        batchrun.resource_tests[key] = 0
        batchrun.resource_tests[key+'_failed'] = 0

    if Args.RCIncludeHeap:
        try:
            batchrun.ClientInstance.SetResourceChecksIncludeHeap(IncludeHeap=Args.RCIncludeHeap)
        except Exception as e:
            print('Unable to set IncludeHeap. Exception: '+str(e))
            exit(1)

    batchrun.start_batch(
        batchname='Netmorph-'+Args.modelname,
        batchsize=batchsize,
        samplerequestsfunc=sample_launch_requests,
        samplerequestsdata=LAUNCHDATA,
        resourceslowbytes=RESOURCESLOWBYTES)
    print('Number of Netmorph sample runs running (out of %d): %d' % (numsamples, batchrun.runs_running()))

    completed_batch = batchrun.monitor_batch(
        batchname='Netmorph-'+Args.modelname,
        batchsize=batchsize,
        evalfunc=evaluate_state_and_check_connectome,
        evalcriteriadata=EVALCRITERIADATA,
        samplerequestsfunc=sample_launch_requests,
        samplerequestsdata=LAUNCHDATA,
        batchdatakeys=BATCHDATAKEYS,
        resourceslowbytes=RESOURCESLOWBYTES,
        deleteresident=Args.deleteresident)

    print('Number of samples: %d' % numsamples)
    print('Runs completed   : %d' % batchrun.runs_completed())
    print('Runs failed      : %d' % batchrun.runs_failed())
    remaining = batchrun.runs_running()+batchrun.runs_prepped()
    print('Runs remaining   : %d' % remaining)

    update_experiments_database(batchrun.batchinfo)

    write_excel_with_results(batchrun, df, Args)

    print('Inspect resource_checks.json for request success/failure tracking data.')
    if remaining > 0:
        print('To complete remaining simply rerun this script.')
    else:
        print('To run batch again, move or delete batchinfo_completed.json.')

    if not completed_batch:
        print('PLEASE NOTE:\nThis batch did NOT complete. Possible API/NES server problem detected!\nSolve the problem and rerun to complete.')

    print(" -- Done.")
    exit(0)

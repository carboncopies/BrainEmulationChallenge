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
import random

import vbpcommon as vbp
from BrainGenix.BG_API import NES
from BrainGenix.Tools.BatchRun import BatchRun, LoadNetmorphConfiguration, ConnectClient

from sys import path
from pathlib import Path
path.insert(0, str(Path(__file__).parent.parent.parent)+'/components')
from NES_interfaces.KGTRecords import plot_weights

# Handle Arguments for Host, Port, etc
# Note that the "rerunfailed" option only operates as expected if used consistently on
# every re-run of the script on the same batch, because it depends on whether "failed"
# is tracked in 'batchinfo_completed.json' or not.
def get_Args():
    Parser = argparse.ArgumentParser(description="BrainGenix-API Batch Run Script")
    Parser.add_argument("-Host", default="localhost", type=str, help="Host to connect to")
    Parser.add_argument("-Port", default=8000, type=int, help="Port number to connect to")
    Parser.add_argument("-UseHTTPS", default=False, type=bool, help="Enable or disable HTTPS")
    Parser.add_argument("-modelfile", default="nesvbp-autoassociative", type=str, help="File to read model instructions from")
    Parser.add_argument("-modelname", default="autoassociative", type=str, help="Stem name of neuronal circuit models to save")
    Parser.add_argument("-savemodels", action="store_true", help="Save generated sample models (def: False)")
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
    Parser.add_argument("-RCIncludeHeap", action="store_true", help="Include slow search of heap in resource check (def: False)")
    Parser.add_argument("-rerunfailed", action="store_true", help="Auto-rerun rather than mark failed samples (def: False)")
    Parser.add_argument("-randomseed", default=20240628, type=int, help="Specify a random seed (def: 20240628, 0: auto-pick)")
    # --- Extended labels (Pyr->Int, Int->Pyr, Int->Int). See extended_connection_labels().
    # Per-pair thresholds (ASSUMPTION, not from LIFtest.py or team docs): a pair is "usable" if its summed g_peak
    # is at least MINSYNAPSES synapse-equivalents (def: 1) of the per-synapse peak conductance from LIFtest.py:
    #   AMPA: 49 channels (0.83*60) x 20 pS = 0.98 nS per synapse;  GABA: 10 channels x 80 pS = 0.80 nS per synapse.
    #   (The earlier default of 7, matching the Pyr->Pyr 6.86 nS target, gave all-zero labels in the smoke test.)
    # Aggregate targets (per target neuron, summed over ALL incoming connections from the presynaptic class) come
    # from LIFtest.py lines ~444-446, SUPERSYNAPSESONINT=8 and SUPERSYNAPSESFROMINT=20:
    #   Pyr->Int AMPA: 8 x 0.98 nS = 7.84 nS at synaptic weight 1.0 (LIFtest.py line 535).
    #   Int->Pyr GABA: 20 x 0.80 nS = 16.0 nS at synaptic weight 0.5 (LIFtest.py line 500), i.e. 8 nS weight-scaled.
    # NES g_peak_sum is the UNWEIGHTED peak conductance, so frac_pyr_inhibited compares it with 16 nS (the
    # LIFtest peak conductance); frac_pyr_inhibited_w05 compares with 16*0.5 = 8 nS (weight-scaled equivalent).
    Parser.add_argument("-MINSYNAPSES", default=1, type=int, help="Synapse-equivalents a pair needs to count as usable for the per-pair labels (def: 1; assumption)")
    Parser.add_argument("-PYRINT_AGG_TARGET_nS", default=7.84, type=float, help="Per-interneuron total incoming AMPA g_peak_sum from pyramidal cells (def: 7.84 = 8 x 0.98, LIFtest SUPERSYNAPSESONINT)")
    Parser.add_argument("-INTPYR_AGG_TARGET_nS", default=16.0, type=float, help="Per-pyramidal total incoming GABA g_peak_sum from interneurons (def: 16.0 = 20 x 0.80, LIFtest SUPERSYNAPSESFROMINT; LIFtest applies weight 0.5)")
    Parser.add_argument("-INTPYR_AGG_WEIGHT", default=0.5, type=float, help="LIFtest GABA weight used for the secondary weight-scaled label frac_pyr_inhibited_w05 (def: 0.5)")
    Parser.add_argument("-GPEAKAMPA_PERSYN_nS", default=0.98, type=float, help="Peak AMPA conductance per synapse in nS (def: 0.98, from LIFtest.py)")
    Parser.add_argument("-GPEAKGABA_PERSYN_nS", default=0.80, type=float, help="Peak GABA conductance per synapse in nS (def: 0.80, from LIFtest.py)")
    Parser.add_argument("-PYRINT_TARGET_nS", default=None, type=float, help="Override g_peak_sum target for Pyr->Int AMPA pairs (def: MINSYNAPSES*GPEAKAMPA_PERSYN_nS)")
    Parser.add_argument("-INTPYR_TARGET_nS", default=None, type=float, help="Override g_peak_sum target for Int->Pyr GABA pairs (def: MINSYNAPSES*GPEAKGABA_PERSYN_nS)")
    Parser.add_argument("-INTINT_TARGET_nS", default=None, type=float, help="Override g_peak_sum target for Int->Int GABA pairs (def: MINSYNAPSES*GPEAKGABA_PERSYN_nS)")
    Parser.add_argument("-KEEPUNKNOWNTYPE", action="store_true", help="Do not infer type for neurons NES reports as type 0 (def: infer interneuron, see extended_connection_labels)")
    Parser.add_argument("-out", default="", type=str, help="Output Excel path (def: derived from -excel as <stem>-labeled-RS<seed>.xlsx)")
    Parser.add_argument("-vizdir", default="", type=str, help="If set, save abstract connectome + positions JSON per sample here (def: none)")
    return Parser.parse_args()

# Load samples parameter values from Excel file, return data frame and column identifiers
def get_sample_data(Args)->tuple:
    df = pds.read_excel(open(Args.excel,'rb'))
    # Bug fix: the Excel files have a header 'dm.weight ' (trailing space), which made extra_prep miss the column
    # and silently use dm.weight=0.5 for every sample.
    df.columns = [str(c).strip() for c in df.columns]
    print(df.head(10))
    print(df.shape)
    return df, df.columns

# Usable connections interpretation
# --- Based on the version in autoassociative_connectome_myg.py
def usable_connections_method1(MySim)->int:
    global batchrun
    # Get connectome
    response = 'not returned'
    try:
        response = MySim.GetAbstractConnectome(Sparse=True, Pause_s=0.1)
        batchrun.RTsuccess('getabsconn')
    except Exception as e:
        print('NES error: failed to receive abstract model connectome')
        batchrun.RTfailed('getabsconn_failed', 'Response: %s, Exception: %s' % (str(response), str(e)) )
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
    global batchrun
    connections_before_dict = 'not returned'
    try:
        connections_before_dict = MySim.GetConnectome(Pause_s=0.1)
        batchrun.RTsuccess('getconn')
    except Exception as e:
        #vbp.ErrorExit(DBdata, 'NES error: failed to receive model connectome')
        print('NES error: failed to receive model connectome')
        batchrun.RTfailed('getconn_failed', 'Response: %s, Exception: %s' % (str(connections_before_dict), str(e)) )
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


# ConnectionTypes codes as returned by GetConnectome() (NES LIFCNeuron.cpp, NeurotransmitterType2ConnectionType)
CONN_AMPA = 1
CONN_GABA = 2
CONN_NMDA = 3
# Neuron types as returned in GetAbstractConnectome()['Types'] and GetSomaPositions()['SomaTypes']
NEURON_UNKNOWN = 0
NEURON_PRINCIPAL = 1
NEURON_INTERNEURON = 2
_CLASSNAME = {NEURON_UNKNOWN: 'unk', NEURON_PRINCIPAL: 'pyr', NEURON_INTERNEURON: 'int'}

# --- Extended labels: Pyr->Int (AMPA), Int->Pyr (GABA), Int->Int (GABA).
# For each class a "pair" is an ordered (pre, post) neuron pair that has at least one synapse of
# the class' neurotransmitter; pair strength is the sum of g_peak_sum over all its connections of that
# type (as for usable_conns2). A pair counts as usable if strength >= target. Cell types come from
# GetAbstractConnectome()['Types'] (1 principal, 2 interneuron), falling back to SomaTypes from
# GetSomaPositions() where 'Types' is 0.
# NOTE: usable_conns2 uses the per-pair criterion (27.44/CUESIZE per pair). The project's own analysis
# suggests the better test is the summed conductance over a CUESIZE cue >= 27.44 nS per non-cue member.
# Raw counts and sums are therefore stored so that other criteria can be derived offline.
def extended_connection_labels(MySim, targets:dict, runID:int=-1, vizdir:str='', infer_unknown:bool=True)->dict:
    global batchrun
    result = {'usable_pyr_int': -1, 'usable_int_pyr': -1, 'usable_int_int': -1,
              'frac_int_driven': -1.0, 'frac_pyr_inhibited': -1.0, 'frac_pyr_inhibited_w05': -1.0, 'rawcounts': {}}
    try:
        conn = MySim.GetConnectome(Pause_s=0.1)
        batchrun.RTsuccess('getconn')
        absconn = MySim.GetAbstractConnectome(Sparse=True, Pause_s=0.1)
        batchrun.RTsuccess('getabsconn')
        somapos = MySim.GetSomaPositions()
    except Exception as e:
        print('NES error: failed to receive connectome/positions for extended labels: %s' % str(e))
        batchrun.RTfailed('getconn_failed', 'Extended labels, Exception: %s' % str(e))
        return result

    N = len(conn['ConnectionTargets'])
    ntypes = list(absconn.get('Types', []))
    stypes = list(somapos.get('SomaTypes', []))
    celltype = []
    for n in range(N):
        t = int(ntypes[n]) if n < len(ntypes) else 0
        if t == NEURON_UNKNOWN and n < len(stypes):
            t = int(stypes[n])
        celltype.append(t)
    # NES infers a neuron's type from the transmitter of its outgoing connections, so a neuron without any
    # outgoing connection is reported as type 0. In the Netmorph autoassociative model pyramidal cells always
    # have outgoing AMPA connections, and (verified on the smoke test) the number of type-0 neurons equals
    # configured interneurons minus typed interneurons, so type-0 neurons are inferred to be interneurons.
    num_unknown = celltype.count(NEURON_UNKNOWN)
    if infer_unknown:
        celltype = [NEURON_INTERNEURON if t == NEURON_UNKNOWN else t for t in celltype]

    # Raw census of every (pre class, post class, connection type) combination.
    census = {}   # key -> {'connections':, 'pairs': set, 'g_peak_sum':, 'num_receptors':}
    pairg = {}    # (pre, post, conntype) -> summed g_peak_sum
    for pre in range(N):
        for i, post in enumerate(conn['ConnectionTargets'][pre]):
            ct = int(conn['ConnectionTypes'][pre][i])
            g = float(conn['ConnectionGPeakSum'][pre][i])
            key = '%s->%s:%d' % (_CLASSNAME.get(celltype[pre], 'unk'), _CLASSNAME.get(celltype[post], 'unk'), ct)
            c = census.setdefault(key, {'connections': 0, 'pairs': set(), 'g_peak_sum_nS': 0.0, 'num_receptors': 0})
            c['connections'] += 1
            c['pairs'].add((pre, post))
            c['g_peak_sum_nS'] += g
            c['num_receptors'] += int(conn['NumReceptors'][pre][i])
            pairg[(pre, post, ct)] = pairg.get((pre, post, ct), 0.0) + g

    def count_at_target(prec, postc, ct, target):
        return int(sum(1 for (pre, post, t), g in pairg.items()
                       if t == ct and celltype[pre] == prec and celltype[post] == postc and g >= target))

    result['usable_pyr_int'] = count_at_target(NEURON_PRINCIPAL, NEURON_INTERNEURON, CONN_AMPA, targets['PYRINT_TARGET_nS'])
    result['usable_int_pyr'] = count_at_target(NEURON_INTERNEURON, NEURON_PRINCIPAL, CONN_GABA, targets['INTPYR_TARGET_nS'])
    result['usable_int_int'] = count_at_target(NEURON_INTERNEURON, NEURON_INTERNEURON, CONN_GABA, targets['INTINT_TARGET_nS'])
    # Aggregate labels: total incoming g_peak_sum onto each target neuron, summed over all presynaptic partners of the class
    inAMPA_fromPyr = [0.0]*N   # per post neuron
    inGABA_fromInt = [0.0]*N
    for (pre, post, ct), g in pairg.items():
        if ct == CONN_AMPA and celltype[pre] == NEURON_PRINCIPAL:
            inAMPA_fromPyr[post] += g
        elif ct == CONN_GABA and celltype[pre] == NEURON_INTERNEURON:
            inGABA_fromInt[post] += g
    ints = [n for n in range(N) if celltype[n] == NEURON_INTERNEURON]
    pyrs = [n for n in range(N) if celltype[n] == NEURON_PRINCIPAL]
    pi_t = targets['PYRINT_AGG_TARGET_nS']
    ip_t = targets['INTPYR_AGG_TARGET_nS']
    ipw = targets['INTPYR_AGG_WEIGHT']
    tol = 1e-9
    result['frac_int_driven'] = (sum(1 for n in ints if inAMPA_fromPyr[n] >= pi_t - tol)/len(ints)) if ints else 0.0
    result['frac_pyr_inhibited'] = (sum(1 for n in pyrs if inGABA_fromInt[n] >= ip_t - tol)/len(pyrs)) if pyrs else 0.0
    result['frac_pyr_inhibited_w05'] = (sum(1 for n in pyrs if inGABA_fromInt[n] >= ip_t*ipw - tol)/len(pyrs)) if pyrs else 0.0
    result['rawcounts'] = {
        'agg_int_incoming_AMPA_from_pyr_nS': {'mean': float(np.mean([inAMPA_fromPyr[n] for n in ints])) if ints else 0.0,
                                              'max': float(max([inAMPA_fromPyr[n] for n in ints])) if ints else 0.0,
                                              'per_neuron': [inAMPA_fromPyr[n] for n in ints]},
        'agg_pyr_incoming_GABA_from_int_nS': {'mean': float(np.mean([inGABA_fromInt[n] for n in pyrs])) if pyrs else 0.0,
                                              'max': float(max([inGABA_fromInt[n] for n in pyrs])) if pyrs else 0.0,
                                              'per_neuron': [inGABA_fromInt[n] for n in pyrs]},
        'n_int_with_zero_incoming_AMPA_from_pyr': sum(1 for n in ints if inAMPA_fromPyr[n] == 0),
        'n_pyr_with_zero_incoming_GABA_from_int': sum(1 for n in pyrs if inGABA_fromInt[n] == 0),
        'num_neurons': N,
        'num_pyramidal': celltype.count(NEURON_PRINCIPAL),
        'num_interneurons': celltype.count(NEURON_INTERNEURON),
        'num_unknown_type_reported_by_NES': num_unknown,
        'unknown_inferred_as_interneuron': infer_unknown,
        'targets_nS': targets,
        'classes': {k: {'connections': v['connections'], 'pairs': len(v['pairs']),
                        'g_peak_sum_nS': v['g_peak_sum_nS'], 'num_receptors': v['num_receptors'],
                        'max_pair_g_peak_sum_nS': max(pairg[(a, b, int(k.split(':')[1]))] for (a, b) in v['pairs'])}
                    for k, v in sorted(census.items())},
    }
    print('Extended labels: pyr->int %d, int->pyr %d, int->int %d, frac_int_driven %.3f, frac_pyr_inhibited %.3f (w05: %.3f)' % (result['usable_pyr_int'], result['usable_int_pyr'], result['usable_int_int'], result['frac_int_driven'], result['frac_pyr_inhibited'], result['frac_pyr_inhibited_w05']))

    if vizdir:
        try:
            save_viz_data(vizdir, runID, conn, absconn, somapos, celltype)
        except Exception as e:
            print('WARNING: could not save visualization data: %s' % str(e))
    return result

# Save abstract connectome + positions for the JS visualizer. Schema: see viz_data/SCHEMA.md
def save_viz_data(vizdir:str, runID:int, conn:dict, absconn:dict, somapos:dict, celltype:list):
    Path(vizdir).mkdir(parents=True, exist_ok=True)
    N = len(celltype)
    regionof = {}
    for rname, ids in absconn.get('Regions', {}).items():
        for nid in ids:
            regionof[int(nid)] = rname
    centers = somapos.get('SomaCenters', [])
    radii = somapos.get('SomaRadius', [])
    stypes = somapos.get('SomaTypes', [])
    neurons = []
    for n in range(N):
        c = centers[n] if n < len(centers) else [None, None, None]
        neurons.append({
            'id': n,
            'soma_type': int(celltype[n]),
            'soma_type_name': {0: 'unknown', 1: 'principal', 2: 'interneuron'}.get(int(celltype[n]), 'unknown'),
            'soma_type_from_positions': int(stypes[n]) if n < len(stypes) else None,
            'region': regionof.get(n),
            'x': c[0], 'y': c[1], 'z': c[2],
            'soma_radius': radii[n] if n < len(radii) else None,
        })
    # Abstract connectome (sparse): [pre, post, num_receptors]
    numrec = {(int(a), int(b)): int(r) for a, b, r in absconn.get('PrePostNumReceptors', [])}
    # Detailed connectome: one entry per (pre, post, type) with summed g_peak_sum
    agg = {}
    for pre in range(N):
        for i, post in enumerate(conn['ConnectionTargets'][pre]):
            ct = int(conn['ConnectionTypes'][pre][i])
            e = agg.setdefault((pre, int(post), ct), {'num_receptors': 0, 'g_peak_sum': 0.0, 'weight': 0.0})
            e['num_receptors'] += int(conn['NumReceptors'][pre][i])
            e['g_peak_sum'] += float(conn['ConnectionGPeakSum'][pre][i])
            e['weight'] += float(conn['ConnectionWeights'][pre][i])
    connections = [{'pre': a, 'post': b, 'type': t, 'type_name': {1: 'AMPA', 2: 'GABA', 3: 'NMDA'}.get(t, 'unknown'),
                    'num_receptors': e['num_receptors'], 'g_peak_sum': e['g_peak_sum'], 'weight_sum': e['weight']}
                   for (a, b, t), e in sorted(agg.items())]
    doc = {
        'schema_version': 1,
        'run_id': runID,
        'regions': {k: [int(x) for x in v] for k, v in absconn.get('Regions', {}).items()},
        'neurons': neurons,
        'connections': connections,
        'abstract_pair_receptors': [{'pre': a, 'post': b, 'num_receptors': r} for (a, b), r in sorted(numrec.items())],
    }
    path = Path(vizdir) / ('sample_%04d.json' % runID)
    with open(path, 'w') as f:
        json.dump(doc, f)
    print('Saved visualization data to %s' % str(path))

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
        # *** Maybe turn tracking back on for this failure if there are fewer when there isn't a connection drop.
        batchrun.RTfailed('netmorphstatus_failed', None) # Was (can be way too many): 'Exception: %s' % str(e) )
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
        result1 = int(usable_connections_method1(MySim))
        result2 = int(usable_connections_method2(MySim, evalcriteriadata['PREPOSTGPEAKSUMTARGET']))
        if result1 == -1 or result2 == -1:
            check_succeeded = False
        netmorphrun['usable_conns1'] = result1
        netmorphrun['usable_conns2'] = result2
        ext = extended_connection_labels(MySim, evalcriteriadata['EXTENDEDTARGETS'], netmorphrun['runID'], evalcriteriadata['vizdir'], evalcriteriadata['infer_unknown'])
        netmorphrun['usable_pyr_int'] = ext['usable_pyr_int']
        netmorphrun['usable_int_pyr'] = ext['usable_int_pyr']
        netmorphrun['usable_int_int'] = ext['usable_int_int']
        for k in ('frac_int_driven', 'frac_pyr_inhibited', 'frac_pyr_inhibited_w05'):
            netmorphrun[k] = ext[k]
        netmorphrun['rawcounts'] = ext['rawcounts']
        if ext['usable_pyr_int'] == -1:
            check_succeeded = False
        return 'completed', 100.0, check_succeeded

    return 'running', Percent, True

# HARD LIMITS from the team's docs. Parameters must never leave these (see NetmorphParOptim/bio_ranges.json).
# Order of pars: days, pyramidal, interneuron, minneuronseparation, shape.radius, shape.thickness, dm.weight
HARD_LIMITS = [('days', 20, 25), ('In.pyramidal', 16, 128), ('In.interneuron', 16, 128), ('In.minneuronseparation', 10, 15),
               ('In.shape.radius', 100, 200), ('In.shape.thickness', 20, 50), ('all_axons.axondm.dm_weight', 0.1, 1.0)]
def assert_within_hard_limits(pars:list, idx:int):
    for (name, lo, hi), v in zip(HARD_LIMITS, pars):
        # dm_weight is written with %.1f, so check the value that will actually be sent
        vv = round(float(v), 1) if name.endswith('dm_weight') else v
        if not (lo - 1e-9 <= vv <= hi + 1e-9):
            raise ValueError('Sample %d: %s=%s outside hard limits [%s, %s]; refusing to run' % (idx, name, v, lo, hi))

def extra_prep(batchinfo:dict, idx:int, extraprepdata:dict)->bool:
    modelname = extraprepdata['modelname']+'%04d' % idx
    batchinfo[idx]['modelname'] = modelname  # Remember which output model belongs to this run

    # Get parameters from data frame
    # This needs to be careful, because the data might be provided in a different order of
    # parameters and some parameters might be missing, needing default values.
    df = extraprepdata['dataframe']
    cols = extraprepdata['cols'] # This is an 'Index' object with a list of strings containing column names.
    pars = []
    if 'days' in cols:
        pars.append(int(df.iloc[idx]['days']))
    else:
        print('Missing "days" column. Using default: 21')
        pars.append(21)
    if 'pyramidal' in cols:
        pyramidal = int(df.iloc[idx]['pyramidal'])
    else:
        pyramidal = extraprepdata['launchdata']['EMBEDMULTIPLE']*extraprepdata['launchdata']['PATTERNSIZE']*extraprepdata['launchdata']['Patterns']
        print('Missing "pyramidal" column. Using default: %d' % pyramidal)
    pars.append(pyramidal)
    if 'interneuron' in cols:
        interneuron = int(df.iloc[idx]['interneuron'])
    else:
        interneuron = extraprepdata['launchdata']['PATTERNSIZE']*extraprepdata['launchdata']['Patterns']
        print('Missing "interneuron" column. Using default: %d' % interneuron)
    pars.append(interneuron)
    if 'minneuronseparation' in cols:
        pars.append(int(df.iloc[idx]['minneuronseparation']))
    else:
        print('Missing "minneuronseparation" column. Using default: 15')
        pars.append(15)
    if 'shape.radius' in cols:
        pars.append(int(df.iloc[idx]['shape.radius']))
    else:
        # V_shape = pi*r^2*h, h is either given or assumed 30 ==> r^2 = V_shape / (pi*h)
        # V_soma = 4/3*pi*r^3, assuming average soma r = 10 um ==> 4188.7902
        if 'shape.thickness' in cols:
            h = int(df.iloc[idx]['shape.thickness'])
        else:
            h = 30
        V_all_somas = 4200 * (pyramidal + interneuron)
        V_shape = V_all_somas * 2
        r2 = V_shape / (3.14*h)
        r = np.sqrt(r2)
        print('Missing "shape.radius" column. Using default: %d' % r)
        pars.append(int(r))
    if 'shape.thickness' in cols:
        pars.append(int(df.iloc[idx]['shape.thickness']))
    else:
        print('Missing "shape.thickness" column. Using default: 30')
        pars.append(30)
    if 'dm.weight' in cols:
        pars.append(round(float(df.iloc[idx]["dm.weight"]), 1))  # sent as %.1f
    else:
        print('Missing "dm.weight" column. Using default: 0.5')
        pars.append(float(0.5))

    assert_within_hard_limits(pars, idx)
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
    sample_modelcontent += RANDOMSEED % launchdata['randomseed']
    return sample_modelcontent


def sample_launch_requests(netmorphrun:dict, launchdata:dict)->bool:
    global batchrun
    sample_modelcontent = get_sample_modelcontent(launchdata, netmorphrun['pars'])
    print('Directives appended for run %d (sent to Netmorph):%s' % (netmorphrun['runID'], sample_modelcontent[len(launchdata['modelcontent']):].replace('\n', ' ')))

    MySim = netmorphrun['Sim']
    print('NES_SIM_ID=%s' % getattr(MySim, 'ID', '?'), flush=True)
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
    print('...launched Nemorph run with data sample ID %d' % netmorphrun['runID'])
    return True

# Update the ExpsDB.json database for all samples in the batch
def update_experiments_database(batchinfo:dict):
    for netmorphrun in batchinfo.values():
        if 'DBdata' in netmorphrun and netmorphrun['status'] != 'prepped': # only ones that were just run and completed or failed
            vbp.UpdateExpsDB(netmorphrun['DBdata'])

# Save resulting label data for all completed runs to excel file
# Note that this retrieves only what was stored in batchinfo_completed.json
# to create the Excel file.
def write_excel_with_results(batchrun, df, Args):
    df['usable_conns1']=0 # add column
    df['usable_conns2']=0 # add column
    NEWCOLS = ['usable_pyr_int', 'usable_int_pyr', 'usable_int_int', 'frac_int_driven', 'frac_pyr_inhibited', 'frac_pyr_inhibited_w05']
    for c in NEWCOLS:
        df[c] = 0.0 if c.startswith('frac_') else 0
    completed_batchinfo = batchrun.get_previously_completed()
    for netmorphrun in completed_batchinfo.values():
        if netmorphrun['status'] == 'completed':
            df.loc[netmorphrun['runID'], 'usable_conns1'] = netmorphrun['usable_conns1']
            df.loc[netmorphrun['runID'], 'usable_conns2'] = netmorphrun['usable_conns2']
            for c in NEWCOLS:
                df.loc[netmorphrun['runID'], c] = netmorphrun.get(c, -1)
        else:
            df.loc[netmorphrun['runID'], 'usable_conns1'] = -1
            df.loc[netmorphrun['runID'], 'usable_conns2'] = -1
            for c in NEWCOLS:
                df.loc[netmorphrun['runID'], c] = -1

    path = Path(Args.excel)
    labeledpath = Args.out if Args.out else str(path.with_suffix(""))+'-labeled-RS'+str(Args.randomseed)+'.xlsx'
    df.to_excel(labeledpath, index=False)
    rawpath = str(Path(labeledpath).with_suffix(''))+'-rawcounts.json'
    with open(rawpath, 'w') as f:
        json.dump({str(k): {'runID': v['runID'], 'status': v['status'], 'pars': v.get('pars'), 'rawcounts': v.get('rawcounts'),
                            'labels': {c: v.get(c) for c in ['usable_conns1', 'usable_conns2']+NEWCOLS}}
                   for k, v in sorted(completed_batchinfo.items())}, f, indent=1)
    print('Raw counts written to: '+rawpath)
    print('Results written to: '+labeledpath)
    print('Note that RS%d in the file name specifies the random seed used.')
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
    In.interneuron=%d;
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

    RANDOMSEED='''
    randomseed=%d;
    '''

    # List of batch keys to store and retrieve across potential multiple restarts of this script
    BATCHDATAKEYS = [
        "modelname",
        "pars",
        "usable_conns1",
        "usable_conns2",
        "usable_pyr_int",
        "usable_int_pyr",
        "usable_int_int",
        "frac_int_driven",
        "frac_pyr_inhibited",
        "frac_pyr_inhibited_w05",
        "rawcounts",
    ]

    RESOURCESLOWBYTES = 2*1024*1024*1024 # 2GB

    Args = get_Args()

    if Args.randomseed == 0:
        Args.randomseed = random.randint(1, 99999999)
    print('Random seed is: '+str(Args.randomseed))

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
        "savemodels": Args.savemodels,
        "vizdir": Args.vizdir,
        "infer_unknown": not Args.KEEPUNKNOWNTYPE,
        "EXTENDEDTARGETS": {
            "PYRINT_TARGET_nS": Args.PYRINT_TARGET_nS if Args.PYRINT_TARGET_nS is not None else Args.MINSYNAPSES*Args.GPEAKAMPA_PERSYN_nS,
            "INTPYR_TARGET_nS": Args.INTPYR_TARGET_nS if Args.INTPYR_TARGET_nS is not None else Args.MINSYNAPSES*Args.GPEAKGABA_PERSYN_nS,
            "INTINT_TARGET_nS": Args.INTINT_TARGET_nS if Args.INTINT_TARGET_nS is not None else Args.MINSYNAPSES*Args.GPEAKGABA_PERSYN_nS,
            "PYRINT_AGG_TARGET_nS": Args.PYRINT_AGG_TARGET_nS,
            "INTPYR_AGG_TARGET_nS": Args.INTPYR_AGG_TARGET_nS,
            "INTPYR_AGG_WEIGHT": Args.INTPYR_AGG_WEIGHT,
        },
    }

    modelcontent = LoadNetmorphConfiguration(Args.modelfile)

    LAUNCHDATA = {
        'modelcontent': modelcontent,
        'EMBEDMULTIPLE': Args.EMBEDMULTIPLE,
        'PATTERNSIZE': Args.PATTERNSIZE,
        'Patterns': Args.Patterns,
        'Dt': Args.Dt,
        'STDP': Args.STDP,
        'randomseed': Args.randomseed,
    }
    EXTRAPREPDATA['launchdata'] = LAUNCHDATA

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

    # Let's add a bit of extra tracking while we're testing large batches
    batchrun.resource_tests['getconn'] = 0
    batchrun.resource_tests['getconn_failed'] = 0
    batchrun.resource_tests['getabsconn'] = 0
    batchrun.resource_tests['getabsconn_failed'] = 0
    batchrun.resource_tests['modelsave'] = 0
    batchrun.resource_tests['modelsave_failed'] = 0
    batchrun.resource_tests['launch'] = 0
    batchrun.resource_tests['launch_failed'] = 0
    batchrun.resource_tests['netmorphstatus'] = 0
    batchrun.resource_tests['netmorphstatus_failed'] = 0

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

    completed_batchinfo = write_excel_with_results(batchrun, df, Args)

    docompare = input('Shall we compare the results from the two label interpretation methods? (y/N) ')
    if docompare == 'y':
        print("Let's compare the results from the two label interpretation methods:")
        sorted_batchinfo = {k: completed_batchinfo[k] for k in sorted(completed_batchinfo)}
        for netmorphrun in sorted_batchinfo.values():
            print('%03d %05d %05d' % (netmorphrun['runID'], netmorphrun['usable_conns1'], netmorphrun['usable_conns2']))

    print('Inspect resource_checks.json for request success/failure tracking data.')
    if remaining > 0:
        print('To complete remaining simply rerun this script.')
    else:
        print('To run batch again, move or delete batchinfo_completed.json.')

    if not completed_batch:
        print('PLEASE NOTE:\nThis batch did NOT complete. Possible API/NES server problem detected!\nSolve the problem and rerun to complete.')

    print(" -- Done.")
    exit(0)

#!../../../venv/bin/python
# analyze_connectome.py
# Loads the already-saved "mushroombody" model (no regrow) and reports
# PN->KC and KC->MBON in-degree statistics from its connectome.

import argparse
import numpy as np
import vbpcommon as vbp
from BrainGenix.BG_API import NES

Parser = argparse.ArgumentParser()
Parser.add_argument("-Host", default="localhost", type=str)
Parser.add_argument("-Port", default=8000, type=int)
Parser.add_argument("-UseHTTPS", default=False, type=bool)
Parser.add_argument("-modelname", default="mushroombody", type=str)
Parser.add_argument("-NumPN", default=50, type=int, help="Number of PN cells (must match what was actually grown)")
Parser.add_argument("-NumKC", default=2000, type=int, help="Number of KC cells (must match what was actually grown)")
Parser.add_argument("-NumMBON", default=34, type=int, help="Number of MBON cells (must match what was actually grown)")
Args = Parser.parse_args()

ClientCfg = NES.Client.Configuration()
ClientCfg.Mode = NES.Client.Modes.Remote
ClientCfg.Host = Args.Host
ClientCfg.Port = Args.Port
ClientCfg.UseHTTPS = Args.UseHTTPS
ClientCfg.AuthenticationMethod = NES.Client.Authentication.Password
ClientCfg.Username = "Admonishing"
ClientCfg.Password = "Instruction"

print(" -- Creating Client Instance")
ClientInstance = NES.Client.Client(ClientCfg)
if not ClientInstance.IsReady():
    print("Client not ready.")
    exit(1)

print(" -- Creating Simulation")
SimulationCfg = NES.Simulation.Configuration()
SimulationCfg.Name = "Netmorph-"+Args.modelname
SimulationCfg.Seed = 0
MySim = ClientInstance.CreateSimulation(SimulationCfg)

print(" -- Loading model: "+Args.modelname)
try:
    MySim.ModelLoad(Args.modelname)
except Exception as e:
    print(" -- ModelLoad FAILED:", repr(e))
    exit(1)

print(" -- Fetching connectome")
try:
    connections_dict = MySim.GetConnectome()
except Exception as e:
    print(" -- GetConnectome FAILED:", repr(e))
    exit(1)

numneurons = len(connections_dict["ConnectionGPeakSum"])
print(" -- Total neurons in connectome: %d" % numneurons)
expected_total = Args.NumPN + Args.NumKC + Args.NumMBON
if numneurons != expected_total:
    print(" -- WARNING: total neurons (%d) does not match NumPN+NumKC+NumMBON (%d)."
          " The population index ranges below are likely WRONG -- check actual"
          " population sizes (e.g. via Netmorph's .neurons output file) before"
          " trusting these numbers." % (numneurons, expected_total))


def get_population_indices(num_pn:int, num_kc:int, num_mbon:int)->dict:
    pn_idx = list(range(0, num_pn))
    kc_idx = list(range(num_pn, num_pn + num_kc))
    mbon_idx = list(range(num_pn + num_kc, num_pn + num_kc + num_mbon))
    return {'PN': pn_idx, 'KC': kc_idx, 'MBON': mbon_idx}


def get_convergence_stats(connections_dict:dict, pre_idx:list, post_idx:list)->tuple:
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
            if types[pre][i] != 1:  # AMPA only
                continue
            post = targets[pre][i]
            if post not in post_set:
                continue
            gpeaksummatrix[pre_pos[pre]][post_pos[post]] += gpeaksum[pre][i]
            if post not in seen_posts_for_this_pre:
                indegree[post] += 1
                seen_posts_for_this_pre.add(post)

    return indegree, gpeaksummatrix


populations = get_population_indices(Args.NumPN, Args.NumKC, Args.NumMBON)

pn_to_kc_indegree, pn_kc_gpeaksum = get_convergence_stats(connections_dict, populations['PN'], populations['KC'])
kc_to_mbon_indegree, kc_mbon_gpeaksum = get_convergence_stats(connections_dict, populations['KC'], populations['MBON'])

pn_to_kc_values = list(pn_to_kc_indegree.values())
kc_to_mbon_values = list(kc_to_mbon_indegree.values())

print("\n=== PN -> KC convergence ===")
if len(pn_to_kc_values) > 0:
    print('mean=%.2f, min=%d, max=%d  (target ~7 for pattern separation)' % (
        float(np.mean(pn_to_kc_values)), min(pn_to_kc_values), max(pn_to_kc_values)))
    print('Distribution (indegree: count of KCs with that indegree):')
    from collections import Counter
    for k, v in sorted(Counter(pn_to_kc_values).items()):
        print('  %3d PN inputs -> %4d KCs' % (k, v))
else:
    print('No KC neurons found -- check population index assumption / NumPN/NumKC/NumMBON args')

print("\n=== KC -> MBON convergence ===")
if len(kc_to_mbon_values) > 0:
    print('mean=%.2f, min=%d, max=%d  (target: dense/near-complete)' % (
        float(np.mean(kc_to_mbon_values)), min(kc_to_mbon_values), max(kc_to_mbon_values)))
else:
    print('No MBON neurons found -- check population index assumption / NumPN/NumKC/NumMBON args')

print("\n -- Done.")

import sys, json, numpy as np
sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe'); sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe_v2/ripple_S1')
import recipelib as L
from slib import dump, N
L.guard_memory(); NES, client = L.connect()
c = NES.Simulation.Configuration(); c.Name='S1-gabaPatchTestA'; c.Seed=0
sim = client.CreateSimulation(c); sid = sim.ID; assert sid >= 0; print('SIM_ID', sid, flush=True)
out = dict(sim_id=sid)
try:
    sim.SetLIFCAbstractedFunctional(_AbstractedFunctional=True); sim.SetSTDP(_DoSTDP=False)
    out['modelload_response'] = str(sim.ModelLoad('v2-arbor-S1-gabax2'))[:200]
    conn = sim.GetConnectome(Pause_s=0.1)
    W = {1: [], 2: [], 3: []}; gp = {1: [], 2: [], 3: []}; bad = 0; seen = 0
    for pre in range(len(conn['ConnectionTargets'])):
        for i, post in enumerate(conn['ConnectionTargets'][pre]):
            t = int(conn['ConnectionTypes'][pre][i]); w = float(conn['ConnectionWeights'][pre][i]); g = float(conn['ConnectionGPeakSum'][pre][i])
            W[t].append(w); gp[t].append(g)
            ref = (dump.GA if t == 2 else dump.G)[pre, int(post)] if t in (1, 2) else None
            if ref is not None:
                seen += 1
                if abs(ref - g) > 1e-3 * max(1, ref): bad += 1
    out['n_neurons'] = len(sim.GetSomaPositions().get('SomaCenters', []))
    for t, nm in [(1, 'AMPA'), (2, 'GABA'), (3, 'NMDA')]:
        out[nm] = dict(n_pairs=len(W[t]), weights_unique=sorted(set(round(x, 4) for x in W[t])), gpeak_sum_total=round(sum(gp[t]), 2))
    out['gpeak_mismatch_vs_original_dump'] = bad; out['pairs_compared'] = seen
    gw = np.array(W[2]); gg = np.array(gp[2]); out['GABA_pair_conductance_total_nS_now'] = float((gw * gg).sum()); out['GABA_pair_conductance_total_nS_original'] = float(0.2 * gg.sum())
    out['ratio'] = out['GABA_pair_conductance_total_nS_now'] / out['GABA_pair_conductance_total_nS_original']
finally:
    try: out['deleted'] = str(sim.DeleteResidentByID(Pause_s=0.1)); print('deleted', sid, out['deleted'])
    except Exception as e: print('DELETE FAILED', sid, e)
json.dump(out, open('testA_result.json', 'w'), indent=1); print(json.dumps(out, indent=1))

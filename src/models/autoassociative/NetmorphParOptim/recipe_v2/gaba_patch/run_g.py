"""usage: run_g.py TAG MODELNAME FACTOR PAIRS SG(0|1) KIND  (KIND as in ripple_S1_R3/run_r3.py) -> raw_TAG.json. Reuses R3 recipe unchanged; only the model differs."""
import sys, json
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/ripple_S1_R3')
import r3lib
from r3lib import *
tag, model, fac, pname, sg, kind = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4], sys.argv[5] == '1', sys.argv[6]
OUTD = '/home/johnjose/cos/netmorph_work/recipe_v2/gaba_patch/'
def fresh_copy_g(NES, client, name, ref_pairs):
    c = NES.Simulation.Configuration(); c.Name = name; c.Seed = 0
    sim = client.CreateSimulation(c); assert sim.ID >= 0
    sim.SetLIFCAbstractedFunctional(_AbstractedFunctional=True); sim.SetLIFCPreciseSpikeTimes(_UsePreciseSpikeTimes=True); sim.SetSTDP(_DoSTDP=False)
    sim.ModelLoad(model)
    n = len(sim.GetSomaPositions().get('SomaCenters', []))
    conn = sim.GetConnectome(Pause_s=0.1); ampa = {}; wa = set(); wg = set()
    for pre in range(len(conn['ConnectionTargets'])):
        for i, post in enumerate(conn['ConnectionTargets'][pre]):
            t = int(conn['ConnectionTypes'][pre][i]); w = round(float(conn['ConnectionWeights'][pre][i]), 3)
            if t == 2: wg.add(w)
            else: wa.add(w)
            if t == 1: ampa[(pre, int(post))] = float(conn['ConnectionGPeakSum'][pre][i])
    miss = [k for k in ref_pairs if k not in ampa]
    gbad = [k for k in ref_pairs if k in ampa and abs(ampa[k] - ref_pairs[k]) > 1e-3 * max(1.0, ref_pairs[k])]
    ok = (n == N and not miss and not gbad and wa == {0.2} and wg == {round(0.2 * fac, 3)})
    return sim, dict(sim_id=sim.ID, model=model, n_neurons=n, ampa_nmda_weights_on_load=sorted(wa), gaba_weights_on_load=sorted(wg), pairs_missing=len(miss), g_mismatch=len(gbad), loaded_ok=bool(ok))
r3lib.fresh_copy = fresh_copy_g
NES, client = L.connect()
p = kind.split(':')
if p[0] == 'single': e = single_run(NES, client, tag, pname, sg)
else:
    rec = 'rec' in p[1:]; q = [x for x in p if x != 'rec']
    e = ripple_run(NES, client, tag, pname, sg, [int(c) for c in q[1]], float(q[2]), float(q[3]), cue3=(int(q[4]) if len(q) > 4 else None), record=rec)
e.update(name=tag, pairs=pname, sg=sg, factor=fac, model=model)
json.dump(e, open(OUTD + 'raw_%s.json' % tag, 'w'), separators=(',', ':'))

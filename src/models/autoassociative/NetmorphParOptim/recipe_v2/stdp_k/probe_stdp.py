#!/usr/bin/env python3
"""CAPABILITY PROBE (not experiment data): does Simulation/SetSTDP work on a loaded E4 model, on which receptors, with what sign/timing dependence?
Forced pre/post spike pairs (distinct strong Pyr->Pyr pairs of s33333), 20 pairings each, STDP on; weights read back with GetConnectome. Patched instance only."""
import sys, json
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/ripple_overlap_j'); sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe'); sys.path.insert(0, '/home/johnjose/BrainGenix/BrainEmulationChallenge/PythonClient')
import numpy as np, ovlib as O, recipelib as L
import run_sim as R
stdp_on = sys.argv[1] == '1'
D, P = O.load('s33333'); model = O.MODELS['s33333']['model']
# strong pairs a->b with distinct cells
cand = [(a, b) for a in range(96) for b in range(96) if a != b and P[a, b] >= 4.125]
used = set(); pairs = []
for a, b in cand:
    if a in used or b in used: continue
    pairs.append((a, b)); used |= {a, b}
dts = [1, 3, 6, 10, 20, 50, -3, -8, -20][:len(pairs)]; pairs = pairs[:len(dts)]
NES, client = R.connect(); cf = NES.Simulation.Configuration(); cf.Name = 'stdp-probe'; cf.Seed = 0
sim = client.CreateSimulation(cf); sid = sim.ID
def weights():
    conn = sim.GetConnectome(Pause_s=0.1); out = {}
    for pre in range(len(conn['ConnectionTargets'])):
        for i, post in enumerate(conn['ConnectionTargets'][pre]):
            out[(pre, int(post), int(conn['ConnectionTypes'][pre][i]))] = float(conn['ConnectionWeights'][pre][i])
    return out
try:
    sim.SetLIFCAbstractedFunctional(_AbstractedFunctional=True); sim.SetLIFCPreciseSpikeTimes(_UsePreciseSpikeTimes=True)
    sim.SetSTDP(_DoSTDP=stdp_on); sim.ModelLoad(model)
    w0 = weights()
    ev = []; t = 20.0
    for k in range(20):
        for (a, b), dt in zip(pairs, dts):
            ev.append((t, a)); ev.append((t + dt, b))
        t += 100.0
    # shift so no negative times
    r = sim.SetSpecificAPTimes([(float(x), int(c)) for x, c in ev]); assert r.get('StatusCode', 1) == 0, r
    sim.RecordAll(-1); sim.RunAndWait(Runtime_ms=float(t + 50), Dt_ms=1.0, timeout_s=900.0)
    w1 = weights(); sp = sim.GetSpikeTimes()['SpikeTimes']
finally:
    print('deleted', sim.DeleteResidentByID())
res = []
for (a, b), dt in zip(pairs, dts):
    res.append(dict(pre=a, post=b, dt_ms=dt, G=float(P[a, b]), types={str(k[2]): (w0[k], w1[k]) for k in w0 if k[0] == a and k[1] == b}, rev=({str(k[2]): (w0[k], w1[k]) for k in w0 if k[0] == b and k[1] == a})))
allt = {}
for (a, b, ty), v in w0.items():
    allt.setdefault(ty, [0, 0]); allt[ty][0] += 1; allt[ty][1] += int(abs(w1[(a, b, ty)] - v) > 1e-6)
print(json.dumps(dict(stdp=stdp_on, pairs=res, changed_by_type=allt, n_spikes=sum(len(v['tSpike_ms']) for v in sp.values())), indent=1, default=float))

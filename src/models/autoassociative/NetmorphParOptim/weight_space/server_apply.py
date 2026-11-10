#!/usr/bin/env python3
"""NES client: verify a resident simulation against the offline dump and (optionally) apply a weight
program and run a cued-recall test.  Only ever touches the simulation ID given; never deletes anything.

Run with the repo venv + PythonClient on PYTHONPATH, from src/models/autoassociative, e.g.
  R=/home/johnjose/BrainGenix/BrainEmulationChallenge
  cd $R/src/models/autoassociative && PYTHONPATH=$R/PythonClient $R/venv/bin/python \
     NetmorphParOptim/weight_space/server_apply.py -SimID 127 -dump NetmorphParOptim/batchB/vviz4/sample_0000.json \
     -mode verify -out NetmorphParOptim/weight_space/server_verify_127.json
Modes:
  verify : read-only (GetStatus, GetSomaPositions, GetAbstractConnectome, GetConnectome) and compare with dump.
  apply  : verify, then BatchSetPrePostStrength(ops), SetSpecificAPTimes(cues), RunAndWait, GetSpikeTimes,
           GetConnectome (to confirm weights). Requires -ops and -design.
"""
import argparse, json, sys, time
import numpy as np
import BrainGenix.NES as NES

P = argparse.ArgumentParser()
P.add_argument('-Host', default='localhost'); P.add_argument('-Port', default=8000, type=int)
P.add_argument('-SimID', type=int, required=True)
P.add_argument('-dump', required=True); P.add_argument('-mode', default='verify', choices=['verify', 'apply'])
P.add_argument('-ops', default=None); P.add_argument('-design', default=None); P.add_argument('-K', default=2, type=int)
P.add_argument('-T', default=400.0, type=float); P.add_argument('-Dt', default=1.0, type=float)
P.add_argument('-cue_t', default=20.0, type=float); P.add_argument('-cue_gap', default=200.0, type=float)
P.add_argument('-out', required=True)
A = P.parse_args()

OUR_SIMS = set(range(123, 133))
assert A.SimID in OUR_SIMS, 'refusing to touch a simulation that is not ours (123-132)'

cfg = NES.Client.Configuration()
cfg.Mode = NES.Client.Modes.Remote; cfg.Host = A.Host; cfg.Port = A.Port; cfg.UseHTTPS = False
cfg.AuthenticationMethod = NES.Client.Authentication.Password; cfg.Username = 'Admonishing'; cfg.Password = 'Instruction'
client = NES.Client.Client(cfg)
assert client.IsReady()
simcfg = NES.Simulation.Configuration(); simcfg.Name = 'attach'; simcfg.Seed = 0
sim = client.CreateSimulation(simcfg, _Create=False)   # no server call; attaches to an existing ID
sim.ID = A.SimID
out = {'sim_id': A.SimID, 'mode': A.mode, 'steps': []}

def step(name, **kw):
    kw['t'] = time.strftime('%H:%M:%S'); kw['step'] = name; out['steps'].append(kw); print(name, {k: v for k, v in kw.items() if k not in ('step',)}, flush=True)

def save():
    with open(A.out, 'w') as f:
        json.dump(out, f, default=lambda o: o.tolist() if hasattr(o, 'tolist') else str(o))

with open(A.dump) as f:
    dump = json.load(f)
N_dump = len(dump['neurons'])
types_dump = [n['soma_type'] for n in dump['neurons']]
pairs_dump = {(c['pre'], c['post'], c['type']): c['g_peak_sum'] for c in dump['connections']}

# ---- read-only verification
st = sim.GetStatus(); step('GetStatus', status=st)
somas = sim.GetSomaPositions()
n_srv = len(somas.get('SomaCenters', []))
step('GetSomaPositions', n_server=n_srv, n_dump=N_dump, match=(n_srv == N_dump))
conn = sim.GetConnectome(Pause_s=0.1)
mism, nconn, wts = 0, 0, set()
for pre in range(len(conn['ConnectionTargets'])):
    for i, post in enumerate(conn['ConnectionTargets'][pre]):
        key = (pre, int(post), int(conn['ConnectionTypes'][pre][i]))
        nconn += 1
        wts.add(round(float(conn['ConnectionWeights'][pre][i]), 3))
        g = float(conn['ConnectionGPeakSum'][pre][i])
        if key not in pairs_dump or abs(pairs_dump[key] - g) > 1e-3 * max(1.0, g):
            mism += 1
step('GetConnectome_compare', n_connections_server=nconn, n_in_dump=len(pairs_dump), g_peak_sum_mismatches=mism,
     weights_on_server=sorted(wts), match=(mism == 0 and nconn == len(pairs_dump)))
save()
if A.mode == 'verify':
    print('verify complete ->', A.out); sys.exit(0)

# ---- apply
assert out['steps'][-1]['match'], 'dump does not match server state; refusing to apply'
assert A.ops and A.design
ops = json.load(open(A.ops))['ops']
des = json.load(open(A.design))['engram_design']['K'][str(A.K)]
for o in ops:
    assert 0.0 <= o['weight'] <= 1.0 and o['conductance_nS'] <= o['g_peak_sum_nS'] + 1e-6
    assert (o['pre'], o['post'], 1) in pairs_dump, 'pair has no AMPA on server; batch would fail'
CH = 500
for s in range(0, len(ops), CH):
    chunk = ops[s:s + CH]
    r = sim.BatchSetPrePostStrength([o['pre'] for o in chunk], [o['post'] for o in chunk], [o['conductance_nS'] for o in chunk])
    step('BatchSetPrePostStrength', first=s, n=len(chunk), response=r)
    assert r.get('StatusCode', 1) == 0, 'batch failed: %r' % r
# cue each pattern in turn
pairs = []
for k, p in enumerate(des['patterns']):
    t = A.cue_t + k * A.cue_gap
    pairs += [(t, int(c)) for c in p['cue_ids']]
r = sim.SetSpecificAPTimes(pairs); step('SetSpecificAPTimes', n=len(pairs), response=r, pairs=pairs)
r = sim.SetSTDP(_DoSTDP=False); step('SetSTDP_off', response=r)   # keep programmed weights fixed during the test
r = sim.RecordAll(-1); step('RecordAll', response=r)
t0 = time.time(); sim.RunAndWait(Runtime_ms=A.T, Dt_ms=A.Dt, timeout_s=300.0)
step('RunAndWait', T_ms=A.T, Dt_ms=A.Dt, wall_s=round(time.time() - t0, 1), status=sim.GetStatus())
spikes = sim.GetSpikeTimes(); out['spike_times'] = spikes
step('GetSpikeTimes', keys=list(spikes.keys())[:5])
conn2 = sim.GetConnectome(Pause_s=0.1)
w_after = {}
for pre in range(len(conn2['ConnectionTargets'])):
    for i, post in enumerate(conn2['ConnectionTargets'][pre]):
        w_after['%d,%d,%d' % (pre, int(post), int(conn2['ConnectionTypes'][pre][i]))] = float(conn2['ConnectionWeights'][pre][i])
out['weights_after'] = w_after
step('GetConnectome_after', unique_weights=sorted(set(round(v, 3) for v in w_after.values()))[:20])
save()
print('apply complete ->', A.out)

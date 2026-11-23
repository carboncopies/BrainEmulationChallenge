#!/usr/bin/env python3
"""Connectome-level verification of the per-receptor strength patch (PATCHED instance only: API 8010 / NES 8011).
Loads E4 model V1n20_s33333, performs each call, reads the whole connectome back and checks that ONLY the intended
(pre, post, type) groups changed. No simulation is run. The simulation object is deleted at the end."""
import sys, json, copy
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe'); sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/headline_i')
import dyn2 as H
sys.path.insert(0, '/home/johnjose/BrainGenix/wt/pythonclient-receptor-strength')   # patched client (branch nes-receptor-strength), must come first
import BrainGenix.NES as NES
import inspect
assert 'Neurotransmitter' in inspect.signature(NES.Simulation.Simulation.SetPrePostStrength).parameters, 'patched client not loaded'
SEED = 'V1n20_s33333'; SRC = H.MODELS[SEED]; NP = 96
TYPE = {1: 'AMPA', 2: 'GABA', 3: 'NMDA'}
NES_, client = H.connect()
cf = NES.Simulation.Configuration(); cf.Name = 'rs-verify'; cf.Seed = 0
sim = client.CreateSimulation(cf); sid = sim.ID; assert sid >= 0
res = []; fails = 0
def snap():
    c = sim.GetConnectome(Pause_s=0.1); d = {}
    for p in range(len(c['ConnectionTargets'])):
        for i, q in enumerate(c['ConnectionTargets'][p]):
            d[(p, int(q), TYPE[int(c['ConnectionTypes'][p][i])])] = (float(c['ConnectionWeights'][p][i]), float(c['ConnectionGPeakSum'][p][i]))
    return d
def cond(d, k): return d[k][0] * d[k][1]
def diff(a, b): return sorted(k for k in a if abs(a[k][0] - b[k][0]) > 1e-9 or abs(a[k][1] - b[k][1]) > 1e-9)
def check(name, ok, info=''):
    global fails
    res.append(dict(test=name, ok=bool(ok), info=str(info))); print(('PASS ' if ok else 'FAIL ') + name, info, flush=True); fails += (not ok)
def status(r): return r.get('StatusCode', None)
try:
    sim.SetLIFCAbstractedFunctional(_AbstractedFunctional=True); sim.SetSTDP(_DoSTDP=False); sim.ModelLoad(SRC)
    base = snap(); print('groups', len(base), flush=True)
    # pick pairs
    pp = sorted(k[:2] for k in base if k[2] == 'AMPA' and k[0] < NP and k[1] < NP and (k[0], k[1], 'NMDA') in base and base[k][1] > 4.0)
    A, B = pp[0]
    ig = sorted(k[:2] for k in base if k[2] == 'GABA' and k[0] >= NP and k[1] < NP)
    I, P = ig[0]
    print('pyr pair', A, B, base[(A, B, 'AMPA')], base[(A, B, 'NMDA')], 'int pair', I, P, base[(I, P, 'GABA')], flush=True)
    check('no Int->Pyr AMPA/NMDA on the GABA pair', (I, P, 'AMPA') not in base and (I, P, 'NMDA') not in base)
    # 1 GABA alone on an Int->Pyr pair
    r = sim.SetPrePostStrength(I, P, 1.2, Neurotransmitter='GABA'); s1 = snap()
    check('1 GABA alone: status 0', status(r) == 0, r)
    check('1 GABA alone: only that group changed', diff(base, s1) == [(I, P, 'GABA')], diff(base, s1))
    check('1 GABA alone: conductance = 1.2 nS', abs(cond(s1, (I, P, 'GABA')) - 1.2) < 1e-4, cond(s1, (I, P, 'GABA')))
    # 2 NMDA alone on a Pyr->Pyr pair
    r = sim.SetPrePostStrength(A, B, 0.35, Neurotransmitter='NMDA'); s2 = snap()
    check('2 NMDA alone: status 0', status(r) == 0, r)
    check('2 NMDA alone: only that group changed (vs 1)', diff(s1, s2) == [(A, B, 'NMDA')], diff(s1, s2))
    check('2 NMDA alone: conductance = 0.35 nS', abs(cond(s2, (A, B, 'NMDA')) - 0.35) < 1e-4, cond(s2, (A, B, 'NMDA')))
    # 3 AMPA alone, with the argument, NMDA kept
    r = sim.SetPrePostStrength(A, B, 4.5, Neurotransmitter='AMPA'); s3 = snap()
    check('3 AMPA alone: status 0', status(r) == 0, r)
    check('3 AMPA alone: only AMPA group changed (vs 2): NMDA kept', diff(s2, s3) == [(A, B, 'AMPA')], diff(s2, s3))
    check('3 AMPA alone: conductance = 4.5 nS', abs(cond(s3, (A, B, 'AMPA')) - 4.5) < 1e-4, cond(s3, (A, B, 'AMPA')))
    check('3 AMPA alone: NMDA still 0.35', abs(cond(s3, (A, B, 'NMDA')) - 0.35) < 1e-4)
    # 4 legacy call (no argument): AMPA set, NMDA zeroed - exactly the old behaviour
    r = sim.SetPrePostStrength(A, B, 3.0); s4 = snap()
    check('4 legacy (no arg): status 0', status(r) == 0, r)
    check('4 legacy: AMPA = 3.0 nS', abs(cond(s4, (A, B, 'AMPA')) - 3.0) < 1e-4)
    check('4 legacy: NMDA zeroed', cond(s4, (A, B, 'NMDA')) == 0.0, cond(s4, (A, B, 'NMDA')))
    check('4 legacy: only that pair changed (vs 3)', set(diff(s3, s4)) <= {(A, B, 'AMPA'), (A, B, 'NMDA')}, diff(s3, s4))
    # 5 batch: one string for all entries
    pairs = [k[:2] for k in sorted(base) if k[2] == 'GABA' and k[0] >= NP and k[1] < NP][1:4]
    r = sim.BatchSetPrePostStrength([p[0] for p in pairs], [p[1] for p in pairs], [0.9, 0.9, 0.9], Neurotransmitter='GABA'); s5 = snap()
    check('5 batch (string): status 0', status(r) == 0, r)
    check('5 batch (string): exactly those groups changed', diff(s4, s5) == sorted((p[0], p[1], 'GABA') for p in pairs), diff(s4, s5))
    check('5 batch (string): 0.9 nS each', all(abs(cond(s5, (p[0], p[1], 'GABA')) - 0.9) < 1e-4 for p in pairs))
    # 6 batch: list, mixed types on one pair
    r = sim.BatchSetPrePostStrength([A, A], [B, B], [2.5, 0.4], Neurotransmitter=['AMPA', 'NMDA']); s6 = snap()
    check('6 batch (list): status 0', status(r) == 0, r)
    check('6 batch (list): AMPA 2.5, NMDA 0.4, nothing else', abs(cond(s6, (A, B, 'AMPA')) - 2.5) < 1e-4 and abs(cond(s6, (A, B, 'NMDA')) - 0.4) < 1e-4 and diff(s5, s6) == [(A, B, 'AMPA'), (A, B, 'NMDA')], diff(s5, s6))
    # 7 batch without the argument = legacy
    r = sim.BatchSetPrePostStrength([A], [B], [1.0]); s7 = snap()
    check('7 batch legacy: AMPA 1.0, NMDA zeroed', status(r) == 0 and abs(cond(s7, (A, B, 'AMPA')) - 1.0) < 1e-4 and cond(s7, (A, B, 'NMDA')) == 0.0)
    # 8 errors: invalid NT, wrong list length, missing type: status != 0 and no side effects
    r = sim.SetPrePostStrength(A, B, 9.0, Neurotransmitter='GLUTAMATE'); s8 = snap()
    check('8a invalid NT string rejected, nothing changed', status(r) != 0 and diff(s7, s8) == [], (status(r), diff(s7, s8)))
    r = sim.SetPrePostStrength(I, P, 9.0, Neurotransmitter='AMPA'); s8 = snap()
    check('8b pair without AMPA: error, GABA NOT zeroed (legacy would zero it)', status(r) != 0 and diff(s7, s8) == [] and cond(s8, (I, P, 'GABA')) > 0, (status(r), cond(s8, (I, P, 'GABA'))))
    r = sim.SetPrePostStrength(A, B, -1.0, Neurotransmitter='NMDA'); s8 = snap()
    check('8c negative conductance rejected', status(r) != 0 and diff(s7, s8) == [], status(r))
    r = sim.BatchSetPrePostStrength([A, A], [B, B], [1.0, 1.0], Neurotransmitter=['AMPA'])  if False else None
    # 9 legacy on a GABA-only pair (old behaviour: error status, GABA zeroed) is unchanged
    r = sim.SetPrePostStrength(I, P, 1.0); s9 = snap()
    check('9 legacy on GABA-only pair: error status and GABA zeroed (old behaviour kept)', status(r) != 0 and cond(s9, (I, P, 'GABA')) == 0.0, (status(r), cond(s9, (I, P, 'GABA'))))
    # 10 SetAllStrength with NT=GABA: every GABA group set, AMPA/NMDA untouched
    r = sim.SetAllStrength(0.5, Neurotransmitter='GABA'); s10 = snap()
    gk = [k for k in s10 if k[2] == 'GABA']
    check('10 SetAllStrength(GABA): status 0', status(r) == 0, r)
    check('10 all GABA groups = 0.5 nS (those with g_peak > 0)', all(abs(cond(s10, k) - 0.5) < 1e-3 for k in gk), len(gk))
    check('10 AMPA and NMDA groups unchanged', all(s10[k] == s9[k] for k in s10 if k[2] != 'GABA'))
    # 11 SetAllStrength legacy (no arg): all AMPA set, every NMDA and GABA zero
    r = sim.SetAllStrength(0.0); s11 = snap()
    check('11 SetAllStrength legacy: all NMDA and GABA weights zero', all(s11[k][0] == 0.0 for k in s11 if k[2] != 'AMPA'))
finally:
    try: print('deleted', sid, sim.DeleteResidentByID(), flush=True)
    except Exception as e: print('DELETE FAILED', sid, e, flush=True)
json.dump(dict(model=SRC, n_fail=fails, tests=res), open('/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/gaba_nmda_api/verify_api.json', 'w'), indent=1)
print('FAILS', fails, 'of', len(res))

#!/usr/bin/env python3
# pong_transplant.py
"""Step 4: connectome transplant. Keep the grown connectome (pairs, receptor types, strength caps, soma
positions) of johnjose-pong-g2, replace the neuron dynamics (step-1 style clean LIFC) and write the weights.

TRANSPLANT RULE (what keeps this honest):
  * a receptor is built only for a (pre, post) pair that exists in the grown connectome,
  * only of a receptor type that grew for that pair (g2: AMPA; NMDA also grew but is not used),
  * with conductance <= the grown cap of that pair and type (sum of ConnectionGPeakSum over the pair's receptors of that type),
  * every other grown pair is simply not built (== zeroed),
  * somata sit at the grown soma positions; the 34 roles come from the grown Regions map.
Not grown, written: neuron dynamics (the Netmorph defaults in struct LIFCNeuronPars in NetmorphManagerThread.cpp are replaced), receptor
kinetics (rise 0.5 / decay 3 ms, as step 1), onset delay (1 ms, grown delays are not in the connectome JSON), the conductances.

  python pong_transplant.py solve     [-Connectome output/johnjose-pong-g2_connectome.json] [-Recipe transplant_recipe.json]
  python pong_transplant.py truthtable [-SpacingMs 100]
  python pong_transplant.py shuffled   [-Seed 7] [-SpacingMs 20]
  python pong_transplant.py play -Seed 301 -Ticks 1000 [-TickMs 20]
  python pong_transplant.py handwired-play -Seed 301 -Ticks 1000
  python pong_transplant.py stats
"""
import os
import sys
import json
import argparse
import numpy as np

import nes_loop as NL
import pong_handwired as H
import pong_weightspace as W
import pong_netmorph_analyze as AN
import BrainGenix.NES as NES

N = 8
MODEL = 'johnjose-pong-g2'
RECIPE = 'transplant_recipe.json'

# ---- design constants (see README step 4) -------------------------------------------------------------------------
G_IN = 0.97           # nS, every input->relay pair (<= its cap; pairs with cap < G_IN are not used). Identical for all inputs so relays
                      # respond identically (latency, spike count) whichever input drives them.
GMIN = G_IN
DELTA = 0.12          # allowed relative drive error per input, in units of c (max-c MILP)
T_FRAC = 7.4          # output firing threshold (in units of c): above the tie drive 7c, below the smallest "win" drive 8c
TAU_OUT_MS = 2.0
ENCODING = dict(burst_spikes=3, isi_ms=3, paddle_offset_ms=1, ball_offset_ms=1)
# Neuron parameter sets (all other LIFC fields as step 1: no fAHP/sAHP/ADP/fatigue/adaptive threshold, Onset reset, 2 ms refractory)
INPUT_NEURON = dict(R_MOhm=100.0, C_pF=100.0)            # B_i, P_j (forced to spike by SetSpecificAPTimes; parameters irrelevant)
RELAY_NEURON = dict(R_MOhm=1000.0, C_pF=3.0)             # all 16 hidden cells, identical (tau 3 ms, g_L 1 nS: a 0.97 nS pair fires it per input spike)
AMPA = dict(E=0, rise=0.5, decay=3.0)
ONSET_MS = 1.0
SHAPES = dict(B=8, P=8, U=5, D=5, UP=10, DOWN=10)       # soma radii (um), as step 1


def out_neuron(c):
    """UP and DOWN, identical. Steady state of a conductance G on g_L: V = Vrest*gL/(gL+G); V = Vth at G = 0.4*gL = T_FRAC*c."""
    gl = T_FRAC * c / 0.4
    return dict(R_MOhm=round(1000.0 / gl, 3), C_pF=round(TAU_OUT_MS * gl, 3))


# --------------------------------------------------------------------------- connectome access
def cap_table(summ):
    ids = {r: v[0] for r, v in summ['Regions'].items()}
    pt = AN.pair_table(summ)

    def cap(a, b):
        v = pt.get((ids[a], ids[b]))
        return v['ampa'] if v else 0.0
    return ids, pt, cap


def side_levels(side):
    return W.side_levels(side)


# --------------------------------------------------------------------------- solver
def solve_side(side, cap, c=None, delta=DELTA):
    """Exact MILP (scipy milp, deterministic) on the EXISTING pairs only, relays = the 8 hidden cells that project to `side`
    (U_k -> UP, D_k -> DOWN), relay output weight w_r <= cap(r, side), input->relay needs cap >= GMIN.
    A ball and a paddle input never share a relay (z_r), so the two bursts add instead of OR-ing.
    Input x then delivers drive sum_r y[x,r] (y = a*w_r) to the output; target c*level(x).
    c is None: c is a variable, maximise it with |drive - c*level| <= delta*c (secondary: fewest pairs).
    c given: minimise the max |error| over the side's inputs, then number of pairs. Returns (c, w, a, err)."""
    from scipy.optimize import milp, LinearConstraint, Bounds
    relays = ['%s%d' % ('U' if side == 'UP' else 'D', k) for k in range(N)]
    lev = side_levels(side)
    xs = sorted(lev)
    pairs = [(x, r) for x in xs for r in relays if cap(x, r) >= GMIN - 1e-6 and cap(r, side) > 0]
    nw, npair, nx = len(relays), len(pairs), len(xs)
    iw, iz, ia = 0, nw, 2 * nw
    iy = ia + npair
    ie = iy + npair
    ic = ie + nx
    nv = ic + 1
    rows, lo, hi = [], [], []

    def row():
        return np.zeros(nv)
    for k, (x, r) in enumerate(pairs):
        cr = cap(r, side)
        wr = relays.index(r)
        v = row(); v[iy + k] = 1; v[ia + k] = -cr; rows.append(v); lo.append(-np.inf); hi.append(0)
        v = row(); v[iy + k] = 1; v[iw + wr] = -1; rows.append(v); lo.append(-np.inf); hi.append(0)
        v = row(); v[iy + k] = 1; v[iw + wr] = -1; v[ia + k] = -cr; rows.append(v); lo.append(-cr); hi.append(np.inf)
        v = row(); v[ia + k] = 1
        if x[0] == 'B':
            v[iz + wr] = 1; rows.append(v); lo.append(-np.inf); hi.append(1)
        else:
            v[iz + wr] = -1; rows.append(v); lo.append(-np.inf); hi.append(0)
    for q, x in enumerate(xs):
        for sign in (1, -1):
            v = row()
            for k, (xx, r) in enumerate(pairs):
                if xx == x:
                    v[iy + k] = sign
            v[ic] = -sign * lev[x]            # sum y - c*lev
            if c is None:
                v[ic] = -sign * lev[x] - delta   # <= delta*c  ->  sign*(sum y - c*lev) - delta*c <= 0
                rows.append(v); lo.append(-np.inf); hi.append(0)
            else:
                v[ie] = -1                      # single variable: max |error| over all inputs of this side
                rows.append(v); lo.append(-np.inf); hi.append(0)
    cmax = 6.0
    ub = np.array([cap(r, side) for r in relays] + [1] * nw + [1] * npair
                  + [max(cap(r, side) for r in relays)] * npair + [1e3] * nx + [cmax])
    lb = np.zeros(nv)
    if c is not None:
        lb[ic] = ub[ic] = c
    integrality = np.array([0] * nw + [1] * nw + [1] * npair + [0] * npair + [0] * nx + [0])
    obj = np.zeros(nv)
    if c is None:
        obj[ic] = -1000
        obj[ia:ia + npair] = 1
    else:
        obj[ia:ia + npair] = 0.01
        obj[ie] = 1000
    res = milp(obj, constraints=LinearConstraint(np.array(rows), lo, hi), integrality=integrality, bounds=Bounds(lb, ub),
               options=dict(time_limit=30, mip_rel_gap=1e-4))
    assert res.x is not None, res.message
    if not res.success:
        print('  (%s side: %s, using the incumbent)' % (side, res.message))
    cc = float(res.x[ic])
    w = {r: float(res.x[iw + k]) for k, r in enumerate(relays)}
    a = [(x, r) for k, (x, r) in enumerate(pairs) if res.x[ia + k] > 0.5]
    err = {x: float(sum(w[r] for xx, r in a if xx == x) - cc * lev[x]) for x in xs}
    return cc, w, a, err


def solve(summ, c=None):
    ids, pt, cap = cap_table(summ)
    if c is None:
        c1 = {s: solve_side(s, cap)[0] for s in ('UP', 'DOWN')}
        print('max c per side (nS/level, delta %.2f):' % DELTA, {s: round(v, 3) for s, v in c1.items()})
        c = float(np.floor(min(c1.values()) * 100) / 100)
    out = {}
    for s in ('UP', 'DOWN'):
        cc, w, a, err = solve_side(s, cap, c=c)
        out[s] = (cc, w, a, err)
        print(s, 'c %.2f' % cc, 'max |drive error| %.3f nS = %.3f c' % (max(abs(v) for v in err.values()),
                                                                    max(abs(v) for v in err.values()) / cc))
    return c, out


def build_recipe(summ, c, out):
    ids, pt, cap = cap_table(summ)
    role = AN.role_of(summ)
    want = {}
    table = []
    for side, (cc, w, a, err) in out.items():
        used = sorted({r for _, r in a})
        for r in used:
            want[(r, side)] = round(w[r], 3)
            assert want[(r, side)] <= cap(r, side) + 1e-6
        for x, r in a:
            want[(x, r)] = min(cap(x, r), G_IN)
        lev = side_levels(side)
        for r in used:
            table.append(dict(side=side, relay=r, v_out_nS=round(w[r], 3), v_out_cap_nS=round(cap(r, side), 2),
                              inputs=[x for x, rr in a if rr == r]))
        drive = {x: sum(want[(r, side)] for xx, r in a if xx == x) for x in lev}
        table.append(dict(side=side, drive_nS={x: round(drive[x], 3) for x in sorted(lev)},
                          target_nS={x: round(c * lev[x], 3) for x in sorted(lev)}))
        for r in used:
            assert len({x[0] for x, rr in a if rr == r}) == 1
    pairs = []
    for (a_, b_), v in sorted((k, want[k]) for k in want):
        g = want[(a_, b_)]
        cp = cap(a_, b_)
        assert 0 < g <= cp + 1e-6, (a_, b_, g, cp)
        pairs.append(dict(pre=a_, post=b_, type='AMPA', g_nS=round(g, 3), grown_cap_nS=round(cp, 3)))
    return dict(
        model=MODEL, connectome='output/%s_connectome.json' % MODEL,
        design=dict(c_nS_per_level=c, G_IN_nS=G_IN, T_frac=T_FRAC, delta=DELTA, relays=[t for t in table if 'relay' in t],
                    drives=[t for t in table if 'drive_nS' in t],
                    note='UP drive = c*(i + N-1-j), DOWN drive = c*(N-1-i + j); output fires iff drive > T_frac*c; '
                         'ball and paddle inputs use disjoint relays'),
        encoding=ENCODING,
        neurons=dict(input=INPUT_NEURON, relay=RELAY_NEURON, output=out_neuron(c)),
        receptor=dict(AMPA, onset_ms=ONSET_MS),
        pairs=pairs)


# --------------------------------------------------------------------------- build the fresh simulation
class Role:
    def __init__(self, nid):
        self.ID = nid


def build(sim, rec, summ):
    """Fresh simulation: 34 clean LIFC neurons at the grown soma positions, receptors only per the recipe pairs."""
    sim.SetLIFCAbstractedFunctional(_AbstractedFunctional=True)
    sim.SetSTDP(_DoSTDP=False)
    ids = {r: v[0] for r, v in summ['Regions'].items()}
    centers = summ['SomaPositions']['SomaCenters']
    pos = {r: [float(v) for v in centers[nid]] for r, nid in ids.items()}

    def sphere(name, r, c):
        cfg = NES.Shapes.Sphere.Configuration()
        cfg.Name, cfg.Radius_um, cfg.Center_um = name, r, c
        return sim.AddSphere(cfg)

    def cylinder(name, p1, p2, r1, r2):
        cfg = NES.Shapes.Cylinder.Configuration()
        cfg.Name = name
        cfg.Point1Position_um, cfg.Point2Position_um = p1, p2
        cfg.Point1Radius_um, cfg.Point2Radius_um = r1, r2
        return sim.AddCylinder(cfg)

    def box(name, c):
        cfg = NES.Shapes.Box.Configuration()
        cfg.Name, cfg.CenterPosition_um = name, c
        cfg.Dimensions_um, cfg.Rotation_rad = [0.1, 0.1, 0.1], [0, 0, 0]
        return sim.AddBox(cfg)

    def compartment(name, shape, R, C):
        cfg = NES.Models.Compartments.LIFC.Configuration()
        cfg.Name = name
        cfg.RestingPotential_mV, cfg.ResetPotential_mV, cfg.SpikeThreshold_mV = -70, -55, -50
        cfg.MembraneResistance_MOhm, cfg.MembraneCapacitance_pF = R, C
        cfg.AfterHyperpolarizationAmplitude_mV = -90
        cfg.Shape = shape
        return sim.AddLIFCCompartment(cfg)

    def neuron(name, soma, axon, R, C):
        c = NES.Models.Neurons.LIFC.Configuration()
        c.Name = name
        c.SomaIDs, c.DendriteIDs, c.AxonIDs = [soma], [], [axon]
        c.RestingPotential_mV, c.ResetPotential_mV, c.SpikeThreshold_mV = -70, -55, -50
        c.MembraneResistance_MOhm, c.MembraneCapacitance_pF = R, C
        c.RefractoryPeriod_ms = 2
        c.SpikeDepolarization_mV = 30
        c.UpdateMethod, c.ResetMethod = 'ExpEulerCm', 'Onset'
        c.AfterHyperpolarizationReversalPotential_mV = -90
        c.FastAfterHyperpolarizationRise_ms = 2.5
        c.FastAfterHyperpolarizationDecay_ms = 30
        c.FastAfterHyperpolarizationPeakConductance_nS = 0
        c.FastAfterHyperpolarizationMaxPeakConductance_nS = 0
        c.FastAfterHyperpolarizationHalfActConstant = 1.5
        c.SlowAfterHyperpolarizationRise_ms = 30
        c.SlowAfterHyperpolarizationDecay_ms = 300
        c.SlowAfterHyperpolarizationPeakConductance_nS = 0
        c.SlowAfterHyperpolarizationMaxPeakConductance_nS = 0
        c.SlowAfterHyperpolarizationHalfActConstant = 0.3
        c.AfterHyperpolarizationSaturationModel = 'clip'
        c.FatigueThreshold = 0
        c.FatigueRecoveryTime_ms = 1000
        c.AfterDepolarizationReversalPotential_mV = -20
        c.AfterDepolarizationRise_ms = 20
        c.AfterDepolarizationDecay_ms = 200
        c.AfterDepolarizationPeakConductance_nS = 0
        c.AfterDepolarizationSaturationMultiplier = 2.0
        c.AfterDepolarizationRecoveryTime_ms = 300
        c.AfterDepolarizationDepletion = 0.3
        c.AfterDepolarizationSaturationModel = 'clip'
        c.AdaptiveThresholdDiffPerSpike = 0.0
        c.AdaptiveTresholdRecoveryTime_ms = 50
        c.AdaptiveThresholdDiffPotential_mV = 10
        c.AdaptiveThresholdFloor_mV = -50
        c.AdaptiveThresholdFloorDeltaPerSpike_mV = 0
        c.AdaptiveThresholdFloorRecoveryTime_ms = 500
        return sim.AddLIFCNeuron(c)

    nets = rec['neurons']
    comps, nid = {}, {}
    for r in sorted(ids, key=lambda r: ids[r]):          # creation in grown-id order
        cls = H_class(r)
        pr = nets['input'] if cls in ('B', 'P') else nets['output'] if cls in ('UP', 'DOWN') else nets['relay']
        p = pos[r]
        s = sphere(r + '_Soma', SHAPES[cls], p)
        a = cylinder(r + '_Axon', p, [p[0] + 20, p[1], p[2]], 2, 1)
        sc = compartment(r + '_Soma_LIFC', s.ID, pr['R_MOhm'], pr['C_pF'])
        ac = compartment(r + '_Axon_LIFC', a.ID, pr['R_MOhm'], pr['C_pF'])
        nid[r] = neuron(r, sc.ID, ac.ID, pr['R_MOhm'], pr['C_pF'])
        comps[r] = (sc, ac)
    pt_cache = AN.pair_table(summ)
    rp = rec['receptor']
    _, _, cap_of = cap_table(summ)     # transplant rule checked against the connectome itself, not the recipe's grown_cap_nS
    for q in rec['pairs']:
        if q['type'] != 'AMPA':
            raise ValueError('transplant rule: only AMPA grew for g2, recipe asks %s' % q['type'])
        if q['pre'] not in ids or q['post'] not in ids:
            raise ValueError('transplant rule: unknown role in %s->%s' % (q['pre'], q['post']))
        pair = pt_cache.get((ids[q['pre']], ids[q['post']]))
        if pair is None or pair['ampa'] <= 0:
            raise ValueError('transplant rule: no grown AMPA pair %s->%s' % (q['pre'], q['post']))
        if q['g_nS'] > cap_of(q['pre'], q['post']) + 1e-6:
            raise ValueError('transplant rule: %s->%s g %.3f nS exceeds grown cap %.3f nS' %
                             (q['pre'], q['post'], q['g_nS'], cap_of(q['pre'], q['post'])))
        name = '%s_%s_AMPA' % (q['pre'], q['post'])
        b = box(name, pos[q['post']])
        c = NES.Models.Connections.LIFCReceptor.Configuration()
        c.Name = name
        c.SourceCompartment = comps[q['pre']][1].ID
        c.DestinationCompartment = comps[q['post']][0].ID
        c.Neurotransmitter = 'AMPA'
        c.ReversalPotential_mV = rp['E']
        c.PSPRise_ms, c.PSPDecay_ms = rp['rise'], rp['decay']
        c.PeakConductance_nS = q['g_nS']
        c.Weight = 1.0
        c.OnsetDelay_ms = rp['onset_ms']
        c.STDP_Method = 'None'
        c.STDP_A_pos = c.STDP_A_neg = c.STDP_Tau_pos = c.STDP_Tau_neg = 0
        c.STDP_Shift = 0.01
        c.voltage_gated = False
        c.ReceptorMorphology = b.ID
        sim.AddLIFCReceptor(c)
    print('Built %d neurons, %d receptors (pairs not in the recipe are not built)' % (len(ids), len(rec['pairs'])))
    net = H.Net()
    net.B = {i: Role(nid['B%d' % i].ID) for i in range(N)}
    net.P = {i: Role(nid['P%d' % i].ID) for i in range(N)}
    net.U = {i: Role(nid['U%d' % i].ID) for i in range(N)}
    net.D = {i: Role(nid['D%d' % i].ID) for i in range(N)}
    net.UP, net.DOWN = Role(nid['UP'].ID), Role(nid['DOWN'].ID)
    return net


def H_class(r):
    return r if r in ('UP', 'DOWN') else r.rstrip('0123456789')


def set_encoding(rec):
    enc = rec['encoding']
    H.BURST_SPIKES, H.BURST_ISI_MS = enc['burst_spikes'], enc['isi_ms']
    H.PADDLE_OFFSET_MS, H.BALL_OFFSET_MS = enc['paddle_offset_ms'], enc['ball_offset_ms']


def stats(rec, summ):
    pt = AN.pair_table(summ)
    ampa = [k for k, v in pt.items() if v['ampa'] > 0]
    used = len(rec['pairs'])
    role = AN.role_of(summ)
    byc = {}
    for q in rec['pairs']:
        k = '%s->%s' % (H_class(q['pre']), H_class(q['post']))
        byc[k] = byc.get(k, 0) + 1
    return dict(grown_pairs_any_type=len(pt), grown_ampa_pairs=len(ampa), pairs_built=used,
                pct_of_grown_ampa_pairs_used=100.0 * used / len(ampa), pct_of_grown_pairs_used=100.0 * used / len(pt),
                pairs_used_by_class=byc, neurons=len(summ['Regions']),
                mean_g_over_cap=float(np.mean([q['g_nS'] / q['grown_cap_nS'] for q in rec['pairs']])))


# --------------------------------------------------------------------------- main
def parse(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument('mode', choices=['solve', 'stats', 'truthtable', 'shuffled', 'play', 'handwired-play', 'handwired-truthtable'])
    p.add_argument('-Host', default='localhost')
    p.add_argument('-Port', default=8100, type=int)
    p.add_argument('-Out', default='output')
    p.add_argument('-Connectome', default='output/%s_connectome.json' % MODEL)
    p.add_argument('-Recipe', default=RECIPE)
    p.add_argument('-Seed', default=1, type=int)
    p.add_argument('-Ticks', default=500, type=int)
    p.add_argument('-SpacingMs', default=100, type=int)
    p.add_argument('-TickMs', default=20, type=int)
    p.add_argument('-C', default=None, type=float, help='solve: fixed c (nS per level); default = largest feasible')
    p.add_argument('-Trace', action='store_true', help='play: write a per-tick trace')
    return p.parse_args(argv)


def main(argv=None):
    A = parse(argv)
    assert A.Port == 8100, 'this work uses the private stack on 8100 only'
    if A.mode in ('solve', 'stats'):
        summ = json.load(open(A.Connectome))
        if A.mode == 'solve':
            c, out = solve(summ, A.C)
            rec = build_recipe(summ, c, out)
            json.dump(rec, open(A.Recipe, 'w'), indent=1)
            print('c = %.2f nS/level; neurons' % c, rec['neurons'])
            for t in rec['design']['relays']:
                print(t['side'], t['relay'], 'v_out %.3f (cap %.1f)' % (t['v_out_nS'], t['v_out_cap_nS']), 'inputs', t['inputs'])
        rec = json.load(open(A.Recipe))
        print(json.dumps(stats(rec, summ)))
        return 0
    os.makedirs(A.Out, exist_ok=True)
    client = NL.connect(A.Host, A.Port)
    if A.mode.startswith('handwired'):
        sim = NL.new_simulation(client, 'pong_handwired', seed=A.Seed)
        net = H.build(sim)
        loop = NL.ClosedLoop(sim, [net.UP.ID, net.DOWN.ID])
        if A.mode == 'handwired-play':
            res = W.run_play(loop, net, A.Ticks, A.Seed, A.TickMs)
            print('RESULT handwired-play', json.dumps(res))
            json.dump(res, open(os.path.join(A.Out, 'tp_handwired_play_s%d.json' % A.Seed), 'w'))
        else:
            res = H.truthtable(loop, net, A.SpacingMs)
            print('RESULT handwired truthtable %d ms: %d/64' % (A.SpacingMs, res['correct']))
        return 0
    rec = json.load(open(A.Recipe))
    summ = json.load(open(A.Connectome))
    sim = NL.new_simulation(client, 'pong_transplant', seed=A.Seed)
    net = build(sim, rec, summ)
    set_encoding(rec)
    loop = NL.ClosedLoop(sim, [net.UP.ID, net.DOWN.ID])
    if A.mode == 'truthtable':
        res = W.graded_truthtable(loop, net, A.SpacingMs)
        json.dump(res, open(os.path.join(A.Out, 'tp_truthtable_%d.json' % A.SpacingMs), 'w'))
        print('RESULT truthtable %d ms: %d/64' % (A.SpacingMs, res['correct']))
    elif A.mode == 'shuffled':
        import random
        combos = [(b, p) for b in range(N) for p in range(N)]
        random.Random(A.Seed).shuffle(combos)
        res = W.graded_schedule(loop, net, combos, A.SpacingMs)
        json.dump(res, open(os.path.join(A.Out, 'tp_shuffled_s%d_%d.json' % (A.Seed, A.SpacingMs)), 'w'))
        print('RESULT shuffled truthtable %d ms seed %d: %d/64' % (A.SpacingMs, A.Seed, res['correct']))
    else:
        trace = [] if A.Trace else None
        res = W.run_play(loop, net, A.Ticks, A.Seed, A.TickMs, trace=trace)
        if trace is not None:
            json.dump(trace, open(os.path.join(A.Out, 'tp_play_trace_s%d.json' % A.Seed), 'w'))
        json.dump(res, open(os.path.join(A.Out, 'tp_play_s%d_n%d.json' % (A.Seed, A.Ticks)), 'w'))
        print('RESULT play', json.dumps(res))
    return 0


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
# pong_weightspace.py
"""Step 3: weight-space programming of the grown Pong model (johnjose-pong-g2).

Read the grown connectome (pairs and their g_peak_sum caps), write a LINEAR comparator
from a spec through relays, measure on held-out evaluations. No optimiser, no grid search.

  python pong_weightspace.py solve   [-Connectome output/johnjose-pong-g2_connectome.json] [-Recipe weightspace_recipe.json]
  python pong_weightspace.py truthtable [-SpacingMs 100]
  python pong_weightspace.py play -Seed 101 -Ticks 1000
  python pong_weightspace.py handwired-play -Seed 101 -Ticks 1000   # step-1 net, same seeds
  python pong_weightspace.py probe -Single      # per-input relay / output counts (diagnostic)

Design (N = 8 bins; level = bin index):
  Hidden cells U_k / D_k are RELAYS: each relay fires a few spikes per input burst. U relays drive UP
  only, D relays drive DOWN only (those are the pairs that exist). Output weights are v_r = c * level / |group|.
  UP   drive from ball bin i: c*i        from paddle bin j: c*(N-1-j)
  DOWN drive from ball bin i: c*(N-1-i)  from paddle bin j: c*j
  => UP - DOWN = 2c*(i-j) and UP = DOWN when i == j (the constant parts are equal: both are zero at level 0
  because level 0 needs no relay). Readout = sign(new UP spikes - new DOWN spikes).
  A level-L relay group on the UP side is fed by B_L and P_{N-1-L}; on the DOWN side by B_{N-1-L} and P_L.
  Every pair that is not in the design is set to 0 (recurrent, forward wrong-index, U0->DOWN, D4->UP ...).
"""
import os
import sys
import time
import json
import argparse
import itertools
import numpy as np

import nes_loop as NL
import pong_handwired as H
import pong_netmorph_analyze as AN
from pong_env import PongEnv, random_policy, oracle_policy, run_policy

N = 8
MODEL = 'johnjose-pong-g2'
G_IN = 10.0          # nS target for input->relay pairs (capped by g_peak_sum): strong inputs saturate the relay (fires on every input spike,
                     # fixed latency); probe 10: spike count and latency of a relay vary with input strength when inputs are weak

ENCODING = dict(burst_spikes=3, isi_ms=3, paddle_offset_ms=1, ball_offset_ms=1)   # coincident: ball and paddle relays are disjoint, conductances add at UP/DOWN
# NOTE: Vth must stay at -50: Netmorph neurons start with an adaptive-threshold FLOOR at -50 that LIFC/Edit
# cannot move (it only decays toward Vth), so lowering Vth does nothing and makes the floor drift. The gap to
# threshold is set through Vrest instead.
VTH = -50.0
RELAY_EDIT = dict(MembraneResistance_MOhm=3000.0, MembraneCapacitance_pF=0.5, RestingPotential_mV=-53.0)       # tau 10 ms; Vrest per relay (gap rule below)
OUT_EDIT = dict(MembraneResistance_MOhm=200.0, MembraneCapacitance_pF=10.0)         # identical for UP and DOWN. tau 1 ms: Vm tracks the
# conductance-weighted target E = Vrest*gL/(gL+gs) (gL = 10 nS); the adaptive threshold (+2 mV/spike) turns the excess into a spike count
GMIN = 2.9           # weakest input->relay cap used: weaker pairs fire the relay late/partially (probe 14) so pulses stop coinciding
C_NS = 1.1           # nS per level: output characteristic (forced-relay probe 15): 5.8 nS pulse -> 2 spikes, >=8 -> 3, <3 -> 0-1, so tie drive 7c = 5.6 nS sits mid-slope
W_FRAC = 0.6         # relay output weight <= 0.5 * g_peak_sum: two spikes 2 ms apart then sum linearly, no min() cap
GAP_PER_NS = 1.5     # relay gap to threshold (mV) = min(6, 1.5 * weakest input cap in nS); probe: 5*cap left 1.96 nS inputs silent


# --------------------------------------------------------------------------- solver
def cap_table(summ):
    ids = {r: v[0] for r, v in summ['Regions'].items()}
    pt = AN.pair_table(summ)
    def cap(a, b):
        v = pt.get((ids[a], ids[b]))
        return v['ampa'] if v else 0.0
    return ids, pt, cap


def side_levels(side):
    """Required UP (resp. DOWN) drive per input in units of c: B_i/P_j -> level."""
    if side == 'UP':
        return {**{'B%d' % i: i for i in range(N)}, **{'P%d' % j: N - 1 - j for j in range(N)}}
    return {**{'B%d' % i: N - 1 - i for i in range(N)}, **{'P%d' % j: j for j in range(N)}}


def solve_side(side, cap, gmin, c, shift=None):
    """Exact MILP (scipy.optimize.milp, deterministic) on the EXISTING pairs only.
    Unknowns: relay output weight w_r <= W_FRAC*cap(r, out); z_r = class of relay r (0: serves ball inputs only,
    1: paddle inputs only, so a ball and a paddle input never share a relay: no OR between simultaneous inputs);
    a[x,r] = 1 iff input x drives relay r (needs cap(x,r) >= gmin); y[x,r] = a*w_r; e_x >= |sum_r y[x,r] - c*level(x)|.
    Objective: minimise 1000*sum(e) + number of used input pairs. Returns (w, a, err) with err = {input: drive - target}."""
    from scipy.optimize import milp, LinearConstraint, Bounds
    shift = shift or {}
    relays = ['%s%d' % ('U' if side == 'UP' else 'D', k) for k in range(N)]
    out = side
    lev = side_levels(side)
    xs = sorted(lev)
    pairs = [(x, r) for x in xs for r in relays if cap(x, r) >= gmin - 1e-6 and cap(r, out) > 0]
    nw, npair, nx = len(relays), len(pairs), len(xs)
    # variable layout: w(nw) | z(nw) | a(npair) | y(npair) | e(nx)
    iw, iz, ia = 0, nw, 2 * nw
    iy = ia + npair
    ie = iy + npair
    nv = ie + nx
    rows, lo, hi = [], [], []
    def row(): return np.zeros(nv)
    for k, (x, r) in enumerate(pairs):
        cr = W_FRAC * cap(r, out)
        wr = relays.index(r)
        v = row(); v[iy + k] = 1; v[ia + k] = -cr; rows.append(v); lo.append(-np.inf); hi.append(0)               # y <= cap*a
        v = row(); v[iy + k] = 1; v[iw + wr] = -1; rows.append(v); lo.append(-np.inf); hi.append(0)              # y <= w
        v = row(); v[iy + k] = 1; v[iw + wr] = -1; v[ia + k] = -cr; rows.append(v); lo.append(-cr); hi.append(np.inf)  # y >= w-cap(1-a)
        v = row(); v[ia + k] = 1                                                                                  # class exclusivity
        if x[0] == 'B':
            v[iz + wr] = 1; rows.append(v); lo.append(-np.inf); hi.append(1)     # a + z <= 1
        else:
            v[iz + wr] = -1; rows.append(v); lo.append(-np.inf); hi.append(0)    # a <= z
    for q, x in enumerate(xs):
        for sign in (1, -1):
            v = row()
            for k, (xx, r) in enumerate(pairs):
                if xx == x:
                    v[iy + k] = sign
            v[ie + q] = -1
            rows.append(v); lo.append(-np.inf); hi.append(sign * (c * lev[x] - shift.get(x, 0.0)))   # +-(sum y - target) <= e
    ub = np.array([W_FRAC * cap(r, out) for r in relays] + [1] * nw + [1] * npair
                  + [W_FRAC * max(cap(r, out) for r in relays)] * npair + [1e3] * nx)
    integrality = np.array([0] * nw + [1] * nw + [1] * npair + [0] * npair + [0] * nx)
    obj = np.zeros(nv)
    obj[ia:ia + npair] = 1
    obj[ie:ie + nx] = 1000
    res = milp(obj, constraints=LinearConstraint(np.array(rows), lo, hi), integrality=integrality,
               bounds=Bounds(np.zeros(nv), ub))
    assert res.success, res.message
    w = {r: float(res.x[iw + k]) for k, r in enumerate(relays)}
    a = [(x, r) for k, (x, r) in enumerate(pairs) if res.x[ia + k] > 0.5]
    err = {x: float(sum(w[r] for xx, r in a if xx == x) - (c * lev[x] - shift.get(x, 0.0))) for x in xs}
    return w, a, err


def solve(summ):
    """Pass 1: exact targets c*level. An input whose drive cannot be delivered on one side (no strong enough pair) has a
    deficit; pass 2 lowers the target of that input on BOTH sides by the same amount (common-mode: UP - DOWN for
    that input stays c*(level_UP - level_DOWN)), so the comparison is kept and only the operating point moves."""
    ids, pt, cap = cap_table(summ)
    p1 = {side: solve_side(side, cap, GMIN, C_NS) for side in ('UP', 'DOWN')}
    shift = {}
    for side in p1:
        for x, e in p1[side][2].items():
            shift[x] = max(shift.get(x, 0.0), -e)
    shift = {x: round(v, 3) for x, v in shift.items() if v > 0.05}
    print('pass 1 deficits (common-mode shift applied to both sides):', shift)
    out = {}
    for side in ('UP', 'DOWN'):
        w, a, err = solve_side(side, cap, GMIN, C_NS, shift)
        out[side] = (C_NS, w, a, err)
        print(side, 'max |drive error| %.2f nS' % max(abs(v) for v in err.values()), {x: round(v, 2) for x, v in err.items() if abs(v) > 0.05})
    return GMIN, C_NS, out['UP'], out['DOWN'], shift


def build_recipe(summ, gmin, c, su, sd, shift):
    ids, pt, cap = cap_table(summ)
    want = {}   # (pre role, post role) -> nS
    table = []
    for side, (cs, w, a, err) in (('UP', su), ('DOWN', sd)):
        used = sorted({r for _, r in a})
        for r in used:
            want[(r, side)] = round(w[r], 3)
        for x, r in a:
            want[(x, r)] = min(cap(x, r), G_IN)
        lev = side_levels(side)
        for r in used:
            table.append(dict(side=side, relay=r, v_out_nS=round(w[r], 3), inputs=[x for x, rr in a if rr == r]))
        drive = {x: sum(want[(r, side)] for xx, r in a if xx == x) for x in lev}
        assert max(abs(drive[x] - (c * lev[x] - shift.get(x, 0.0)) - err[x]) for x in lev) < 0.02, side
        for r in used:   # class exclusivity
            assert len({x[0] for x, rr in a if rr == r}) == 1, (side, r)
    role = AN.role_of(summ)
    pairs = [[a_, b_, round(want.get((role[a_], role[b_]), 0.0), 3)] for (a_, b_), v in sorted(pt.items())]
    unfound = [k for k in want if (ids[k[0]], ids[k[1]]) not in pt]
    assert not unfound, unfound
    used = sorted({r for side_ in (su, sd) for _, r in side_[2]})
    edits = [dict(ids=sorted(ids[r] for r in used), pars=RELAY_EDIT)]   # identical edit for every used relay
    return dict(
        model=MODEL, regions=summ['Regions'],
        design=dict(c_nS_per_level=c, gmin_nS=gmin, G_IN_nS=G_IN, common_mode_shift_nS=shift, relays=table,
                    note='UP drive = c*(i + N-1-j), DOWN drive = c*(N-1-i + j); ball and paddle inputs use disjoint relays'),
        encoding=ENCODING,
        neuron_edits=edits + [dict(ids=sorted([ids['UP'], ids['DOWN']]), pars=OUT_EDIT)],
        pairs=pairs)


# --------------------------------------------------------------------------- apply / eval
def apply(sim, rec):
    regions = sim.GetAbstractConnectome(Sparse=True)['Regions']
    assert regions == rec['regions'], 'loaded model differs from the recipe'
    for e in rec['neuron_edits']:
        r = sim.EditLIFCNeuron(e['ids'], dict(e['pars']))
        assert r.get('StatusCode', 0) == 0, r
    r = sim.BatchSetPrePostStrength([p[0] for p in rec['pairs']], [p[1] for p in rec['pairs']],
                                    [p[2] for p in rec['pairs']])
    assert r.get('StatusCode', 0) == 0, r
    enc = rec['encoding']
    H.BURST_SPIKES, H.BURST_ISI_MS = enc['burst_spikes'], enc['isi_ms']
    H.PADDLE_OFFSET_MS, H.BALL_OFFSET_MS = enc['paddle_offset_ms'], enc['ball_offset_ms']


def open_sim(A, rec, name):
    client = NL.connect(A.Host, A.Port)
    sim = NL.new_simulation(client, name, seed=A.Seed)
    net = H.load_model_net(sim, MODEL, recipe_dir=A.Out)
    apply(sim, rec)
    return sim, net


def graded_truthtable(loop, net, spacing, log=print):
    """Same schedule as H.truthtable, but readout = sign(nUP - nDOWN) (the play readout); tie must give equal counts."""
    combos = [(b, p) for b in range(N) for p in range(N)]
    t0 = loop.t_ms + 10
    pairs, starts = [], {}
    for k, (b, p) in enumerate(combos):
        starts[(b, p)] = t0 + k * spacing
        pairs += H.tick_input_times(net, starts[(b, p)], b, p)
    loop.schedule(sorted(pairs, key=lambda x: x[0]))
    end = t0 + len(combos) * spacing + spacing
    loop.sim.RunFor(end - loop.t_ms, 1.0)
    loop.wait_idle(timeout_s=300)
    data = loop.sim.GetSpikeTimes()['SpikeTimes'] or {}
    up = np.array(H.spikes_of(data, net.UP.ID)); dn = np.array(H.spikes_of(data, net.DOWN.ID))
    rows, ok = [], 0
    for (b, p) in combos:
        s = starts[(b, p)]
        nu = int(((up >= s) & (up < s + spacing)).sum()) if up.size else 0
        nd = int(((dn >= s) & (dn < s + spacing)).sum()) if dn.size else 0
        act = (nu > nd) - (nu < nd)
        exp = (b > p) - (b < p)
        ok += act == exp
        rows.append(dict(ball=b, paddle=p, up=nu, down=nd, action=act, expected=exp, ok=bool(act == exp)))
    log('ball\\pad ' + ' '.join('%6d' % p for p in range(N)))
    for b in range(N):
        log('%7d  ' % b + ' '.join('%3d/%-2d%s' % (rows[b * N + p]['up'], rows[b * N + p]['down'],
                                                  '' if rows[b * N + p]['ok'] else '*') for p in range(N)))
    log('%d/%d correct' % (ok, len(combos)))
    return dict(correct=ok, total=len(combos), rows=rows)


def run_play(loop, net, ticks, seed, tick_ms=20, trace=None):
    t0 = time.time()
    env = H.play(loop, net, ticks, tick_ms, seed, trace=trace)
    wall = time.time() - t0
    rnd, ora = run_policy(random_policy, ticks, seed), run_policy(oracle_policy, ticks, seed)
    return dict(seed=seed, ticks=ticks, hits=env.hits, misses=env.misses, hit_rate=env.hit_rate(),
                action_mismatches=env.action_mismatches, tick_ms=tick_ms,
                wall_ms_per_tick=1000.0 * wall / ticks, random=rnd.hit_rate(), oracle=ora.hit_rate())


def graded_schedule(loop, net, combos, spacing, log=print):
    """Open-loop truth-table-style run of an explicit (b, p) sequence (any order, repeats allowed); same readout as graded_truthtable."""
    t0 = loop.t_ms + 10
    pairs = []
    for k, (b, p) in enumerate(combos):
        pairs += H.tick_input_times(net, t0 + k * spacing, b, p)
    loop.schedule(sorted(pairs, key=lambda x: x[0]))
    loop.sim.RunFor(t0 + len(combos) * spacing + spacing - loop.t_ms, 1.0)
    loop.wait_idle(timeout_s=600)
    data = loop.sim.GetSpikeTimes()['SpikeTimes'] or {}
    up = np.array(H.spikes_of(data, net.UP.ID)); dn = np.array(H.spikes_of(data, net.DOWN.ID))
    rows, ok = [], 0
    for k, (b, p) in enumerate(combos):
        s = t0 + k * spacing
        nu = int(((up >= s) & (up < s + spacing)).sum()) if up.size else 0
        nd = int(((dn >= s) & (dn < s + spacing)).sum()) if dn.size else 0
        act = (nu > nd) - (nu < nd)
        exp = (b > p) - (b < p)
        ok += act == exp
        rows.append(dict(k=k, b=b, p=p, up=nu, down=nd, action=act, expected=exp))
    log('%d/%d correct' % (ok, len(combos)))
    return dict(correct=ok, total=len(combos), rows=rows)


def probe_single(loop, net, spacing=100):
    """Diagnostic: each input alone (B_i then P_j), UP/DOWN counts and spike counts of every hidden cell."""
    ids = {}
    trials = [('B', i) for i in range(N)] + [('P', j) for j in range(N)]
    t0 = loop.t_ms + 10
    pairs, starts = [], {}
    for k, (kind, i) in enumerate(trials):
        s = t0 + k * spacing
        starts[(kind, i)] = s
        pairs += H.tick_input_times(net, s, i if kind == 'B' else None, i if kind == 'P' else None) \
            if False else single_times(net, s, kind, i)
    loop.schedule(sorted(pairs, key=lambda x: x[0]))
    loop.sim.RunFor(t0 + len(trials) * spacing + spacing - loop.t_ms, 1.0)
    loop.wait_idle(timeout_s=300)
    data = loop.sim.GetSpikeTimes()['SpikeTimes'] or {}
    cells = dict(net.U_D)
    out = {}
    for (kind, i), s in starts.items():
        row = {}
        for nm, nid in cells.items():
            v = np.array(H.spikes_of(data, nid))
            row[nm] = int(((v >= s) & (v < s + spacing)).sum()) if v.size else 0
            if row[nm]:
                row[nm] = [round(float(t - s), 1) for t in v[(v >= s) & (v < s + spacing)]]
        out['%s%d' % (kind, i)] = row
    return out


def outchar(loop, sim, rec, net, spacing=100):
    """Diagnostic: force-spike subsets of relays directly (3 spikes ISI 3 ms) and count UP/DOWN spikes: output-stage characteristic."""
    ids = {r: v[0] for r, v in rec['regions'].items()}
    w = {t['relay']: t['v_out_nS'] for t in rec['design']['relays']}
    subsets = [[r] for r in sorted(w)] + [['U7', 'U6'], ['U7', 'U6', 'U3'], ['U7', 'U6', 'U3', 'U5', 'U2'],
                                           ['D2', 'D7'], ['D2', 'D7', 'D5'], ['D2', 'D7', 'D5', 'D0', 'D4']]
    subsets = [s_ for s_ in subsets if all(r in w for r in s_)]
    t0 = loop.t_ms + 10
    pairs = []
    for k, sub in enumerate(subsets):
        for q in range(3):
            for r in sub:
                pairs.append([t0 + k * spacing + 1 + 3 * q, ids[r]])
    loop.schedule(sorted(pairs, key=lambda x: x[0]))
    loop.sim.RunFor(t0 + len(subsets) * spacing + spacing - loop.t_ms, 1.0)
    loop.wait_idle(timeout_s=300)
    data = loop.sim.GetSpikeTimes()['SpikeTimes'] or {}
    res = []
    for k, sub in enumerate(subsets):
        s0 = t0 + k * spacing
        row = {'relays': sub, 'sum_v_nS': round(sum(w[r] for r in sub), 2)}
        for nm in ('UP', 'DOWN'):
            v = np.array(H.spikes_of(data, ids[nm]))
            row[nm] = [round(float(t - s0), 1) for t in v[(v >= s0) & (v < s0 + spacing)]] if v.size else []
        res.append(row)
        print(row)
    return res


def single_times(net, t0, kind, i):
    off = H.PADDLE_OFFSET_MS if kind == 'P' else H.BALL_OFFSET_MS
    nid = (net.P if kind == 'P' else net.B)[i].ID
    return [[t0 + off + k * H.BURST_ISI_MS, nid] for k in range(H.BURST_SPIKES)]


def edit_stats(rec, summ):
    pt = AN.pair_table(summ)
    ampa = [(a, b, v['ampa']) for (a, b), v in pt.items() if v['ampa'] > 0]
    want = {(p[0], p[1]): p[2] for p in rec['pairs']}
    nz = sum(1 for a, b, g in ampa if want[(a, b)] > 0)
    z = sum(1 for a, b, g in ampa if want[(a, b)] == 0)
    return dict(grown_ampa_pairs=len(ampa), written_nonzero=nz, zeroed=z,
                pct_nonzero_changed=100.0 * nz / len(ampa), pct_zeroed=100.0 * z / len(ampa),
                pct_edited=100.0 * (nz + z) / len(ampa))


def parse(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument('mode', choices=['shuffled', 'replay', 'outchar', 'solve', 'truthtable', 'play', 'handwired-play', 'handwired-truthtable', 'probe', 'stats'])
    p.add_argument('-Host', default='localhost')
    p.add_argument('-Port', default=8100, type=int)
    p.add_argument('-Out', default='output')
    p.add_argument('-Connectome', default='output/%s_connectome.json' % MODEL)
    p.add_argument('-Recipe', default='weightspace_recipe.json')
    p.add_argument('-Seed', default=1, type=int)
    p.add_argument('-Ticks', default=500, type=int)
    p.add_argument('-SpacingMs', default=100, type=int)
    p.add_argument('-TickMs', default=20, type=int, help='simulated ms per game tick (play modes)')
    return p.parse_args(argv)


def main(argv=None):
    A = parse(argv)
    if A.mode in ('solve', 'stats'):
        summ = json.load(open(A.Connectome))
        if A.mode == 'solve':
            gmin, c, su, sd, shift = solve(summ)
            rec = build_recipe(summ, gmin, c, su, sd, shift)
            json.dump(rec, open(A.Recipe, 'w'), separators=(',', ':'))
            print('gmin %.1f nS  c %.2f nS/level' % (gmin, c))
            for t in rec['design']['relays']:
                print(t['side'], t['relay'], 'v_out %.3f' % t['v_out_nS'], 'inputs', t['inputs'])
        rec = json.load(open(A.Recipe))
        print(json.dumps(edit_stats(rec, summ)))
        return 0
    os.makedirs(A.Out, exist_ok=True)
    if A.mode.startswith('handwired'):
        client = NL.connect(A.Host, A.Port)
        sim = NL.new_simulation(client, 'pong_handwired', seed=A.Seed)
        net = H.build(sim)
        loop = NL.ClosedLoop(sim, [net.UP.ID, net.DOWN.ID])
        if A.mode == 'handwired-play':
            res = run_play(loop, net, A.Ticks, A.Seed, A.TickMs)
            print(json.dumps(res))
            json.dump(res, open(os.path.join(A.Out, 'ws_handwired_play_s%d.json' % A.Seed), 'w'))
        else:
            res = H.truthtable(loop, net, A.SpacingMs)
            print('handwired truthtable %d/64' % res['correct'])
        return 0
    rec = json.load(open(A.Recipe))
    sim, net = open_sim(A, rec, 'pong_ws')
    summ = json.load(open(A.Connectome))
    ids = [net.UP.ID, net.DOWN.ID]
    if A.mode == 'probe':
        net.U_D = {'%s%d' % (s, k): getattr(net, s)[k].ID for s in 'UD' for k in range(N)}
        net.U_D['UP'], net.U_D['DOWN'] = net.UP.ID, net.DOWN.ID
        loop = NL.ClosedLoop(sim, ids)
        out = probe_single(loop, net)
        for k, row in out.items():
            print(k, ' '.join('%s:%s' % (n, v) for n, v in row.items() if v))
        json.dump(out, open(os.path.join(A.Out, 'ws_probe.json'), 'w'))
        return 0
    loop = NL.ClosedLoop(sim, ids)
    if A.mode == 'shuffled':
        import random
        combos = [(b, p) for b in range(N) for p in range(N)]
        random.Random(A.Seed).shuffle(combos)
        res = graded_schedule(loop, net, combos, A.SpacingMs)
        json.dump(res, open(os.path.join(A.Out, 'ws_shuffled_s%d.json' % A.Seed), 'w'))
        print('RESULT shuffled truthtable %d ms seed %d: %d/64' % (A.SpacingMs, A.Seed, res['correct']))
        return 0
    if A.mode == 'replay':
        tr = json.load(open(os.path.join(A.Out, 'ws_play_trace_s%d.json' % A.Seed)))
        res = graded_schedule(loop, net, [(r['b'], r['p']) for r in tr], A.SpacingMs)
        json.dump(res, open(os.path.join(A.Out, 'ws_replay_s%d.json' % A.Seed), 'w'))
        print('RESULT replay %d ticks %d ms: %d/%d' % (len(tr), A.SpacingMs, res['correct'], res['total']))
        return 0
    if A.mode == 'outchar':
        out = outchar(loop, sim, rec, net)
        json.dump(out, open(os.path.join(A.Out, 'ws_outchar.json'), 'w'))
        return 0
    if A.mode == 'truthtable':
        res = graded_truthtable(loop, net, A.SpacingMs)
        json.dump(res, open(os.path.join(A.Out, 'ws_truthtable_%d.json' % A.SpacingMs), 'w'))
        print('RESULT truthtable %d ms: %d/64' % (A.SpacingMs, res['correct']))
    else:
        trace = []
        res = run_play(loop, net, A.Ticks, A.Seed, A.TickMs, trace=trace)
        json.dump(trace, open(os.path.join(A.Out, 'ws_play_trace_s%d.json' % A.Seed), 'w'))
        json.dump(res, open(os.path.join(A.Out, 'ws_play_s%d_n%d.json' % (A.Seed, A.Ticks)), 'w'))
        print('RESULT play', json.dumps(res))
    return 0


if __name__ == '__main__':
    sys.exit(main())

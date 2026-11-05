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
G_IN = 10.0          # nS target for input->relay pairs (capped by g_peak_sum)

ENCODING = dict(burst_spikes=2, isi_ms=2, paddle_offset_ms=1, ball_offset_ms=7)
RELAY_EDIT = dict(MembraneResistance_MOhm=1000.0, MembraneCapacitance_pF=10.0,       # tau 10 ms; gap to threshold 10 mV so
                  SpikeThreshold_mV=-60.0)                                           # even ~1 nS caps fire a relay
OUT_EDIT = dict(MembraneResistance_MOhm=50.0, MembraneCapacitance_pF=400.0,          # tau 20 ms integrator, ~0.45 mV per nS-spike
                SpikeThreshold_mV=-62.0, RefractoryPeriod_ms=3.0)                    # identical for UP and DOWN


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


def solve_side(side, cap, gmin, c=None):
    """Exact MILP (scipy.optimize.milp, deterministic) on the EXISTING pairs only.
    Unknowns: relay output weight w_r <= cap(r, out); a[x,r] = 1 iff input x drives relay r (needs
    cap(x,r) >= gmin); y[x,r] = a*w_r. Constraint: sum_r y[x,r] = c * level(x) for every input x.
    c=None: maximise c. c given: minimise the number of used input pairs. Returns (c, w, a) or None."""
    from scipy.optimize import milp, LinearConstraint, Bounds
    relays = ['%s%d' % ('U' if side == 'UP' else 'D', k) for k in range(N)]
    out = 'UP' if side == 'UP' else 'DOWN'
    lev = side_levels(side)
    xs = sorted(lev)
    pairs = [(x, r) for x in xs for r in relays if cap(x, r) >= gmin - 1e-6 and cap(r, out) > 0]
    nw, npair = len(relays), len(pairs)
    # variable layout: w(nw) | c | a(npair) | y(npair)
    iw, ic, ia, iy = 0, nw, nw + 1, nw + 1 + npair
    nv = iy + npair
    rows, lo, hi = [], [], []
    def row(): return np.zeros(nv)
    for k, (x, r) in enumerate(pairs):
        cr = cap(r, out)
        wr = relays.index(r)
        v = row(); v[iy + k] = 1; v[ia + k] = -cr; rows.append(v); lo.append(-np.inf); hi.append(0)        # y <= cap*a
        v = row(); v[iy + k] = 1; v[iw + wr] = -1; rows.append(v); lo.append(-np.inf); hi.append(0)       # y <= w
        v = row(); v[iy + k] = 1; v[iw + wr] = -1; v[ia + k] = -cr; rows.append(v); lo.append(-cr); hi.append(np.inf)  # y >= w-cap(1-a)
    for x in xs:
        v = row()
        for k, (xx, r) in enumerate(pairs):
            if xx == x:
                v[iy + k] = 1
        v[ic] = -lev[x]
        rows.append(v); lo.append(0); hi.append(0)
    ub = np.array([cap(r, out) for r in relays] + [50.0] + [1] * npair + [max(cap(r, out) for r in relays)] * npair)
    lb = np.zeros(nv)
    if c is not None:
        lb[ic] = ub[ic] = c
    integrality = np.array([0] * (nw + 1) + [1] * npair + [0] * npair)
    obj = np.zeros(nv)
    if c is None:
        obj[ic] = -1
    else:
        obj[ia:ia + npair] = 1
    res = milp(obj, constraints=LinearConstraint(np.array(rows), lo, hi), integrality=integrality, bounds=Bounds(lb, ub))
    if not res.success:
        return None
    w = {r: float(res.x[iw + k]) for k, r in enumerate(relays)}
    a = [(x, r) for k, (x, r) in enumerate(pairs) if res.x[ia + k] > 0.5]
    return float(res.x[ic]), w, a


def solve(summ):
    """Highest gmin (weakest input->relay cap allowed) for which c >= 2 nS/level is feasible on both sides."""
    ids, pt, cap = cap_table(summ)
    for gmin in (5.0, 4.0, 3.0, 2.0, 1.0, 0.9):
        ru, rd = solve_side('UP', cap, gmin), solve_side('DOWN', cap, gmin)
        print('gmin %.1f: c_max UP %s DOWN %s' % (gmin, ru and round(ru[0], 3), rd and round(rd[0], 3)))
        if ru and rd and min(ru[0], rd[0]) >= 2.0:
            break
    assert ru and rd, 'no feasible assignment'
    c = np.floor(min(ru[0], rd[0]) * 20) / 20     # common gain, 0.05 nS grid
    su, sd = solve_side('UP', cap, gmin, c), solve_side('DOWN', cap, gmin, c)
    return gmin, c, su, sd


def build_recipe(summ, gmin, c, su, sd):
    ids, pt, cap = cap_table(summ)
    want = {}   # (pre role, post role) -> nS
    table = []
    for side, (cs, w, a) in (('UP', su), ('DOWN', sd)):
        out = side
        used = sorted({r for _, r in a})
        for r in used:
            want[(r, out)] = round(w[r], 3)
        for x, r in a:
            want[(x, r)] = min(cap(x, r), G_IN)
        lev = side_levels(side)
        for r in used:
            table.append(dict(side=side, relay=r, v_out_nS=round(w[r], 3),
                              inputs={x: round(want[(x, r)], 2) for x, rr in a if rr == r}))
        # verify the achieved drive is affine in the level
        drive = {x: sum(want[(r, out)] for xx, r in a if xx == x) for x in lev}
        err = max(abs(drive[x] - c * lev[x]) for x in lev)
        assert err < 0.02, (side, err)
    role = AN.role_of(summ)
    pairs = []
    for (a_, b_), v in sorted(pt.items()):
        pairs.append([a_, b_, round(want.get((role[a_], role[b_]), 0.0), 3)])
    unfound = [k for k in want if (ids[k[0]], ids[k[1]]) not in pt]
    assert not unfound, unfound
    relays = sorted(ids['%s%d' % (s_, k)] for s_ in 'UD' for k in range(N))
    return dict(
        model=MODEL, regions=summ['Regions'],
        design=dict(c_nS_per_level=c, gmin_nS=gmin, G_IN_nS=G_IN, relays=table,
                    note='UP drive = c*(i + N-1-j), DOWN drive = c*(N-1-i + j) in relay-spike units'),
        encoding=ENCODING,
        neuron_edits=[dict(ids=relays, pars=RELAY_EDIT),
                      dict(ids=sorted([ids['UP'], ids['DOWN']]), pars=OUT_EDIT)],
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


def run_play(loop, net, ticks, seed):
    env = H.play(loop, net, ticks, 20, seed)
    rnd, ora = run_policy(random_policy, ticks, seed), run_policy(oracle_policy, ticks, seed)
    return dict(seed=seed, ticks=ticks, hits=env.hits, misses=env.misses, hit_rate=env.hit_rate(),
                action_mismatches=env.action_mismatches, random=rnd.hit_rate(), oracle=ora.hit_rate())


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
        out['%s%d' % (kind, i)] = row
    return out


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
    p.add_argument('mode', choices=['solve', 'truthtable', 'play', 'handwired-play', 'handwired-truthtable', 'probe', 'stats'])
    p.add_argument('-Host', default='localhost')
    p.add_argument('-Port', default=8100, type=int)
    p.add_argument('-Out', default='output')
    p.add_argument('-Connectome', default='output/%s_connectome.json' % MODEL)
    p.add_argument('-Recipe', default='weightspace_recipe.json')
    p.add_argument('-Seed', default=1, type=int)
    p.add_argument('-Ticks', default=500, type=int)
    p.add_argument('-SpacingMs', default=100, type=int)
    return p.parse_args(argv)


def main(argv=None):
    A = parse(argv)
    if A.mode in ('solve', 'stats'):
        summ = json.load(open(A.Connectome))
        if A.mode == 'solve':
            gmin, c, su, sd = solve(summ)
            rec = build_recipe(summ, gmin, c, su, sd)
            json.dump(rec, open(A.Recipe, 'w'), separators=(',', ':'))
            print('gmin %.1f nS  c %.2f nS/level' % (gmin, c))
            for t in rec['design']['relays']:
                print(t['side'], t['relay'], 'v_out %.3f' % t['v_out_nS'], 'inputs(nS)', t['inputs'])
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
            res = run_play(loop, net, A.Ticks, A.Seed)
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
            print(k, ' '.join('%s:%d' % (n, v) for n, v in row.items() if v))
        json.dump(out, open(os.path.join(A.Out, 'ws_probe.json'), 'w'))
        return 0
    loop = NL.ClosedLoop(sim, ids)
    if A.mode == 'truthtable':
        res = graded_truthtable(loop, net, A.SpacingMs)
        json.dump(res, open(os.path.join(A.Out, 'ws_truthtable_%d.json' % A.SpacingMs), 'w'))
        print('RESULT truthtable %d ms: %d/64' % (A.SpacingMs, res['correct']))
    else:
        res = run_play(loop, net, A.Ticks, A.Seed)
        json.dump(res, open(os.path.join(A.Out, 'ws_play_s%d_n%d.json' % (A.Seed, A.Ticks)), 'w'))
        print('RESULT play', json.dumps(res))
    return 0


if __name__ == '__main__':
    sys.exit(main())

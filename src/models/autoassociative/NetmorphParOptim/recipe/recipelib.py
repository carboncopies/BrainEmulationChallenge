"""Shared library for the Netmorph autoassociative-memory recipe (BrainGenix-NES).

Design (identical to the verified round-1/2 experiments, fable_loop/it5 + r2_it3):
  * Engram group = ncue cue cells + (size-ncue) non-cue cells (K disjoint groups).
  * cue -> non-cue pairs : conductance T/ncue each (T = 18 nS, ~20% above the ~15 nS NES firing threshold)
  * cue -> cue pairs     : 0
  * non-cue -> non-cue   : w_post * g, w_post = min(1, 27.44 / sum_cue g(c->post))
  * non-cue -> cue       : full as-grown conductance (weight 1)
  * every other Pyr->Pyr pair (pruning): 0
  * Pyr->Int (feedback-only inhibition routing): weight 1, except presynaptic cue cells which are
    scaled so a cue alone delivers <= 10 nS to any interneuron: min(1, 10/C_gi)
  * Int->Pyr, Int->Int GABA: not programmable, stay at 0.2 as grown. STDP off.
The NES API (BatchSetPrePostStrength) takes a target conductance in nS per (pre,post); the stored
weight is conductance / g_peak_sum (always in [0,1]). AMPA only: the API zeroes NMDA on programmed pairs.
"""
import json, os, sys, time, itertools
import numpy as np

W = '/home/johnjose/cos/netmorph_work'
RECIPE = W + '/recipe'
T_DEFAULT = 18.0
WPOST_TARGET = 27.44
INH_CUE_CAP = 10.0
SEEDS = {
    20240628: dict(dump=W + '/fable_loop/it1/viz_a/sample_0000.json', model='fable-it1a-sim133', dir='seed20240628'),
    1001: dict(dump=W + '/fable_loop/r2_seeds/viz_1001/sample_0000.json', model='fable-r2-seed1001', dir='seed1001'),
    1002: dict(dump=W + '/fable_loop/r2_seeds/viz_1002/sample_0000.json', model='fable-r2-seed1002', dir='seed1002'),
    1003: dict(dump=W + '/fable_loop/r2_seeds/viz_1003/sample_0000.json', model='fable-r2-seed1003', dir='seed1003'),
}
# groups as (members, cue) used in the verified round-1/2 experiments for seed 20240628 (fable_loop/it5/build_it5.py)
GROUPS_20240628 = [([4, 18, 20, 22, 29, 51, 59, 63], [22, 29, 51, 63]),
                   ([8, 27, 33, 39, 41, 42, 44, 60], [8, 27, 33, 44]),
                   ([0, 12, 17, 19, 21, 37, 49, 50], [12, 17, 19, 50])]

class Dump:
    def __init__(self, path):
        d = json.load(open(path))
        self.neurons = d['neurons']; self.N = len(self.neurons)
        self.types = np.array([n['soma_type'] for n in self.neurons])
        self.pyr = [int(i) for i in np.where(self.types == 1)[0]]
        self.its = [int(i) for i in np.where(self.types == 2)[0]]
        assert self.pyr == list(range(len(self.pyr))) and self.its == list(range(len(self.pyr), self.N))
        self.G = np.zeros((self.N, self.N)); self.GA = np.zeros((self.N, self.N))
        for c in d['connections']:
            if c['type'] == 1: self.G[c['pre'], c['post']] += c['g_peak_sum']
            elif c['type'] == 2: self.GA[c['pre'], c['post']] += c['g_peak_sum']

def load_groups(seed, dump):
    if seed == 20240628: return [(sorted(m), sorted(c)) for m, c in GROUPS_20240628]
    dz = json.load(open(W + '/fable_loop/r2_seeds/design_%d.json' % seed))['groups']
    return [(sorted(g['members']), sorted(g['cue'])) for g in dz]

def search_group(G, avail, ncue, nnon):
    """max-min cue selection (same criterion as fable_loop/r2_seeds/design_engrams.py): choose ncue cue cells
    maximising the smallest cue->noncue pair conductance over the best nnon non-cue targets."""
    avail = np.array(sorted(avail)); n = len(avail); best = None
    combos = itertools.combinations(range(n), ncue)
    while True:
        chunk = list(itertools.islice(combos, 40000))
        if not chunk: break
        idx = np.array(chunk); gid = avail[idx]
        V = G[gid][:, :, avail].min(axis=1)
        rows = np.arange(len(idx))[:, None]; V[rows, idx] = -np.inf
        top = -np.sort(-V, axis=1)[:, :nnon]
        score = top[:, nnon - 1]; ssum = top.sum(axis=1)
        order = np.lexsort((-ssum, -score)); b = order[0]
        cand = (score[b], ssum[b], gid[b].copy(), V[b].copy())
        if best is None or (cand[0], cand[1]) > (best[0], best[1]): best = cand
    sc, ss, C, v = best
    nc = [int(avail[j]) for j in np.argsort(-v, kind='stable')[:nnon]]
    return sorted(int(c) for c in C), sorted(nc), float(sc)

def design_groups(dump, K, size, ncue, exclude=()):
    """greedy disjoint groups; returns list of (members, cue, score)."""
    avail = set(dump.pyr) - set(exclude); out = []
    for _ in range(K):
        C, NC, sc = search_group(dump.G, avail, ncue, size - ncue)
        out.append((sorted(C + NC), C, sc)); avail -= set(C) | set(NC)
    return out

def build_pairs(dump, groups, bg=0.0, inh=True, T=T_DEFAULT):
    """groups: list of (members, cue). returns dict (pre,post)->(g, conductance_nS, role)."""
    G = dump.G; pyr, its = dump.pyr, dump.its
    grp = {m: k for k, (mem, _) in enumerate(groups) for m in mem}
    cueset = {c: k for k, (_, cue) in enumerate(groups) for c in cue}
    wpost = {}
    for k, (mem, cue) in enumerate(groups):
        for m in [m for m in mem if m not in cue]:
            S = sum(float(G[c, m]) for c in cue)
            wpost[m] = 1.0 if S == 0 else min(1.0, WPOST_TARGET / S)
            for c in cue:
                if G[c, m] > 0: assert G[c, m] >= T / len(cue) - 1e-9, ('cue->noncue pair too weak', c, m, float(G[c, m]))
    def Cgi(k, i): return sum(float(G[c, i]) for c in groups[k][1])
    def inhw(p, i):
        if p in cueset:
            C = Cgi(cueset[p], i); assert C > 0
            return min(1.0, INH_CUE_CAP / C)
        return 1.0
    d = {}
    for a in pyr:
        for b in pyr:
            if a == b or G[a, b] <= 0: continue
            g = float(G[a, b])
            if a in grp and b in grp and grp[a] == grp[b]:
                cue = groups[grp[a]][1]; ac = a in cue; bc = b in cue
                if ac and not bc: v = T / len(cue); role = 'cue->noncue'
                elif not ac and not bc: v = wpost[b] * g; role = 'noncue->noncue'
                elif not ac and bc: v = g; role = 'noncue->cue'
                else: v = 0.0; role = 'cue->cue(zeroed)'
            else: v = bg * g; role = 'pruned' if bg == 0 else 'background'
            d[(a, b)] = (g, v, role)
    for a in pyr:
        for b in its:
            if G[a, b] <= 0: continue
            g = float(G[a, b])
            if inh:
                w = inhw(a, b); role = 'pyr->int(cue-capped)' if w < 1 else 'pyr->int'
            else: w = 0.0; role = 'pyr->int(off)'
            d[(a, b)] = (g, g * w, role)
    for (a, b), (g, v, r) in d.items(): assert 0 <= v <= g + 1e-9
    return d

# ---------------------------------------------------------------- NES access
def connect():
    sys.path.insert(0, '/home/johnjose/BrainGenix/BrainEmulationChallenge/PythonClient')
    import BrainGenix.NES as NES
    cfg = NES.Client.Configuration()
    cfg.Mode = NES.Client.Modes.Remote; cfg.Host = 'localhost'; cfg.Port = 8000; cfg.UseHTTPS = False
    cfg.AuthenticationMethod = NES.Client.Authentication.Password; cfg.Username = 'Admonishing'; cfg.Password = 'Instruction'
    client = NES.Client.Client(cfg); assert client.IsReady(), 'NES not ready'
    return NES, client

def mem_available_gb():
    for l in open('/proc/meminfo'):
        if l.startswith('MemAvailable'): return int(l.split()[1]) / 1048576.0

def guard_memory():
    m = mem_available_gb()
    assert m >= 60, 'available memory %.1f GB < 60 GB: stopping' % m
    return m

PRISTINE = {'fable-it1a-sim133', 'fable-r2-seed1001', 'fable-r2-seed1002', 'fable-r2-seed1003', 'fable-r2it4-d03', 'fable-r2it4-d07'}

def fresh_copy(NES, client, model, name, ref_pairs):
    """Create a NEW simulation, ModelLoad the pristine saved model into it (the saved model is only read),
    verify the loaded connectome against ref_pairs {(pre,post):g_nS} (AMPA) and as-grown weights 0.2."""
    c = NES.Simulation.Configuration(); c.Name = name; c.Seed = 0
    sim = client.CreateSimulation(c)
    assert sim.ID >= 0
    sim.SetLIFCAbstractedFunctional(_AbstractedFunctional=True)
    sim.SetLIFCPreciseSpikeTimes(_UsePreciseSpikeTimes=True)
    sim.SetSTDP(_DoSTDP=False)
    r = sim.ModelLoad(model)
    n = len(sim.GetSomaPositions().get('SomaCenters', []))
    conn = sim.GetConnectome(Pause_s=0.1)
    ampa = {}; w = set(); nconn = 0
    for pre in range(len(conn['ConnectionTargets'])):
        for i, post in enumerate(conn['ConnectionTargets'][pre]):
            nconn += 1; w.add(round(float(conn['ConnectionWeights'][pre][i]), 3))
            if int(conn['ConnectionTypes'][pre][i]) == 1: ampa[(pre, int(post))] = float(conn['ConnectionGPeakSum'][pre][i])
    miss = [k for k in ref_pairs if k not in ampa]
    gbad = [k for k in ref_pairs if k in ampa and abs(ampa[k] - ref_pairs[k]) > 1e-3 * max(1.0, ref_pairs[k])]
    ok = (n == 94 and not miss and not gbad and w == {0.2})
    return sim, dict(sim_id=sim.ID, n_neurons=n, n_connections=nconn, weights_on_load=sorted(w), pairs_missing=len(miss),
                     g_mismatch=len(gbad), loaded_ok=bool(ok), model=model, modelload_response=str(r))

def apply_pairs(sim, pairs, chunk=500):
    """pairs: list of (pre,post,conductance_nS,g_nS). Apply, then read back every pair and compare weight."""
    for s in range(0, len(pairs), chunk):
        ch = pairs[s:s + chunk]
        r = sim.BatchSetPrePostStrength([p[0] for p in ch], [p[1] for p in ch], [p[2] for p in ch])
        assert r.get('StatusCode', 1) == 0, 'batch failed %r' % r
    conn = sim.GetConnectome(Pause_s=0.1)
    got = {}; nmda_nonzero = 0
    for pre in range(len(conn['ConnectionTargets'])):
        for i, post in enumerate(conn['ConnectionTargets'][pre]):
            t = int(conn['ConnectionTypes'][pre][i]); wv = float(conn['ConnectionWeights'][pre][i])
            if t == 1: got[(pre, int(post))] = wv
            elif t == 3 and wv != 0: nmda_nonzero += 1
    mism = []
    for pre, post, cond, g in pairs:
        exp = cond / g
        if (pre, post) not in got or abs(got[(pre, post)] - exp) > 2e-4: mism.append((pre, post, exp, got.get((pre, post))))
    return dict(n_pairs=len(pairs), n_readback_mismatch=len(mism), mismatches=mism[:20],
                weight_min=min(p[2] / p[3] for p in pairs), weight_max=max(p[2] / p[3] for p in pairs),
                nmda_nonzero_after=nmda_nonzero)

def run_events(sim, events, spacing=2000.0, t0=20.0, tail=1000.0):
    """events: list of dict(cue=[ids], offsets=[ms]|None). Returns (event_times, spikes{nid:[t]})."""
    pairs = []; times = []
    for k, e in enumerate(events):
        t = t0 + k * spacing; times.append(t)
        offs = e.get('offsets') or [0.0] * len(e['cue'])
        pairs += [(float(t + o), int(c)) for c, o in zip(e['cue'], offs)]
    r = sim.SetSpecificAPTimes(pairs); assert r.get('StatusCode', 1) == 0, r
    sim.RecordAll(-1)
    dur = t0 + len(events) * spacing + tail
    sim.RunAndWait(Runtime_ms=float(dur), Dt_ms=1.0, timeout_s=900.0)
    sp = sim.GetSpikeTimes()['SpikeTimes']
    return times, {int(k): sorted(float(x) for x in v['tSpike_ms']) for k, v in sp.items()}

def analyse(events, times, spikes, groups, npyr=67, win=300.0):
    """per-event classification. groups: list of (members, cue)."""
    ingrp = {m for mem, _ in groups for m in mem}
    out = []; used = set()
    for e, t in zip(events, times):
        cue = e['cue']; gi = e.get('group')
        def w(i): return [x - t for x in spikes.get(i, []) if t <= x < t + win]
        for i, xs in spikes.items():
            for x in xs:
                if t <= x < t + win: used.add((i, x))
        r = dict(label=e['label'], cue=cue, offsets=e.get('offsets'), group=gi, t_ms=t)
        if gi is not None:
            mem, gc = groups[gi]; nc = [m for m in mem if m not in gc]
            fired = [m for m in nc if w(m)]
            r['noncue_total'] = len(nc); r['noncue_fired'] = len(fired)
            r['latency_ms'] = min((x for m in fired for x in w(m)), default=None)
            r['target_member_spikes'] = sum(len(w(m)) for m in mem)
            r['uncued_cue_cells_fired'] = [c for c in gc if c not in cue and w(c)]
            og = [(k, m) for k, (mm, _) in enumerate(groups) if k != gi for m in mm if w(m)]
        else:
            fired = []; og = [(k, m) for k, (mm, _) in enumerate(groups) for m in mm if m not in cue and w(m)]
            r['noncue_fired'] = 0
        r['other_group_members_fired'] = len(og)
        op = [i for i in range(npyr) if i not in ingrp and w(i)]
        r['other_pyr_fired'] = len(op); r['other_pyr_spikes'] = sum(len(w(i)) for i in op)
        ints = [i for i in range(npyr, 94) if w(i)]
        r['interneurons_fired'] = len(ints); r['interneuron_spikes'] = sum(len(w(i)) for i in ints)
        r['last_pyr_spike_ms'] = max((x for i in range(npyr) for x in w(i)), default=None)
        r['total_spikes'] = sum(len(w(i)) for i in range(94))
        out.append(r)
    r_out = sum(1 for i, xs in spikes.items() for x in xs if (i, x) not in used)
    return out, r_out

def verdict(r, complete_expected):
    """clean = expected completion/no-completion AND no cross-pattern/other-pyramidal activity."""
    no_leak = r['other_group_members_fired'] == 0 and r['other_pyr_fired'] == 0
    if complete_expected:
        ok = r['noncue_fired'] == r['noncue_total'] and no_leak
    else:
        ok = r['noncue_fired'] == 0 and no_leak
    return bool(ok)

def raster(spikes, t, pre=5.0, post=150.0):
    return [[i, round(x - t, 3)] for i in sorted(spikes) for x in spikes[i] if t - pre <= x < t + post]

def standard_events(groups, extra_cross=True):
    """per group: full cue, 2-cell, 3-cell (two subsets); plus mixed cross-pattern cues."""
    ev = []
    for gi, (mem, cue) in enumerate(groups):
        n = len(cue)
        ev.append(dict(label='G%d full %d-cell cue' % (gi, n), group=gi, cue=list(cue), expect_complete=True))
        ev.append(dict(label='G%d 2-cell cue' % gi, group=gi, cue=list(cue[:2]), expect_complete=False))
        if n >= 4:
            ev.append(dict(label='G%d 3-cell cue (a)' % gi, group=gi, cue=list(cue[:3]), expect_complete=False))
            ev.append(dict(label='G%d 3-cell cue (b)' % gi, group=gi, cue=list(cue[1:4]), expect_complete=False))
    if extra_cross and len(groups) >= 2:
        c0, c1 = groups[0][1], groups[1][1]
        ev.append(dict(label='cross: 2 cells of G0 + 2 cells of G1', group=None, cue=list(c0[:2]) + list(c1[:2]), expect_complete=False))
        ev.append(dict(label='cross: 3 cells of G0 + 1 cell of G1', group=None, cue=list(c0[:3]) + [c1[0]], expect_complete=False))
    return ev

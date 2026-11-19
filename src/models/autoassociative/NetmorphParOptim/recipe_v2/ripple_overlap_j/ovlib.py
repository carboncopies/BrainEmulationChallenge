"""Overlap library: model table, exact candidate lists, overlap-limited random-restart packing, R3 pair programming for overlapping memories.
No NES calls here. Pair programming equals headline_i/dyn2.pair_list for disjoint memories (unit-checked in unit_check.py)."""
import sys, json, itertools, random, math
from collections import defaultdict
import numpy as np
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe')
import recipelib as L
R = '/home/johnjose/cos/netmorph_work/recipe_v2/'
THR = 4.125; T = 16.5; LNN = 8.0; LNC = 8.0; CAPCUE = 10.0
def _m(seed, pre, folder): return ('s%d' % seed, pre + 'V1n20_s%d_p0d0175_i0d030000' % seed, R + folder + '/grow_V1n20_s%d_p0d0175_i0d03/viz/sample_0000.json' % seed)
MODELS = {}
for seed, pre, folder in [(16180, 'v2-ihe-', 'inhib_e'), (27182, 'v2-ihf-', 'inhib_f'), (31415, 'v2-ihf-', 'inhib_f'), (11111, 'v2-hdh-', 'headline_h'), (22222, 'v2-hdh-', 'headline_h'),
                          (33333, 'v2-hdi-', 'headline_i'), (44444, 'v2-hdi-', 'headline_i'), (55555, 'v2-hdi-', 'headline_i'), (66666, 'v2-hdi-', 'headline_i'), (77777, 'v2-hdi-', 'headline_i')]:
    k, mn, dp = _m(seed, pre, folder); MODELS[k] = dict(model=mn, dump=dp, seed=seed, folder=folder)
def load(key):
    D = L.Dump(MODELS[key]['dump']); return D, D.G[:96, :96].copy()
def candidates(P, m):
    """exact: every 4-cue set with >= m common strong (>=THR) targets outside the cue; returns list of (C tuple, targets list)"""
    nb = {n: [c for c in range(96) if c != n and P[c, n] >= THR] for n in range(96)}
    byC = defaultdict(set)
    for n, v in nb.items():
        if len(v) >= 4:
            for C in itertools.combinations(sorted(v), 4): byC[C].add(n)
    return [(C, sorted(t for t in T_ if t not in C)) for C, T_ in byC.items() if len([t for t in T_ if t not in C]) >= m]
def pack(cands, m, k, seed=0, restarts=60, max_tries=80):
    """largest packing found with pairwise overlap <= k and role-consistent sharing (a shared cell has the same role in both memories).
    memory = (cue tuple, noncue tuple). Incremental vectorised constraint arrays on the cue sets."""
    if not cands: return []
    rr = random.Random(seed); rs = np.random.RandomState(seed)
    nC = len(cands); Cm = np.zeros((nC, 96), dtype=np.float32)
    for i, (C, _) in enumerate(cands): Cm[i, list(C)] = 1
    best = []
    for _ in range(restarts):
        viol = np.zeros(nC, dtype=bool); mem = []; cueU = set(); ncU = set(); dead = np.zeros(nC, dtype=bool)
        while True:
            ok = np.where(~(viol | dead))[0]
            if len(ok) == 0: break
            placed = False
            for _t in range(max_tries):
                if len(ok) == 0: break
                i = int(ok[rs.randint(len(ok))]); C, Tl = cands[i]
                budget = {}
                good = True
                for j, (cj, nj) in enumerate(mem):
                    s = len(set(C) & set(cj))      # shared cue cells (role consistent: C & nc_j already empty by viol)
                    if s > k: good = False; break
                    budget[j] = k - s
                if not good: dead[i] = True; ok = ok[ok != i]; continue
                Tf = [t for t in Tl if t not in cueU]
                if len(Tf) < m: dead[i] = True; ok = ok[ok != i]; continue
                found = None
                for trial in range(10):
                    pref = [t for t in Tf if t in ncU]; oth = [t for t in Tf if t not in ncU]; rr.shuffle(pref); rr.shuffle(oth)
                    order = (pref + oth) if trial % 2 == 0 else (oth + pref)
                    if trial >= 6: order = Tf[:]; rr.shuffle(order)
                    N = order[:m]
                    if all(len(set(N) & set(nj)) <= budget[j] for j, (cj, nj) in enumerate(mem)): found = N; break
                if found is None: dead[i] = True; ok = ok[ok != i]; continue
                N = tuple(sorted(found)); mem.append((tuple(C), N)); cueU |= set(C); ncU |= set(N)
                cv = np.zeros(96, dtype=np.float32); cv[list(C)] = 1; nv = np.zeros(96, dtype=np.float32); nv[list(N)] = 1
                viol |= (Cm @ nv) > 0          # candidate cue cell may not be a non-cue cell of an existing memory
                viol |= (Cm @ cv) > k          # candidate shares more than k cue cells with this memory
                placed = True; break
            if not placed: break
        if len(mem) > len(best): best = mem[:]
    return [dict(cue=list(c), noncue=list(n), members=sorted(set(c) | set(n))) for c, n in best]
def overlap_hist(groups):
    h = defaultdict(int); typ = defaultdict(int)
    for a, b in itertools.combinations(groups, 2):
        sh = set(a['members']) & set(b['members']); k = len(sh)
        h[k] += 1
        if k:
            sc = len(sh & set(a['cue'])); sn = len(sh & set(a['noncue'])); typ['%d:C%dN%d' % (k, sc, sn)] += 1
    return dict(h), dict(typ)
def pair_list_ov(D, groups, c):
    """groups = list of (members, cue). R3 programming; per-post-cell caps over the union of pre cells of all memories; cue->interneuron cap per memory (min)."""
    G = D.G; nP = 96; N = D.N
    W = np.zeros((N, N))
    if c > 0: W[:nP, :nP] = np.minimum(1.0, c / np.maximum(G[:nP, :nP], 1e-9))
    mems = [(sorted(m), sorted(cu)) for m, cu in groups]
    for mem, cue in mems:
        for a in mem:
            for b in mem:
                if a != b and not (a in cue and b in cue and c > 0): W[a, b] = 0.0
    nc_of = [[m for m in mem if m not in cue] for mem, cue in mems]
    for (mem, cue), nc in zip(mems, nc_of):
        for n in nc:
            for cc in cue:
                assert G[cc, n] >= T / 4 - 1e-9, (cc, n, G[cc, n]); W[cc, n] = (T / 4) / G[cc, n]
    # loops: per post cell n (non-cue in >= 1 memory): union of non-cue pre cells over those memories
    for n in set(x for nc in nc_of for x in nc):
        pre = set()
        for (mem, cue), nc in zip(mems, nc_of):
            if n in nc: pre |= set(m for m in nc if m != n)
        s = sum(G[m, n] for m in pre); sc = min(1.0, LNN / s) if s > 0 else 0.0
        for m in pre:
            if G[m, n] > 0: W[m, n] = sc
    for cc in set(x for mem, cue in mems for x in cue):
        pre = set()
        for (mem, cue), nc in zip(mems, nc_of):
            if cc in cue: pre |= set(nc)
        s = sum(G[m, cc] for m in pre); sc = min(1.0, LNC / s) if s > 0 else 0.0
        for m in pre:
            if G[m, cc] > 0: W[m, cc] = sc
    W[:nP, nP:] = 1.0
    for mem, cue in mems:
        for k in range(nP, N):
            Cs = sum(G[cc, k] for cc in cue)
            if Cs > CAPCUE:
                for cc in cue: W[cc, k] = min(W[cc, k], CAPCUE / Cs)
    out = []
    for a in range(nP):
        for b in range(N):
            g = float(G[a, b])
            if a == b or g <= 0: continue
            out.append((a, b, round(min(float(W[a, b]), 1.0) * g, 6), round(g, 6)))
    return out

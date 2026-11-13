"""Generalised R3 design for any grown network. usage: rdesign.py TAG DUMP_JSON K [seed] -> designs/groups_TAG_K.json + pairs/pairs_TAG_K_c{0,0.15}.json
Design rules identical to R3 (fable_design_S1): disjoint K x (4 cue + 4 non-cue), every cue->noncue pair >= 4.5 nS,
annealing for max closed-loop inhibition (spike-weighted GABA from cap-aware drivable interneurons onto own non-cue cells).
Recipe: cue T=16.5 (4.125/pair), loop cap 8 nS per cell (noncue->noncue, noncue->cue), cue->cue 0, background min(0.2 g, c), Pyr->Int weight 1."""
import sys, os, json, random, time
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/fable_design_S1')
import numpy as np
from net import *   # L (recipelib), T0, CUE_OFFS, Net, ...
HERE = os.path.dirname(os.path.abspath(__file__))
DRIVE_THR = 13.84
def nspk(d, cyc=2): return cyc if d >= 20 else ((cyc + 1) // 2 if d >= 15 else (1 if d >= 10 else 0))
def mk(dump_path):
    D = L.Dump(dump_path); return D
def drivable(D, groups):
    G = D.G; out = []
    for mem, cue in groups:
        nc = [m for m in mem if m not in cue]
        out.append({k: float(min(sum(G[c, k] for c in cue), 10.0) + sum(G[m, k] for m in nc)) for k in D.its})
    return out
def own_inh(D, groups):
    """per memory: spike-weighted GABA onto own non-cue cells (max and mean over non-cue), and list of drivable (>=13.84) ints"""
    dd = drivable(D, groups); res = []
    for (mem, cue), d in zip(groups, dd):
        nc = [m for m in mem if m not in cue]
        v = [sum(nspk(d[k]) * D.GA[k, n] for k in D.its) for n in nc]
        res.append(dict(mean=float(np.mean(v)), mx=float(max(v)), drv=[k for k in D.its if d[k] >= DRIVE_THR]))
    return res
def design(D, K, seed=1, restarts=30, tmax=300, thr=4.5):
    NP = len(D.pyr); Gp = D.G[:NP, :NP]; rng = random.Random(seed); PYR = D.pyr
    def cost(gr):
        r = own_inh(D, gr); pen = sum(3 * max(0, 2 - len(x['drv'])) for x in r)
        return -float(np.mean([x['mean'] for x in r])) - float(min(x['mean'] for x in r)) + pen
    def valid(gr):
        used = [m for mem, _ in gr for m in mem]
        if len(set(used)) != len(used): return False
        return all(Gp[c, n] >= thr for mem, cue in gr for c in cue for n in mem if n not in cue)
    def init():
        avail = set(PYR); gs = []
        for _ in range(K):
            for _t in range(5000):
                cue = rng.sample(sorted(avail), 4)
                cand = [n for n in sorted(avail) if n not in cue and all(Gp[c, n] >= thr for c in cue)]
                if len(cand) >= 4:
                    nc = rng.sample(cand, 4); gs.append((sorted(cue + nc), sorted(cue))); avail -= set(cue + nc); break
            else: return None
        return gs
    best = None; t0 = time.time(); nfail = 0
    for rs in range(restarts):
        g = init()
        if g is None:
            nfail += 1; continue
        c = cost(g); NIT = 4000
        for it in range(NIT):
            T = 3.0 * (1 - it / NIT) + 0.05
            gi = rng.randrange(K); used = {m for m2, _ in g for m in m2}; free = [p for p in PYR if p not in used]
            new = [(list(m), list(c2)) for m, c2 in g]; m, cu = new[gi]
            if rng.random() < 0.7:
                old = rng.choice(m); nw = rng.choice(free); m[m.index(old)] = nw
                if old in cu: cu[cu.index(old)] = nw
            else:
                a, b = rng.sample(m, 2)
                if (a in cu) == (b in cu): continue
                if a in cu: cu[cu.index(a)] = b
                else: cu[cu.index(b)] = a
            new[gi] = (sorted(m), sorted(cu))
            if not valid(new): continue
            c2 = cost(new)
            if c2 < c or rng.random() < np.exp((c - c2) / T): g, c = new, c2
            if best is None or c < best[0]: best = (c, [(list(a), list(b)) for a, b in g])
        print('restart', rs, 'cost', round(c, 2), 'best', round(best[0], 2), round(time.time() - t0), flush=True)
        if time.time() - t0 > tmax: break
    return None if best is None else best[1]
def build(D, groups, T=16.5, Ln=8.0, bg=0.2, pc=0.15):
    G = D.G; N = D.N; nP = len(D.pyr); W = np.zeros((N, N))
    W[:nP, :nP] = np.minimum(bg, pc / np.maximum(G[:nP, :nP], 1e-9)) if pc is not None else bg
    for mem, cue in groups:
        nc = [m for m in mem if m not in cue]
        for a in mem:
            for b in mem:
                if a != b: W[a, b] = 0.0
        for n in nc:
            for c in cue: assert G[c, n] >= T / 4 - 1e-9; W[c, n] = (T / 4) / G[c, n]
            s = sum(G[m, n] for m in nc if m != n); sc = min(1.0, Ln / s) if s > 0 else 0.0
            for m in nc:
                if m != n and G[m, n] > 0: W[m, n] = sc
        for c in cue:
            s = sum(G[m, c] for m in nc); sc = min(1.0, Ln / s) if s > 0 else 0.0
            for m in nc:
                if G[m, c] > 0: W[m, c] = sc
    W[:nP, nP:] = 1.0
    return W
def export(D, groups, fn, **kw):
    G = D.G; W = build(D, groups, **kw); nP = len(D.pyr); out = []
    cueof = {c for m, cu in groups for c in cu}; memof = {x: i for i, (m, cu) in enumerate(groups) for x in m}
    for a in range(nP):
        for b in range(D.N):
            g = float(G[a, b])
            if a == b or g <= 0: continue
            w = float(W[a, b]); assert -1e-12 <= w <= 1 + 1e-9
            if b >= nP: role = 'pyr->int'
            elif a in memof and b in memof and memof[a] == memof[b]: role = ('cue' if a in cueof else 'noncue') + '->' + ('cue' if b in cueof else 'noncue')
            else: role = 'background'
            out.append([a, b, round(min(w, 1.0) * g, 6), round(g, 6), role])
    json.dump(dict(groups=[dict(members=m, cue=c, noncue=[x for x in m if x not in c]) for m, c in groups], params=kw, pairs=out), open(fn, 'w'))
    return out
if __name__ == '__main__':
    tag, dp, K = sys.argv[1], sys.argv[2], int(sys.argv[3]); seed = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    D = mk(dp); thr = 4.5
    gr = design(D, K, seed, thr=thr)
    if gr is None:
        thr = 4.125; print('no design at 4.5 nS; relaxing to 4.125'); gr = design(D, K, seed, thr=thr)
    assert gr is not None, 'design failed'
    r = own_inh(D, gr); Gp = D.G[:96, :96]
    info = [dict(group=i, members=m, cue=c, noncue=[x for x in m if x not in c], min_pair=float(min(Gp[a, n] for a in c for n in m if n not in c)),
                 drivable_ints=r[i]['drv'], own_inh_mean_nS=r[i]['mean']) for i, (m, c) in enumerate(gr)]
    os.makedirs(HERE + '/designs', exist_ok=True)
    def best8(k):
        v = sorted((float(D.G[p, k]) for p in D.pyr), reverse=True)
        return max(min(sum(v[4:8]), 10.0) + sum(v[0:4]), min(sum(v[0:4]), 10.0) + sum(v[4:8]))
    netdrv = [k for k in D.its if best8(k) >= DRIVE_THR]
    json.dump(dict(tag=tag, K=K, thr=thr, network_drivable_cap_aware=netdrv, n_network_drivable=len(netdrv), groups=info), open(HERE + '/designs/groups_%s_K%d.json' % (tag, K), 'w'), indent=1)
    print('network cap-aware drivable ints (best 8 cells):', len(netdrv), netdrv)
    for bgc in (0.0, 0.15): export(D, gr, HERE + '/pairs/pairs_%s_K%d_c%g.json' % (tag, K, bgc), T=16.5, Ln=8.0, bg=0.2, pc=bgc)
    for i in info: print(i)

"""Offline: K=4 disjoint 8-cell memories (4 cue + 4 non-cue) on S1 by annealing. Constraint: cue->noncue pair >= 4.5 nS.
Objective (differs from arbor A, which MINIMISED cross-inhibition): make inhibition matter but not kill recall.
  - each memory must drive >=2 interneurons at >=13.84 nS (cap-aware, standard rule drive) [relaxed: counted on drive incl. non-cue],
    penalty otherwise; and >=1 more at >=11
  - maximise mean spike-weighted cross-inhibition onto other memories' non-cue cells (target ~15-60 nS; ripple_05: 92 nS passed, 177 nS failed)
    penalty when max pair > 70."""
import sys, json, time
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/ripple_S1')
from slib import *
K = 4; seed = int(sys.argv[1]) if len(sys.argv) > 1 else 1
import random; rng = random.Random(seed)
PYR = dump.pyr; Gp = G[:96, :96]
def cost(groups):
    M, dd = cross_matrix(groups, DR_RELAX)
    off = M[~np.eye(K, dtype=bool)]
    pen = 0.0
    for d in dd:
        v = sorted(d.values(), reverse=True)
        n14 = sum(x >= 13.84 for x in v); n11 = sum(x >= 11 for x in v)
        pen += 4 * max(0, 1 - n14) + 1 * max(0, 2 - n11)
    pen += 2 * max(0, off.max() - 70)
    return float(-3 * off.mean() - off.min() + pen)
def valid(groups):
    used = [m for mem, _ in groups for m in mem]
    if len(set(used)) != len(used): return False
    for mem, cue in groups:
        nc = [m for m in mem if m not in cue]
        if any(Gp[c, n] < 4.5 for c in cue for n in nc): return False
    return True
def init():
    avail = set(PYR); gs = []
    for _ in range(K):
        for _t in range(3000):
            cue = rng.sample(sorted(avail), 4)
            cand = [n for n in sorted(avail) if n not in cue and all(Gp[c, n] >= 4.5 for c in cue)]
            if len(cand) >= 4:
                nc = rng.sample(cand, 4); gs.append((sorted(cue + nc), sorted(cue))); avail -= set(cue + nc); break
        else: return None
    return gs
best = None; t0 = time.time()
for rs in range(40):
    g = init()
    if g is None: print('init fail'); continue
    c = cost(g); NIT = 5000
    for it in range(NIT):
        T = 4.0 * (1 - it / NIT) + 0.05
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
    if time.time() - t0 > 540: break
groups = best[1]; M, dd = cross_matrix(groups, DR_RELAX)
print(groups); print(np.round(M, 1))
json.dump(dict(K=K, seed=seed, cost=best[0], groups=[dict(members=m, cue=c, noncue=[x for x in m if x not in c]) for m, c in groups],
  cross_spike_weighted=M.tolist(), drive={str(i): {str(k): round(v, 2) for k, v in d.items() if v >= 5} for i, d in enumerate(dd)}, dr_relax=DR_RELAX, drivable_old=DRIVABLE),
  open(OUT + 'design_K4.json', 'w'), indent=1)

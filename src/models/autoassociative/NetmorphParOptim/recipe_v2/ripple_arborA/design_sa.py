"""Offline: select K=4 disjoint 8-cell memories (4 cue + 4 non-cue) on arbor A by simulated annealing.
Constraints: every cue->noncue pair g_peak_sum >= 4.5 nS (18 nS cue programmable with weight<=1);
soft: >=1 DRIVABLE interneuron with memory drive >= 16 nS (so feedback inhibition fires). Objective: minimise max spike-weighted
cross-inhibition (drivable interneurons only) into non-cue members of other memories, plus self-inhibition floor."""
import sys, json, random, time
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/ripple_arborA')
from alib import *
K = int(sys.argv[1]) if len(sys.argv) > 1 else 4
seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1
rng = random.Random(seed)
PYR = dump.pyr
Gp = G[:96, :96]
def feasible_noncue_for_cue(cue):
    return [n for n in PYR if n not in cue and all(Gp[c, n] >= 4.5 for c in cue)]
def cost(groups):
    M, dd = cross_matrix(groups)
    off = M[~np.eye(len(groups), dtype=bool)]
    pen = 0.0
    for d in dd:
        if max(d.values()) < 16: pen += 5 * (16 - max(d.values()))
    # self inhibition floor: mean spike-weighted GABA onto own non-cue members
    selfi = []
    for gi, (mem, cue) in enumerate(groups):
        nc = [m for m in mem if m not in cue]
        selfi.append(np.mean([sum(nspk(d := dd[gi][k]) * GA[k, n] for k in dd[gi]) for n in nc]))
    return float(off.max() + 0.3 * off.mean()) + pen - 0.5 * min(min(selfi), 6.0)
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
        for _try in range(2000):
            cue = rng.sample(sorted(avail), 4)
            cand = [n for n in sorted(avail) if n not in cue and all(Gp[c, n] >= 4.5 for c in cue)]
            if len(cand) >= 4:
                nc = rng.sample(cand, 4); gs.append((sorted(cue + nc), sorted(cue))); avail -= set(cue + nc); break
        else: return None
    return gs
best = None
t0 = time.time()
for rs in range(30):
    g = init()
    if g is None: continue
    c = cost(g); T = 5.0
    for it in range(6000):
        T = 5.0 * (1 - it / 6000) + 0.05
        gi = rng.randrange(K); mem, cue = g[gi]
        used = {m for m2, _ in g for m in m2}; free = [p for p in PYR if p not in used]
        new = [(list(m), list(c2)) for m, c2 in g]
        m, cu = new[gi]
        if rng.random() < 0.7:
            old = rng.choice(m); nw = rng.choice(free)
            m[m.index(old)] = nw
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
    if time.time() - t0 > 600: break
groups = best[1]
M, dd = cross_matrix(groups)
print(groups); print(np.round(M, 1))
json.dump(dict(K=K, seed=seed, cost=best[0], groups=[dict(members=m, cue=c, noncue=[x for x in m if x not in c]) for m, c in groups],
               cross_spike_weighted_max=M.tolist(), drive={str(i): {str(k): round(v, 2) for k, v in d.items() if v >= 5} for i, d in enumerate(dd)}, drivable_ints=DRIVABLE),
          open(OUT + 'design_K%d.json' % K, 'w'), indent=1)

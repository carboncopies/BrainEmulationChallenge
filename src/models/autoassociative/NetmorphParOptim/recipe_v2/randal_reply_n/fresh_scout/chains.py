"""fresh_scout: heteroassociative chains. Cue sets C (4 cells) from lpw candidates with >= 4 common targets (R3EQ rules, pair >= 4.125, sum >= T). Edge C -> C' if C' (a sorted 4-subset of the
targets of C, disjoint from C) is itself a cue set. Longest simple path / any cycle found by DFS with depth limit 12 (cell-disjoint successive groups not required beyond C' disjoint from C).
Exploratory, threshold model only: a chain link means 'firing group A drives group B above threshold', no silence rules."""
import sys, json, itertools, numpy as np
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/lp_weights'); sys.path.insert(0, '.')
import lpw_lib as L
src = open('prune_p29.py').read().split("out = {}; rs")[0]; exec(src)
sys.setrecursionlimit(10000)
def chains(G):
    cfg = L.Cfg(G, **L.R3EQ); cand = L.candidates(cfg, 4); cs = {tuple(sorted(C)): set(t) for C, t in cand}
    succ = {}
    for C, tl in cs.items():
        tl2 = sorted(t for t in tl if t not in C)
        if len(tl2) > 24: tl2 = tl2[:24]
        succ[C] = [Cp for Cp in itertools.combinations(tl2, 4) if Cp in cs]
    best = [0]; cyc = [False]
    def dfs(C, seen, depth):
        best[0] = max(best[0], depth)
        if depth >= 12: return
        for Cp in succ[C]:
            if Cp in seen: cyc[0] = True; continue
            seen.add(Cp); dfs(Cp, seen, depth + 1); seen.discard(Cp)
    for C in list(cs)[:300]: dfs(C, {C}, 1)
    return dict(n_cue_sets=len(cs), n_edges=sum(len(v) for v in succ.values()), longest_chain_groups=best[0], cycle_found=cyc[0])
for seed in ('33333', '44444'):
    for name, p in (('base', H + 'headline_i/grow_V1n20_s%s_p0d0175_i0d03/viz/sample_0000.json' % seed), ('B1', R + 'grow_B1_s%s/viz/sample_0000.json' % seed)):
        G, n = Gof(p); print(seed, name, chains(G), flush=True)

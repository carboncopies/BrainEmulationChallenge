#!/usr/bin/env python3
"""Offline: designs for task C (K sweep on seed 20240628, group-size sweep). Writes sweep_designs.json."""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recipelib as L
seed = 20240628; dump = L.Dump(L.SEEDS[seed]['dump']); G = dump.G
base = L.load_groups(seed, dump)
out = {'K': {}, 'size': {}}
# K sweep: first K verified groups; extra groups (K=4,5,...) by max-min search on the remaining pyramidal cells (8 cells, cue 4)
used = {m for mem, _ in base for m in mem}; groups = [(m, c) for m, c in base]; extra = []
while True:
    C, NC, sc = L.search_group(G, set(dump.pyr) - {m for mem, _ in groups for m in mem}, 4, 4)
    print('extra group candidate', C, NC, 'min cue->noncue pair nS %.3f' % sc, flush=True)
    if sc < 4.5 - 1e-9 or len(groups) >= 7: break
    groups.append((sorted(C + NC), C)); extra.append(dict(members=sorted(C + NC), cue=C, score=sc))
out['K_groups'] = [dict(members=m, cue=c) for m, c in groups]; out['K_extra_scores'] = extra
print('feasible disjoint 8-cell groups (min pair >= 4.5 nS):', len(groups))
for size, ncue in [(6, 3), (8, 4), (10, 5)]:
    t = time.time(); gs = L.design_groups(dump, 3, size, ncue)
    need = L.T_DEFAULT / ncue
    print('size', size, [(g[1], round(g[2], 2)) for g in gs], 'need >= %.2f nS per cue pair' % need, '%.0fs' % (time.time() - t), flush=True)
    out['size'][str(size)] = [dict(members=m, cue=c, score=s, required_pair_nS=need) for m, c, s in gs]
json.dump(out, open(L.RECIPE + '/sweep_designs.json', 'w'), indent=1)

#!/usr/bin/env python3
"""usage: make_designs.py EFFTAG -> design_D42_<tag>.json (feas2 disjoint groups, from feas_<tag>.json) and design_O1_<tag>.json (ovlib.pack, overlap <= 1, 4+2, 150 restarts). Offline."""
import sys, json
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/ripple_overlap_j'); sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe')
import ovlib as O, recipelib as L
HERE = '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/fresh_run/'
tag = sys.argv[1]; dump = HERE + 'grow_%s/viz/sample_0000.json' % tag
D = L.Dump(dump); P = D.G[:96, :96].copy()
f = json.load(open(HERE + 'feas_%s.json' % tag))
g42 = [dict(cue=sorted(c), noncue=sorted(t), members=sorted(set(c) | set(t))) for c, t in f['groups_m2']]
for g in g42:
    for t in g['noncue']:
        for c in g['cue']: assert P[c, t] >= 4.125
json.dump(dict(groups=g42), open(HERE + 'design_D42_%s.json' % tag, 'w'))
cands = O.candidates(P, 2); best = []
for sd in range(3):
    g = O.pack(cands, 2, 1, seed=sd, restarts=50)
    if len(g) > len(best): best = g
json.dump(dict(groups=best, k=1, n_memories=len(best), n_cands=len(cands), hist=O.overlap_hist(best)[0]), open(HERE + 'design_O1_%s.json' % tag, 'w'))
print(tag, 'D42', len(g42), 'O1', len(best), 'cands', len(cands), 'overlap hist', O.overlap_hist(best)[0])

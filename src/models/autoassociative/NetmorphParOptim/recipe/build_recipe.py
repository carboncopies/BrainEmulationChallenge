#!/usr/bin/env python3
"""Offline: build weights.json, engrams.json and static demo data (types, positions) for one seed.
usage: build_recipe.py SEED   (pure python/numpy; no server access)"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recipelib as L
seed = int(sys.argv[1]); S = L.SEEDS[seed]; out = os.path.join(L.RECIPE, S['dir']); os.makedirs(out, exist_ok=True)
dump = L.Dump(S['dump']); groups = L.load_groups(seed, dump)
pairs = L.build_pairs(dump, groups, bg=0.0, inh=True)
rows = [[a, b, round(g, 6), round(v, 6), round(v / g, 6), role] for (a, b), (g, v, role) in sorted(pairs.items())]
json.dump({'seed': seed, 'model': S['model'], 'api': 'BatchSetPrePostStrength(pre, post, conductance_nS); weight = conductance_nS / g_peak_sum_nS',
           'T4_nS': L.T_DEFAULT, 'columns': ['pre', 'post', 'g_peak_sum_nS (AMPA, as grown at weight 1)', 'conductance_nS (programmed)', 'weight (=cond/g, in [0,1])', 'role'],
           'n_pairs': len(rows), 'stdp': False, 'pairs': rows}, open(os.path.join(out, 'weights.json'), 'w'))
ing = {m for mem, _ in groups for m in mem}
json.dump({'seed': seed, 'model': S['model'], 'n_neurons': dump.N, 'pyramidal_ids': dump.pyr, 'interneuron_ids': dump.its,
           'groups': [{'group': k, 'members': mem, 'cue': cue, 'noncue': [m for m in mem if m not in cue]} for k, (mem, cue) in enumerate(groups)],
           'ungrouped_pyramidal': [p for p in dump.pyr if p not in ing]}, open(os.path.join(out, 'engrams.json'), 'w'), indent=1)
from collections import Counter
print(seed, 'pairs', len(rows), Counter(r[5] for r in rows), 'wmin', min(r[4] for r in rows), 'wmax', max(r[4] for r in rows))

#!/usr/bin/env python3
"""usage: prune_fr.py SEED. Reads grow_B1_s<seed>/viz dump (B1 = Pyr D 0.035); writes grow_B1P_s<seed>/viz (strongest pairs kept: sort by num_receptors desc, seeded random tie break, keep floor(0.29*9120)=2644 pairs)
and grow_B1Q_s<seed>/viz (random control: random 2644 pairs kept). Pyr->Pyr pairs outside the keep set are removed from the dump (weight 0 effective); kept pairs unchanged. prune_<seed>.json = kept/removed pair lists."""
import sys, json, os, numpy as np
HERE = '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/fresh_run/'
seed = sys.argv[1]; keepn = int(0.29 * 9120)
dump = json.load(open(HERE + 'grow_B1_s%s/viz/sample_0000.json' % seed))
typ = {n['id']: n['soma_type'] for n in dump['neurons']}
isPP = lambda c: c['type'] == 1 and typ[c['pre']] == 1 and typ[c['post']] == 1
pp = [(c['pre'], c['post'], c['num_receptors']) for c in dump['connections'] if isPP(c)]
rs = np.random.RandomState(20261123 + int(seed)); key = rs.rand(len(pp))
orderP = sorted(range(len(pp)), key=lambda i: (-pp[i][2], key[i])); keepP = {(pp[i][0], pp[i][1]) for i in orderP[:keepn]}
rs2 = np.random.RandomState(777 + int(seed)); keepQ = {(pp[i][0], pp[i][1]) for i in rs2.permutation(len(pp))[:keepn]}
info = {}
for tag, keep in (('P', keepP), ('Q', keepQ)):
    d = json.loads(json.dumps(dump)); d['connections'] = [c for c in d['connections'] if not isPP(c) or (c['pre'], c['post']) in keep]
    d['abstract_pair_receptors'] = [e for e in d['abstract_pair_receptors'] if not (typ[e['pre']] == 1 and typ[e['post']] == 1) or (e['pre'], e['post']) in keep]
    od = HERE + 'grow_B1%s_s%s/viz' % (tag, seed); os.makedirs(od, exist_ok=True); json.dump(d, open(od + '/sample_0000.json', 'w'), separators=(',', ':'))
    kept_n = [n for a, b, n in pp if (a, b) in keep]
    info[tag] = dict(pairs_grown=len(pp), pairs_kept=len(keep & {(a, b) for a, b, n in pp}), min_syn_kept=min(kept_n), syn_total_kept=int(sum(kept_n)), syn_total_grown=int(sum(n for a, b, n in pp)))
    print(seed, tag, info[tag], flush=True)
json.dump(info, open(HERE + 'prune_%s.json' % seed, 'w'))

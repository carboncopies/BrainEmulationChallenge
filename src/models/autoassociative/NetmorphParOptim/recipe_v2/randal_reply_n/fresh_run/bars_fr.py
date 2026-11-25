"""Bars 1-7 + soft flags per entry of fr_results.json. usage: bars_fr.py -> bars_fr.json (+ printed table)"""
import json, sys, numpy as np
HERE = '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/fresh_run/'
res = json.load(open(HERE + 'fr_results.json')); out = {}
for k, v in sorted(res.items()):
    d = json.load(open(HERE + 'grow_%s/viz/sample_0000.json' % k)); typ = {n['id']: n['soma_type'] for n in d['neurons']}
    pp = [c['num_receptors'] for c in d['connections'] if c['type'] == 1 and typ[c['pre']] == 1 and typ[c['post']] == 1 and c['pre'] != c['post']]
    p = len(pp) / 9120; spc = sum(pp) / len(pp); ge5 = float(np.mean(np.array(pp) >= 5))
    n = v['n_int']; thr = (n + 2) // 3
    m = dict(p=p, spc=spc, A=100 * v['inhib_frac_ip_over_ip_pp'], IP=v['syn_per_pair_int_pyr'], PI=v['syn_per_pair_pyr_int'], drv=v['drivable_8cell_capaware'], zero=v['zero_pyr_input'], bio=v['bio_check'], PP=sum(pp), frac_ge5=ge5)
    b = {1: 0.1 <= p <= 0.3, 2: 1.9 <= spc <= 4.5, 3: 4 <= m['IP'] <= 9, 4: 1.5 <= m['PI'] <= 4.5, 5: m['drv'] >= thr, 6: m['bio'] == 'pass', 7: 25 <= m['A'] <= 50}
    m['fails'] = [i for i, x in b.items() if not x]; m['all7'] = not m['fails']; m['softflag_ge5_over_20pct'] = ge5 > 0.20; out[k] = m
    print('%-12s p %.3f spc %.2f A %.1f IP %.2f PI %.2f drv %d zero %d PP %d ge5 %.3f fails %s' % (k, p, spc, m['A'], m['IP'], m['PI'], m['drv'], m['zero'], sum(pp), ge5, m['fails']))
json.dump(out, open(HERE + 'bars_fr.json', 'w'), indent=1, default=float)

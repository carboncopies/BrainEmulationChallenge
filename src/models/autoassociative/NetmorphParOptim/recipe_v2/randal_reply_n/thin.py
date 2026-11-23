#!/usr/bin/env python3
"""(B) weight-0 thinning. usage: thin.py SEED BARM(B1|B2). Reads the real higher-D dump (grow_<B>_s<seed>) and the baseline dump (headline_i), writes
grow_<B>R_s<seed>/viz/sample_0000.json (rule R, random per-synapse thinning) and grow_<B>W_s<seed> (rule W, fewest-synapse pairs zeroed first) as dump copies
with Pyr->Pyr AMPA num_receptors / g_peak_sum / weight_sum scaled (pair weight n_kept/n); writes thin_<B>_s<seed>.json (pair weights for rule R used by dyn3)."""
import sys, json, os, numpy as np
H = '/home/johnjose/cos/netmorph_work/recipe_v2/'; HERE = H + 'randal_reply_n/'
seed, B = sys.argv[1], sys.argv[2]
base = json.load(open(H + 'headline_i/grow_V1n20_s%s_p0d0175_i0d03/viz/sample_0000.json' % seed))
dump = json.load(open(HERE + 'grow_%s_s%s/viz/sample_0000.json' % (B, seed)))
typ = {n['id']: n['soma_type'] for n in dump['neurons']}
isPP = lambda c: c['type'] == 1 and typ[c['pre']] == 1 and typ[c['post']] == 1
tot_base = sum(c['num_receptors'] for c in base['connections'] if c['type'] == 1 and typ[c['pre']] == 1 and typ[c['post']] == 1)
pp = [c for c in dump['connections'] if isPP(c)]; tot = sum(c['num_receptors'] for c in pp); r = tot_base / tot
print('baseline Pyr->Pyr synapses', tot_base, 'higher-D', tot, 'keep prob r = %.4f' % r)
rng = np.random.default_rng(20261122 + int(seed) % 1000 + (1 if B == 'B2' else 0))
keepR = {}
for c in pp: keepR[(c['pre'], c['post'])] = int(rng.binomial(c['num_receptors'], r))
# rule W: remove pairs with the fewest synapses first (ties random) until total <= tot_base
order = sorted(pp, key=lambda c: (c['num_receptors'], rng.random())); keepW = {(c['pre'], c['post']): c['num_receptors'] for c in pp}; cur = tot
for c in order:
    if cur <= tot_base: break
    cur -= c['num_receptors']; keepW[(c['pre'], c['post'])] = 0
for rule, keep in (('R', keepR), ('W', keepW)):
    d = json.loads(json.dumps(dump)); conns = []; kept_syn = 0
    for c in d['connections']:
        if isPP(c):
            n = c['num_receptors']; k = keep[(c['pre'], c['post'])]
            if k == 0: continue
            f = k / n; c['num_receptors'] = k; c['g_peak_sum'] *= f; c['weight_sum'] *= f; kept_syn += k
        conns.append(c)
    d['connections'] = conns
    d['abstract_pair_receptors'] = [e for e in d['abstract_pair_receptors'] if not (typ[e['pre']] == 1 and typ[e['post']] == 1) or keep.get((e['pre'], e['post']), 0) > 0]
    for e in d['abstract_pair_receptors']:
        if typ[e['pre']] == 1 and typ[e['post']] == 1: e['num_receptors'] = keep[(e['pre'], e['post'])]
    od = HERE + 'grow_%s%s_s%s/viz' % (B, rule, seed); os.makedirs(od, exist_ok=True); json.dump(d, open(od + '/sample_0000.json', 'w'), separators=(',', ':'))
    npairs = sum(1 for v in keep.values() if v > 0); print(rule, 'kept synapses', kept_syn, 'pairs', npairs, 'of', len(pp), 'pair fraction %.4f' % (npairs / 9120))
json.dump(dict(seed=seed, B=B, r=r, tot_base=tot_base, tot=tot, keepR={'%d_%d' % k: v for k, v in keepR.items()}, n_orig={'%d_%d' % (c['pre'], c['post']): c['num_receptors'] for c in pp}), open(HERE + 'thin_%s_s%s.json' % (B, seed), 'w'))

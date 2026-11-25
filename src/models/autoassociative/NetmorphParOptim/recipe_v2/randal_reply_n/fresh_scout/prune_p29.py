"""fresh_scout: 'weakest-pair weight-0' pruning of the higher-D grown networks (B1 = Pyr D 0.035, B2 = D 0.05) down to the connection-probability bar p <= 0.29,
keeping the pairs with the MOST synapses (ties random). Offline, threshold model, same primary packer as lp_weights (T 16.5, theta 12.375, H 49.5, w >= 0.1),
3 restarts, six-cell memories. Compares with the baseline E4 (D 0.0175) and the unpruned B1/B2. Exploratory, not preregistered."""
import sys, json, numpy as np
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/lp_weights')
import lpw_lib as L
H = '/home/johnjose/cos/netmorph_work/recipe_v2/'; R = H + 'randal_reply_n/'
def Gof(path):
    d = json.load(open(path)); typ = {n['id']: n['soma_type'] for n in d['neurons']}; G = np.zeros((96, 96)); n = np.zeros((96, 96))
    for c in d['connections']:
        if c['type'] == 1 and typ[c['pre']] == 1 and typ[c['post']] == 1 and c['pre'] < 96 and c['post'] < 96 and c['pre'] != c['post']:
            G[c['pre'], c['post']] = c['g_peak_sum']; n[c['pre'], c['post']] = c['num_receptors']
    return G, n
def prune(G, n, pmax, rs):
    idx = np.argwhere(n > 0); order = np.lexsort((rs.rand(len(idx)), -n[idx[:, 0], idx[:, 1]]))   # most synapses first
    keep = int(pmax * 96 * 95); H_ = np.zeros_like(G)
    for i in order[:keep]: H_[tuple(idx[i])] = G[tuple(idx[i])]
    return H_
def pack_counts(G):
    cfg = L.Cfg(G, **L.PRIMARY); cand = L.candidates(cfg, 2); res = dict(n_cand=len(cand))
    for kk in (0, 2):
        res['k%d' % kk] = max([len(L.pack(cfg, cand, 2, kk, sd, max_rej=400, max_mem=80)[0]) for sd in range(3)]) if cand else 0
    # 4+4 (m = 4 targets)
    cand4 = L.candidates(cfg, 4); res['n_cand44'] = len(cand4); res['k0_44'] = max([len(L.pack(cfg, cand4, 4, 0, sd, max_rej=400, max_mem=80)[0]) for sd in range(3)]) if cand4 else 0
    return res
def stats(G, n):
    A = G > 0; nz = G[A] / 0.98
    return dict(p=float(A.sum() / (96 * 95)), spc=float(nz.mean()), frac_ge5=float((nz >= 4.9).mean()), strong_pairs=int((G >= 4.125).sum()), in_cv=float(A.sum(0).std() / A.sum(0).mean()))
out = {}; rs = np.random.RandomState(7)
for seed in ('33333', '44444'):
    srcs = {'base': H + 'headline_i/grow_V1n20_s%s_p0d0175_i0d03/viz/sample_0000.json' % seed, 'B1': R + 'grow_B1_s%s/viz/sample_0000.json' % seed, 'B2': R + 'grow_B2_s%s/viz/sample_0000.json' % seed}
    for name, p in srcs.items():
        G, n = Gof(p); variants = {'unpruned': G}
        if name != 'base': variants['P29'] = prune(G, n, 0.29, rs); variants['P25'] = prune(G, n, 0.25, rs)
        for v, Gv in variants.items():
            key = '%s_%s_%s' % (seed, name, v); r = dict(stats(Gv, n), **pack_counts(Gv)); out[key] = r; print(key, {k: (round(x, 3) if isinstance(x, float) else x) for k, x in r.items()}, flush=True)
json.dump(out, open('prune_p29.json', 'w'), indent=1)

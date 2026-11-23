import json, math, numpy as np, sys
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/math_run')
import mrlib as M, lpw_lib as L
KEYS = ['s16180','s27182','s31415','s11111','s22222','s33333','s44444','s55555','s66666','s77777']
LP = '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/lp_weights/'
rows = []
for k in KEYS:
    G = L.load(k); st = M.gstats(G); A = G > 0; din = A.sum(0)
    nstrong = int((G >= 4.125).sum()); r = nstrong / (96 * 95)
    E_er = math.comb(96, 4) * math.comb(92, 2) * r ** 8
    cfg = L.Cfg(G, **dict(L.PRIMARY, H=1e9)); cand = len(L.candidates(cfg, 2))
    # N such that E_ER >= 10 at the same r
    N = 20
    while math.comb(N, 4) * math.comb(N - 4, 2) * r ** 8 < 10 and N < 5000: N += 1
    cj = json.load(open(LP + 'cap_%s.json' % k)); cj2 = json.load(open(LP + 'caphinf_%s.json' % k))
    cp = {f: cj['primary']['fams'][f]['n_mem'] for f in ('m2_k0', 'm2_k3')}; ch = {f: cj2['Hinf']['fams'][f]['n_mem'] for f in ('m2_k0', 'm2_k3')}
    row = dict(model=k, **st, strong_pairs=nstrong, r_strong=r, E_ER=E_er, observed_cands=cand, ratio=(cand / E_er if E_er > 0 else float('inf')), N_for_E10=N,
               C_mean=float(din.mean()), C_median=float(np.median(din)), ref_2C_over_pi=2 * float(din.mean()) / math.pi, ref_2Cmedian_over_pi=2 * float(np.median(din)) / math.pi,
               packer_primary_k0=cp['m2_k0'], packer_primary_k3=cp['m2_k3'], packer_Hinf_k0=ch['m2_k0'], packer_Hinf_k3=ch['m2_k3'])
    rows.append(row); print(k, {a: (round(b, 4) if isinstance(b, float) else b) for a, b in row.items() if a in ('r_strong','E_ER','observed_cands','ratio','N_for_E10','C_mean','C_median','ref_2C_over_pi','packer_primary_k3','packer_Hinf_k3','in_cv')}, flush=True)
json.dump(rows, open('part4.json', 'w'), indent=1)

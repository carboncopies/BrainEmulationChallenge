"""C4: threshold cascade MC on the 10 graphs vs Amini-style directed configuration-model mean-field. Output c4.json"""
import json, numpy as np
import mtlib as M
from scipy.stats import binom
rs = np.random.RandomState(4)
def mc(W, T, k, n=60):
    fin = []
    for _ in range(n):
        f = np.zeros(96, bool); f[rs.choice(96, k, replace=False)] = True
        for _ in range(30):
            new = ((f.astype(float) @ W) >= T) & ~f
            if not new.any(): break
            f |= new
        fin.append(f.sum())
    return float(np.mean(fin)), float(np.median(fin))
def mf(W, T, alpha):
    A = W > 0; din = A.sum(0); dout = A.sum(1); meanw = np.where(din > 0, W.sum(0) / np.maximum(din, 1), 1.0)
    om = np.ceil(T / meanw).astype(int); q = alpha; wout = dout / dout.sum()
    for _ in range(400):
        pa = alpha + (1 - alpha) * np.array([binom.sf(om[i] - 1, din[i], q) if din[i] > 0 else 0.0 for i in range(96)]); qn = float((wout * pa).sum())
        if abs(qn - q) < 1e-9: break
        q = qn
    return float(pa.mean())
res = {}
for s in M.SEEDS:
    G = M.G(s); r = {}
    for wl, fac in (('0.2G', 0.2), ('0.1G', 0.1)):
        W = fac * G
        for T in (15.0,):
            ks = [1, 2, 4, 6, 8, 10, 14, 20, 30, 40]; curve = []
            for k in ks: curve.append((k, mc(W, T, k)[0], mf(W, T, k / 96)*96))
            kc_mc = next((k for k, a, b in curve if a > 50), None); kc_mf = next((k for k, a, b in curve if b > 50), None)
            r[wl] = dict(curve=curve, kc_mc=kc_mc, kc_mf=kc_mf, mean_in_sum=float(W.sum(0).mean()), max_in_sum=float(W.sum(0).max()))
    res[s] = r; print(s, {w: (v['kc_mc'], v['kc_mf'], round(v['mean_in_sum'], 1)) for w, v in r.items()}, flush=True)
json.dump(res, open('c4.json', 'w'))

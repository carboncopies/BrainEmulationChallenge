import numpy as np, json, sys
import design_p2 as D, rn
out = {}
for seed in (66666, 77777):
    key, A, net, pos, G, lo, hi, LH = D.setup(seed)
    Y = D.design_casc(pos, lo, hi, q=9, seed=seed, iters=3000); np.save('p2_E20_s%d.npy' % seed, Y)
    out[seed] = dict(rho=D.rho(Y), max_pair=float(Y.max()), min_in=float(Y.sum(0).min()), max_in=float(Y.sum(0).max())); print(seed, out[seed], flush=True)

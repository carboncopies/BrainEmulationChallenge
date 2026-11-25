"""POST-HOC (not preregistered, labelled): set-point normalisation of the learned input per cell (down only) to X* = 1.5T, 2T, 2.5T, 3T, then the 3T cap; same packing and criteria as Stage 1, overlap o = floor(k/8)."""
import sys, json, time
from multiprocessing import Pool
import fllib as F
from run_stage1 import KEYS, KS
def job(a):
    key, k, xs = a; net = F.Net(key); best = []; Ms = []
    for sd in range(3):
        sysm = F.pack(net, k, k // 8, ('sp', xs), 100 + sd, R=300); Ms.append(len(sysm))
        if len(sysm) > len(best): best = sysm
    return dict(key=key, k=k, xs=xs, M=Ms, best=best)
if __name__ == '__main__':
    t0 = time.time(); tasks = [(key, k, xs) for key in KEYS for k in KS for xs in (1.5, 2.0, 2.5, 3.0)]; out = []
    with Pool(6) as p:
        for i, r in enumerate(p.imap_unordered(job, tasks)):
            out.append(r); print(i + 1, len(tasks), r['key'], r['k'], r['xs'], r['M'], '%.0fs' % (time.time() - t0), flush=True)
    json.dump(out, open('posthoc_sp.json', 'w')); print('done')

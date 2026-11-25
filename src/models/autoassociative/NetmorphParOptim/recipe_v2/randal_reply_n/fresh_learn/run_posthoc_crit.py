"""POST-HOC (not preregistered, labelled): which criterion binds? Variants of the Stage 1 criteria with the same packing: NO25 = drop the 25%-cue silence requirement (assembly may ignite from 25% cues; still: 75% cues complete exactly, unrelated cues silent, no spurious extra cells);
NO25+C50 = additionally require completion from 50% cues (>= 95%). H = 3T cap and H = none, overlap o = floor(k/8)."""
import sys, json, time
from multiprocessing import Pool
import fllib as F
from run_stage1 import KEYS, KS
VAR = {'NO25': dict(no_s25=True), 'NO25_C50': dict(no_s25=True, c50=True)}
def job(a):
    key, k, H, v = a; net = F.Net(key); best = []; Ms = []
    for sd in range(3):
        sysm = F.pack(net, k, k // 8, H, 100 + sd, R=300, req=VAR[v]); Ms.append(len(sysm))
        if len(sysm) > len(best): best = sysm
    return dict(key=key, k=k, H=H, v=v, M=Ms, best=best)
if __name__ == '__main__':
    t0 = time.time(); tasks = [(key, k, H, v) for key in KEYS for k in KS for H in (None, 3.0) for v in VAR]; out = []
    with Pool(6) as p:
        for i, r in enumerate(p.imap_unordered(job, tasks)):
            out.append(r); print(i + 1, len(tasks), r['key'], r['k'], r['H'], r['v'], r['M'], '%.0fs' % (time.time() - t0), flush=True)
    json.dump(out, open('posthoc_crit.json', 'w')); print('done')

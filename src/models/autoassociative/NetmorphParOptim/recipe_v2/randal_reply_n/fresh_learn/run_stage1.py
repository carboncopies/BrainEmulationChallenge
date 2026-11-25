"""fresh_learn Stage 1 runner (PREREGISTRATION.md). Offline. usage: run_stage1.py [nproc]"""
import sys, json, time, itertools
import numpy as np
from multiprocessing import Pool
import fllib as F
KEYS = ['s16180','s27182','s31415','s11111','s22222','s33333','s44444','s55555','s66666','s77777']
KS = [6, 8, 12, 17, 20, 25]; HS = [None, 5.0, 3.0, 2.0, 1.5]
def job(a):
    key, k, H, ovmode = a; net = F.Net(key); o = 0 if ovmode == 'o0' else k // 8; best = []; Ms = []
    for sd in range(3):
        sysm = F.pack(net, k, o, H, 100 + sd, R=300); Ms.append(len(sysm))
        if len(sysm) > len(best): best = sysm
    return dict(key=key, k=k, H=H, ov=ovmode, o=o, M=Ms, best=best)
def rjob(a):
    key, k = a; net = F.Net(key); return dict(key=key, k=k, rand_held=F.random_control(net, k, 3.0, n=5000))
if __name__ == '__main__':
    npr = int(sys.argv[1]) if len(sys.argv) > 1 else 6; t0 = time.time()
    tasks = [(key, k, H, ov) for key in KEYS for k in KS for H in HS for ov in ('o0', 'ov')]
    # primary first so partial results are useful
    tasks.sort(key=lambda t: (not (t[2] == 3.0 and t[3] == 'ov'), t[1]))
    out = []
    with Pool(npr) as p:
        for i, r in enumerate(p.imap_unordered(job, tasks)):
            out.append(r); print(i + 1, len(tasks), r['key'], r['k'], r['H'], r['ov'], r['M'], '%.0fs' % (time.time() - t0), flush=True)
            if (i + 1) % 50 == 0: json.dump(out, open('stage1_runs.json', 'w'))
        json.dump(out, open('stage1_runs.json', 'w'))
        rr = list(p.imap_unordered(rjob, [(key, k) for key in KEYS for k in KS]))
    json.dump(rr, open('stage1_random.json', 'w')); print('done', time.time() - t0)

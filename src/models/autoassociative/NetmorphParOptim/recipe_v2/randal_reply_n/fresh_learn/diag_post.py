"""POST-HOC diagnostic (labelled): for the best allocated standalone candidate (H = none and H = 3T), which preregistered criterion binds? Not part of the verdict."""
import numpy as np, fllib as F, json
KEYS = ['s16180','s27182','s31415','s11111','s22222','s33333','s44444','s55555','s66666','s77777']
rows = []
for key in KEYS:
    net = F.Net(key); rs = np.random.RandomState(9)
    for k in (8, 12, 17, 20):
        cands = []
        for r in range(150):
            A, ob = F.alloc(net, k, [], 0, rs)
            if A is not None: cands.append((ob, A))
        cands.sort(key=lambda t: -t[0]); seen = set(); top = []
        for ob, A in cands:
            if tuple(A) in seen: continue
            seen.add(tuple(A)); top.append(A)
            if len(top) >= 10: break
        for H in (None, 3.0):
            best = None
            for A in top:
                ok, res = F.evaluate(net, [A], H); r = res[0]
                score = (r['held'], r['c75'], r['c50'])
                if best is None or score > best[0]: best = (score, r)
            rows.append(dict(key=key, k=k, H=H, **best[1]))
    print(key, flush=True)
json.dump(rows, open('diag_post.json', 'w'))
import collections
for H in (None, 3.0):
    for k in (8, 12, 17, 20):
        rr = [r for r in rows if r['k'] == k and r['H'] == H]
        print('H', H, 'k', k, 'models with a held candidate', sum(r['held'] for r in rr), '| best-cand median c75 %.2f c50 %.2f s25 %.2f su %.2f spurious %.2f' % tuple(np.median([r[x] for r in rr]) for x in ('c75', 'c50', 's25', 'su', 'spurious')))

import json, numpy as np, collections, fllib as F
R = json.load(open('stage1_runs.json')); KEYS = ['s16180','s27182','s31415','s11111','s22222','s33333','s44444','s55555','s66666','s77777']
# (1) how many cells can receive enough ceiling input at all
print('cells with sum of ceiling input U_in >= 22 nS / >= 33 nS / >= 49.5 nS, and with >=5 inputs of >=2 nS:')
for key in KEYS:
    net = F.Net(key); s = net.U.sum(0); print(key, int((s >= 22).sum()), int((s >= 33).sum()), int((s >= 49.5).sum()), 'hubs(floor>49.5)', int((net.floorsum > 49.5).sum()))
# (2) held systems in the primary variants: partial-cue rate and weight statistics
rows = []
for r in R:
    if r['H'] in (5.0, 3.0) and r['ov'] == 'ov' and len(r['best']) >= 1 and r['k'] in (12, 17, 20, 25):
        net = F.Net(r['key']); sysm = r['best']; Fm, info = F.build_F(net, sysm, r['H']); ok, res = F.evaluate(net, sysm, r['H'], n75=200, n50=200, n25=200, nu=200)
        learned = np.zeros((96, 96), bool)
        for A in sysm: ix = np.ix_(A, A); learned[ix] |= net.pos[ix]
        w = Fm[learned] / net.G[learned]; syn = net.G[learned] / 0.98
        rows.append(dict(key=r['key'], k=r['k'], H=r['H'], M=len(sysm), held200=bool(ok), c75=float(np.mean([x['c75'] for x in res])), c50=float(np.mean([x['c50'] for x in res])), s25=float(np.mean([x['s25'] for x in res])),
                         su=float(np.mean([x['su'] for x in res])), w_ge_0p9=float((w >= 0.9).mean()), ge5syn=float((syn >= 4.9).mean()), n_scaled=info['n_scaled'], n_hub_cells=len(info.get('hub_cells', []))))
for x in rows: print({a: (round(b, 3) if isinstance(b, float) else b) for a, b in x.items()})
json.dump(rows, open('stats_final.json', 'w'), indent=1)

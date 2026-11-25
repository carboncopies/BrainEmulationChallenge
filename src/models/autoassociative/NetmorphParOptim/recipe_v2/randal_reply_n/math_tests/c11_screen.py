"""Exploratory offline screen (reduced model rn.py): E20-type designs (rho scale) x neuron arms x r, for 50%-cue completion with termination. usage: c11_screen.py -> c11.json"""
import sys, json, numpy as np
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/loopedwsp_scout/stability')
import rn, design_p2 as D
ARMS = {'N0': dict(reset='TOVM', sahp=rn.SAHP0), 'R': dict(reset='AFTER', sahp=rn.SAHP0), 'S2': dict(reset='TOVM', sahp=(30., 1000., 2., 4.)), 'RS2': dict(reset='AFTER', sahp=(30., 1000., 2., 4.)),
        'RS3': dict(reset='AFTER', sahp=(30., 1500., 3., 6.)), 'S3': dict(reset='TOVM', sahp=(30., 1500., 3., 6.)), 'X4': dict(reset='TOVM', sahp=(30., 1500., 4., 8.))}
res = {}
for seed in (66666, 77777):
    key, A, net, pos, G, lo, hi, LH = D.setup(seed); E20 = np.load('p2_E20_s%d.npy' % seed); rs = np.random.RandomState(seed); cues = []; kinds = []
    for kind, q in (('p75', 13), ('p50', 9), ('p25', 4), ('p1', 1)):
        for t in range(8):
            cues.append([(1.0 + 1.5 * rs.rand(), int(i)) for i in rs.choice(17, q, replace=False)]); kinds.append((kind, set(c[1] for c in cues[-1])))
    for f in (0.85, 0.92, 1.0):
        Y = np.where(pos, lo + f * (E20 - lo), 0.)
        for an, kw in ARMS.items():
            for r in (0.56, 1.0):
                XN = np.minimum(r * Y, rn.NMDA_CAP * np.where(pos, G, 0.)); R = rn.sim(Y, XN, cues, T=300., dt=0.1, **kw); t = np.arange(R.shape[0]) * 0.1
                agg = {k: dict(n=0, comp=0, rec=0, end=0) for k in ('p75', 'p50', 'p25', 'p1')}
                for e, (kind, cued) in enumerate(kinds):
                    sp = R[:, e, :] > 0; fired = sp[t <= 31].any(0); unc = [i for i in range(17) if i not in cued]; comp = all(fired[i] for i in unc); rec = any(fired[i] for i in unc)
                    last = float(t[np.where(sp.any(1))[0].max()]) if sp.any() else 0.; d = agg[kind]; d['n'] += 1; d['comp'] += int(comp); d['rec'] += int(rec); d['end'] += int(last <= 100.)
                k = '%s_f%.2f_%s_r%g' % (key, f, an, r); res[k] = agg
                ok50 = agg['p50']['comp'] >= 4 and agg['p50']['end'] == 8 and agg['p75']['comp'] >= 7 and agg['p25']['rec'] + agg['p1']['rec'] == 0
                if ok50 or (agg['p50']['comp'] >= 4 and agg['p50']['end'] >= 6): print(k, {a: (v['comp'], v['rec'], v['end']) for a, v in agg.items()}, 'PASS_T-like' if ok50 else '', flush=True)
json.dump(res, open('c11.json', 'w'))
print('done', len(res))

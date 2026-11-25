"""C3: spectral design tests (threshold model + transcribed stored outcomes). Output c3.json"""
import sys, json, numpy as np
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/loopedwsp_scout/stability')
import rn, fllib as FL, pwlib as PW
from scipy.stats import rankdata
out = {}
alloc = json.load(open('/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/partial_cue/alloc_b.json'))
def rho(Y): return float(np.max(np.abs(np.linalg.eigvals(Y))))
# (i) rho, d~ per stored arm
rows = []
for key in ('s66666', 's77777'):
    A = alloc[key]['A17']
    for arm in ('L0', 'LH', 'W70', 'W50', 'H2'):
        if key == 's66666' and arm == 'H2': continue
        m = rn.member_matrices(key, arm, A); XA = m['XA']; dt = float((XA ** 2).sum() / XA.sum())
        rows.append(dict(model=key, arm=arm, rho=rho(XA), dtilde=dt, ratio=rho(XA) / dt, mean_pair=float(XA[XA > 0].mean()), density=float((XA > 0).mean())))
out['arms'] = rows
# (ii)-(iii) AUC of rho for termination: transcribed from neuron_reset_ahp README (steps B2, C, D): (model, design, rho, all completing events end <=100 ms?)
tab = [('s77777', 'LH', 21.5, 0), ('s66666', 'LH', 22.9, 0), ('s77777', 'W70', 17.0, 1), ('s66666', 'W70', 17.9, 0), ('s77777', 'L0', 34.3, 0), ('s66666', 'L0', 32.7, 0),
       ('s77777', 'E16', 16.0, 1), ('s77777', 'E16.5', 16.5, 1), ('s77777', 'E16.7', 16.7, 1), ('s77777', 'E16.9', 16.9, 1), ('s77777', 'E17.1', 17.1, 1),
       ('s66666', 'E16', 16.0, 1), ('s66666', 'E16.5', 16.5, 1), ('s66666', 'E16.7', 16.7, 0), ('s66666', 'E16.9', 16.9, 0), ('s66666', 'E17.1', 17.1, 0),
       ('s66666', 'L1hold', 16.5, 1), ('s66666', 'L2hold', 16.5, 1), ('s66666', 'L1free', 17.08, 0), ('s77777', 'L1hold', 16.5, 1), ('s77777', 'L2hold', 16.5, 1), ('s77777', 'L1free', 17.04, 1)]
def auc(x, y):
    x = np.array(x, float); y = np.array(y); r = rankdata(-x)   # higher rho -> predicts NOT terminating
    pos = r[y == 1]; neg = r[y == 0]; return float(np.mean([(p < n) + 0.5 * (p == n) for p in pos for n in neg]))
out['auc_pooled'] = auc([t[2] for t in tab], [t[3] for t in tab])
for k in ('s66666', 's77777'):
    sub = [t for t in tab if t[0] == k]; out['auc_' + k] = auc([t[2] for t in sub], [t[3] for t in sub])
    pos = [t[2] for t in sub if t[3]]; neg = [t[2] for t in sub if not t[3]]
    out['rho_range_terminating_' + k] = [min(pos), max(pos)]; out['rho_min_nonterminating_' + k] = min(neg)
out['n_table'] = len(tab)
# (iv) analytic bound: every member needs sum of its m smallest others >= Teff for all m-subsets of cue => in-sum >= 16 Teff/m => rho >= min colsum >= 16 Teff/m
out['analytic_rho_min_over_Teff'] = {'13of17': 16 / 13, '9of17': 16 / 9, '4of17': 16 / 4}
# calibrate Teff from stored data: 75% (13/17) completes at rho 16.0-16.9 (s77777) -> Teff >= 13/16 * rho
out['Teff_if_75pct_just_completes_at_rho'] = {str(r): 13 / 16 * r for r in (15.8, 16.5, 16.9)}
out['rho_needed_50pct_if_Teff_13p4_to_13p9_uniform_bound'] = [16 / 9 * 13 / 16 * 16.5, 16 / 9 * 13 / 16 * 17.1]
# cascade (bootstrap) version: random search min rho s.t. q-subsets complete by cascade (threshold model, Teff) on A17 of each graph
def cascade(F, cues, Teff):
    fired = cues.copy()
    for _ in range(17):
        new = (fired.astype(float) @ F >= Teff - 1e-9) & ~fired
        if not new.any(): break
        fired |= new
    return fired
rs = np.random.RandomState(1); res = {}
for key in ('s66666', 's77777'):
    net = FL.Net(key); A = list(alloc[key]['A17']); ix = np.ix_(A, A); G = net.G[ix]; pos = G > 0; lo = 0.1 * G; hi = np.minimum(G, 6.86)
    for Teff in (13.6, 15.0):
        for q in (13, 9):
            cues = np.zeros((300, 17), bool)
            for t in range(300): cues[t, rs.choice(17, q, replace=False)] = True
            def score(Y):
                f = cascade(Y, cues, Teff); return float(f.all(1).mean())
            # start: all pairs at hi, find minimal uniform scale k so that completion >= 0.95, then try coordinate shrinking (random search) keeping completion >= 0.95
            Y = np.where(pos, hi, 0.); k = 1.0
            Yb = Y.copy(); best = None
            if score(Yb) < 0.95: res['%s_T%s_q%d' % (key, Teff, q)] = dict(feasible=False, max_completion=score(Yb), rho_at_max=rho(Yb)); continue
            cur = Yb; r0 = rho(cur)
            for it in range(1500):
                i, j = rs.randint(17, size=2)
                if not pos[i, j]: continue
                Z = cur.copy(); Z[i, j] = max(lo[i, j], Z[i, j] * rs.uniform(0.5, 0.95))
                if score(Z) >= 0.95 and rho(Z) < rho(cur): cur = Z
            res['%s_T%s_q%d' % (key, Teff, q)] = dict(feasible=True, rho_min_found=rho(cur), rho_ceiling_matrix=r0, density=float(pos.mean()), mean_in=float(cur.sum(0).mean()), min_in=float(cur.sum(0).min()))
            print(key, Teff, q, res['%s_T%s_q%d' % (key, Teff, q)], flush=True)
out['cascade_min_rho'] = res
json.dump(out, open('c3.json', 'w'), indent=1, default=float); print(json.dumps({k: v for k, v in out.items() if k not in ('arms',)}, default=float)[:3000]); print(json.dumps(rows, default=float)[:2500])

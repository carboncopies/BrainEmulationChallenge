"""C6 (worst-case slack ranking of members vs known failing cells) and C7 (per-cell polytope for 50% cues on A17 by cutting planes)."""
import sys, json, numpy as np, itertools
from scipy.optimize import linprog
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/loopedwsp_scout/stability')
import rn, fllib as FL
alloc = json.load(open('/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/partial_cue/alloc_b.json'))
def rho(Y): return float(np.max(np.abs(np.linalg.eigvals(Y))))
FAIL = {'s66666': [28, 46, 57, 65, 77, 79], 's77777': [65, 70, 3, 4, 46]}   # step D list + cells missing in step E failed events (neuron_reset_ahp README D, E)
CORE = {'s66666': [28, 46, 57], 's77777': [65, 70, 3]}
out = {'C6': {}, 'C7': {}}
def scaled(net, A, target):
    X, _ = FL.build_F(net, [A], 3.0); ix = np.ix_(A, A); pos = net.pos[ix]; fl = net.fl[ix]; M = X[ix]; lo, hi = 0., 1.
    for _ in range(60):
        k = (lo + hi) / 2; Y = np.where(pos, fl + k * (M - fl), M); lo, hi = (k, hi) if rho(Y) < target else (lo, k)
    return Y
for key in ('s66666', 's77777'):
    net = FL.Net(key); A = list(alloc[key]['A17']); Y = scaled(net, A, 16.5); n = 17
    # C6: worst-case 13-subset input per member (sum of 13 smallest of 16 in-weights), plus the mean-sd rule from step E
    ws = []; ins = Y.sum(0)
    for i in range(n):
        w = np.sort(np.delete(Y[:, i], i)); ws.append(float(w[:13].sum()))
    ws = np.array(ws); order = np.argsort(ws); rank = {A[j]: r for r, j in enumerate(order)}
    thr = ins.mean() - ins.std()
    out['C6'][key] = dict(members=A, worst13_input=[round(float(x), 2) for x in ws], rank_of_core_failing={str(c): rank.get(c) for c in CORE[key]}, rank_of_all_failing={str(c): rank.get(c) for c in FAIL[key] if c in rank},
                          members_below_mean_minus_sd_by_insum=[A[j] for j in range(n) if ins[j] < thr], lowest5_by_worst13=[A[j] for j in order[:5]], insum=[round(float(x), 2) for x in ins])
    # C7: per-member cutting-plane LP: weights w (16 others), bounds, cap 49.5 incl non-member floor input, maximise s: sum of 9 smallest >= Teff + s, sum of 4 largest <= THETA_sil - s
    for Teff in (13.6, 15.0):
        for (q, sil, name) in ((13, 4, '75%_vs_25%'), (9, 4, '50%_vs_25%'), (9, 6, '50%_vs_37%')):
            res = []
            for i in range(n):
                js = [j for j in range(n) if j != i]; G = net.G[np.ix_(A, A)][js, i]; lo = 0.1 * G; hi = np.minimum(G, 6.86)
                # silence level: a sil-subset must stay below Teff - 1.0 (1 nS margin) ; completion for q-subsets must reach Teff
                Tsil = Teff - 1.0; subsC = [tuple(range(q))]; subsS = [tuple(range(sil))]; s_best = None
                for it in range(60):
                    Aub = []; bub = []
                    for S in subsC: r = np.zeros(17); r[list(S)] = -1; r[16] = 1; Aub.append(r); bub.append(-Teff)
                    for S in subsS: r = np.zeros(17); r[list(S)] = 1; r[16] = 1; Aub.append(r); bub.append(Tsil)
                    rr = linprog(np.r_[np.zeros(16), -1], A_ub=np.array(Aub), b_ub=bub, bounds=[(l, h) for l, h in zip(lo, hi)] + [(-30, 30)], method='highs')
                    if rr.status != 0: s_best = -30; break
                    w = rr.x[:16]; s = rr.x[16]; o = np.argsort(w); newC = tuple(sorted(o[:q])); newS = tuple(sorted(o[::-1][:sil])); ch = False
                    if newC not in subsC and w[list(newC)].sum() < Teff + s - 1e-9: subsC.append(newC); ch = True
                    if newS not in subsS and w[list(newS)].sum() > Tsil - s + 1e-9: subsS.append(newS); ch = True
                    s_best = s
                    if not ch: break
                res.append(float(s_best))
            out['C7'][f'{key}_Teff{Teff}_{name}'] = dict(min_slack_over_members=min(res), n_members_feasible=int(sum(r >= -1e-9 for r in res)), slack_median=float(np.median(res)))
            print(key, Teff, name, out['C7'][f'{key}_Teff{Teff}_{name}'], flush=True)
    print(key, json.dumps(out['C6'][key]), flush=True)
# K42 50% arithmetic: 2 cue cells deliver at most 2*6.86 = 13.72 nS < 16.5 (T) and < 15 (Teff=15)
out['C7']['K42_50pct_cap_arith'] = dict(max_2cell_input=2 * 6.86, T=16.5, Teff=15.0, feasible_at_T=False, feasible_at_Teff15=False, feasible_at_Teff13p6=True)
json.dump(out, open('c6c7.json', 'w'), indent=1)

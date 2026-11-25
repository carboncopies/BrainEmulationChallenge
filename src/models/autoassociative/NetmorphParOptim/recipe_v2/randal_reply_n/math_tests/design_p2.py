"""PHASE 2 designs: member matrices Y (17x17) for s66666/s77777. BASE is the stored recipe (built in the sim runner by run_nr5.make_arm); here only the math designs. Writes p2_<name>_s<seed>.npy and p2_designs.json (flags)."""
import sys, json, numpy as np
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/loopedwsp_scout/stability')
import rn, fllib as FL
from scipy.optimize import linprog
alloc = json.load(open('/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/partial_cue/alloc_b.json'))
RHO = 16.5; TEFF = 13.6
def rho(Y): return float(np.max(np.abs(np.linalg.eigvals(Y))))
def setup(seed):
    key = 's%d' % seed; A = list(alloc[key]['A17']); net = FL.Net(key); ix = np.ix_(A, A); pos = net.pos[ix].copy(); np.fill_diagonal(pos, False); G = net.G[ix]
    lo = np.where(pos, 0.1 * G, 0.); hi = np.where(pos, np.minimum(G, 6.86), 0.); LH, _ = FL.build_F(net, [A], 3.0); return key, A, net, pos, G, lo, hi, LH[ix]
def rescale(Z, pos, lo, target=RHO):
    a, b = 0., 1.
    for _ in range(60):
        k = (a + b) / 2; W = np.where(pos, lo + k * (Z - lo), 0.); a, b = (k, b) if rho(W) < target else (a, k)
    return np.where(pos, lo + k * (Z - lo), 0.)
def worst13(Y):
    return np.array([np.sort(np.delete(Y[:, i], i))[:13].sum() for i in range(Y.shape[0])])
def design_W13(Y0, pos, lo, hi):
    """a-priori rule: members with worst-13 input < mean - 1 SD are boosted until their worst-13 input equals the mean; hold rho (fixed point)."""
    Y = Y0.copy()
    for it in range(100):
        w = worst13(Y); thr = w.mean() - w.std(); Z = Y.copy()
        for j in range(17):
            if w[j] < thr:
                col = Z[:, j].copy()
                for _ in range(40):                              # raise the smallest in-weights first (water filling) until worst13 reaches the mean
                    ww = np.sort(np.delete(col, j))[:13].sum()
                    if ww >= w.mean() - 1e-6: break
                    cand = [i for i in range(17) if i != j and pos[i, j] and col[i] < hi[i, j] - 1e-9]
                    if not cand: break
                    i0 = min(cand, key=lambda i: col[i]); col[i0] = min(hi[i0, j], col[i0] + (w.mean() - ww) / 2)
                Z[:, j] = col
        Y2 = rescale(Z, pos, lo)
        if np.abs(Y2 - Y).max() < 1e-4: break
        Y = Y2
    return Y
def lp_slack(G, lo, hi, pos, Teff=TEFF, q=13, sil=4, cap=49.5):
    n = 17; Y = np.zeros((n, n)); svals = []
    for i in range(n):
        js = [j for j in range(n) if j != i and pos[j, i]]; L = lo[js, i]; H = hi[js, i]; m = len(js); subsC = [tuple(range(min(q, m)))]; subsS = [tuple(range(min(sil, m)))]
        def solve(subsC, subsS, s_fix=None):
            Aub = []; bub = []
            for S in subsC: r = np.zeros(m + 1); r[list(S)] = -1; r[m] = 1; Aub.append(r); bub.append(-Teff)
            for S in subsS: r = np.zeros(m + 1); r[list(S)] = 1; r[m] = 1; Aub.append(r); bub.append(Teff - 1.0)
            r = np.zeros(m + 1); r[:m] = 1; Aub.append(r); bub.append(max(cap, L.sum()))
            if s_fix is None: return linprog(np.r_[np.zeros(m), -1], A_ub=np.array(Aub), b_ub=bub, bounds=[(l, h) for l, h in zip(L, H)] + [(-30, 30)], method='highs')
            A2 = np.array(Aub); A2[:, m] = 0; b2 = np.array(bub, float); A2[:len(subsC), m] = 0
            for k_ in range(len(Aub)): b2[k_] = bub[k_] - Aub[k_][m] * s_fix
            return linprog(np.r_[np.ones(m), 0], A_ub=A2, b_ub=b2, bounds=[(l, h) for l, h in zip(L, H)] + [(0, 0)], method='highs')
        for it in range(80):
            rr = solve(subsC, subsS); w = rr.x[:m]; s = rr.x[m]; o = np.argsort(w); nC = tuple(sorted(o[:min(q, m)])); nS = tuple(sorted(o[::-1][:min(sil, m)])); ch = False
            if nC not in subsC and w[list(nC)].sum() < Teff + s - 1e-9: subsC.append(nC); ch = True
            if nS not in subsS and w[list(nS)].sum() > Teff - 1.0 - s + 1e-9: subsS.append(nS); ch = True
            if not ch: break
        sstar = float(rr.x[m]); svals.append(sstar); s_use = min(sstar, 1.0)
        r2 = solve(subsC, subsS, s_fix=s_use)                    # minimal total weight achieving slack s_use
        wv = r2.x[:m] if r2.status == 0 else rr.x[:m]
        for k_, j in enumerate(js): Y[j, i] = wv[k_]
    return Y, svals
def design_casc(pos, lo, hi, Teff=TEFF, q=13, seed=1, iters=3000):
    rs = np.random.RandomState(seed); cues = np.zeros((400, 17), bool)
    for t in range(400): cues[t, rs.choice(17, q, replace=False)] = True
    def comp(F):
        fired = cues.copy()
        for _ in range(17):
            new = (fired.astype(float) @ F >= Teff - 1e-9) & ~fired
            if not new.any(): break
            fired |= new
        return fired.all(1).mean()
    cur = hi.copy()
    for it in range(iters):
        i, j = rs.randint(17, size=2)
        if not pos[i, j]: continue
        Z = cur.copy(); Z[i, j] = max(lo[i, j], Z[i, j] * rs.uniform(0.5, 0.95))
        if comp(Z) >= 0.98 and rho(Z) < rho(cur): cur = Z
    return cur
if __name__ == '__main__':
    out = {}
    for seed in (66666, 77777):
        key, A, net, pos, G, lo, hi, LH = setup(seed)
        base = rescale(LH, pos, lo)
        Yw = design_W13(base, pos, lo, hi); np.save('p2_W13_s%d.npy' % seed, Yw)
        Yl, sv = lp_slack(G, lo, hi, pos); Yl = rescale(Yl, pos, lo); np.save('p2_LPS_s%d.npy' % seed, Yl)
        Yc = design_casc(pos, lo, hi, seed=seed); Yc = rescale(Yc, pos, lo); np.save('p2_CASC_s%d.npy' % seed, Yc)
        Yr = np.load('c10_m%d_soft_Y.npy' % seed); np.save('p2_RN_s%d.npy' % seed, Yr)
        for nm, Y in (('W13', Yw), ('LPS', Yl), ('CASC', Yc), ('RN', Yr)):
            ins = Y.sum(0) + (rn.member_matrices(key, 'LH', A)['member_input'] - rn.member_matrices(key, 'LH', A)['XA'].sum(0))
            out['%s_s%d' % (nm, seed)] = dict(rho=rho(Y), max_pair=float(Y.max()), min_in=float(Y.sum(0).min()), max_total_input=float(ins.max()), members_over_495=int((ins > 49.5 + 1e-6).sum()),
                                              w_over_G_min=float(np.min(Y[pos] / G[pos])), w_over_G_max=float(np.max(Y[pos] / G[pos])), worst13_min=float(worst13(Y).min()), n_pairs=int(pos.sum()))
            print(nm, seed, out['%s_s%d' % (nm, seed)], flush=True)
        out['LPS_s%d_slack_star' % seed] = sv
    json.dump(out, open('p2_designs.json', 'w'), indent=1, default=float)

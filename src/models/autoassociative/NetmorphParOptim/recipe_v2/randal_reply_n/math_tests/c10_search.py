"""C10: reduced-model (rn.py) design search on A17 member matrix. usage: c10_search.py SEED GENS CAPMODE(soft|none) [TAG]. Outputs c10_<tag>.json and design npy."""
import sys, json, time, numpy as np
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/loopedwsp_scout/stability')
import rn, fllib as FL
seed = int(sys.argv[1]); GENS = int(sys.argv[2]); capmode = sys.argv[3]; tag = sys.argv[4] if len(sys.argv) > 4 else 'm%d_%s' % (seed, capmode)
key = 's%d' % seed; alloc = json.load(open('/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/partial_cue/alloc_b.json')); A = list(alloc[key]['A17'])
net = FL.Net(key); ix = np.ix_(A, A); pos = net.pos[ix].copy(); np.fill_diagonal(pos, False); G = net.G[ix]; lo = np.where(pos, 0.1 * G, 0.); hi = np.where(pos, np.minimum(G, 6.86), 0.)
base_m = rn.member_matrices(key, 'LH', A, r=1.0); bg = base_m['member_input'] - base_m['XA'].sum(0)     # non-member + diagonal-free background input per member
def rho(Y): return float(np.max(np.abs(np.linalg.eigvals(Y))))
def scaled_E(target=16.5):
    M = base_m['XA'].copy(); lo_, hi_ = 0., 1.
    for _ in range(60):
        k = (lo_ + hi_) / 2; Y = np.where(pos, lo + k * (M - lo), 0.); lo_, hi_ = (k, hi_) if rho(Y) < target else (lo_, k)
    return np.where(pos, lo + k * (M - lo), 0.)
def boost(Y, target=16.5):
    for _ in range(60):
        ins = Y.sum(0); thr = ins.mean() - ins.std(); Z = Y.copy()
        for j in range(17):
            if ins[j] < thr:
                room = np.where(pos[:, j], hi[:, j] - Y[:, j], 0); need = ins.mean() - ins[j]
                if room.sum() > 0: Z[:, j] = Y[:, j] + room * min(1.0, need / room.sum())
        lo_, hi_ = 0., 1.
        for _ in range(50):
            k = (lo_ + hi_) / 2; W = np.where(pos, lo + k * (Z - lo), 0.); lo_, hi_ = (k, hi_) if rho(W) < target else (lo_, k)
        Y2 = np.where(pos, lo + k * (Z - lo), 0.)
        if np.abs(Y2 - Y).max() < 1e-4: break
        Y = Y2
    return Y
def make_events(rs, n=6):
    ev = []; kinds = []
    for kind, q in (('p75', 13), ('p50', 9), ('p25', 4), ('p1', 1)):
        for t in range(n):
            c = rs.choice(17, q, replace=False); ev.append([(1.0 + 0.5 * rs.rand(), int(i)) for i in c]); kinds.append((kind, set(int(i) for i in c)))
    return ev, kinds
DT = 0.1; TM = 300.
def evaluate(Y, ev, kinds, r=1.0):
    XN = np.minimum(r * Y, rn.NMDA_CAP * np.where(pos, G, 0.)); R = rn.sim(Y, XN, ev, T=TM, dt=DT)          # (steps, E, 17)
    res = {}; t = np.arange(R.shape[0]) * DT
    for k0 in ('p75', 'p50', 'p25', 'p1'): res[k0] = dict(n=0, comp=0, recruit=0, term=0, comp_term=0)
    for e, (kind, cued) in enumerate(kinds):
        sp = R[:, e, :] > 0; w = (t <= 31.0)
        fired = sp[w].any(0); unc = [i for i in range(17) if i not in cued]
        comp = all(fired[i] for i in unc) if unc else True; recruit = any(fired[i] for i in unc)
        last = t[np.where(sp.any(1))[0].max()] if sp.any() else 0.0; ended = last <= 100.0
        d = res[kind]; d['n'] += 1; d['comp'] += int(comp); d['recruit'] += int(recruit); d['term'] += int(ended); d['comp_term'] += int(comp and ended)
    return res
def J(res, Y, capmode):
    c75 = res['p75']['comp'] / res['p75']['n']; c50 = res['p50']['comp'] / res['p50']['n']
    rec = (res['p25']['recruit'] + res['p1']['recruit']) / (res['p25']['n'] + res['p1']['n'])
    nonterm = sum(res[k]['comp'] - res[k]['comp_term'] for k in ('p75', 'p50')) / max(1, res['p75']['n'] + res['p50']['n'])
    ins = Y.sum(0) + bg; over = np.clip(ins - 49.5, 0, None).sum()
    return 6 * c75 + 4 * c50 - 5 * rec - 5 * nonterm - (0.05 * over if capmode == 'soft' else 0.0) - 0.002 * rho(Y) * 0, dict(c75=c75, c50=c50, rec=rec, nonterm=nonterm, over=float(over))
rs = np.random.RandomState(100 + seed); evT, kT = make_events(rs); evH, kH = make_events(np.random.RandomState(900 + seed), n=12)
Y0 = boost(scaled_E(16.5)); base = {}
for nm, Yb in (('E16.5', scaled_E(16.5)), ('E16.5+boost', Y0)):
    rT = evaluate(Yb, evT, kT); rH = evaluate(Yb, evH, kH); base[nm] = dict(train=J(rT, Yb, capmode)[1], held=J(rH, Yb, capmode)[1], resH=rH, rho=rho(Yb))
    print(nm, base[nm]['train'], base[nm]['held'], flush=True)
cur = Y0.copy(); curJ, _ = J(evaluate(cur, evT, kT), cur, capmode); sig = 0.12; t0 = time.time(); hist = []
for g in range(GENS):
    cand = []
    for _ in range(10):
        Z = cur.copy(); m = (rs.rand(17, 17) < 0.25) & pos; Z = np.where(m, np.clip(Z + (hi - lo) * rs.randn(17, 17) * sig, lo, hi), Z)
        if rs.rand() < 0.3:  # also multiplicative global/column moves
            j = rs.randint(17); Z[:, j] = np.clip(lo[:, j] + (Z[:, j] - lo[:, j]) * np.exp(0.15 * rs.randn()), lo[:, j], hi[:, j])
        cand.append(Z)
    sc = [J(evaluate(Z, evT, kT), Z, capmode)[0] for Z in cand]; b = int(np.argmax(sc))
    if sc[b] > curJ: cur, curJ = cand[b], sc[b]
    else: sig = max(0.03, sig * 0.97)
    hist.append(float(curJ))
    if g % 10 == 0: print('gen', g, round(curJ, 3), round(sig, 3), round(time.time() - t0), flush=True)
rT = evaluate(cur, evT, kT); rH = evaluate(cur, evH, kH)
out = dict(seed=seed, capmode=capmode, gens=GENS, base=base, final=dict(train=J(rT, cur, capmode)[1], held=J(rH, cur, capmode)[1], resH=rH, resT=rT, rho=rho(cur), max_pair=float(cur.max()), min_input=float((cur.sum(0) + bg).min()), max_input=float((cur.sum(0) + bg).max())), hist=hist, members=A)
json.dump(out, open('c10_%s.json' % tag, 'w'), default=float); np.save('c10_%s_Y.npy' % tag, cur); print('FINAL', json.dumps(out['final']['held']), json.dumps(out['final']['train']), flush=True)

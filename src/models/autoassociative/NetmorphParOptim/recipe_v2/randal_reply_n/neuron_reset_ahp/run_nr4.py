#!/usr/bin/env python3
"""PREREGISTRATION_D runner. usage: run_nr4.py SEED LEVEL HOLD [--design-only]   LEVEL L1 (target = mean member in-assembly input) | L2 (mean + 1 SD); HOLD hold | free.
HOLD free: boost once on the rho-16.5 design (rho rises). HOLD hold: alternate boost and rescale of all member pairs above the 0.1 G floor
(X = fl + k (X - fl), k bisected so rho = 16.5) until the failing cells sit at the target of the final matrix and rho = 16.5 (fixed point, tol 1e-4 nS).
Base: E16.5 eigenvalue design (run_nr2.make_scaled, rho 16.5 before boost), original neurons (N0 copy), r 1.0, GABA x1, single-spike cue, 9,000 ms spacing.
Boost: for each preregistered failing cell m, every incoming member AMPA pair X[a, m] (a in A17, grown pair present) becomes min(s_m * X[a, m], min(G[a, m], 6.86)),
with s_m >= 1 found by bisection so that the in-assembly input sum_a X[a, m] equals the target (computed on the base design, before any boost).
Nothing else changes. Writes rawD_<tag>.json."""
import sys, os, json, shutil, time, numpy as np
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/neuron_reset_ahp')
import run_nr as NR, run_nr2 as NR2
SPACING = 9000.0; RHO = 16.5; CAP = 6.86
FAIL = {66666: [28, 46, 57], 77777: [65, 70]}
def rescale(Y, pos, fl, target):
    lo, hi = 0.0, 1.0
    for _ in range(60):
        k = (lo + hi) / 2; Z = np.where(pos, fl + k * (Y - fl), Y)
        lo, hi = (k, hi) if NR2.rho(Z) < target else (lo, k)
    return np.where(pos, fl + k * (Y - fl), Y), k
def boost_once(Y, pos, G, A, seed, level):
    inA = Y.sum(0); Y = Y.copy()
    target = float(inA.mean() + (inA.std() if level == 'L2' else 0.0)); rep = {}
    for m in FAIL[seed]:
        j = A.index(m); col = Y[:, j].copy(); ceil = np.where(pos[:, j], np.minimum(G[:, j], CAP), col)
        assert (col <= ceil + 1e-9).all()
        if col.sum() >= target: rep[m] = dict(s=1.0, before=float(col.sum()), after=float(col.sum()), reached=True); continue
        lo, hi = 1.0, 20.0
        for _ in range(80):
            s = (lo + hi) / 2; new = np.where(pos[:, j], np.minimum(s * col, ceil), col)
            lo, hi = (s, hi) if new.sum() < target else (lo, s)
        new = np.where(pos[:, j], np.minimum(s * col, ceil), col)
        rep[m] = dict(s=float(s), before=float(col.sum()), after=float(new.sum()), reached=bool(abs(new.sum() - target) < 1e-3), n_pairs_at_ceiling=int(((new >= ceil - 1e-9) & pos[:, j]).sum()),
                      max_pair=float(new.max()), max_w=float((new[pos[:, j]] / G[pos[:, j], j]).max()))
        Y[:, j] = new
    return Y, rep, target, inA
def make_boost(base_arm_matrix, seed, level, hold):
    def arm_matrix(net, A, arm):
        X, info = base_arm_matrix(net, A, arm); X = X.copy(); A = list(A); ix = np.ix_(A, A)
        Y0 = X[ix]; pos = net.pos[ix]; G = net.G[ix]; fl = net.fl[ix]; Y = Y0; it = 0; ks = []
        Y, rep, target, inA = boost_once(Y0, pos, G, A, seed, level)
        if hold:
            for it in range(1, 200):
                Y, k = rescale(Y, pos, fl, RHO); ks.append(k); Yb, rep, target, _ = boost_once(Y, pos, G, A, seed, level)
                done = abs(Yb.sum() - Y.sum()) < 1e-4; Y = Yb
                if done: break
            Y, k = rescale(Y, pos, fl, RHO); assert all(abs(Y[:, A.index(m)].sum() - target) < 1e-2 for m in FAIL[seed]), 'fixed point not reached'
        inA = Y0.sum(0)
        X[ix] = Y; w = Y[pos] / G[pos]; assert w.min() >= 0.1 - 1e-6 and w.max() <= 1.0 + 1e-6 and Y.max() <= CAP + 1e-6
        tot = X.sum(0)
        info = dict(info); info.update(boost_hold=hold, hold_iterations=it, hold_k_last=ks[-1] if ks else None, boost_level=level, boost_target=target, boost=rep, rho_after_boost=NR2.rho(Y), inA_before=[float(x) for x in inA], inA_failing_after={str(m): float(Y[:, A.index(m)].sum()) for m in FAIL[seed]}, inA_after=[float(x) for x in Y.sum(0)],
                    total_input_failing={str(m): float(tot[m]) for m in FAIL[seed]}, members_over_3T_after=int(sum(tot[m] > 49.5 + 1e-6 for m in A)), max_member_input_after=float(max(tot[m] for m in A)))
        make_boost.info = info; print('boost design', json.dumps(info), flush=True)
        return X, info
    return arm_matrix
def main():
    design_only = '--design-only' in sys.argv; args = [a for a in sys.argv[1:] if a != '--design-only']
    seed, level, hold = int(args[0]), args[1], args[2]; assert seed in FAIL and level in ('L1', 'L2') and hold in ('hold', 'free')
    import run_pl as M
    M.SP = SPACING; M.arm_matrix = make_boost(NR2.make_scaled(M.arm_matrix, RHO), seed, level, hold == 'hold')
    if design_only:
        import fllib as FL
        key = 's%d' % seed; D, _ = M.O.load(key); net = FL.Net(key); A = json.load(open(NR.PC + 'alloc_b.json'))[key]['A17']
        plist, Xm, info = M.plist_for(D, net, A, 'LH')
        print('SUMMARY', json.dumps(dict(seed=seed, level=level, hold=hold, iters=info['hold_iterations'], inA_failing_after={m: round(v, 2) for m, v in info['inA_failing_after'].items()}, target=round(info['boost_target'], 2), rho_after=round(info['rho_after_boost'], 3),
              boost={m: {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()} for m, r in info['boost'].items()},
              total_input_failing={m: round(v, 2) for m, v in info['total_input_failing'].items()}, members_over_3T=info['members_over_3T_after'],
              max_member_input=round(info['max_member_input_after'], 2), max_pair=round(max(c for a, b, c, g in plist if b < M.NP), 3))))
        return
    tag = 'D_E16.5_s%d_%s_%s' % (seed, level, hold); out_json = NR.HERE + 'rawD_%s.json' % tag
    assert not os.path.exists(out_json), out_json
    run_dir = NR.HERE + 'runs/%s/' % tag; os.makedirs(run_dir, exist_ok=True)
    shutil.copyfile(NR.PC + 'alloc_b.json', run_dir + 'alloc_b.json'); M.HERE = run_dir
    key = 's%d' % seed; orig = M.O.MODELS[key]['model']; copy = 'nr4-%s-%d' % (tag.replace('.', 'p'), int(time.time()))
    assert not os.path.exists(NR.MDIR + copy)
    rep = NR.patch_copy(NR.MDIR + orig, NR.MDIR + copy, 'N0'); print('patched', json.dumps(rep), flush=True)
    M.O.MODELS[key]['model'] = copy
    try:
        sys.argv = ['run', str(seed), 'LH', '1', '1']; M.main()
    finally:
        if os.path.exists(NR.MDIR + copy): os.remove(NR.MDIR + copy); print('removed copy', copy, flush=True)
    d = json.load(open(run_dir + 'rawB_s%d_LH_r1_f1.json' % seed))
    assert abs(d['events'][1]['t'] - d['events'][0]['t'] - SPACING) < 1e-6
    info = getattr(make_boost, 'info', None)
    d.update(design='LH', wdesign='E16.5', spacing_ms=SPACING, neuron_arm='N0', ncue=1, boost_level=level, boost_hold=hold, failing=FAIL[seed], neuron_patch=rep, model_copy=copy,
             model_orig=orig, nr_tag=tag, eigen=dict(info, eig_rho=info['rho_after_boost']) if info else None)
    json.dump(d, open(out_json, 'w'), separators=(',', ':'), default=float); print('wrote', out_json, flush=True)
if __name__ == '__main__': main()

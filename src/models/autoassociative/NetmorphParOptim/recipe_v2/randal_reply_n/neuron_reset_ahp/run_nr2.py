#!/usr/bin/env python3
"""PREREGISTRATION_B runner. usage: run_nr2.py WDESIGN SEED ARM R F   WDESIGN LH | E16 | E16.5 ; ARM N0 R S2 RS2 RS3.
Same as run_nr.py (model copy with patched pyramidal neuron fields, unchanged partial_cue/run_pl.py) plus: event spacing 9,000 ms (run_pl.SP),
and for E designs the member pairs of the LH matrix are rescaled above the 0.1 G floor (X = fl + k (X_LH - fl)) so that the dominant
eigenvalue of the 17x17 member AMPA matrix equals the target. Writes rawB2_<tag>.json."""
import sys, os, json, shutil, time, numpy as np
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/neuron_reset_ahp')
import run_nr as NR
SPACING = 9000.0
def rho(X): return float(max(abs(np.linalg.eigvals(X))))
def make_scaled(orig_arm_matrix, target):
    def arm_matrix(net, A, arm):
        assert arm == 'LH'
        X, info = orig_arm_matrix(net, A, arm); X = X.copy(); ix = np.ix_(A, A); pos = net.pos[ix]; fl = net.fl[ix]; M = X[ix]
        assert np.allclose(fl[pos], 0.1 * net.G[ix][pos], rtol=1e-4)
        lo, hi = 0.0, 1.0
        for _ in range(60):
            k = (lo + hi) / 2; Y = np.where(pos, fl + k * (M - fl), M)
            lo, hi = (k, hi) if rho(Y) < target else (lo, k)
        Y = np.where(pos, fl + k * (M - fl), M); X[ix] = Y
        w = Y[pos] / net.G[ix][pos]; assert w.min() >= 0.1 - 1e-6 and w.max() <= 1.0 + 1e-6
        info = dict(info); info.update(eig_target=target, eig_k=k, eig_rho=rho(Y), eig_rho_LH=rho(M), member_w_min=float(w.min()), member_w_mean=float(w.mean()), member_w_max=float(w.max()))
        make_scaled.info = info; print('eigen design', json.dumps(info), flush=True)
        return X, info
    return arm_matrix
def main():
    wd, seed, arm, r, f = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5]
    assert wd in ('LH', 'E16', 'E16.5') and arm in NR.ARMS
    tag = 'B2_%s_s%d_%s_r%s_f%s' % (wd, seed, arm, r, f); out_json = NR.HERE + 'rawB2_%s.json' % tag
    assert not os.path.exists(out_json), out_json
    run_dir = NR.HERE + 'runs/%s/' % tag; os.makedirs(run_dir, exist_ok=True)
    import run_pl as M
    shutil.copyfile(NR.PC + 'alloc_b.json', run_dir + 'alloc_b.json'); M.HERE = run_dir; M.SP = SPACING
    if wd != 'LH': M.arm_matrix = make_scaled(M.arm_matrix, float(wd[1:]))
    key = 's%d' % seed; orig = M.O.MODELS[key]['model']; copy = 'nr2-%s-%d' % (tag.replace('.', 'p'), int(time.time()))
    assert not os.path.exists(NR.MDIR + copy)
    rep = NR.patch_copy(NR.MDIR + orig, NR.MDIR + copy, arm); print('patched', json.dumps(rep), flush=True)
    M.O.MODELS[key]['model'] = copy
    try:
        sys.argv = ['run', str(seed), 'LH', r, f]; M.main()
    finally:
        if os.path.exists(NR.MDIR + copy): os.remove(NR.MDIR + copy); print('removed copy', copy, flush=True)
    d = json.load(open(run_dir + 'rawB_s%d_LH_r%s_f%s.json' % (seed, r, f)))
    assert abs(d['events'][1]['t'] - d['events'][0]['t'] - SPACING) < 1e-6
    d.update(design='LH', wdesign=wd, spacing_ms=SPACING, neuron_arm=arm, neuron_patch=rep, model_copy=copy, model_orig=orig, nr_tag=tag,
             eigen=getattr(make_scaled, 'info', None) if wd != 'LH' else None)
    json.dump(d, open(out_json, 'w'), separators=(',', ':'), default=float); print('wrote', out_json, flush=True)
if __name__ == '__main__': main()

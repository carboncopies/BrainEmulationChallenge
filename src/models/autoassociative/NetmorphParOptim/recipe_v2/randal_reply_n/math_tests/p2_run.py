#!/usr/bin/env python3
"""PHASE 2 runner (PREREGISTRATION_P2.md). usage: p2_run.py SEED DESIGN API_PORT [--design-only]. DESIGN in BASE W13 LPS CASC RN E20. Own patched instance only (API_PORT).
BASE = stored recipe via run_nr5.make_arm(M, seed, 'P'); math designs replace the member block of the LH arm matrix by p2_<DESIGN>_s<seed>.npy. Writes rawP2_<tag>.json."""
import sys, os, json, time, numpy as np
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/neuron_reset_ahp')
import run_nr as NR, run_nr5 as NR5
HERE = '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/math_tests/'; CUEKEY = 'M2025-'; SPACING = 9000.0
def main():
    flags = [a for a in sys.argv[1:] if a.startswith('--')]; args = [a for a in sys.argv[1:] if not a.startswith('--')]
    seed, design, port = int(args[0]), args[1], int(args[2]); assert seed in (66666, 77777) and design in ('BASE', 'W13', 'LPS', 'CASC', 'RN', 'E20')
    import run_pl as M
    M.X.PORT = port; key = 's%d' % seed; A17 = json.load(open(NR.PC + 'alloc_b.json'))[key]['A17']
    M.SP = SPACING; orig_make = M.make_events; M.make_events = lambda A, k: orig_make(A, CUEKEY + k)
    if design == 'BASE':
        M.arm_matrix = NR5.make_arm(M, seed, 'P'); info_holder = NR5.make_arm
    else:
        Y = np.load(HERE + 'p2_%s_s%d.npy' % (design, seed)); orig_arm = M.arm_matrix
        def arm_matrix(net, A, a):
            X0, info0 = orig_arm(net, A, a); X = X0.copy(); A = list(A); ix = np.ix_(A, A); pos = net.pos[ix].copy(); np.fill_diagonal(pos, False)
            assert np.all(Y[~pos] == 0) and np.all(Y[pos] >= 0.1 * net.G[ix][pos] - 1e-6) and np.all(Y[pos] <= np.minimum(net.G[ix][pos], 6.86) + 1e-6)
            X[ix] = Y; info = dict(info0); r = float(np.max(np.abs(np.linalg.eigvals(Y)))); info.update(arm=design, eig_rho=r, rho_after_boost=r); arm_matrix.info = info; return X, info
        M.arm_matrix = arm_matrix
    tag = 'P2_%s_s%d' % (design, seed); out_json = HERE + 'rawP2_%s.json' % tag
    if '--design-only' in flags:
        import fllib as FL
        D, _ = M.O.load(key); net = FL.Net(key); plist, Xm, info = M.plist_for(D, net, A17, 'LH'); ins = Xm.sum(0)
        print(json.dumps(dict(tag=tag, n_plist=len(plist), max_pair=max(c for a, b, c, g in plist if b < 96), members_over_3T=int(sum(ins[m] > 49.5 + 1e-6 for m in A17)), max_member_input=round(float(max(ins[m] for m in A17)), 2),
                              rho=round(float(info.get('eig_rho', info.get('rho_after_boost', 0))), 3)))); return
    assert not os.path.exists(out_json), out_json
    run_dir = HERE + 'runs/%s/' % tag; os.makedirs(run_dir, exist_ok=True)
    import shutil; shutil.copyfile(NR.PC + 'alloc_b.json', run_dir + 'alloc_b.json'); M.HERE = run_dir
    sys.argv = ['run', str(seed), 'LH', '1', '1']; M.main()
    d = json.load(open(run_dir + 'rawB_s%d_LH_r1_f1.json' % seed)); assert abs(d['events'][1]['t'] - d['events'][0]['t'] - SPACING) < 1e-6
    info = NR5.make_arm.info if design == 'BASE' else M.arm_matrix.info
    rho = info.get('rho_after_boost', info.get('eig_rho'))
    d.update(design='LH', wdesign=design, spacing_ms=SPACING, neuron_arm='N0', ncue=1, cue_key=CUEKEY + key, boost_arm=design, boost_level='L1' if design == 'BASE' else design, boost_hold='hold', failing=[], nr_tag=tag, eigen=dict(eig_rho=rho), api_port=port)
    json.dump(d, open(out_json, 'w'), separators=(',', ':'), default=float); print('wrote', out_json, flush=True)
if __name__ == '__main__': main()

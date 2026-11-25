#!/usr/bin/env python3
"""PREREGISTRATION_E runner. usage: run_nr5.py SEED ARM [--design-only | --cues-only]   ARM D (boost cells = step-D failing cells) | P (pre-fixed: members with
in-assembly input < mean - 1 SD on the base E16.5 matrix, selected once from the matrix only).
Both arms: boost the selected cells to the mean member in-assembly input (L1) with rho held at 16.5 (run_nr4 fixed point), original neurons (N0 copy), r 1.0, GABA x1,
single-spike cue, 9,000 ms spacing. NEW cue subsets: run_pl.make_events with the key CUEKEY + key (RNG seed crc32('pl-E1111-s<seed>'); index 1111 = first index meeting the PREREGISTRATION_E coverage rule), shared by both arms.
Writes rawE_<tag>.json."""
import sys, os, json, shutil, time, numpy as np
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/neuron_reset_ahp')
import run_nr as NR, run_nr2 as NR2, run_nr4 as NR4
CUEKEY = 'E1111-'; SPACING = 9000.0; RHO = 16.5; DFAIL = {66666: [28, 46, 57], 77777: [65, 70]}
def new_cues(orig_make_events):
    def make_events(A, key): return orig_make_events(A, CUEKEY + key)
    return make_events
def make_arm(M, seed, arm):
    base = NR2.make_scaled(M.arm_matrix, RHO)
    def arm_matrix(net, A, a):
        X0, info0 = base(net, A, a); A = list(A); inA = X0[np.ix_(A, A)].sum(0)
        cells = DFAIL[seed] if arm == 'D' else [m for j, m in enumerate(A) if inA[j] < inA.mean() - inA.std()]
        NR4.FAIL[seed] = list(cells)
        X, info = NR4.make_boost(lambda n, AA, aa: (X0.copy(), info0), seed, 'L1', True)(net, A, a)
        info = dict(info); info.update(arm=arm, boost_cells=[int(c) for c in cells], select_threshold=float(inA.mean() - inA.std()), inA_base={str(m): float(inA[j]) for j, m in enumerate(A)})
        make_arm.info = info; return X, info
    return arm_matrix
def main():
    flags = [a for a in sys.argv[1:] if a.startswith('--')]; args = [a for a in sys.argv[1:] if not a.startswith('--')]
    seed, arm = int(args[0]), args[1]; assert seed in DFAIL and arm in ('D', 'P')
    import run_pl as M
    key = 's%d' % seed; A17 = json.load(open(NR.PC + 'alloc_b.json'))[key]['A17']
    M.SP = SPACING; M.make_events = new_cues(M.make_events); M.arm_matrix = make_arm(M, seed, arm)
    if '--cues-only' in flags:
        ev, run_ms = M.make_events(A17, key); print(json.dumps(dict(seed=seed, run_ms=run_ms, events=[dict(i=i, kind=e['kind'], cue=e['cue']) for i, e in enumerate(ev)]))); return
    if '--design-only' in flags:
        import fllib as FL
        D, _ = M.O.load(key); net = FL.Net(key); plist, Xm, info = M.plist_for(D, net, A17, 'LH')
        print('SUMMARY', json.dumps(dict(seed=seed, arm=arm, cells=info['boost_cells'], threshold=round(info['select_threshold'], 2), inA_base={m: round(info['inA_base'][str(m)], 2) for m in info['boost_cells']},
              inA_after={m: round(v, 2) for m, v in info['inA_failing_after'].items()}, iters=info['hold_iterations'], rho=round(info['rho_after_boost'], 3),
              other_mean_after=round(float(np.mean([v for j, v in enumerate(info['inA_after']) if A17[j] not in info['boost_cells']])), 2),
              total_input_boosted={m: round(v, 2) for m, v in info['total_input_failing'].items()}, members_over_3T=info['members_over_3T_after'],
              max_member_input=round(info['max_member_input_after'], 2), max_pair=round(max(c for a, b, c, g in plist if b < M.NP), 3))))
        return
    tag = 'E_%s_s%d' % (arm, seed); out_json = NR.HERE + 'rawE_%s.json' % tag
    assert not os.path.exists(out_json), out_json
    run_dir = NR.HERE + 'runs/%s/' % tag; os.makedirs(run_dir, exist_ok=True)
    shutil.copyfile(NR.PC + 'alloc_b.json', run_dir + 'alloc_b.json'); M.HERE = run_dir
    orig = M.O.MODELS[key]['model']; copy = 'nr5-%s-%d' % (tag, int(time.time())); assert not os.path.exists(NR.MDIR + copy)
    rep = NR.patch_copy(NR.MDIR + orig, NR.MDIR + copy, 'N0'); print('patched', json.dumps(rep), flush=True)
    M.O.MODELS[key]['model'] = copy
    try:
        sys.argv = ['run', str(seed), 'LH', '1', '1']; M.main()
    finally:
        if os.path.exists(NR.MDIR + copy): os.remove(NR.MDIR + copy); print('removed copy', copy, flush=True)
    d = json.load(open(run_dir + 'rawB_s%d_LH_r1_f1.json' % seed))
    assert abs(d['events'][1]['t'] - d['events'][0]['t'] - SPACING) < 1e-6
    info = make_arm.info
    d.update(design='LH', wdesign='E16.5', spacing_ms=SPACING, neuron_arm='N0', ncue=1, cue_key=CUEKEY + key, boost_arm=arm, boost_level='L1', boost_hold='hold',
             failing=info['boost_cells'], neuron_patch=rep, model_copy=copy, model_orig=orig, nr_tag=tag, eigen=dict(info, eig_rho=info['rho_after_boost']))
    json.dump(d, open(out_json, 'w'), separators=(',', ':'), default=float); print('wrote', out_json, flush=True)
if __name__ == '__main__': main()

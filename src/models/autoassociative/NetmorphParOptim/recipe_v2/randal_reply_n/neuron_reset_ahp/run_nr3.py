#!/usr/bin/env python3
"""PREREGISTRATION_C runner. usage: run_nr3.py WDESIGN SEED NCUE   WDESIGN E16 | E16.7 | E16.9 | E17.1 ; NCUE 1 | 2.
Original neurons only (arm N0: model-file copy with no field changed, same route as B2), r 1.0, GABA x1, 9,000 ms spacing, unchanged run_pl.py.
Member pairs rescaled above the 0.1 G floor so that the dominant eigenvalue of the 17x17 member AMPA matrix equals the target (run_nr2.make_scaled).
NCUE 2: every forced cue spike (every cue kind) gets a second forced spike on the same cell 4.0 ms later. Writes rawC_<tag>.json.
--design-only: print the eigen design (k, weights, member input) and exit without a simulation."""
import sys, os, json, shutil, time
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/neuron_reset_ahp')
import run_nr as NR, run_nr2 as NR2
SPACING = 9000.0; DT2 = 4.0; WDS = ('E16', 'E16.7', 'E16.9', 'E17.1')
def two_spike(orig_make_events):
    def make_events(A, key):
        ev, run_ms = orig_make_events(A, key)
        for e in ev:
            e['cues1'] = list(e['cues']); e['cues'] = sorted(e['cues'] + [(t + DT2, c) for t, c in e['cues']])
        return ev, run_ms
    return make_events
def main():
    design_only = '--design-only' in sys.argv; args = [a for a in sys.argv[1:] if a != '--design-only']
    wd, seed, ncue = args[0], int(args[1]), int(args[2]); assert wd in WDS and ncue in (1, 2)
    import run_pl as M
    M.SP = SPACING; M.arm_matrix = NR2.make_scaled(M.arm_matrix, float(wd[1:]))
    if design_only:
        import numpy as np, fllib as FL
        key = 's%d' % seed; D, _ = M.O.load(key); net = FL.Net(key); A = json.load(open(NR.PC + 'alloc_b.json'))[key]['A17']
        plist, Xm, info = M.plist_for(D, net, A, 'LH'); ins = Xm.sum(0)
        print(json.dumps(dict(wd=wd, seed=seed, k=round(info['eig_k'], 4), rho=round(info['eig_rho'], 3), w=[round(info[x], 3) for x in ('member_w_min', 'member_w_mean', 'member_w_max')],
                              max_pair=round(max(c for a, b, c, g in plist if b < M.NP), 3), max_member_input=round(float(max(ins[m] for m in A)), 2),
                              members_over_3T=int(sum(ins[m] > 49.5 + 1e-6 for m in A)))))
        return
    tag = 'C_%s_s%d_cue%d' % (wd, seed, ncue); out_json = NR.HERE + 'rawC_%s.json' % tag
    assert not os.path.exists(out_json), out_json
    run_dir = NR.HERE + 'runs/%s/' % tag; os.makedirs(run_dir, exist_ok=True)
    shutil.copyfile(NR.PC + 'alloc_b.json', run_dir + 'alloc_b.json'); M.HERE = run_dir
    if ncue == 2: M.make_events = two_spike(M.make_events)
    key = 's%d' % seed; orig = M.O.MODELS[key]['model']; copy = 'nr3-%s-%d' % (tag.replace('.', 'p'), int(time.time()))
    assert not os.path.exists(NR.MDIR + copy)
    rep = NR.patch_copy(NR.MDIR + orig, NR.MDIR + copy, 'N0'); print('patched', json.dumps(rep), flush=True)
    M.O.MODELS[key]['model'] = copy
    try:
        sys.argv = ['run', str(seed), 'LH', '1', '1']; M.main()
    finally:
        if os.path.exists(NR.MDIR + copy): os.remove(NR.MDIR + copy); print('removed copy', copy, flush=True)
    d = json.load(open(run_dir + 'rawB_s%d_LH_r1_f1.json' % seed))
    assert abs(d['events'][1]['t'] - d['events'][0]['t'] - SPACING) < 1e-6
    d.update(design='LH', wdesign=wd, spacing_ms=SPACING, neuron_arm='N0', ncue=ncue, cue_dt2=DT2 if ncue == 2 else None, neuron_patch=rep, model_copy=copy,
             model_orig=orig, nr_tag=tag, eigen=getattr(NR2.make_scaled, 'info', None))
    json.dump(d, open(out_json, 'w'), separators=(',', ':'), default=float); print('wrote', out_json, flush=True)
if __name__ == '__main__': main()

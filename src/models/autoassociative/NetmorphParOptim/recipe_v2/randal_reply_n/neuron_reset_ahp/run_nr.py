#!/usr/bin/env python3
"""neuron_reset_ahp runner (PREREGISTRATION.md). PATCHED instance only (API 8010 / NES 8011).
usage: run_nr.py DESIGN SEED ARM R F   DESIGN LH (partial_cue/run_pl.py arm LH) | D0 (partial_cue/run_pc.py design D0); ARM N0 R S2 RS2 RS3.
Makes a COPY of the model in the instance's model folder, patches neuron fields of pyramidal cells 0-95 only, reads them back, runs the unchanged
partial_cue code with the copy substituted (per-run output folder), deletes the copy in finally. Writes raw_<tag>.json + neuron_patch report."""
import sys, os, json, shutil, time, numpy as np
HERE = '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/neuron_reset_ahp/'
PC = '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/partial_cue/'
MDIR = '/home/johnjose/BrainGenix/wt/linefix-instance/out/Admonishing/Models/'
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/gaba_vm'); sys.path.insert(0, PC)
from modelfile import neurons, NDT
NP, N = 96, 116
ARMS = {'N0': {}, 'R': dict(ResetMethod=2, Vreset=-55.0),
        'S2': dict(sAHP_g=2.0, sAHP_gmax=4.0, sAHP_decay=1000.0),
        'RS2': dict(ResetMethod=2, Vreset=-55.0, sAHP_g=2.0, sAHP_gmax=4.0, sAHP_decay=1000.0),
        'RS3': dict(ResetMethod=2, Vreset=-55.0, sAHP_g=3.0, sAHP_gmax=6.0, sAHP_decay=1500.0)}
FIELDS = ('ResetMethod', 'Vreset', 'Vth', 'sAHP_rise', 'sAHP_decay', 'sAHP_g', 'sAHP_gmax', 'AHPsat', 'fAHP_g', 'fAHP_gmax')
EXPECT_ORIG = dict(ResetMethod=0, Vreset=-55.0, sAHP_g=1.0, sAHP_gmax=2.0, sAHP_decay=300.0, sAHP_rise=30.0, AHPsat=0)

def patch_copy(src, dst, arm):
    shutil.copyfile(src, dst)
    h, roff, nl = neurons(dst, N); mm = np.memmap(dst, dtype='u1', mode='r+')
    for k, n_ in enumerate(nl[:NP]):
        v = np.ndarray(shape=(1,), dtype=NDT, buffer=mm, offset=n_['off'])
        for f, want in EXPECT_ORIG.items(): assert abs(float(v[f][0]) - want) < 1e-4, (k, f, float(v[f][0]))
        for f, val in ARMS[arm].items(): v[f] = val
    mm.flush(); del mm
    h2, _, nl2 = neurons(dst, N); h0, _, nl0 = neurons(src, N)
    for k in range(N):   # read back: pyramids = arm values, everything else identical to the original
        a, b = nl2[k]['rec'], nl0[k]['rec']
        for f in NDT.names:
            if f == 'hdr': continue
            want = ARMS[arm].get(f, None) if k < NP else None
            if want is None: assert np.array_equal(a[f], b[f]), (k, f)
            else: assert abs(float(a[f]) - want) < 1e-4, (k, f)
    assert os.path.getsize(dst) == os.path.getsize(src)
    return dict(arm=arm, set=ARMS[arm], pyr0={f: float(nl2[0]['rec'][f]) for f in FIELDS}, int96={f: float(nl2[96]['rec'][f]) for f in FIELDS},
                pyr_checked=NP, all_other_fields_identical=True)

def main():
    design, seed, arm, r, f = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5]
    assert design in ('LH', 'D0') and arm in ARMS
    tag = '%s_s%d_%s_r%s_f%s' % (design, seed, arm, r, f); out_json = HERE + 'raw_%s.json' % tag
    assert not os.path.exists(out_json), out_json
    run_dir = HERE + 'runs/%s/' % tag; os.makedirs(run_dir, exist_ok=True)
    if design == 'LH':
        import run_pl as M; shutil.copyfile(PC + 'alloc_b.json', run_dir + 'alloc_b.json'); argv = [str(seed), 'LH', r, f]
        res = run_dir + 'rawB_s%d_LH_r%s_f%s.json' % (seed, r, f)
    else:
        import run_pc as M; argv = [str(seed), 'D0', r, f]; res = run_dir + 'raw_s%d_D0_r%s_f%s.json' % (seed, r, f)
    M.HERE = run_dir
    key = 's%d' % seed; orig = M.O.MODELS[key]['model']; copy = 'nr-%s-%d' % (tag.replace('.', 'p'), int(time.time()))
    assert not os.path.exists(MDIR + copy)
    rep = patch_copy(MDIR + orig, MDIR + copy, arm); print('patched', json.dumps(rep), flush=True)
    M.O.MODELS[key]['model'] = copy
    try:
        sys.argv = ['run'] + argv; M.main()
    finally:
        if os.path.exists(MDIR + copy): os.remove(MDIR + copy); print('removed copy', copy, flush=True)
    d = json.load(open(res)); d.update(design=design, neuron_arm=arm, neuron_patch=rep, model_copy=copy, model_orig=orig, nr_tag=tag)
    json.dump(d, open(out_json, 'w'), separators=(',', ':'), default=float); print('wrote', out_json, flush=True)

if __name__ == '__main__': main()

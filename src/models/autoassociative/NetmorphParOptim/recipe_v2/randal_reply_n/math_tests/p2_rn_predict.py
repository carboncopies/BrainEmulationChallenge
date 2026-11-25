"""reduced-model predictions (rn.py) of the phase-2 designs on the NEW cue set (key M2025-): written to p2_rn_pred.json BEFORE any phase-2 sim. Also saves the cue set."""
import sys, json, numpy as np
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/partial_cue'); sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/nmda_gaba_exp')
import run_pl as RP
import design_p2 as D, rn
CUEKEY = 'M2025-'; out = {}
def design_P(Y0, pos, lo, hi):
    Y = Y0.copy()
    for it in range(60):
        ins = Y.sum(0); thr = ins.mean() - ins.std(); Z = Y.copy()
        for j in range(17):
            if ins[j] < thr:
                room = np.where(pos[:, j], hi[:, j] - Y[:, j], 0); need = ins.mean() - ins[j]
                if room.sum() > 0: Z[:, j] = Y[:, j] + room * min(1.0, need / room.sum())
        Y2 = D.rescale(Z, pos, lo)
        if np.abs(Y2 - Y).max() < 1e-4: break
        Y = Y2
    return Y
for seed in (66666, 77777):
    key, A, net, pos, G, lo, hi, LH = D.setup(seed)
    RP.SP = 9000.0; ev, run_ms = RP.make_events(A, CUEKEY + key); idx = {c: i for i, c in enumerate(A)}
    cues = [[(t - e['t'], idx[c]) for (t, c) in e['cues'] if c in idx] for e in ev]; kinds = [e['kind'] for e in ev]
    json.dump(dict(seed=seed, key=CUEKEY + key, kinds=kinds, cues=[e['cue'] for e in ev]), open('p2_cues_s%d.json' % seed, 'w'))
    base = D.rescale(LH, pos, lo); designs = {'BASE': design_P(base, pos, lo, hi)}
    for nm in ('W13', 'LPS', 'CASC', 'RN', 'E20'): designs[nm] = np.load('p2_%s_s%d.npy' % (nm, seed))
    np.save('p2_BASEmodel_s%d.npy' % seed, designs['BASE'])
    for nm, Y in designs.items():
        XN = np.minimum(1.0 * Y, rn.NMDA_CAP * np.where(pos, G, 0.)); R = rn.sim(Y, XN, cues, T=300., dt=0.1); t = np.arange(R.shape[0]) * 0.1; res = {}
        for e, (kind, ce) in enumerate(zip(kinds, cues)):
            cued = set(m for _, m in ce); sp = R[:, e, :] > 0; fired = sp[t <= 31].any(0); unc = [i for i in range(17) if i not in cued]
            comp = all(fired[i] for i in unc) if unc else True; rec = any(fired[i] for i in unc); last = float(t[np.where(sp.any(1))[0].max()]) if sp.any() else 0.
            d = res.setdefault(kind, dict(n=0, comp=0, recruit=0, ended100=0)); d['n'] += 1; d['comp'] += int(comp); d['recruit'] += int(rec); d['ended100'] += int(last <= 100.)
        out['%s_s%d' % (nm, seed)] = res; print(nm, seed, {k: (v['comp'], v['recruit'], v['ended100'], v['n']) for k, v in res.items()}, flush=True)
json.dump(out, open('p2_rn_pred.json', 'w'), indent=1)

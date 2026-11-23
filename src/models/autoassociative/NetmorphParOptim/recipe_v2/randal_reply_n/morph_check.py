#!/usr/bin/env python3
"""(C) morphology check: quantitative flags + PNGs from NetMorph node files. usage: morph_check.py LABEL=OUTDIR ... (or LABEL=@tag using pv_results.json outdir / models.json).
Writes morph_check.json and png/<label>_*.png. Disc centre assumed (0,0,-300) (region In centerZ -300; radius 120, thickness 30)."""
import sys, os, json, glob, collections, numpy as np
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n')
import morph_e4 as ME
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
HERE = '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/'; C0 = np.array([0., 0., -300.]); R = 120.; HT = 15.
def analyse(label, d):
    nt, pos, par, typ, soma, kind = ME.load(d)
    ids = [i for i in par if par[i] in pos]
    cells = collections.defaultdict(list)
    for i in ids: cells[(soma[i], typ[i])].append(i)
    ctype = {s: nt[s][0] for s in nt}
    out = dict(label=label, dir=d, n_nodes=len(ids)); fib = {}
    seglen = np.array([np.linalg.norm(pos[i] - pos[par[i]]) for i in ids]); out['max_segment_um'] = float(seglen.max()); out['n_segments_gt25um'] = int((seglen > 25).sum()); out['p99_segment_um'] = float(np.percentile(seglen, 99))
    # per fibre class
    for cls in ('interneuron|axon', 'interneuron|dendrite', 'pyramidal|axon', 'pyramidal|dendrite'):
        ct, t = cls.split('|'); P = [i for (s, tt), L in cells.items() if tt == t and ctype[s] == ct for i in L]
        if not P: continue
        xyz = np.array([pos[i] for i in P]) - C0; rad = np.hypot(xyz[:, 0], xyz[:, 1]); z = np.abs(xyz[:, 2])
        fib[cls] = dict(n=len(P), frac_outside_disc_radius=float((rad > R).mean()), frac_outside_slab=float((z > HT).mean()), frac_beyond_2x_radius=float((rad > 2 * R).mean()),
                        median_radius=float(np.median(rad)), p99_radius=float(np.percentile(rad, 99)), centre_density_ratio=None)
        # node density per volume: centre r<40 vs rim 80<r<120, over |z|<=60 (the same z range)
        m = z <= 60; ctr = ((rad < 40) & m).sum() / (np.pi * 40 ** 2); rim = (((rad >= 80) & (rad < 120)) & m).sum() / (np.pi * (120 ** 2 - 80 ** 2)); fib[cls]['centre_density_ratio'] = float(ctr / rim) if rim else None
    out['fibres'] = fib
    # tip straightness + self contact for interneuron axons (sample up to 6 cells) and pyramidal axons (6 cells)
    chld = collections.defaultdict(list)
    for i in ids: chld[par[i]].append(i)
    def tips_straight(sm, t):
        tips = [i for i in cells[(sm, t)] if kind[i] == 'growthcones']; vals = []
        root = [i for i in pos if kind.get(i) == 'rootnodes' and soma.get(i) == sm]
        for tp in tips[:400]:
            L = 0.; j = tp; k = 0
            while j in par and par[j] in pos and k < 20000:
                L += np.linalg.norm(pos[j] - pos[par[j]]); j = par[j]; k += 1
            if L > 0: vals.append(float(np.linalg.norm(pos[tp] - pos[j]) / L))
        return vals
    def selfcontact(sm, t):
        P = cells[(sm, t)]; X = np.array([pos[i] for i in P]); from scipy.spatial import cKDTree
        tr = cKDTree(X); pairs = tr.query_pairs(2.0); idx = {i: n for n, i in enumerate(P)}
        near = set()
        for a, b in pairs:
            ia, ib = P[a], P[b]
            # skip near relatives: walk up 10 parents
            anc = set(); j = ia; 
            for _ in range(10):
                if j not in par: break
                j = par[j]; anc.add(j)
            if ib in anc or par.get(ib) == ia: continue
            anc2 = set(); j = ib
            for _ in range(10):
                if j not in par: break
                j = par[j]; anc2.add(j)
            if ia in anc2 or (anc & anc2): continue
            near.add(a); near.add(b)
        return len(near) / len(P)
    sel = collections.defaultdict(list)
    for (s, t), L in cells.items(): sel[(ctype[s], t)].append(s)
    for key in (('interneuron', 'axon'), ('pyramidal', 'axon')):
        ss = sorted(sel[key])[:6]; st = []; sc = []
        for sm in ss: st += tips_straight(sm, key[1]); sc.append(selfcontact(sm, key[1]))
        out['%s_%s_tip_straightness_median' % key] = float(np.median(st)) if st else None; out['%s_%s_selfcontact_frac_mean' % key] = float(np.mean(sc))
    # PNGs
    os.makedirs(HERE + 'png', exist_ok=True)
    def segs(sm, t, step=1):
        L = cells[(sm, t)][::step]; return [(pos[par[i]], pos[i]) for i in L]
    ints = sorted(sel[('interneuron', 'axon')]); pyrs = sorted(sel[('pyramidal', 'axon')])
    fig, ax = plt.subplots(1, 2, figsize=(15, 7))
    cmap = plt.get_cmap('tab20')
    for n, sm in enumerate(pyrs):
        for k, (a, b) in enumerate([(0, 1), (0, 2)]):
            S = segs(sm, 'axon', 6); ax[k].add_collection(LineCollection([[(p[a], p[b]), (q[a], q[b])] for p, q in S], colors=(0.5, 0.5, 0.5, 0.12), linewidths=0.25))
    for n, sm in enumerate(ints):
        for k, (a, b) in enumerate([(0, 1), (0, 2)]):
            S = segs(sm, 'axon', 2); ax[k].add_collection(LineCollection([[(p[a], p[b]), (q[a], q[b])] for p, q in S], colors=[cmap(n % 20)], linewidths=0.4, alpha=0.7))
    th = np.linspace(0, 2 * np.pi, 200); ax[0].plot(R * np.cos(th), R * np.sin(th), 'k--', lw=0.8); ax[1].plot([-R, R, R, -R, -R], [-300 - HT, -300 - HT, -300 + HT, -300 + HT, -300 - HT], 'k--', lw=0.8)
    for k, tl in enumerate(('top view (x,y)', 'side view (x,z)')): ax[k].set_title('%s  %s  (grey: pyramidal axons 1/6 of nodes; colours: 20 interneuron axons; dashed: disc / slab)' % (label, tl), fontsize=7); ax[k].autoscale(); ax[k].set_aspect('equal')
    fig.tight_layout(); fig.savefig(HERE + 'png/%s_network.png' % label, dpi=110); plt.close(fig)
    fig, ax = plt.subplots(2, 3, figsize=(15, 9)); pick = ints[:3] + pyrs[:3]
    for q, sm in enumerate(pick):
        a_ = ax[q // 3][q % 3]; isint = q < 3
        for t, col, lw in (('axon', 'tab:red' if isint else 'tab:orange', 0.5), ('dendrite', 'tab:blue', 0.5)):
            if (sm, t) in cells: a_.add_collection(LineCollection([[(p[0], p[1]), (qq[0], qq[1])] for p, qq in segs(sm, t, 1)], colors=col, linewidths=lw))
        a_.plot(*nt[sm][1][:2], 'ko', ms=5); a_.plot(R * np.cos(th), R * np.sin(th), 'k--', lw=0.6); a_.autoscale(); a_.set_aspect('equal'); a_.set_title('%s %s soma %s (red/orange axon, blue dendrite), top view' % (label, 'interneuron' if isint else 'pyramidal', sm), fontsize=7)
    fig.tight_layout(); fig.savefig(HERE + 'png/%s_cells.png' % label, dpi=110); plt.close(fig)
    return out
if __name__ == '__main__':
    res = json.load(open(HERE + 'morph_check.json')) if os.path.exists(HERE + 'morph_check.json') else {}
    for a in sys.argv[1:]:
        lab, d = a.split('=', 1)
        if d.startswith('@'): d = ME.finddir(json.load(open(HERE + 'models.json'))[d[1:]])
        res[lab] = analyse(lab, d); r = res[lab]; print(lab, 'maxseg %.1f gt25 %d' % (r['max_segment_um'], r['n_segments_gt25um']), {k: round(v['frac_outside_slab'], 2) for k, v in r['fibres'].items()}, flush=True)
        json.dump(res, open(HERE + 'morph_check.json', 'w'), indent=1)

#!/usr/bin/env python3
"""#3 metrics for C1 growths and baselines (index blocks 6g..6g+5, g = 0..7 as pseudo-groups for baselines). usage: c1_metrics.py SEED -> c1_metrics_<seed>.json"""
import sys, json, itertools, numpy as np
R = '/home/johnjose/cos/netmorph_work/recipe_v2/'; HERE = R + 'randal_reply_n/fresh_run/'
def mats(path):
    d = json.load(open(path)); typ = {n['id']: n['soma_type'] for n in d['neurons']}; S = np.zeros((96, 96)); G = np.zeros((96, 96))
    for c in d['connections']:
        if c['type'] == 1 and typ[c['pre']] == 1 and typ[c['post']] == 1 and c['pre'] != c['post']: S[c['pre'], c['post']] = c['num_receptors']; G[c['pre'], c['post']] = c['g_peak_sum']
    return S, G
def metrics(S, G, blocks, label):
    own = tot = 0; wp = []; strong = 0; usable = []; gp_syn = []
    for blk in blocks:
        for a in blk:
            tot += S[a].sum(); own += sum(S[a, b] for b in blk if b != a)
        pairs = [S[a, b] for a in blk for b in blk if a != b]; wp += pairs; gp_syn += pairs; strong += sum(1 for a in blk for b in blk if a != b and G[a, b] >= 4.125)
        ok = False; best = 0
        for cue in itertools.combinations(blk, 4):
            tg = [m for m in blk if m not in cue]; n = sum(1 for t in tg for c in cue if G[c, t] >= 4.125); best = max(best, n)
            if n == 8: ok = True
        usable.append(dict(block=list(blk), usable=ok, best_strong_cue_target_pairs_of_8=best))
    wp = np.array(wp); A = S > 0
    return dict(label=label, own_group_share=own / tot if tot else None, chance=5 / 95, mean_syn_within_pair=float(wp.mean()), frac_within_pairs_ge1=float((wp >= 1).mean()), frac_within_pairs_ge5=float((wp >= 5).mean()),
                strong_pairs_within_groups=int(strong), strong_pairs_all=int((G >= 4.125).sum()), n_usable_groups=sum(u['usable'] for u in usable), usable=usable, p=float(A.sum() / 9120), spc=float(S[A].mean()))
seed = sys.argv[1]; out = {}
blocks_g = [list(range(6 * g, 6 * g + 6)) for g in range(8)]; blocks_u = [list(range(48 + 6 * g, 54 + 6 * g)) for g in range(8)]
bp = R + 'headline_i/grow_V1n20_s%s_p0d0175_i0d03/viz/sample_0000.json' % seed; Sb, Gb = mats(bp)
out['baseline_blocks_0_47'] = metrics(Sb, Gb, blocks_g, 'baseline E4, index blocks 0-47 (pseudo-groups)')
out['baseline_blocks_48_95'] = metrics(Sb, Gb, blocks_u, 'baseline E4, index blocks 48-95 (pseudo-groups)')
try:
    Sc, Gc = mats(HERE + 'grow_C1_s%s/viz/sample_0000.json' % seed)
    out['C1_grouped'] = metrics(Sc, Gc, blocks_g, 'C1 grouped cells 0-47 (steered)')
    out['C1_ungrouped_blocks'] = metrics(Sc, Gc, blocks_u, 'C1 ungrouped cells 48-95 (pseudo-groups, control)')
except FileNotFoundError: print('C1 growth missing')
json.dump(out, open(HERE + 'c1_metrics_%s.json' % seed, 'w'), indent=1)
for k, v in out.items(): print(k, {a: (round(b, 3) if isinstance(b, float) else b) for a, b in v.items() if a != 'usable'})

import json, numpy as np
KEYS = ['s16180','s27182','s31415','s11111','s22222','s33333','s44444','s55555','s66666','s77777']
D = {k: json.load(open('dist_%s.json' % k)) for k in KEYS}
out = []; P = out.append
P('## Part 1: distributed-cue assemblies (c cue + 2 targets), best of 5 greedy restarts; median (min-max) over 10 models')
P('| variant | c | k | candidates (median) | memories median (min-max) | models >= 1 | models >= 5 (k=0) / >= 6 (k=2) | cell budget bound 96/(c+2) |'); P('|---|---|---|---|---|---|---|---|')
for vn in ('primary', 'Hinf'):
    for c in (8, 12, 17, 20):
        for k in (0, 2):
            r = [D[m][vn]['c%d_k%d' % (c, k)] for m in KEYS]; n = [x['n_mem'] for x in r]; thr = 5 if k == 0 else 6
            P('| %s | %d | %d | %g | %g (%d-%d) | %d | %d | %d |' % (vn, c, k, np.median([x['n_cands'] for x in r]), np.median(n), min(n), max(n), sum(v >= 1 for v in n), sum(v >= thr for v in n), 96 // (c + 2)))
P('\n### Biological statistics of the primary designs (pooled over models with >= 1 memory)')
P('| c | k | models with design | designed pairs (mean) | synapses per designed pair median [mean over models] | share of designed pairs with >=5 synapses | share single-synapse | weight median [min-max] | share w>=0.9 | x max (nS) | max non-hub input (nS) | active fraction | independent check (bounds, w-range, H, no-new-pair, Dale) | cascade 16.5: full exact / sub-cue clean | cascade 15.0 |'); P('|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|')
for c in (8, 12, 17, 20):
    for k in (0, 2):
        r = [D[m]['primary']['c%d_k%d' % (c, k)] for m in KEYS if D[m]['primary']['c%d_k%d' % (c, k)].get('design')]
        if not r: P('| %d | %d | 0 | | | | | | | | | | | | |' % (c, k)); continue
        ds = [x['design'] for x in r]; vf = [x['verify'] for x in r]
        okall = all(v['bounds'] and v['no_new_pairs'] and v['dale'] and v['H_ok'] and v['w_range'] for v in vf)
        f = lambda t: (sum(v['cascade_%s' % t]['full_exact'] for v in vf), sum(v['cascade_%s' % t]['n_mem'] for v in vf), sum(v['cascade_%s' % t]['subcue_clean'] for v in vf), sum(v['cascade_%s' % t]['n_subcue'] for v in vf))
        a, b = f('16.5'), f('15.0')
        P('| %d | %d | %d | %.1f | %.1f [%.1f] | %.2f | %.2f | %.2f [%.2f-%.2f] | %.2f | %.2f | %.1f | %.3f | %s | %d/%d, %d/%d | %d/%d, %d/%d |' % (c, k, len(r), np.mean([d['n_designed'] for d in ds]), np.median([d['syn_per_pair_median'] for d in ds]), np.mean([d['syn_per_pair_mean'] for d in ds]), np.mean([d['frac_pairs_ge5syn'] for d in ds]), np.mean([d['frac_single'] for d in ds]), np.median([d['w_med'] for d in ds]), min(d['w_min'] for d in ds), max(d['w_max'] for d in ds), np.mean([d['frac_w_ge_0p9'] for d in ds]), max(d['x_max'] for d in ds), max(d['max_input_nonhub'] for d in ds), np.mean([d['frac_active'] for d in ds]), 'ALL OK' if okall else 'VIOLATION', a[0], a[1], a[2], a[3], b[0], b[1], b[2], b[3]))
open('results_dist.md', 'w').write('\n'.join(out)); print('\n'.join(out))

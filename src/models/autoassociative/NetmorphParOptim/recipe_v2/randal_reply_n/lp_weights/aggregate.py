import json, glob, numpy as np, lpw_lib as L
KEYS = ['s16180', 's27182', 's31415', 's11111', 's22222', 's33333', 's44444', 's55555', 's66666', 's77777']
FAMS = ['m2_k0', 'm2_k1', 'm2_k2', 'm2_k3', 'm4_k0', 'm4_k3']
R3REF = {'m2_k0': [2, 4, 3, 2, 3, 3, 2, 2, 3, 4], 'm2_k1': [4, 6, 7, 4, 6, 6, 4, 4, 7, 8], 'm2_k2': [13, 18, 29, 12, 25, 16, 17, 7, 16, 20], 'm2_k3': [64, 110, 201, 53, 197, 51, 108, 16, 33, 77], 'm4_k0': [0, 1, 1, 0, 1, 1, 0, 0, 1, 1], 'm4_k3': [0, 1, 3, 0, 5, 1, 0, 0, 1, 2]}
cap = {}; 
for k in KEYS:
    cap[k] = {}
    for f in ('cap_%s.json', 'capr3_%s.json', 'caphinf_%s.json'):
        try: cap[k].update(json.load(open(f % k)))
        except Exception as e: print('missing', f % k)
VARS = ['primary', 'H2T', 'H5T', 'Hinf', 'hubs_waived', 'theta14', 'Hinf_theta14', 'w0', 'r3equiv']
out = []; P = out.append
P('## Capacity (largest LP-feasible packing found, lower bound) per model; R3 = ripple_overlap_j counts (same graphs)')
P('Families: m2 = 4 cue + 2 non-cue, m4 = 4 + 4; k = max pairwise shared cells. Variant meaning in README.md section 2.')
for vn in VARS:
    P('\n### variant `%s`' % vn)
    P('| model | ' + ' | '.join(FAMS) + ' | hubs (cells whose min input > H) |'); P('|---|' + '---|' * (len(FAMS) + 1))
    for i, k in enumerate(KEYS):
        R = cap[k].get(vn)
        if not R: continue
        P('| %s | ' % k + ' | '.join(str(R['fams'][f]['n_mem']) for f in FAMS) + ' | %s |' % (R['hubs'],))
    vals = {f: [cap[k][vn]['fams'][f]['n_mem'] for k in KEYS if vn in cap[k]] for f in FAMS}
    P('| **median (min-max)** | ' + ' | '.join('%g (%d-%d)' % (np.median(v), min(v), max(v)) for v in vals.values()) + ' | |')
P('| R3 reference median (min-max) | ' + ' | '.join('%g (%d-%d)' % (np.median(R3REF[f]), min(R3REF[f]), max(R3REF[f])) for f in FAMS) + ' | |')
P('\n## R3 packings filtered through the LP constraints (kept / R3 size, summed over models; per-model medians)')
filt = {k: json.load(open('filt_%s.json' % k)) for k in KEYS}
P('| variant | ' + ' | '.join(FAMS) + ' |'); P('|---|' + '---|' * len(FAMS))
for vn in ['primary', 'H2T', 'H5T', 'hubs_waived', 'theta14', 'w0', 'r3equiv']:
    cells = []
    for f in FAMS:
        kept = [filt[k][vn][f]['kept'] for k in KEYS]; tot = [filt[k][vn][f]['r3_n'] for k in KEYS]
        cells.append('%d / %d (median %g)' % (sum(kept), sum(tot), np.median(kept)))
    P('| %s | ' % vn + ' | '.join(cells) + ' |')
P('\nRejection reasons for the R3 memories (primary, all models, all families): ' + json.dumps({r: sum(filt[k]['primary'][f]['rejected'][r] for k in KEYS for f in FAMS) for r in ('pair_weak', 'hub_target', 'cap_H', 'closure')}))
P('\n## Weight statistics of the solved designs (final LP, stage B)')
P('| variant | family | n designs | designed pairs (mean) | designed x all at margin | designed w median [min-max] | designed w >= 0.9 | designed pairs at 6.86 nS cap | all variable pairs at lower bound (mean) | raised pairs (mean) | max non-hub cell input (nS) | cells within 2% of H (mean frac) |')
P('|---|---|---|---|---|---|---|---|---|---|---|---|')
for vn in ['primary', 'hubs_waived', 'r3equiv', 'Hinf', 'theta14', 'w0']:
    for f in ['m2_k0', 'm2_k1', 'm2_k3']:
        ws = [cap[k][vn]['fams'][f]['wstats'] for k in KEYS if vn in cap[k] and cap[k][vn]['fams'][f].get('wstats') and cap[k][vn]['fams'][f]['n_mem'] > 0]
        if not ws: continue
        g = lambda key: [w[key] for w in ws if key in w]
        P('| %s | %s | %d | %.1f | %.2f | %.2f [%.2f-%.2f] | %.2f | %.3f | %.3f | %.0f | %.1f | %.3f |' % (vn, f, len(ws), np.mean(g('n_designed')), np.mean(g('des_frac_at_margin')), np.median(g('des_w_med')), min(g('des_w_min')), max(g('des_w_max')), np.mean(g('des_frac_w_ge_0p9')), np.mean(g('des_frac_at_cap686')), np.mean(g('frac_at_lb')), np.mean(g('frac_raised')) * 2153, max(g('max_cell_input_nonhub')), np.mean(g('frac_nonhub_within2pct_H'))))
P('\n## Verification (independent re-check of every stored design)')
ver = {k: json.load(open('verify_%s.json' % k)) for k in KEYS}
n = 0; ok = dict(lp=0, bounds=0, w=0, cap=0, H=0, nonew=0, dale=0); casc = {t: dict(full=0, nfull=0, part=0, npart=0) for t in ('16.5', '15.0')}; byvar = {}
for k in KEYS:
    for key, e in ver[k].items():
        n += 1; ok['lp'] += e['lp_status'] == 0
        if e['lp_status'] != 0: byvar.setdefault(key.split('|')[0] + ' ' + key.split('|')[1], []).append(k); continue
        ok['bounds'] += e['bounds_ok']; ok['w'] += e['w_in_range']; ok['cap'] += e['cap_ok']; ok['H'] += e['H_ok']; ok['nonew'] += e['no_new_pairs']; ok['dale'] += e['dale_ok']
        for t in ('16.5', '15.0'):
            c = e['cascade_%s' % t]; casc[t]['full'] += c['full_exact']; casc[t]['nfull'] += e['n_mem']; casc[t]['part'] += c['partial_clean']; casc[t]['npart'] += c['n_partial']
P('designs checked: %d; LP feasible: %d; bounds ok %d; w in [lbw,1] %d; per-pair cap 6.86 ok %d; homeostatic cap ok %d; no added pair %d; Dale (x >= 0) %d' % (n, ok['lp'], ok['bounds'], ok['w'], ok['cap'], ok['H'], ok['nonew'], ok['dale']))
for t in ('16.5', '15.0'): P('cascade threshold %s: full cue completes exactly its memory %d / %d memories; 3-cell cue completes nothing %d / %d' % (t, casc[t]['full'], casc[t]['nfull'], casc[t]['part'], casc[t]['npart']))
P('LP-infeasible stored designs (should be none): %s' % json.dumps(byvar))
# bio facts on the grown pairs
P('\n## Grown pair statistics (as grown, 10 models)')
fr = []; hub = []
for k in KEYS:
    G = L.load(k); nz = G[G > 0]; fr.append(((nz >= 4.9).mean(), (nz < 1.5).mean(), np.median(nz / 0.98), (G.sum(0) > 49.5).sum(), (G.sum(0) > 495).sum(), G.sum(0).max()))
fr = np.array(fr)
P('share of grown pairs with >= 5 synapses (needed for a 4.125 nS cue->target pair at w <= 1): mean %.3f (range %.3f-%.3f); share with a single synapse: %.3f; median synapses per pair %.1f; cells with as-grown input above H=49.5 nS: mean %.1f (%.0f-%.0f); cells above 495 nS (lower-bound sum above H): %s; largest as-grown input of a cell: %.0f nS' % (fr[:, 0].mean(), fr[:, 0].min(), fr[:, 0].max(), fr[:, 1].mean(), fr[:, 2].mean(), fr[:, 3].mean(), fr[:, 3].min(), fr[:, 3].max(), fr[:, 4].astype(int).tolist(), fr[:, 5].max()))
open('results_tables.md', 'w').write('\n'.join(out)); print('\n'.join(out))

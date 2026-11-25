#!/usr/bin/env python3
"""PREREGISTRATION_B analysis: rawB2_*.json -> resultsB.md, summaryB.json, best-arm choice (B1 rule). Measures from analyze_nr.py (full cue counts as
complete), residual sAHP at cue onset as in posthoc_residual_sahp.py (preregistered in B). 3-s references = raw_LH_*.json of this folder."""
import json, glob, numpy as np
import analyze_nr as AN
HERE = AN.HERE
P = {'N0': (1., 2., 30., 300.), 'R': (1., 2., 30., 300.), 'S2': (2., 4., 30., 1000.), 'RS2': (2., 4., 30., 1000.), 'RS3': (3., 6., 30., 1500.)}
LHREF50 = {(77777, 0.56): 2, (77777, 1.0): 6, (66666, 0.56): 5, (66666, 1.0): 5}
def gs(sp, t, g, gm, tr, td):
    s = sp[sp < t]; s = s[s > t - 10 * td]
    if not len(s): return 0.0
    tp = tr * td / (td - tr) * np.log(td / tr); nrm = np.exp(-tp / td) - np.exp(-tp / tr)
    return float(min(g * ((np.exp(-(t - s) / td) - np.exp(-(t - s) / tr)) / nrm).sum(), gm))
def resid(d):
    sp = {int(k): np.array(v) for k, v in d['spikes'].items()}; A = d['A']; out = []
    for e in d['events']:
        if e['kind'] != 'p50': continue
        nonc = [m for m in A if m not in e['cue']]; out.append(float(np.mean([gs(sp.get(m, np.array([])), e['t'], *P[d['neuron_arm']]) for m in nonc])))
    return float(np.median(out))
def summarize(fn):
    d = json.load(open(fn)); rows = AN.rows_of(d, 'LH'); s = AN.summ_LH(rows)
    s.update(seed=d['seed'], arm=d['neuron_arm'], r=float(d['r']), f=float(d['f']), wdesign=d.get('wdesign', 'LH'), spacing=d.get('spacing_ms', 3000.0),
             resid50=resid(d), eigen=d.get('eigen'), flags=d['flags'])
    s['TERM'] = s['stops100'][1] > 0 and s['stops100'][0] == s['stops100'][1]
    if s['wdesign'] == 'LH': s['RECOVER'] = s['p50'][0] >= LHREF50[(s['seed'], s['r'])] - 1
    s['PASS75'] = s['p75'][0] >= 5 and s['p25_recruit'][0] == 0 and s['p1_recruit'][0] == 0 and s['unrel_recruit'][0] == 0 and s['TERM'] and s['events_nonmember'][0] == 0
    return s, rows
if __name__ == '__main__':
    S = {}; R = {}
    for fn in sorted(glob.glob(HERE + 'raw_LH_*.json')) + sorted(glob.glob(HERE + 'rawB2_*.json')):
        s, rows = summarize(fn); k = '%s_%s_s%d_%s_r%g_f%g' % ('9s' if s['spacing'] == 9000 else '3s', s['wdesign'], s['seed'], s['arm'], s['r'], s['f']); S[k] = s; R[k] = rows
    json.dump(S, open(HERE + 'summaryB.json', 'w'), indent=1, default=str); json.dump(R, open(HERE + 'eventsB.json', 'w'))
    f = AN.f
    out = ['# PREREGISTRATION_B results (non-contaminated events; 3s rows = stored runs of this folder; resid50 = median reconstructed residual sAHP (nS) at 50%-cue onsets)\n',
           '| spacing | design | model | arm | r | rho | 75% | 50% | 25%, 1-cell, unrel recruit | median last | max last | stops100 | spk/member | non-member events | contam | resid50 | TERM | RECOVER | PASS75 | PASS_T |', '|' + '---|' * 20]
    for k in sorted(S, key=lambda k: (S[k]['wdesign'], S[k]['seed'], S[k]['arm'], S[k]['r'], S[k]['spacing'])):
        s = S[k]
        if s['spacing'] == 3000 and not (s['arm'] in ('RS2', 'RS3', 'N0') and s['f'] == 1): continue
        rho = '%.2f' % s['eigen']['eig_rho'] if s['eigen'] else ('LH')
        out.append('| %s | %s | s%d | %s | %g | %s | %s | %s | %s, %s, %s | %s | %s | %s | %s | %s | %d | %.2f | %s | %s | %s | %s |' % (k[:2], s['wdesign'], s['seed'], s['arm'], s['r'], rho, f(s['p75']), f(s['p50']),
                   f(s['p25_recruit']), f(s['p1_recruit']), f(s['unrel_recruit']), f(s['median_last']), f(s['max_last']), f(s['stops100']), f(s['median_per_member']), f(s['events_nonmember']),
                   s['contaminated'], s['resid50'], s['TERM'], s.get('RECOVER', '-'), s['PASS75'], s['PASS_T']))
    # B1 best-arm rule (PREREGISTRATION_B)
    b1 = {a: [S[k] for k in S if k.startswith('9s_LH') and S[k]['arm'] == a] for a in ('RS2', 'RS3')}
    if all(len(v) == 2 for v in b1.values()):
        key = {a: (sum(x['TERM'] for x in v), sum(x['p50'][0] for x in v), -sum(x['events_nonmember'][0] for x in v), 1 if a == 'RS2' else 0) for a, v in b1.items()}
        best = max(key, key=lambda a: key[a]); out += ['', 'B1 best-arm rule keys (TERM models, 50%% completions, -non-member events, RS2 tie-break): %s -> **%s**' % (key, best)]
        json.dump(dict(keys=key, best=best), open(HERE + 'b1_best_arm.json', 'w'))
    open(HERE + 'resultsB.md', 'w').write('\n'.join(out) + '\n'); print('\n'.join(out))

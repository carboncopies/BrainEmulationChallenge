#!/usr/bin/env python3
"""PREREGISTRATION_C analysis: rawC_*.json (+ B2 N0/RS2 E16 and E16.5 references) -> resultsC.md, summaryC.json, eventsC.json.
Measures as analyze_nr.py, criteria TERM / PASS75 / PASS_T as analyze_b.py. Manipulation check (C1): cue-cell spikes in [t, t+8) per cue cell and event."""
import json, glob, numpy as np
import analyze_nr as AN, analyze_b as AB
HERE = AN.HERE; f = AN.f
def manip(d):
    sp = {int(k): np.array(v) for k, v in d['spikes'].items()}; n = []
    for e in d['events']:
        for c in e['cue']:
            x = sp.get(c, np.array([])); n.append(int(((x >= e['t']) & (x < e['t'] + 8)).sum()))
    n = np.array(n); return dict(frac_ge2=float((n >= 2).mean()), median=float(np.median(n)), n=len(n))
def summ(fn):
    d = json.load(open(fn)); rows = AN.rows_of(d, 'LH'); s = AN.summ_LH(rows)
    s['TERM'] = s['stops100'][1] > 0 and s['stops100'][0] == s['stops100'][1]
    s['PASS75'] = s['p75'][0] >= 5 and s['p25_recruit'][0] == 0 and s['p1_recruit'][0] == 0 and s['unrel_recruit'][0] == 0 and s['TERM'] and s['events_nonmember'][0] == 0
    s.update(seed=d['seed'], arm=d['neuron_arm'], rho=d['eigen']['eig_rho'], ncue=d.get('ncue', 1), src='C' if 'rawC_' in fn else 'B2', manip=manip(d),
             max_member_input=d['flags']['max_member_input'], members_over_3T=d['flags']['members_over_3T'], max_pair=d['flags']['max_pair'],
             nmda=dict(capped=d['program'].get('nmda_capped'), set=d['program'].get('nmda_set')))
    return s, rows
if __name__ == '__main__':
    S = {}; R = {}
    files = sorted(glob.glob(HERE + 'rawC_*.json')) + sorted(glob.glob(HERE + 'rawB2_B2_E16*_r1_f1.json'))
    for fn in files:
        s, rows = summ(fn); k = '%s_rho%.1f_s%d_%s_cue%d' % (s['src'], s['rho'], s['seed'], s['arm'], s['ncue']); S[k] = s; R[k] = rows
    json.dump(S, open(HERE + 'summaryC.json', 'w'), indent=1, default=str); json.dump(R, open(HERE + 'eventsC.json', 'w'))
    hdr = '| src | model | rho | neurons | cue spikes | 75% | 50% | full | 25%, 1-cell, unrel recruit | median last (ms) | max last | stops100 | spk/member | non-member events | contam | cue cells >=2 spk in 8 ms | TERM | PASS75 | PASS_T |'
    out = ['# PREREGISTRATION_C results (9 s spacing, r 1.0, GABA x1; B2 rows = stored references; non-contaminated events; last includes forced cue spikes)\n', hdr, '|' + '---|' * 19]
    for k in sorted(S, key=lambda k: (S[k]['seed'], S[k]['ncue'], S[k]['arm'] != 'N0', S[k]['rho'])):
        s = S[k]
        out.append('| %s | s%d | %.1f | %s | %d | %s | %s | %s | %s, %s, %s | %s | %s | %s | %s | %s | %d | %.2f | %s | %s | %s |' % (s['src'], s['seed'], s['rho'], s['arm'], s['ncue'],
                   f(s['p75']), f(s['p50']), f(s['full']), f(s['p25_recruit']), f(s['p1_recruit']), f(s['unrel_recruit']), f(s['median_last']), f(s['max_last']), f(s['stops100']),
                   f(s['median_per_member']), f(s['events_nonmember']), s['contaminated'], s['manip']['frac_ge2'], s['TERM'], s['PASS75'], s['PASS_T']))
    out += ['', 'Input cap: ' + '; '.join('%s max member input %.1f nS, members > 49.5 nS: %d, max pair %.2f nS' % (k, S[k]['max_member_input'], S[k]['members_over_3T'], S[k]['max_pair']) for k in sorted(S) if S[k]['src'] == 'C')]
    open(HERE + 'resultsC.md', 'w').write('\n'.join(out) + '\n'); print('\n'.join(out))

#!/usr/bin/env python3
"""PREREGISTRATION_E analysis: rawE_*.json -> resultsE.md, summaryE.json, eventsE.json. Measures as analyze_d.py; boosted cells per run from d['failing']."""
import json, glob
import analyze_nr as AN, analyze_d as AD
HERE = AN.HERE; f = AN.f
if __name__ == '__main__':
    S = {}; R = {}
    for fn in sorted(glob.glob(HERE + 'rawE_*.json')):
        d = json.load(open(fn)); AD.FAIL[d['seed']] = d['failing']; s, rows = AD.summ(fn)
        s['arm'] = d['boost_arm']; s['cue_key'] = d['cue_key']; k = 's%d_%s' % (s['seed'], s['arm']); S[k] = s; R[k] = rows
    json.dump(S, open(HERE + 'summaryE.json', 'w'), indent=1, default=str); json.dump(R, open(HERE + 'eventsE.json', 'w'))
    jf = lambda j: ', '.join('%d: %d/%d' % (m, a, b) for m, (a, b) in j.items())
    out = ['# PREREGISTRATION_E results (new cues E1111, 9 s spacing, r 1.0, GABA x1, original neurons, single-spike cue, L1 boost, rho held 16.5; non-contaminated events)\n',
           '| model | arm | boosted cells | 75% | 50% | full | 25%, 1-cell, unrel recruit | median / max last (ms) | stops100 | ignited completing events | spk/member | non-member events | JOIN 75% | JOIN 50% | missing in failed 75% events | max member input / members > 49.5 | max pair | TERM | PASS75 | PASS_T |',
           '|' + '---|' * 20]
    for k in sorted(S, key=lambda k: (S[k]['seed'], S[k]['arm'])):
        s = S[k]
        out.append('| s%d | %s | %s | %s | %s | %s | %s, %s, %s | %s / %s | %s | %d | %s | %s | %s | %s | %s | %.1f / %d | %.2f | %s | %s | %s |' % (s['seed'], s['arm'], ','.join(map(str, s['join75'])), f(s['p75']), f(s['p50']), f(s['full']),
                   f(s['p25_recruit']), f(s['p1_recruit']), f(s['unrel_recruit']), f(s['median_last']), f(s['max_last']), f(s['stops100']), s['n_ignite'], f(s['median_per_member']), f(s['events_nonmember']),
                   jf(s['join75']), jf(s['join50']), s['missing75'] or '-', s['max_member_input'], s['members_over_3T'], s['max_pair'], s['TERM'], s['PASS75'], s['PASS_T']))
    open(HERE + 'resultsE.md', 'w').write('\n'.join(out) + '\n'); print('\n'.join(out))

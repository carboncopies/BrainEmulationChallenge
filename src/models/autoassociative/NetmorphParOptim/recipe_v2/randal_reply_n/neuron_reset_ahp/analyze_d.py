#!/usr/bin/env python3
"""PREREGISTRATION_D analysis: rawD_*.json + B2 E16.5 N0 base runs -> resultsD.md, summaryD.json, eventsD.json.
Measures as analyze_nr.py; TERM / PASS75 / PASS_T as analyze_b.py; JOIN of boosted cells; missing members in incomplete 75% events."""
import json, glob, numpy as np
import analyze_nr as AN
HERE = AN.HERE; f = AN.f; FAIL = {66666: [28, 46, 57], 77777: [65, 70]}
def join(d, rows, kind):
    sp = {int(k): np.array(v) for k, v in d['spikes'].items()}; out = {}
    for m in FAIL[d['seed']]:
        n = k = 0
        for e, r in zip(d['events'], rows):
            if e['kind'] != kind or r['cont'] or m in e['cue']: continue
            x = sp.get(m, np.array([])); n += 1; k += int(((x >= e['t']) & (x < e['t'] + 30)).any())
        out[m] = (k, n)
    return out
def missing(d, rows):
    sp = {int(k): np.array(v) for k, v in d['spikes'].items()}; out = []
    for e, r in zip(d['events'], rows):
        if e['kind'] != 'p75' or r['cont'] or r['complete']: continue
        out.append([c for c in d['A'] if c not in e['cue'] and not ((sp.get(c, np.array([])) >= e['t']) & (sp.get(c, np.array([])) < e['t'] + 30)).any()])
    return out
def summ(fn):
    d = json.load(open(fn)); rows = AN.rows_of(d, 'LH'); s = AN.summ_LH(rows)
    s['TERM'] = s['stops100'][1] > 0 and s['stops100'][0] == s['stops100'][1]
    s['PASS75'] = s['p75'][0] >= 5 and s['p25_recruit'][0] == 0 and s['p1_recruit'][0] == 0 and s['unrel_recruit'][0] == 0 and s['TERM'] and s['events_nonmember'][0] == 0
    s.update(seed=d['seed'], design=('%s-%s' % (d['boost_level'], d['boost_hold'])) if 'boost_level' in d else 'base', rho=d['eigen']['eig_rho'],
             join75=join(d, rows, 'p75'), join50=join(d, rows, 'p50'), missing75=missing(d, rows), n_ignite=sum(1 for r in AN.completing(rows) if not r['stops100']),
             max_member_input=d['flags']['max_member_input'], members_over_3T=d['flags']['members_over_3T'], max_pair=d['flags']['max_pair'])
    return s, rows
if __name__ == '__main__':
    S = {}; R = {}
    for fn in sorted(glob.glob(HERE + 'rawB2_B2_E16.5_*_N0_r1_f1.json')) + sorted(glob.glob(HERE + 'rawD_*.json')):
        s, rows = summ(fn); k = 's%d_%s' % (s['seed'], s['design']); S[k] = s; R[k] = rows
    json.dump(S, open(HERE + 'summaryD.json', 'w'), indent=1, default=str); json.dump(R, open(HERE + 'eventsD.json', 'w'))
    out = ['# PREREGISTRATION_D results (9 s spacing, r 1.0, GABA x1, original neurons, single-spike cue; base = B2 E16.5 run; non-contaminated events)\n',
           '| model | design | rho | 75% | 50% | full | 25%, 1-cell, unrel recruit | median / max last (ms) | stops100 | ignited completing events | non-member events | JOIN 75% (boosted cells) | JOIN 50% | missing in failed 75% events | max member input / members > 49.5 | TERM | PASS75 | PASS_T |',
           '|' + '---|' * 18]
    order = ['base', 'L1-hold', 'L2-hold', 'L1-free']
    for k in sorted(S, key=lambda k: (S[k]['seed'], order.index(S[k]['design']))):
        s = S[k]; jf = lambda j: ', '.join('%d: %d/%d' % (m, a, b) for m, (a, b) in j.items())
        out.append('| s%d | %s | %.2f | %s | %s | %s | %s, %s, %s | %s / %s | %s | %d | %s | %s | %s | %s | %.1f / %d | %s | %s | %s |' % (s['seed'], s['design'], s['rho'], f(s['p75']), f(s['p50']), f(s['full']),
                   f(s['p25_recruit']), f(s['p1_recruit']), f(s['unrel_recruit']), f(s['median_last']), f(s['max_last']), f(s['stops100']), s['n_ignite'], f(s['events_nonmember']),
                   jf(s['join75']), jf(s['join50']), s['missing75'] or '-', s['max_member_input'], s['members_over_3T'], s['TERM'], s['PASS75'], s['PASS_T']))
    open(HERE + 'resultsD.md', 'w').write('\n'.join(out) + '\n'); print('\n'.join(out))

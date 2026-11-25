#!/usr/bin/env python3
"""raw_*.json -> results.md, events.json, scoring.json. Definitions: PREREGISTRATION.md (Measures, Criteria). LH references = stored partial_cue addendum B runs."""
import json, glob, numpy as np
HERE = '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/neuron_reset_ahp/'
PC = '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/partial_cue/'
NP = 96; WC = 30.0
def rows_of(d, design):
    sp = {int(k): np.array(sorted(v)) for k, v in d['spikes'].items()}; pyr = {i: sp[i] for i in sp if i < NP}
    def cnt(cells, a, b): return int(sum(((pyr[i] >= a) & (pyr[i] < b)).sum() for i in cells if i in pyr))
    def fires(i, a, b): return i in pyr and bool(((pyr[i] >= a) & (pyr[i] < b)).any())
    rows = []; prev_rev = None
    for k, e in enumerate(d['events']):
        t = e['t']; cue = set(e['cue'])
        mem = set(d['A']) if design == 'LH' else set(d['groups'][e['group']]['members'])
        allm = mem if design == 'LH' else set(x for g in d['groups'] for x in g['members'])
        nonc = [m for m in mem if m not in cue]
        allp = np.sort(np.concatenate([x[(x >= t) & (x < t + 1000)] for x in pyr.values()])) if pyr else np.array([])
        r = dict(i=k, kind=e['kind'], ncue=len(cue), label=e.get('label', ''))
        r['cont'] = cnt(range(NP), t - 1500, t) > 60
        r['complete'] = (e['kind'] not in ('unrel', 'x2')) and all(fires(m, t, t + WC) for m in nonc)   # full cue (nonc empty) counts as complete (DEVIATIONS 1)
        if design == 'D0' and e['kind'] == 'x2': r['complete'] = False
        r['recruit'] = any(fires(i, t, t + WC) for i in range(NP) if i not in cue)
        r['last_ms'] = round(float(allp[-1] - t), 2) if len(allp) else 0.0
        r['stops100'] = cnt(range(NP), t + 100, t + 450) == 0
        r['pyr450'] = cnt(range(NP), t, t + 450); r['per_member'] = round(cnt(mem, t, t + 450) / len(mem), 3)
        r['nonmember450'] = cnt([i for i in range(NP) if i not in allm and i not in cue], t, t + 450)
        r['prev_reverb'] = prev_rev; prev_rev = r['pyr450'] > 50
        rows.append(r)
    return rows
def ok(rows): return [r for r in rows if not r['cont']]
def frac(rows, kind, key): x = [r for r in ok(rows) if r['kind'] == kind]; return (sum(bool(r[key]) for r in x), len(x))
def completing(rows, kinds=('full', 'p75', 'p50')): return [r for r in ok(rows) if r['kind'] in kinds and r['complete']]
def med(v): return float(np.median(v)) if len(v) else None
def summ_LH(rows):
    c = completing(rows)
    s = dict(full=frac(rows, 'full', 'complete'), p75=frac(rows, 'p75', 'complete'), p50=frac(rows, 'p50', 'complete'), p25_recruit=frac(rows, 'p25', 'recruit'),
             p1_recruit=frac(rows, 'p1', 'recruit'), unrel_recruit=frac(rows, 'unrel', 'recruit'), n_completing=len(c),
             median_last=med([r['last_ms'] for r in c]), max_last=max([r['last_ms'] for r in c], default=None),
             stops100=(sum(r['stops100'] for r in c), len(c)), median_per_member=med([r['per_member'] for r in c]),
             median_pyr450=med([r['pyr450'] for r in c]), events_nonmember=(sum(r['nonmember450'] > 0 for r in ok(rows)), len(ok(rows))),
             contaminated=sum(r['cont'] for r in rows))
    s['PASS_T'] = (s['p75'][0] >= 5 and s['p50'][0] >= 4 and s['p25_recruit'][0] == 0 and s['p1_recruit'][0] == 0 and s['unrel_recruit'][0] == 0
                   and s['stops100'][0] == s['stops100'][1] and s['events_nonmember'][0] == 0)
    # carry-over (P10): completing events split by whether the previous event reverberated
    a = [r['last_ms'] for r in c if r['prev_reverb'] is True]; b = [r['last_ms'] for r in c if r['prev_reverb'] is False]
    s['carry'] = dict(after_reverb=(med(a), len(a)), after_quiet=(med(b), len(b)))
    return s
def summ_D0(rows):
    full = [r for r in ok(rows) if r['kind'] == 'full']
    s = dict(full=frac(rows, 'full', 'complete'), p3_complete=frac(rows, 'p3', 'complete'), p3_recruit=frac(rows, 'p3', 'recruit'), p2_recruit=frac(rows, 'p2', 'recruit'),
             p1_recruit=frac(rows, 'p1', 'recruit'), x2_recruit=frac(rows, 'x2', 'recruit'), full_stops100=(sum(r['stops100'] for r in full), len(full)),
             full_median_last=med([r['last_ms'] for r in full]), events_nonmember=(sum(r['nonmember450'] > 0 for r in ok(rows)), len(ok(rows))),
             contaminated=sum(r['cont'] for r in rows))
    s['SAFE'] = (s['full'][0] == s['full'][1] and s['p3_recruit'][0] == 0 and s['p2_recruit'][0] == 0 and s['p1_recruit'][0] == 0 and s['x2_recruit'][0] == 0
                 and s['full_stops100'][0] == s['full_stops100'][1] and s['events_nonmember'][0] == 0)
    return s
def f(p): return '%d/%d' % p if isinstance(p, (tuple, list)) else ('-' if p is None else ('%.1f' % p if isinstance(p, float) else str(p)))
if __name__ == '__main__':
    S = {}; allrows = {}
    refs = {('LH', 77777, 'LH-ref', 1.0, 1.0): PC + 'rawB_s77777_LH_r1_f1.json', ('LH', 66666, 'LH-ref', 1.0, 1.0): PC + 'rawB_s66666_LH_r1_f1.json',
            ('LH', 77777, 'LH-ref', 0.56, 1.0): PC + 'rawB_s77777_LH_r0.56_f1.json', ('LH', 66666, 'LH-ref', 0.56, 1.0): PC + 'rawB_s66666_LH_r0.56_f1.json',
            ('D0', 77777, 'D0-ref', 0.56, 1.0): PC + 'raw_s77777_D0_r0.56_f1.json', ('D0', 66666, 'D0-ref', 0.56, 1.0): PC + 'raw_s66666_D0_r0.56_f1.json'}
    for fn in sorted(glob.glob(HERE + 'raw_*.json')):
        d = json.load(open(fn)); refs[(d['design'], d['seed'], d['neuron_arm'], float(d['r']), float(d['f']))] = fn
    for key, fn in refs.items():
        d = json.load(open(fn)); rows = rows_of(d, key[0]); allrows['%s_s%d_%s_r%g_f%g' % key] = rows
        S[key] = summ_LH(rows) if key[0] == 'LH' else summ_D0(rows)
        S[key]['flags'] = {k: d['flags'].get(k) for k in ('members_over_3T', 'max_member_input', 'max_pair', 'max_pair_pyr', 'pairs_over_cap') if k in d['flags']}
        if 'program' in d: S[key]['nmda'] = {k: d['program'].get(k) for k in ('nmda_capped', 'nmda_set', 'achieved_r') if k in d['program']}
    json.dump(allrows, open(HERE + 'events.json', 'w'))
    json.dump({'%s_s%d_%s_r%g_f%g' % k: v for k, v in S.items()}, open(HERE + 'summary.json', 'w'), indent=1, default=str)
    out = ['# neuron_reset_ahp results (non-contaminated events; completing = full/75%/50% events that complete; LH-ref and D0-ref = stored partial_cue runs)\n',
           '## Dense assembly (A17, arm LH weights)', '| model | neuron arm | r | GABA | full | 75% compl | 50% compl | 25% recruit | 1-cell | unrel | median last (ms) | max last | stops100 | median spikes/member | median pyr450 | events w/ non-member | contam | PASS_T | carry (after reverb / after quiet) |', '|' + '---|' * 19]
    order = ['LH-ref', 'N0', 'R', 'S2', 'RS2', 'RS3']
    for key in sorted([k for k in S if k[0] == 'LH'], key=lambda k: (k[1], -k[3], k[4], order.index(k[2]))):
        s = S[key]; c = s['carry']
        out.append('| s%d | %s | %g | x%g | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %d | %s | %s (%d) / %s (%d) |' % (key[1], key[2], key[3], key[4], f(s['full']), f(s['p75']), f(s['p50']), f(s['p25_recruit']),
                   f(s['p1_recruit']), f(s['unrel_recruit']), f(s['median_last']), f(s['max_last']), f(s['stops100']), f(s['median_per_member']), f(s['median_pyr450']),
                   f(s['events_nonmember']), s['contaminated'], 'PASS' if s['PASS_T'] else 'fail', f(c['after_reverb'][0]), c['after_reverb'][1], f(c['after_quiet'][0]), c['after_quiet'][1]))
    out += ['', '## R3 safety (D0, r 0.56)', '| model | neuron arm | full complete | 3-of-4 complete | 3-of-4 recruit | 2-of-4 recruit | 1-cell recruit | cross recruit | full stops100 | full median last (ms) | events w/ non-member | contam | SAFE |', '|' + '---|' * 13]
    for key in sorted([k for k in S if k[0] == 'D0'], key=lambda k: (k[1], k[2] != 'D0-ref')):
        s = S[key]
        out.append('| s%d | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %d | %s |' % (key[1], key[2], f(s['full']), f(s['p3_complete']), f(s['p3_recruit']), f(s['p2_recruit']), f(s['p1_recruit']),
                   f(s['x2_recruit']), f(s['full_stops100']), f(s['full_median_last']), f(s['events_nonmember']), s['contaminated'], 'SAFE' if s['SAFE'] else 'not safe'))
    open(HERE + 'results.md', 'w').write('\n'.join(out) + '\n'); print('\n'.join(out))

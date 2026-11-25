#!/usr/bin/env python3
"""Score every grown model with the realism tester (one report per arm, seeds as models), evaluate the preregistered criteria,
write results.json + results_tables.md. usage: analyze.py [--no-tester]"""
import json, os, re, subprocess, sys, glob, statistics as st
H = os.path.dirname(os.path.abspath(__file__))
RT = '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/realism_tester'
ARMS = ['A09', 'A05', 'A02', 'A01', 'Bs', 'Bsd']; SEEDS = [66666, 77777, 88888, 99999]

def runs():
    out = {}
    for lg in sorted(glob.glob(H + '/batch_i*/run.log')):
        bd = os.path.dirname(lg); comp = {}
        f = bd + '/batchinfo_completed.json'
        if os.path.exists(f): comp = {int(k): v for k, v in json.load(open(f)).items()}
        for l in open(lg, errors='replace'):
            m = re.match(r'NETMORPH_OUT runID=(\d+) arm=(\S+) seed=(\d+) dir=(\S+)', l)
            if m:
                rid, arm, seed, d = int(m[1]), m[2], int(m[3]), m[4].rstrip('/')
                out[(arm, seed)] = dict(dir=d, batch=os.path.basename(bd), runID=rid, status=comp.get(rid, {}).get('status', 'unknown'))
        for l in open(lg, errors='replace'):
            m = re.match(r'NES_SIM_ID=(\S+) runID=(\d+) arm=(\S+) seed=(\d+)', l)
            if m and (m[3], int(m[4])) in out: out[(m[3], int(m[4]))]['nes_sim_id'] = m[1]
    return out

KEYS = ['ball_index.axon.all', 'ball_index.axon.interneuron', 'ball_index.axon.pyramidal', 'ball_index.dendrite.all',
        'length.axon.interneuron', 'length.axon.pyramidal', 'length.dendrite.interneuron', 'length.dendrite.pyramidal',
        'reach_max.axon.interneuron', 'reach_max.axon.pyramidal', 'reach_mean.axon.interneuron', 'reach_mean.axon.pyramidal',
        'conn_prob.pyramidal.to.pyramidal', 'conn_prob.interneuron.to.pyramidal', 'conn_prob.pyramidal.to.interneuron', 'conn_prob.interneuron.to.interneuron',
        'syn_per_pair.pyramidal.to.pyramidal', 'syn_per_pair.interneuron.to.pyramidal', 'syn_per_pair.pyramidal.to.interneuron', 'syn_per_pair.interneuron.to.interneuron',
        'targets.interneuron', 'targets.pyramidal', 'sources.interneuron', 'sources.pyramidal']

def dist_band(p, lo=0.10, hi=0.25): return 0.0 if lo <= p <= hi else (lo - p if p < lo else p - hi)

def main(tester=True):
    R = runs(); json.dump({'%s_s%d' % k: v for k, v in R.items()}, open(H + '/runs.json', 'w'), indent=1)
    data = {}
    for arm in ARMS:
        ok = [(s, R[(arm, s)]) for s in SEEDS if (arm, s) in R and R[(arm, s)]['status'] == 'completed' and os.path.isdir(R[(arm, s)]['dir'])]
        if not ok: continue
        out = H + '/reports/' + arm
        if tester and not os.path.exists(out + '/results.json'):
            cmd = [sys.executable, RT + '/realism_tester.py', '--profile', 'ca3', '--out', out]
            for s, r in ok: cmd += ['--model', r['dir'], '--name', 's%d' % s]
            subprocess.run(cmd, check=True)
        res = json.load(open(out + '/results.json'))
        for M in res['models']:
            s = int(M['name'][1:]); mt = M['metrics']
            data[(arm, s)] = {k: dict(mean=mt[k]['mean'], median=mt[k].get('median')) for k in KEYS if k in mt}
            data[(arm, s)]['_status_counts'] = {x: sum(1 for c in M['comparisons'] if c['status'] == x) for x in ('pass', 'flag', 'unknown', 'info', 'n/a')}
    # criteria, paired by seed against A09
    crit = {}
    for arm in ARMS:
        if arm == 'A09': continue
        c = dict(S1=[], S1lit=[], S2=[], S3=[], C1=[], PPbar2=[])
        for s in SEEDS:
            a, b = data.get((arm, s)), data.get(('A09', s))
            if not a: continue
            C1 = a['syn_per_pair.interneuron.to.pyramidal']['mean'] >= 4.0; c['C1'].append(C1)
            c['PPbar2'].append(1.9 <= a['syn_per_pair.pyramidal.to.pyramidal']['mean'] <= 4.5)
            c['S1lit'].append(a['ball_index.axon.all']['mean'] <= 2)
            if not b: continue
            c['S1'].append(a['ball_index.axon.all']['mean'] <= b['ball_index.axon.all']['mean'] / 10)
            c['S2'].append(all(dist_band(a[k]['mean']) <= dist_band(b[k]['mean']) and (dist_band(a[k]['mean']) < dist_band(b[k]['mean']) or dist_band(b[k]['mean']) == 0)
                               for k in ('conn_prob.interneuron.to.pyramidal', 'conn_prob.pyramidal.to.pyramidal')))
            c['S3'].append(a['reach_max.axon.interneuron']['mean'] >= 1.5 * b['reach_max.axon.interneuron']['mean'])
        n = {k: (sum(v), len(v)) for k, v in c.items()}
        ok = lambda k: n[k][0] >= 3
        n['success'] = ok('S1') and ok('S2') and ok('S3') and ok('C1')
        crit[arm] = n
    # reproducibility vs stored headline_i models (tester demo results)
    rep = {}
    demo = RT + '/report/demo_netmorph/results.json'
    if os.path.exists(demo):
        for M in json.load(open(demo))['models']:
            s = int(M['name'][1:])
            if ('A09', s) in data:
                rep['s%d' % s] = {k: dict(stored=M['metrics'][k]['mean'], new=data[('A09', s)][k]['mean'], rel=(data[('A09', s)][k]['mean'] / M['metrics'][k]['mean'] - 1) if M['metrics'][k]['mean'] else None)
                                  for k in KEYS if k.startswith(('length.', 'conn_prob', 'syn_per_pair', 'ball_index.axon.all'))}
    json.dump(dict(data={'%s_s%d' % k: v for k, v in data.items()}, criteria=crit, reproducibility=rep), open(H + '/results.json', 'w'), indent=1, default=str)
    tables(data, crit, rep)

def fmt(x):
    if x is None: return '-'
    return ('%.3g' % x) if abs(x) < 1000 else ('%.0f' % x)

def tables(data, crit, rep):
    L = ['# Results tables (generated by analyze.py)', '', 'Values: realism-tester mean over cells/pairs (median over cells in brackets for lengths/reach/targets); one row per arm x seed; arm row = median over seeds.', '']
    groups = [('Ball index and reach', ['ball_index.axon.all', 'ball_index.axon.interneuron', 'ball_index.dendrite.all', 'reach_max.axon.interneuron', 'reach_max.axon.pyramidal', 'reach_mean.axon.interneuron']),
              ('Connection probability and synapses per pair', ['conn_prob.pyramidal.to.pyramidal', 'conn_prob.interneuron.to.pyramidal', 'conn_prob.pyramidal.to.interneuron', 'conn_prob.interneuron.to.interneuron',
                                                               'syn_per_pair.pyramidal.to.pyramidal', 'syn_per_pair.interneuron.to.pyramidal', 'syn_per_pair.pyramidal.to.interneuron', 'syn_per_pair.interneuron.to.interneuron']),
              ('Lengths, targets, sources', ['length.axon.interneuron', 'length.axon.pyramidal', 'length.dendrite.interneuron', 'length.dendrite.pyramidal', 'targets.interneuron', 'targets.pyramidal', 'sources.interneuron', 'sources.pyramidal'])]
    short = lambda k: k.replace('ball_index.', 'ball.').replace('conn_prob.', 'p.').replace('syn_per_pair.', 'spp.').replace('interneuron', 'I').replace('pyramidal', 'P').replace('.to.', '>').replace('reach_max.', 'rmax.').replace('reach_mean.', 'rmean.').replace('dendrite', 'den')
    for title, ks in groups:
        L += ['## ' + title, '', '| arm | seed | ' + ' | '.join(short(k) for k in ks) + ' |', '|' + '---|' * (len(ks) + 2)]
        for arm in ARMS:
            rows = [(s, data[(arm, s)]) for s in SEEDS if (arm, s) in data]
            for s, d in rows:
                L.append('| %s | %d | ' % (arm, s) + ' | '.join(fmt(d.get(k, {}).get('mean')) + (' (%s)' % fmt(d[k]['median']) if k.startswith(('length', 'reach', 'targets', 'sources')) and k in d else '') for k in ks) + ' |')
            if rows:
                L.append('| **%s** | median | ' % arm + ' | '.join('**%s**' % fmt(st.median([d[k]['mean'] for _, d in rows if k in d])) for k in ks) + ' |')
        L.append('')
    L += ['## Preregistered criteria (counts of seeds meeting each, paired with A09 of the same seed)', '', '| arm | S1 ball <= A09/10 | ball <= 2 (lit) | S2 p toward 0.10-0.25 | S3 Int reach >= 1.5x | C1 Int>Pyr/pair >= 4 | Pyr>Pyr/pair in 1.9-4.5 | success |', '|---|---|---|---|---|---|---|---|']
    for arm, n in crit.items():
        L.append('| %s | %d/%d | %d/%d | %d/%d | %d/%d | %d/%d | %d/%d | %s |' % (arm, *n['S1'], *n['S1lit'], *n['S2'], *n['S3'], *n['C1'], *n['PPbar2'], 'YES' if n['success'] else 'no'))
    L += ['', '## Tester status counts (ca3 profile: pass / flag / unknown / info)', '']
    for arm in ARMS:
        for s in SEEDS:
            if (arm, s) in data: c = data[(arm, s)]['_status_counts']; L.append('- %s s%d: %d / %d / %d / %d' % (arm, s, c['pass'], c['flag'], c['unknown'], c['info']))
    if rep:
        L += ['', '## Reproducibility: A09 (this run) vs the stored headline_i E4 models, same seed', '', '| seed | metric | stored | new | rel. diff |', '|---|---|---|---|---|']
        for s, d in rep.items():
            for k, v in d.items(): L.append('| %s | %s | %s | %s | %s |' % (s, k, fmt(v['stored']), fmt(v['new']), '%+.4f%%' % (100 * v['rel']) if v['rel'] is not None else '-'))
    open(H + '/results_tables.md', 'w').write('\n'.join(L) + '\n')

if __name__ == '__main__': main(tester='--no-tester' not in sys.argv)

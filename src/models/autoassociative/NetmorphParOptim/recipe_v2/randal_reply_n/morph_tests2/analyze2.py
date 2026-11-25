#!/usr/bin/env python3
"""morph_tests2 scoring: realism tester per arm (ca3_verified, seeds as models), capacity proxy per run, growth time + RAM vs cells,
preregistered criteria, results.json + results_tables.md.  usage: analyze2.py   (run with the venv python)"""
import json, os, re, subprocess, sys, glob, statistics as st, math
import numpy as np
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
RT = '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/realism_tester'
SIZES = ['x1', 'x1.5', 'x2', 'x3']; DMS = ['dm09', 'dm02', 'dm01']
ARMS = ['%s_%s' % (s, d) for s in SIZES for d in DMS] + ['ctrl_dm01']
NCELL = {'x1': 116, 'x1.5': 174, 'x2': 232, 'x3': 348, 'ctrl': 116}
SEEDS = [66666, 77777, 88888]
KEYS = ['ball_index.axon.all', 'ball_index.axon.interneuron', 'ball_index.dendrite.all', 'reach_max.axon.interneuron', 'reach_max.axon.pyramidal', 'reach_mean.axon.interneuron',
        'conn_prob.pyramidal.to.pyramidal', 'conn_prob.interneuron.to.pyramidal', 'conn_prob.pyramidal.to.interneuron', 'conn_prob.interneuron.to.interneuron',
        'syn_per_pair.pyramidal.to.pyramidal', 'syn_per_pair.interneuron.to.pyramidal', 'syn_per_pair.pyramidal.to.interneuron', 'syn_per_pair.interneuron.to.interneuron',
        'sources.pyramidal.from.pyramidal', 'sources.pyramidal.from.interneuron', 'targets.interneuron.to.pyramidal', 'targets.pyramidal.to.pyramidal',
        'length.axon.interneuron', 'length.axon.pyramidal', 'length.dendrite.pyramidal', 'cells_per_volume']

def runs():
    out = {}
    for lg in sorted(glob.glob(H + '/batch_i*_b*/run.log')):
        bd = os.path.dirname(lg); k = int(re.search(r'batch_i(\d+)_b', bd)[1]); comp = {}
        if os.path.exists(bd + '/batchinfo_completed.json'): comp = {int(a): v for a, v in json.load(open(bd + '/batchinfo_completed.json')).items()}
        res = open(bd + '/result.txt').read() if os.path.exists(bd + '/result.txt') else ''
        T = {}
        for l in open(lg, errors='replace'):
            m = re.search(r'NETMORPH_OUT runID=(\d+) arm=(\S+) seed=(\d+) dir=(\S+) t=(\d+)', l)
            if m: T.setdefault(int(m[1]), {}).update(arm=m[2], seed=int(m[3]), dir=m[4].rstrip('/'), t0=int(m[5]))
            m = re.search(r'(NETMORPH_DONE|CHECK_DONE) runID=(\d+) t=(\d+)', l)
            if m and int(m[2]) in T: T[int(m[2])][m[1]] = int(m[3])
            m = re.search(r'NES_SIM_ID=(\S+) runID=(\d+)', l)
            if m: T.setdefault(int(m[2]), {})['nes_sim_id'] = m[1]
        for rid, v in T.items():
            if 'arm' not in v: continue
            v.update(batch=os.path.basename(bd), instance=k, runID=rid, status=comp.get(rid, {}).get('status', 'unknown'), viz='%s/viz/sample_%04d.json' % (bd, rid),
                     # NETMORPH_DONE can share a line with the tqdm bar, so re.search; CHECK_DONE (<=12 s later) is a fallback only
                     growth_s=(v['NETMORPH_DONE'] - v['t0']) if 'NETMORPH_DONE' in v else ((v['CHECK_DONE'] - v['t0']) if 'CHECK_DONE' in v else None),
                     growth_from=('NETMORPH_DONE' if 'NETMORPH_DONE' in v else 'CHECK_DONE'), check_s=(v['CHECK_DONE'] - v['NETMORPH_DONE']) if 'CHECK_DONE' in v and 'NETMORPH_DONE' in v else None,
                     batch_result=res.strip())
            out[(v['arm'], v['seed'])] = v
    return out

def main():
    R = runs(); json.dump({'%s_s%d' % k: v for k, v in R.items()}, open(H + '/runs.json', 'w'), indent=1)
    data = {}
    for arm in ARMS:
        ok = [(s, R[(arm, s)]) for s in SEEDS if (arm, s) in R and R[(arm, s)]['status'] == 'completed' and os.path.isdir(R[(arm, s)]['dir'])]
        out = H + '/reports/' + arm
        if ok and not os.path.exists(out + '/results.json'):
            cmd = [sys.executable, RT + '/realism_tester.py', '--profile', 'ca3_verified', '--out', out]
            for s, r in ok: cmd += ['--model', r['dir'], '--name', 's%d' % s]
            subprocess.run(cmd, check=True)
        if not os.path.exists(out + '/results.json'): continue
        for M in json.load(open(out + '/results.json'))['models']:
            s = int(M['name'][1:]); mt = M['metrics']
            data[(arm, s)] = {k: dict(mean=mt[k]['mean'], median=mt[k].get('median')) for k in KEYS if k in mt}
            data[(arm, s)]['_status'] = {x: sum(1 for c in M['comparisons'] if c['status'] == x) for x in ('pass', 'flag', 'unknown', 'info', 'n/a')}
    # capacity proxy (cached)
    capf = H + '/capacity.json'; cap = json.load(open(capf)) if os.path.exists(capf) else {}
    import capacity as C
    for (arm, s), v in R.items():
        key = '%s_s%d' % (arm, s)
        if key not in cap and v['status'] == 'completed' and os.path.exists(v['viz']):
            cap[key] = C.capacity(v['viz']); json.dump(cap, open(capf, 'w'), indent=1, default=int); print('capacity', key, cap[key]['pairs_ge_thr'], cap[key]['max_disjoint_m4'], cap[key]['max_disjoint_m2'], flush=True)
    # criteria per arm
    crit = {}
    for arm in ARMS:
        c = dict(S1=[], S1lit=[], S2=[], S3=[], C1=[], PP12=[])
        for s in SEEDS:
            a = data.get((arm, s))
            if not a: continue
            c['S1'].append(a['ball_index.axon.all']['mean'] <= 10); c['S1lit'].append(a['ball_index.axon.all']['mean'] <= 2)
            pp, ip = a['conn_prob.pyramidal.to.pyramidal']['mean'], a['conn_prob.interneuron.to.pyramidal']['mean']
            c['S2'].append(0.009 <= pp <= 0.10 and ip <= 0.375)
            c['S3'].append(a['reach_max.axon.interneuron']['mean'] >= 390)
            c['C1'].append(a['syn_per_pair.interneuron.to.pyramidal']['mean'] >= 4.0)
            c['PP12'].append(1 <= a['syn_per_pair.pyramidal.to.pyramidal']['mean'] <= 2)
        n = {k: (sum(v), len(v)) for k, v in c.items()}
        n['success'] = all(n[k][0] >= 2 for k in ('S1', 'S2', 'S3', 'C1')) if n['S1'][1] else None
        crit[arm] = n
    # cost scaling: per-growth time (launch -> NetMorph done) and instance RSS
    cost = {}
    for (arm, s), v in R.items():
        cost.setdefault(arm.split('_')[0], []).append(v.get('growth_s'))
    rss = {}
    for f in glob.glob(H + '/batch_i*_b*/result.txt'):
        m = re.search(r'nes_rss_kb_after=(-?\d+)', open(f).read()); bd = os.path.dirname(f)
        sizes = sorted(set(r['size'] for r in json.load(open(bd + '/launch.json'))['rows']))
        if m: rss[os.path.basename(bd)] = dict(sizes=sizes, rss_after_GB=int(m[1]) / 1048576)
    peak = {}
    if os.path.exists(H + '/monitor.log'):
        for l in open(H + '/monitor.log').read().splitlines()[1:]:
            for tok in l.split('\t')[-1].split():
                i, g = tok.split(':'); peak[i] = max(peak.get(i, 0), float(g or 0))
    fit = None
    pts = [(NCELL[a], t) for a, ts in cost.items() if a != 'ctrl' for t in ts if t]
    if len(set(p[0] for p in pts)) >= 2:
        x = np.log([p[0] for p in pts]); y = np.log([p[1] for p in pts]); b, a0 = np.polyfit(x, y, 1); fit = dict(exponent=float(b), prefactor_s=float(math.exp(a0)), law='growth_s = %.3g * N^%.2f' % (math.exp(a0), b))
    json.dump(dict(data={'%s_s%d' % k: v for k, v in data.items()}, criteria=crit, capacity=cap, growth_s=cost, instance_rss_after=rss, instance_peak_rss_GB=peak, time_fit=fit),
              open(H + '/results.json', 'w'), indent=1, default=str)
    tables(data, crit, cap, cost, rss, peak, fit)

def fmt(x):
    if x is None: return '-'
    if isinstance(x, (int,)) and not isinstance(x, bool): return str(x)
    return ('%.3g' % x) if abs(x) < 1000 else ('%.0f' % x)

def med(vals):
    vals = [v for v in vals if v is not None]; return st.median(vals) if vals else None

def tables(data, crit, cap, cost, rss, peak, fit):
    L = ['# morph_tests2 results (generated by analyze2.py)', '', 'Realism tester means over cells/pairs (median over cells in brackets where shown); per seed rows, bold = median over seeds.', '']
    short = lambda k: k.replace('ball_index.', 'ball.').replace('conn_prob.', 'p.').replace('syn_per_pair.', 'spp.').replace('interneuron', 'I').replace('pyramidal', 'P').replace('.to.', '>').replace('.from.', '<').replace('reach_max.', 'rmax.').replace('reach_mean.', 'rmean.').replace('dendrite', 'den').replace('sources.', 'src.').replace('targets.', 'tgt.')
    groups = [('Ball, reach', ['ball_index.axon.all', 'ball_index.axon.interneuron', 'ball_index.dendrite.all', 'reach_max.axon.interneuron', 'reach_max.axon.pyramidal', 'reach_mean.axon.interneuron']),
              ('Connection probability, synapses per pair', ['conn_prob.pyramidal.to.pyramidal', 'conn_prob.interneuron.to.pyramidal', 'conn_prob.pyramidal.to.interneuron', 'conn_prob.interneuron.to.interneuron',
                                                             'syn_per_pair.pyramidal.to.pyramidal', 'syn_per_pair.interneuron.to.pyramidal', 'syn_per_pair.pyramidal.to.interneuron', 'syn_per_pair.interneuron.to.interneuron']),
              ('Inputs/outputs per cell, lengths, density', ['sources.pyramidal.from.pyramidal', 'sources.pyramidal.from.interneuron', 'targets.interneuron.to.pyramidal', 'targets.pyramidal.to.pyramidal', 'length.axon.interneuron', 'length.axon.pyramidal', 'length.dendrite.pyramidal', 'cells_per_volume'])]
    for title, ks in groups:
        L += ['## ' + title, '', '| arm | seed | ' + ' | '.join(short(k) for k in ks) + ' |', '|' + '---|' * (len(ks) + 2)]
        for arm in ARMS:
            rows = [(s, data[(arm, s)]) for s in SEEDS if (arm, s) in data]
            for s, d in rows:
                L.append('| %s | %d | ' % (arm, s) + ' | '.join(fmt(d.get(k, {}).get('mean')) + (' (%s)' % fmt(d[k]['median']) if k.startswith(('sources', 'targets')) and k in d else '') for k in ks) + ' |')
            if rows: L.append('| **%s** | med | ' % arm + ' | '.join('**%s**' % fmt(med([d[k]['mean'] for _, d in rows if k in d])) for k in ks) + ' |')
        L.append('')
    L += ['## Preregistered criteria (seeds meeting each; success = S1, S2, S3, C1 each in >= 2 of 3)', '', '| arm | S1 ball <= 10 | ball <= 2 | S2 p P>P 0.009-0.10 & I>P <= 0.375 | S3 Int reach >= 390 | C1 I>P/pair >= 4 | P>P/pair 1-2 | success |', '|---|---|---|---|---|---|---|---|']
    for arm, n in crit.items():
        if n['S1'][1]: L.append('| %s | %d/%d | %d/%d | %d/%d | %d/%d | %d/%d | %d/%d | %s |' % (arm, *n['S1'], *n['S1lit'], *n['S2'], *n['S3'], *n['C1'], *n['PP12'], 'YES' if n['success'] else 'no'))
    L += ['', '## Capacity proxy (pyramidal AMPA matrix from the viz dump; pair threshold 4.125 nS)', '', '| arm | seed | n_pyr | p (dump) | strong pairs | strong out/cell | lambda_max nS | lambda_max strong nS | disjoint 4+4 | disjoint 4+2 | sampled LB |', '|---|---|---|---|---|---|---|---|---|---|---|']
    for arm in ARMS:
        for s in SEEDS:
            c = cap.get('%s_s%d' % (arm, s))
            if c: L.append('| %s | %d | %d | %.4f | %d | %.2f | %.1f | %.1f | %d | %d | %s |' % (arm, s, c['n_pyr'], c['p_conn'], c['pairs_ge_thr'], c['strong_out_per_cell'], c['lambda_max_nS'], c['lambda_max_strong_nS'], c['max_disjoint_m4'], c['max_disjoint_m2'], 'LB' if c['sampled_LB'] else ''))
    L += ['', '## Growth cost vs cell count', '', '| size | cells | growth s (launch to NetMorph done), per run | median |', '|---|---|---|---|']
    for sz in SIZES + ['ctrl']:
        ts = cost.get(sz, [])
        L.append('| %s | %d | %s | %s |' % (sz, NCELL[sz], ' '.join(fmt(t) for t in ts), fmt(med(ts))))
    if fit: L += ['', 'Fit over all non-control runs: **%s** (N = total cells; runs were 3 concurrent per NES and up to 27 on the machine).' % fit['law']]
    L += ['', '| sub-batch | sizes | NES RSS after (GB) |', '|---|---|---|'] + ['| %s | %s | %.2f |' % (b, ','.join(v['sizes']), v['rss_after_GB']) for b, v in sorted(rss.items())]
    if peak: L += ['', 'Peak NES RSS per instance during the run (monitor, GB): ' + ', '.join('%s %.1f' % (k, v) for k, v in sorted(peak.items()))]
    open(H + '/results_tables.md', 'w').write('\n'.join(L) + '\n')

if __name__ == '__main__': main()

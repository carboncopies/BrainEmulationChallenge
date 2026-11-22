"""Analysis of raw_*.json -> summary.json and summary.txt. Simulated results: weights (class means, decreases, cap), training stability, probe recall. Offline literature-rule analysis (L1, L2) on the training spike trains (clearly separate)."""
import json, glob, collections, math, sys
import numpy as np
TOL = 1e-4; NP = 96
LIT = {'L1_Song2000': (0.005, 0.00525, 20.0, 20.0), 'L2_BiPoo_taus': (0.005, 0.00525, 16.8, 33.7)}
def classes(groups):
    cue = {}; nc = {}; mem = {}
    for gi, g in enumerate(groups):
        for c in g['cue']: cue[c] = gi; mem[c] = gi
        for n in g['noncue']: nc[n] = gi; mem[n] = gi
    def cl(a, b):
        if b >= NP:
            return 'e_cue->Int' if a in cue else ('h_other' if a in mem else 'g_nonmember')
        if a not in mem or b not in mem: return 'g_nonmember'
        if mem[a] != mem[b]: return 'f_between'
        if a in cue and b in nc: return 'a_cue->noncue'
        if a in nc and b in nc: return 'b_noncue<->noncue'
        if a in nc and b in cue: return 'c_noncue->cue'
        if a in cue and b in cue: return 'd_cue->cue'
        return 'h_other'
    return cl
def lit_update(W, train_events, spikes, rule, arm):
    Ap, Am, tp, tm = rule; w = {k: v[0] for k, v in W.items()}; sp = {int(k): v for k, v in spikes.items()}
    for e in train_events:
        t0 = e['t']; act = {i: [x for x in v if t0 <= x < t0 + 500] for i, v in sp.items()}; act = {i: v for i, v in act.items() if v}
        for (a, b), v in W.items():
            if a in act and b in act:
                dw = 0.0
                for ta in act[a]:
                    for tb in act[b]:
                        d = tb - ta
                        dw += Ap * math.exp(-d / tp) if d > 0 else (-Am * math.exp(d / tm) if d < 0 else 0.0)
                if dw: w[(a, b)] = min(1.0, max(0.0, w[(a, b)] + dw))
    return w
rows = []
for f in sorted(glob.glob('raw_*.json')):
    d = json.load(open(f)); G = d['groups']; cl = classes(G); mem = set(x for g in G for x in g['members'])
    W = {(a, b): (w0, w1, g) for a, b, w0, w1, g in d['weights']}
    r = dict(tag=d['tag'], key=d['key'], arm=d['arm'], R=d['R'], c=d['c'], n_mem=len(G), cap_viol=d.get('cap_violations'))
    byc = collections.defaultdict(list); dec = 0; chg = 0; cap = [0, 0]
    for (a, b), (w0, w1, g) in W.items():
        dw = w1 - w0; byc[cl(a, b)].append(dw); dec += dw < -TOL; chg += abs(dw) > TOL
        if cl(a, b) == 'a_cue->noncue': cap[0] += 1; cap[1] += w1 >= 1 - 1e-4
    r['dw'] = {k: dict(n=len(v), mean=float(np.mean(v)), min=float(np.min(v)), max=float(np.max(v)), nchg=int(sum(abs(x) > TOL for x in v))) for k, v in byc.items()}
    r['decreased'] = int(dec); r['changed'] = int(chg); r['n_pairs'] = len(W); r['cap_frac_a'] = cap[1] / max(1, cap[0]); r['w_range'] = (min(v[1] for v in W.values()), max(v[1] for v in W.values()))
    if d['R'] > 0:
        sp = {int(k): v for k, v in d['train_spikes'].items()}; ev = d['train_events']; nm = []; ints = []; runaway = 0
        for e in ev:
            t0 = e['t']; n_ = sum(1 for i in range(NP) if i not in mem for x in sp.get(i, []) if t0 <= x < t0 + 500); nm.append(n_); ints.append(sum(1 for i in range(NP, 116) for x in sp.get(i, []) if t0 <= x < t0 + 500))
        r['train'] = dict(events=len(ev), nonmember_max=max(nm), nonmember_total=sum(nm), runaway_events=int(sum(x > 50 for x in nm)), int_spikes_mean=float(np.mean(ints)), int_spikes_first=float(np.mean(ints[:len(G)])), int_spikes_last=float(np.mean(ints[-len(G):])))
        r['lit'] = {}
        for name, rule in LIT.items():
            w = lit_update(W, ev, sp, rule, d['arm']); byl = collections.defaultdict(list); decl = 0
            for (a, b), (w0, w1, g) in W.items():
                dw = w[(a, b)] - w0; byl[cl(a, b)].append(dw); decl += dw < -TOL
            r['lit'][name] = dict(decreased=int(decl), cls={k: dict(mean=float(np.mean(v)), n=len(v)) for k, v in byl.items()}, nc_cue_zero=float(np.mean([w[(a, b)] <= 1e-4 for (a, b) in W if cl(a, b) == 'c_noncue->cue'])) if any(cl(a, b) == 'c_noncue->cue' for (a, b) in W) else None)
    sp2 = {int(k): v for k, v in d['probe_spikes'].items()}; pm = []
    for e in d['probe_events']:
        g = G[e['group']]; t0 = e['t']; w = lambda x: [s for s in sp2.get(x, []) if t0 <= s < t0 + 450]
        comp10 = all(any(0 <= s - t0 < 10 for s in sp2.get(n, [])) for n in g['noncue']); ncf = sum(1 for n in g['noncue'] if w(n))
        other = set(x for j, h in enumerate(G) if j != e['group'] for x in h['members']) - set(g['members']); cross = sum(1 for x in other if w(x))
        nonm = sum(1 for i in range(NP) if i not in mem and w(i))
        pm.append(dict(group=e['group'], label=e['label'], comp10=bool(comp10), nc_fired=ncf, nc_total=len(g['noncue']), cross=cross, nonmember=nonm))
    r['probe'] = pm; rows.append(r)
json.dump(rows, open('summary.json', 'w'), default=float, indent=1)
# ---- text summary
out = []
def P(*a): out.append(' '.join(str(x) for x in a))
cell = collections.defaultdict(list)
for r in rows: cell[(r['arm'] if r['R'] > 0 else 'ctrl', r['R'], r['c'])].append(r)
P('== SIMULATED: mean weight change by class (pooled pairs; n pairs) ==')
for k in sorted(cell):
    rs = cell[k]; agg = collections.defaultdict(lambda: [0, 0.0]); decs = sum(r['decreased'] for r in rs); npairs = sum(r['n_pairs'] for r in rs)
    for r in rs:
        for c, v in r['dw'].items(): agg[c][0] += v['n']; agg[c][1] += v['mean'] * v['n']
    P(k, 'models', len(rs), 'decreased', decs, 'of', npairs, '|', ' '.join('%s %+.4f (%d)' % (c, agg[c][1] / agg[c][0], agg[c][0]) for c in sorted(agg)), '| cue->noncue at cap %.2f' % np.mean([r['cap_frac_a'] for r in rs]), '| cap viol', sum(sum((r['cap_viol'] or {}).values()) for r in rs))
P('\n== SIMULATED: training stability (non-member Pyr spikes per event) ==')
for k in sorted(cell):
    rs = [r for r in cell[k] if 'train' in r]
    if rs: P(k, 'runaway events', sum(r['train']['runaway_events'] for r in rs), 'of', sum(r['train']['events'] for r in rs), 'max non-member/event', max(r['train']['nonmember_max'] for r in rs), 'models with any runaway', sum(r['train']['runaway_events'] > 0 for r in rs), 'int spikes/event first %.1f last %.1f' % (np.mean([r['train']['int_spikes_first'] for r in rs]), np.mean([r['train']['int_spikes_last'] for r in rs])))
P('\n== SIMULATED: probe recall after training (memories; full completes / 3-cell cue completes (any non-cue fires) / non-member spike trials / cross) ==')
for k in sorted(cell):
    rs = cell[k]; nm = 0; fc = 0; t3 = 0; t3n = 0; nmt = 0; nme = 0; cr = 0; t3mem = 0; memsum = 0
    for r in rs:
        for g in range(r['n_mem']):
            ev = [e for e in r['probe'] if e['group'] == g]; memsum += 1
            fc += [e for e in ev if e['label'] == 'full'][0]['comp10']
            lk = any(e['nc_fired'] > 0 for e in ev if e['label'] != 'full'); t3mem += lk
            nmt += any(e['nonmember'] > 0 for e in ev); cr += any(e['cross'] > 0 for e in ev)
    P(k, 'memories', memsum, 'full completes', fc, '3-cell completes (>=1 non-cue)', t3mem, 'memories with non-member spikes', nmt, 'with cross', cr)
P('\n== OFFLINE (literature rules applied to the training spike trains; NOT simulated) ==')
for rule in LIT:
    for k in sorted(cell):
        rs = [r for r in cell[k] if 'lit' in r]
        if not rs: continue
        agg = collections.defaultdict(lambda: [0, 0.0])
        for r in rs:
            for c, v in r['lit'][rule]['cls'].items(): agg[c][0] += v['n']; agg[c][1] += v['mean'] * v['n']
        z = [r['lit'][rule]['nc_cue_zero'] for r in rs if r['lit'][rule]['nc_cue_zero'] is not None]
        P(rule, k, 'decreased', sum(r['lit'][rule]['decreased'] for r in rs), '|', ' '.join('%s %+.4f' % (c, agg[c][1] / agg[c][0]) for c in sorted(agg)), '| noncue->cue at 0: %.2f' % (np.mean(z) if z else float('nan')))
open('summary.txt', 'w').write('\n'.join(out)); print('\n'.join(out))

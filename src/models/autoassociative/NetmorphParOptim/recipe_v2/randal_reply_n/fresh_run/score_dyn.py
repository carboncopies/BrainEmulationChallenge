"""score raw_*.json of fr_dyn: per tag -> events clean / completes / silent / cross-completion. usage: score_dyn.py -> dyn_scores.json"""
import json, glob, sys
HERE = '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/fresh_run/'; NP = 96; WIN = 50.0; CWIN = 10.0
out = {}
for fn in sorted(glob.glob(HERE + 'raw_*.json')):
    d = json.load(open(fn)); G = d['groups']; sp = {int(k): v for k, v in d['spikes'].items()}; allmem = {m for g in G for m in g['members']}
    cuecells = [set(g['cue']) for g in G]; nc = [set(g['noncue']) for g in G]
    # exclusive non-cue members of another memory: non-cue of g2 that are not members of the cued memory g
    s = dict(tag=d['tag'], real=d['real'], c=d['c'], n_mem=len(G), full=0, full_complete=0, full_clean=0, full_cross_any=0, full_cross_full=0, p3=0, p3_silent=0, p3_clean=0, nonmember_spike_events=0, int_spikes_full=0, load_ok=True, wall=d['wall_s'])
    for e in d['events']:
        gi = e['group']; t = e['t']; mem = set(G[gi]['members']); w = lambda i: [x - t for x in sp.get(i, []) if t <= x < t + WIN]
        fired_nc = [m for m in G[gi]['noncue'] if any(x < CWIN for x in w(m))]
        cross = {}
        for g2, gg in enumerate(G):
            if g2 == gi: continue
            ex = [m for m in gg['noncue'] if m not in mem]
            if ex: cross[g2] = (sum(1 for m in ex if w(m)), len(ex))
        anycross = any(a > 0 for a, b in cross.values()); fullcross = any(a == b for a, b in cross.values())
        nonmem = [i for i in range(NP) if i not in allmem and w(i)]
        # cells of the cued memory's cue that were not cued must stay silent in p3 : the 4th cue cell counts as a non-cue member here
        if e['kind'] == 'full':
            s['full'] += 1; comp = len(fired_nc) == len(G[gi]['noncue']); s['full_complete'] += comp; s['full_cross_any'] += anycross; s['full_cross_full'] += fullcross
            s['full_clean'] += bool(comp and not anycross and not nonmem); s['int_spikes_full'] += sum(len(w(i)) for i in range(NP, 116))
        else:
            missing = (set(G[gi]['cue']) - set(e['cue']))
            fired = [m for m in list(G[gi]['noncue']) + list(missing) if w(m)]
            silent = not [m for m in G[gi]['noncue'] if w(m)]
            s['p3'] += 1; s['p3_silent'] += silent; s['p3_clean'] += bool(silent and not anycross and not nonmem)
        s['nonmember_spike_events'] += bool(nonmem)
    out[d['tag']] = s
    print('%-28s mem %2d full %2d/%2d complete %2d clean | cross any %d full %d | 3-cell %2d/%2d silent %2d clean | nonmember-ev %d' % (d['tag'], s['n_mem'], s['full'], s['full_complete'], s['full_clean'], s['full_cross_any'], s['full_cross_full'], s['p3'], s['p3_silent'], s['p3_clean'], s['nonmember_spike_events']))
json.dump(out, open(HERE + 'dyn_scores.json', 'w'), indent=1)

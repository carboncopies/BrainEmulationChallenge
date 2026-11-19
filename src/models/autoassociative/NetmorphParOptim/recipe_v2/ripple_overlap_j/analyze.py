"""Analysis of raw_*.json (ov and rip modes) -> per-event rows. usage: analyze.py [glob]   writes events_ov.json, events_rip.json"""
import sys, json, glob, itertools
import numpy as np
NP = 96
def load(f): return json.load(open(f))
def ov_rows(d):
    sp = {int(k): v for k, v in d['spikes'].items()}; G = d['groups']; N = 116
    allmem = set(x for g in G for x in g['members']); rows = []
    for e in d['events']:
        gi = e['group']; g = G[gi]; t0 = e['t']; mem = set(g['members']); nc = g['noncue']
        w = lambda i, a=0.0, b=450.0: [x - t0 for x in sp.get(i, []) if t0 + a <= x < t0 + b]
        comp10 = all(any(0 <= x < 10 for x in w(m)) for m in nc); ncf = [m for m in nc if w(m)]
        other = set(x for j, h in enumerate(G) if j != gi for x in h['members']) - mem
        cross = [x for x in other if w(x)]
        fullx = []; partx = []
        for j, h in enumerate(G):
            if j == gi: continue
            ex = [m for m in h['noncue'] if m not in mem]
            if ex and all(w(m) for m in ex): fullx.append(j)
            sh = len(mem & set(h['members']))
            exm = set(h['members']) - mem
            partx.append((j, sh, bool(any(w(m) for m in exm))))
        nonmem = [i for i in range(NP) if i not in allmem and w(i)]
        ints = [i for i in range(NP, N) if w(i)]
        if e['label'] == 'full': clean = comp10 and not cross and not fullx and not nonmem
        else: clean = (not ncf) and not cross and not fullx and not nonmem
        rows.append(dict(key=d['key'], tag=d['tag'], c=d['c'], sg=int(d['sg']), group=gi, label=e['label'], expect=e['expect'], complete10=comp10, nc_fired=len(ncf), nc_total=len(nc),
                         cross_cells=len(cross), full_cross=len(fullx), part=partx, nonmember_pyr=len(nonmem), n_nonmember_spikes=sum(len(w(i)) for i in nonmem), int_spikes=sum(len(w(i)) for i in range(NP, N)), ints=len(ints), clean=bool(clean)))
    return rows
def volleys(times, gap=2.0):
    ts = sorted(times); v = []
    for x in ts:
        if v and x - v[-1][-1] < gap: v[-1].append(x)
        else: v.append([x])
    return v
def rip_rows(d):
    sp = {int(k): v for k, v in d['spikes'].items()}; G = d['groups']; N = 116
    allmem = set(x for g in G for x in g['members']); rows = []
    for e in d['events']:
        gi = e['group']; g = G[gi]; t0 = e['t']; mem = set(g['members']); nc = g['noncue']
        w = lambda i: [x - t0 for x in sp.get(i, []) if t0 <= x < t0 + 100.0]
        ncf = [m for m in nc if w(m)]; replay = len(ncf) == len(nc)
        lat = min((x for m in nc for x in w(m)), default=None)
        ncs = [x for m in nc for x in w(m)]; vol = volleys(ncs); starts = [v[0] for v in vol]
        freq = (1000.0 / float(np.mean(np.diff(starts)))) if len(starts) >= 3 else None
        msp = [x for m in mem for x in w(m)]; dur = (max(msp) - min(msp)) if msp else None
        mvol = volleys(msp)
        other = set(x for j, h in enumerate(G) if j != gi for x in h['members']) - mem
        cross = [x for x in other if w(x)]
        nonmem = [i for i in range(NP) if i not in allmem and w(i)]
        ints = [i for i in range(NP, N) if w(i)]; isp = [x for i in range(NP, N) for x in w(i)]
        mstarts = [v[0] for v in mvol]
        lock = (sum(1 for x in isp if any(1.0 <= x - s <= 6.0 for s in [t for t in msp])) / len(isp)) if isp else None
        rows.append(dict(key=d['key'], tag=d['tag'], c=d['c'], sg=int(d['sg']), group=gi, label=e['label'], f=e['f'], n=e['n'], nc_fired=len(ncf), nc_total=len(nc), replay=bool(replay), latency=lat, volleys_nc=len(vol), freq=freq,
                         duration=dur, member_volleys=len(mvol), ints=len(ints), int_frac=len(ints) / 20.0, int_spikes=len(isp), lock=lock, cross_cells=len(cross), nonmember_pyr=len(nonmem),
                         n_nonmember_spikes=sum(len(w(i)) for i in nonmem), runaway=bool(sum(len(w(i)) for i in nonmem) > 50), last_pyr=max((x for i in range(NP) for x in w(i)), default=None)))
    return rows
if __name__ == '__main__':
    pat = sys.argv[1] if len(sys.argv) > 1 else 'raw_*.json'
    ov = []; rp = []
    for f in sorted(glob.glob(pat)):
        d = load(f)
        (ov if d['mode'] == 'ov' else rp).extend(ov_rows(d) if d['mode'] == 'ov' else rip_rows(d))
    json.dump(ov, open('events_ov.json', 'w'), default=float); json.dump(rp, open('events_rip.json', 'w'), default=float)
    print(len(ov), 'ov events', len(rp), 'rip events')

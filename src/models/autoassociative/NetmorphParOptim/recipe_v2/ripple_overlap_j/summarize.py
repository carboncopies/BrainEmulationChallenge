"""Tables from events_ov.json / events_rip.json (run analyze.py first). Prints markdown-ish tables and writes summary.json"""
import json, collections, statistics as st
import numpy as np
ov = json.load(open('events_ov.json')); rp = json.load(open('events_rip.json'))
def fam(tag): return tag.split('_')[1]            # F1 F2 F3 F8
S = {}
print('== OVERLAP: clean rate by design family, c, GABA ==')
rows = collections.defaultdict(lambda: [0, 0])
full = collections.defaultdict(lambda: dict(n=0, comp=0, clean=0, cross=0, fullx=0, nonmem=0))
three = collections.defaultdict(lambda: dict(n=0, clean=0))
for e in ov:
    k = (fam(e['tag']), e['c'], e['sg'])
    if e['label'] == 'full':
        d = full[k]; d['n'] += 1; d['comp'] += e['complete10']; d['clean'] += e['clean']; d['cross'] += (e['cross_cells'] > 0); d['fullx'] += (e['full_cross'] > 0); d['nonmem'] += (e['nonmember_pyr'] > 0)
    else:
        d = three[k]; d['n'] += 1; d['clean'] += e['clean']
for k in sorted(full):
    d = full[k]; t = three[k]
    print('%s c %-4s %s  full cue: n %3d complete %3d clean %3d | any-cross %3d full-cross %3d nonmember-Pyr %3d | 3-cell: n %3d clean %3d' % (k[0], k[1], 'SG' if k[2] else 'on', d['n'], d['comp'], d['clean'], d['cross'], d['fullx'], d['nonmem'], t['n'], t['clean']))
S['ov_full'] = {'%s|%s|%d' % k: v for k, v in full.items()}; S['ov_three'] = {'%s|%s|%d' % k: v for k, v in three.items()}
# pair-level cross-completion by overlap size (full cues): other memory j with shared k cells: any exclusive member fired
pk = collections.defaultdict(lambda: [0, 0])
for e in ov:
    if e['label'] != 'full' or e['c'] > 1.5: continue
    for j, sh, hit in e['part']:
        pk[(fam(e['tag']), e['sg'], sh)] [0] += 1; pk[(fam(e['tag']), e['sg'], sh)][1] += int(hit)
print('== pair level: cued memory i, other memory j sharing s cells; fraction of (i,j) with any exclusive member of j firing (all c<=1.5) ==')
for k in sorted(pk): 
    if k[2] <= 3: print(k, pk[k][1], '/', pk[k][0])
S['ov_pairs'] = {'%s|%d|%d' % k: v for k, v in pk.items()}
# GABA on vs SG agreement per event (c <= 1.5)
ag = [0, 0]; idx = {}
for e in ov: idx[(e['tag'].rsplit('_sg', 1)[0], e['group'], e['label'])] = idx.get((e['tag'].rsplit('_sg', 1)[0], e['group'], e['label']), {}); idx[(e['tag'].rsplit('_sg', 1)[0], e['group'], e['label'])][e['sg']] = e['clean']
for v in idx.values():
    if 0 in v and 1 in v: ag[0] += 1; ag[1] += int(v[0] == v[1])
print('GABA on vs silenced: same clean/not-clean in', ag[1], 'of', ag[0], 'paired events')
S['ov_gaba_agree'] = ag
print('\n== RIPPLE ==')
R = collections.defaultdict(list)
for e in rp: R[(e['label'], e['c'], e['sg'])].append(e)
labs = ['control'] + ['rip n%d f%d' % (n, f) for n in (2, 3) for f in (100, 150, 200, 250)]
for c in (0, 0.15, 1.5):
    for sg in (0, 1):
        print('c', c, 'SG' if sg else 'on')
        for l in labs:
            v = R.get((l, c, sg), [])
            if not v: continue
            rep = sum(x['replay'] for x in v); fr = [x['freq'] for x in v if x['freq']]; du = [x['duration'] for x in v if x['replay'] and x['duration'] is not None]
            ints = [x['int_frac'] for x in v if x['replay']]; lk = [x['lock'] for x in v if x['replay'] and x['lock'] is not None]
            nf = np.mean([x['nc_fired'] / x['nc_total'] for x in v]); cr = sum(x['cross_cells'] > 0 for x in v); nm = sum(x['nonmember_pyr'] > 0 for x in v); ra = sum(x['runaway'] for x in v)
            print('  %-12s n %3d replay %3d fracNC %.2f | volleys>=3: %2d freq %s dur(med) %s intfrac(med) %s lock(med) %s | cross %d nonmem %d runaway %d' % (l, len(v), rep, nf, len(fr), ('%.0f' % st.median(fr)) if fr else '-', ('%.1f' % st.median(du)) if du else '-', ('%.2f' % st.median(ints)) if ints else '-', ('%.2f' % st.median(lk)) if lk else '-', cr, nm, ra))
json.dump(S, open('summary.json', 'w'), default=float, indent=1)

#!/usr/bin/env python3
"""Score raw_*.json against the PREREGISTRATION measures -> summary.json + printed tables."""
import json, glob, os, sys, numpy as np
HERE = '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/gaba_vm/'
NP = 96; N = 116
def score(r):
    groups = [(sorted(m), sorted(c)) for m, c in json.load(open('/home/johnjose/cos/netmorph_work/recipe_v2/headline_i/groups_D42_V1n20_s33333.json'))['groups']] if False else None
    import sys as _s; _s.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/headline_i'); import dyn2 as H
    groups = H.load_groups(H.HERE + 'groups_D42_V1n20_s33333.json')
    sp = {int(k): np.array(v) for k, v in r['spikes'].items()}
    allmem = {m for mm, _ in groups for m in mm}
    def win(i, a, b): x = sp.get(i, np.array([])); return x[(x >= a) & (x < b)]
    solo = {}; rows = []
    for e in r['events']:
        t = e['t']; g1 = e['first']; mem1, cue1 = groups[g1]; nc1 = [m for m in mem1 if m not in cue1]
        d = dict(label=e['label'], first=g1, second=e['second'], delta=e['delta'])
        f1 = [win(m, t, t + 10) for m in nc1]
        d['first_complete'] = all(len(x) > 0 for x in f1); d['first_lat'] = [round(float(x[0] - t), 3) if len(x) else None for x in f1]
        if e['second'] is None:
            late = sum(len(win(m, t + 15, t + 450)) for m in mem1)
            nonmem = sum(len(win(i, t, t + 450)) for i in range(NP) if i not in allmem)
            othermem = sum(len(win(m, t, t + 450)) for gg, (mm, _) in enumerate(groups) if gg != g1 for m in mm)
            pyr = [x for i in range(NP) for x in win(i, t, t + 450)]
            ints = {i: win(i, t, t + 450) for i in range(NP, N)}
            d.update(late_member_spikes=late, nonmember_pyr_spikes=nonmem, other_memory_spikes=othermem, last_pyr_ms=round(float(max(pyr) - t), 3) if pyr else None,
                     member_spikes=sum(len(win(m, t, t + 450)) for m in mem1), ints_fired=[i for i in ints if len(ints[i])], int_spikes=int(sum(len(v) for v in ints.values())),
                     int_first_ms=round(float(min(v[0] for v in ints.values() if len(v)) - t), 3) if any(len(v) for v in ints.values()) else None)
            solo[g1] = d
        else:
            g2 = e['second']; mem2, cue2 = groups[g2]; nc2 = [m for m in mem2 if m not in cue2]; t2 = t + e['delta']
            f2 = [win(m, t2, t2 + 10) for m in nc2]
            pre2 = [win(m, t, t2) for m in nc2]
            d['second_complete'] = all(len(x) > 0 for x in f2); d['second_lat'] = [round(float(x[0] - t2), 3) if len(x) else None for x in f2]
            d['second_noncue_fired_before_cue2'] = int(sum(len(x) for x in pre2))
            d['second_noncue_fired'] = int(sum(len(x) > 0 for x in f2))
            d['nonmember_pyr_spikes'] = sum(len(win(i, t, t + 450)) for i in range(NP) if i not in allmem)
            d['late_member_spikes'] = sum(len(win(m, t + 15, t + 450)) for m in mem1) + sum(len(win(m, t2 + 15, t + 450)) for m in mem2)
            d['all_pyr_spikes'] = sum(len(win(i, t, t + 450)) for i in range(NP))
            d['int_spikes'] = sum(len(win(i, t, t + 450)) for i in range(NP, N))
            d['ints_fired'] = [i for i in range(NP, N) if len(win(i, t, t + 450))]
        rows.append(d)
    for d in rows:
        if d['second'] is not None:
            s = solo.get(d['second']); d['second_solo_complete'] = s['first_complete'] if s else None
            d['discard'] = bool(d['second_solo_complete'] and not d['second_complete'])
            if s and d['second_complete']: d['second_delay_vs_solo'] = [round(a - b, 3) if a is not None and b is not None else None for a, b in zip(d['second_lat'], s['first_lat'])]
    return rows, solo
def main():
    S = {}
    for f in sorted(glob.glob(HERE + 'raw_*.json')):
        r = json.load(open(f)); rows, solo = score(r); tag = r['tag']
        two = [d for d in rows if d['second'] is not None and d['label'][0] == 'G']
        disc = {str(int(dl)): sum(d['discard'] for d in two if d['delta'] == dl) for dl in (5.0, 10.0, 20.0, 50.0)}
        # added after first results (not preregistered): count only events where the network responded (first memory completed)
        discv = {str(int(dl)): sum(d['discard'] for d in two if d['delta'] == dl and d['first_complete']) for dl in (5.0, 10.0, 20.0, 50.0)}
        nval = {str(int(dl)): sum(1 for d in two if d['delta'] == dl and d['first_complete']) for dl in (5.0, 10.0, 20.0, 50.0)}
        burst = {str(int(dl)): int(sum(d['nonmember_pyr_spikes'] + d['late_member_spikes'] for d in two if d['delta'] == dl)) for dl in (5.0, 10.0, 20.0, 50.0)}
        ints2 = {str(int(dl)): round(float(np.mean([d['int_spikes'] for d in two if d['delta'] == dl])), 1) for dl in (5.0, 10.0, 20.0, 50.0)}
        S[tag] = dict(c=r['c'], gaba=r['gaba'], knob=r['knob'], prog=r['prog'], wall_s=r.get('wall_s'), load=r.get('load'), patch=r.get('patch'),
                      solo={str(k): {kk: v[kk] for kk in ('first_complete', 'first_lat', 'late_member_spikes', 'nonmember_pyr_spikes', 'other_memory_spikes', 'last_pyr_ms', 'member_spikes', 'ints_fired', 'int_spikes', 'int_first_ms')} for k, v in solo.items()},
                      discards_of_6=disc, discards_valid=discv, valid_events_of_6=nval, twocue_late_spikes=burst, twocue_mean_int_spikes=ints2, events=rows)
        so = S[tag]['solo']
        print('%-22s c=%-4s gaba=%-3s knob=%-8s solo complete %s | late member %s | nonmember %s | last pyr %s | ints %s first %s | discards d5/10/20/50 %s' % (
            tag, r['c'], r['gaba'], r['knob'], [so[k]['first_complete'] for k in sorted(so)], [so[k]['late_member_spikes'] for k in sorted(so)],
            [so[k]['nonmember_pyr_spikes'] for k in sorted(so)], [so[k]['last_pyr_ms'] for k in sorted(so)], [len(so[k]['ints_fired']) for k in sorted(so)], [so[k]['int_first_ms'] for k in sorted(so)],
            '/'.join(str(disc[k]) for k in ('5', '10', '20', '50'))) + ' | valid-only %s of %s | 2-cue late spikes %s | int spikes %s' % (
            '/'.join(str(discv[k]) for k in ('5', '10', '20', '50')), '/'.join(str(nval[k]) for k in ('5', '10', '20', '50')), '/'.join(str(burst[k]) for k in ('5', '10', '20', '50')), '/'.join(str(ints2[k]) for k in ('5', '10', '20', '50'))))
    json.dump(S, open(HERE + 'summary.json', 'w'), indent=1, default=float)
if __name__ == '__main__': main()

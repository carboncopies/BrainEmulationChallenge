import json, sys, os, glob
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/ripple_S1')
import numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from slib import *
groups = groups_from(OUT + 'design_K4.json')
R = {os.path.basename(f)[4:-5]: json.load(open(f)) for f in sorted(glob.glob(OUT + 'raw_*.json'))}
rows = []
for v, r in R.items():
    for k, e in r['runs'].items():
        if k == 'single':
            ev = e['events']; f = [x for x in ev if x['expect_complete']]; t = [x for x in ev if not x['expect_complete']]
            rows.append(dict(variant=v, case='single', complete4=sum(x['noncue_fired'] == 4 for x in f), false3=sum(x['noncue_fired'] > 0 for x in t),
              clean=all(x['clean'] for x in ev), member_spikes=[x['member_spikes'] for x in f], int_spikes=[x['interneuron_spikes'] for x in f],
              other_pyr=sum(x['other_pyr_fired'] + x['other_group_members_fired'] for x in ev), lat=sorted(set(round(x['latency_ms'], 2) for x in f)), last_pyr=[round(x['last_pyr_spike_ms'], 1) if x['last_pyr_spike_ms'] else None for x in f]))
        else:
            a = e['analysis']; m = a['memories']
            rows.append(dict(variant=v, case=k, complete=[x['n_noncue_fired_10ms'] for x in m], maxlat=round(max(x['latency_last_noncue_ms'] or 99 for x in m), 2),
              burst_end=[round(x['last_member_spike_after_cue_ms'], 1) for x in m], member_spikes=[x['member_spikes_total'] for x in m], int_spk=[x['int_spikes_in_window'] for x in m],
              ct=len(a['crosstalk_events']), spur=a['spurious_nonmember_pyr_spikes'], last=round(a['activity_end_after_first_cue_ms'], 1), le100=a['activity_ends_within_100ms'],
              burst40=a['burst_over_40ms_groups'], pyr_spk=a['total_pyr_spikes'], int_total=a['total_interneuron_spikes'], ints=a['ints_that_fired'], ok=a['ripple_success']))
json.dump(rows, open(OUT + 'summary.json', 'w'), indent=0)
for r in rows: print(r)
def fig(v, case, fn, zoom=None):
    e = R[v]['runs'][case]; vm = e['vm']; t = np.array(vm['times_ms']); sp = {int(k): x for k, x in e['spikes'].items()}
    fg, ax = plt.subplots(3, 1, figsize=(11, 10), sharex=True, gridspec_kw=dict(height_ratios=[2, 1.3, 1.3])); cols = ['C0', 'C1', 'C2', 'C3']; y = 0; yt = []
    for gi, (m, c) in enumerate(groups):
        for n in m:
            ax[0].plot(sp.get(n, []), [y] * len(sp.get(n, [])), '|', color=cols[gi], ms=5); yt.append((y, 'P%d%s' % (n, '*' if n in c else ''))); y += 1
    for i in vm['interneurons']:
        ax[0].plot(sp.get(i, []), [y] * len(sp.get(i, [])), '|', color='k', ms=5); yt.append((y, 'I%d' % i)); y += 1
    ax[0].set_yticks([a for a, _ in yt]); ax[0].set_yticklabels([b for _, b in yt], fontsize=5)
    for gi, on in e['events']:
        for a in ax: a.axvline(on, color=cols[gi], lw=.6, ls=':')
    ax[0].set_title('%s %s dt=%g ms raster (colour=memory, *=cue, black=interneurons)' % (v, case.split('_dt')[0], e['dt_ms']), fontsize=9)
    for gi, (m, c) in enumerate(groups):
        nc = [x for x in m if x not in c]
        ax[1].plot(t, vm['vm_mV'][str(nc[0])], color=cols[gi], lw=.8, label='G%d non-cue %d' % (gi, nc[0])); ax[1].plot(t, vm['vm_mV'][str(c[0])], color=cols[gi], lw=.5, ls='--', label='G%d cue %d' % (gi, c[0]))
    ax[1].set_ylabel('Vm pyr (mV)'); ax[1].legend(fontsize=5, ncol=4)
    for i in vm['interneurons'][:8]: ax[2].plot(t, vm['vm_mV'][str(i)], lw=.7, label='I%d' % i)
    ax[2].set_ylabel('Vm interneuron (mV)'); ax[2].legend(fontsize=5, ncol=4); ax[2].set_xlabel('ms after first cue')
    if zoom: ax[2].set_xlim(*zoom)
    fg.tight_layout(); fg.savefig(OUT + fn, dpi=100); plt.close(fg)
if 'E1' in R:
    fig('E1', 'o0123s12_dt1', 'fig_E1_best_dt1.png'); fig('E1', 'o0123s20_dt1', 'fig_E1_worst_dt1.png')
    fig('E1', 'o0123s12_dt0.1', 'fig_E1_best_zoom_dt0.1.png', zoom=(8, 28)); fig('E1', 'o0123s20_dt0.1', 'fig_E1_worst_zoom_dt0.1.png', zoom=(54, 74))

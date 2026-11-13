import json, sys
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/ripple_arborA')
import numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from alib import *
groups = groups_from(OUT + 'design_K4.json')
R = {v: json.load(open(OUT + 'raw_%s.json' % v)) for v in ['E1', 'NI']}
rows = []
for v in ['E1', 'NI']:
    for k, e in R[v]['runs'].items():
        if k == 'single': 
            ev = e['events']; rows.append(dict(variant=v, case='single-memory (4-cell completes / 3-cell does not)', completes_4cell='%d/4 groups' % sum(x['noncue_fired'] == 4 for x in ev if x['expect_complete']),
                three_cell_false_completions=sum(x['noncue_fired'] > 0 for x in ev if not x['expect_complete']), all_clean=all(x['clean'] for x in ev),
                lat=sorted(set(round(x['latency_ms'], 2) for x in ev if x['latency_ms'])), member_spikes=[x['member_spikes'] for x in ev if x['expect_complete']], int_spikes=[x['interneuron_spikes'] for x in ev if x['expect_complete']])); continue
        a = e['analysis']
        rows.append(dict(variant=v, case=k, memories_complete=[m['n_noncue_fired_10ms'] for m in a['memories']], max_latency_ms=round(max(m['latency_last_noncue_ms'] for m in a['memories']), 2),
            burst_end_after_cue_ms=[round(m['last_member_spike_after_cue_ms'], 1) for m in a['memories']], int_spikes_per_event=[m['int_spikes_in_window'] for m in a['memories']],
            crosstalk=len(a['crosstalk_events']), spurious_nonmember_pyr=a['spurious_nonmember_pyr_spikes'], last_spike_after_first_cue_ms=round(a['activity_end_after_first_cue_ms'], 1),
            within_100ms=a['activity_ends_within_100ms'], terminates=a['terminates'], total_pyr_spikes=a['total_pyr_spikes'], total_int_spikes=a['total_interneuron_spikes'], ints_fired=a['ints_that_fired'], ripple_success=a['ripple_success']))
json.dump(rows, open(OUT + 'summary.json', 'w'), indent=1)
for r in rows: print(r)
# figures
def fig(v, case, fn, zoom=None):
    e = R[v]['runs'][case]; vm = e['vm']; t = np.array(vm['times_ms']); sp = {int(k): x for k, x in e['spikes'].items()}
    mem = [m for mm, _ in groups for m in mm]; fig, ax = plt.subplots(3, 1, figsize=(11, 10), sharex=True, gridspec_kw=dict(height_ratios=[2, 1.3, 1.3]))
    cols = ['C0', 'C1', 'C2', 'C3']; y = 0; yt = []
    for gi, (m, c) in enumerate(groups):
        for n in m:
            ax[0].plot(sp.get(n, []), [y] * len(sp.get(n, [])), '|', color=cols[gi], ms=5); yt.append((y, 'P%d%s' % (n, '*' if n in c else ''))); y += 1
    for i in vm['interneurons']:
        ax[0].plot(sp.get(i, []), [y] * len(sp.get(i, [])), '|', color='k', ms=5); yt.append((y, 'I%d' % i)); y += 1
    ax[0].set_yticks([a for a, _ in yt]); ax[0].set_yticklabels([b for _, b in yt], fontsize=5)
    for gi, on in e['events']:
        for a in ax: a.axvline(on, color=cols[gi], lw=.6, ls=':')
    ax[0].set_title('%s %s dt=%g ms  spike raster (colour = memory, * = cue cell, black = interneurons). dotted = cue onset' % (v, case.split('_dt')[0], e['dt_ms']), fontsize=9)
    for gi, (m, c) in enumerate(groups):
        nc = [x for x in m if x not in c]
        ax[1].plot(t, vm['vm_mV'][str(nc[0])], color=cols[gi], lw=.8, label='G%d non-cue %d' % (gi, nc[0]))
        ax[1].plot(t, vm['vm_mV'][str(c[0])], color=cols[gi], lw=.5, ls='--', label='G%d cue %d' % (gi, c[0]))
    ax[1].set_ylabel('Vm pyramidal (mV)'); ax[1].legend(fontsize=5, ncol=4)
    for i in vm['interneurons'][:8]: ax[2].plot(t, vm['vm_mV'][str(i)], lw=.7, label='I%d' % i)
    ax[2].set_ylabel('Vm interneuron (mV)'); ax[2].legend(fontsize=5, ncol=4); ax[2].set_xlabel('ms after first cue')
    if zoom: ax[2].set_xlim(*zoom)
    fig.tight_layout(); fig.savefig(OUT + fn, dpi=110); plt.close(fig)
fig('E1', 'o0123s12_dt1', 'fig_E1_best_dt1.png'); fig('E1', 'o0123s20_dt1', 'fig_E1_worst_dt1.png')
fig('E1', 'o0123s12_dt0.1', 'fig_E1_best_zoom_dt0.1.png', zoom=(8, 28)); fig('E1', 'o0123s20_dt0.1', 'fig_E1_worst_zoom_dt0.1.png', zoom=(54, 74))

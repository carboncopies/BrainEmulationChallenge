import sys, json, glob, os
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/ripple_S1_R3')
from r3lib import *
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
R = {os.path.basename(f)[4:-5]: json.load(open(f)) for f in sorted(glob.glob(OUT + 'raw_s*.json'))}
groups, _, _ = load_pairs('R3_c0')
summ = {}
for n, e in R.items():
    if e['kind'] == 'single':
        ev = e['events']; f = [x for x in ev if x['expect_complete']]; t = [x for x in ev if not x['expect_complete']]
        summ[n] = dict(pairs=e['pairs'], sg=e['sg'], kind='single', complete=[x['noncue_fired'] for x in f], latency=[round(x['latency_ms'], 2) for x in f], member_spikes=[x['member_spikes'] for x in f],
            burst_end=[round(x['burst_end_ms'], 2) for x in f], int_spikes=[x['interneuron_spikes'] for x in f], ints=sorted({i for x in f for i in x['ints_fired']}), false3=sum(x['noncue_fired'] > 0 for x in t),
            spurious=sum(x['other_pyr_fired'] for x in ev), crosstalk=sum(x['other_group_members_fired'] for x in ev), all_clean=all(x['clean'] for x in ev), readback=e['readback'])
    else:
        a = e['analysis']; m = a['memories']
        summ[n] = dict(pairs=e['pairs'], sg=e['sg'], kind='ripple', order=[g for g, _ in e['events']], dt=e['dt_ms'], cue3=a['cue3_group'], complete=[x['n_noncue_fired_10ms'] for x in m],
            burst_end=[round(x['last_member_spike_after_cue_ms'], 2) for x in m], member_spikes=[x['member_spikes_total'] for x in m], int_spikes=[x['int_spikes_in_window'] for x in m],
            crosstalk=len(a['crosstalk_events']), spurious=a['spurious_nonmember_pyr_spikes'], last=round(a['activity_end_after_first_cue_ms'], 2), burst_gt40=a['burst_over_40ms_groups'],
            ints=a['ints_that_fired'], pyr_spk=a['total_pyr_spikes'], int_total=a['total_interneuron_spikes'], success=a['ripple_success'], readback=e['readback'])
json.dump(summ, open(OUT + 'summary.json', 'w'), indent=0)
for n, s in summ.items(): print(n, {k: v for k, v in s.items() if k != 'readback'})
# bio audit
aud = {}
for pn in ['R3_c0', 'P_T18_L10_c0', 'R3_c0.15', 'R3_c0.25', 'R3_c0.5']:
    _, pl, raw = load_pairs(pn); d = {}
    for kind, sel in [('Pyr->Pyr', lambda b: b < NP), ('Pyr->Int', lambda b: b >= NP)]:
        x = np.array([c / g for a, b, c, g in pl if sel(b)]); cc = np.array([c for a, b, c, g in pl if sel(b)])
        d[kind] = dict(n=int(len(x)), n_zero=int((x == 0).sum()), frac_zero=round(float((x == 0).mean()), 4), n_0_to_0p1=int(((x > 0) & (x < 0.1 - 1e-9)).sum()), n_0p1_to_1=int(((x >= 0.1 - 1e-9) & (x <= 1 + 1e-9)).sum()),
                       n_above_1=int((x > 1 + 1e-9).sum()), min_nonzero_w=float(x[x > 0].min()) if (x > 0).any() else None, max_w=float(x.max()), max_conductance_nS=float(cc.max()))
    d['all_weights_in_0_1'] = all(0 <= c / g <= 1 + 1e-9 for a, b, c, g in pl)
    d['n_pairs_total'] = len(pl)
    aud[pn] = d
json.dump(aud, open(OUT + 'bio_audit.json', 'w'), indent=1)
print(json.dumps(aud, indent=1))
cols = ['C0', 'C1', 'C2', 'C3']
def fig(n, fn, zoom=None):
    e = R[n]; vm = e['vm']; t = np.array(vm['times_ms']); sp = {int(k): x for k, x in e['spikes'].items()}
    fg, ax = plt.subplots(3, 1, figsize=(11, 10), sharex=True, gridspec_kw=dict(height_ratios=[2, 1.3, 1.3])); y = 0; yt = []
    for gi, (m, c) in enumerate(groups):
        for k in m:
            ax[0].plot(sp.get(k, []), [y] * len(sp.get(k, [])), '|', color=cols[gi], ms=5); yt.append((y, 'P%d%s' % (k, '*' if k in c else ''))); y += 1
    for i in vm['interneurons']:
        ax[0].plot(sp.get(i, []), [y] * len(sp.get(i, [])), '|', color='k', ms=5); yt.append((y, 'I%d' % i)); y += 1
    ax[0].set_yticks([a for a, _ in yt]); ax[0].set_yticklabels([b for _, b in yt], fontsize=5)
    for gi, on in e['events']:
        for a in ax: a.axvline(on, color=cols[gi], lw=.6, ls=':')
    ax[0].set_title('R3 %s (%s, spacing order %s) dt=%g ms raster (colour=memory, *=cue, black=interneurons)' % (n, e['pairs'], [g for g, _ in e['events']], e['dt_ms']), fontsize=9)
    for gi, (m, c) in enumerate(groups):
        nc = [x for x in m if x not in c]
        ax[1].plot(t, vm['vm_mV'][str(nc[0])], color=cols[gi], lw=.8, label='G%d non-cue %d' % (gi, nc[0])); ax[1].plot(t, vm['vm_mV'][str(c[0])], color=cols[gi], lw=.5, ls='--', label='G%d cue %d' % (gi, c[0]))
    ax[1].set_ylabel('Vm pyr (mV)'); ax[1].legend(fontsize=5, ncol=4)
    for i in vm['interneurons'][:8]: ax[2].plot(t, vm['vm_mV'][str(i)], lw=.7, label='I%d' % i)
    ax[2].set_ylabel('Vm interneuron (mV)'); ax[2].legend(fontsize=5, ncol=4); ax[2].set_xlabel('ms after first cue')
    if zoom: ax[2].set_xlim(*zoom)
    fg.tight_layout(); fg.savefig(OUT + fn, dpi=100); plt.close(fg)
fig('s6_rip12', 'fig_R3_best_dt1.png'); fig('s8_rip20', 'fig_R3_worst_dt1.png')
fig('s10_rip12_dt01', 'fig_R3_best_zoom_dt0.1.png', zoom=(8, 28)); fig('s16_rip20_dt01', 'fig_R3_worst_zoom_dt0.1.png', zoom=(40, 70))

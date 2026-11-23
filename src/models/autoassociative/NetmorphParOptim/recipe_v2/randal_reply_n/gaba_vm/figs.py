#!/usr/bin/env python3
"""Vm trace figures for Randal. usage: figs.py  (reads raw_*.json + vm_*.npz; writes fig_*.png)
GABA conductance on a cell is reconstructed offline from interneuron spike times and the loaded connectome pair conductances
with the simulator's kernel (rise 0.5, decay 10 ms, peak-normalised, onset delay 1.0 ms; Receptor.cpp g_norm); the GABA current is g x (Vm - E_GABA), E_GABA = -70 mV."""
import json, os, sys, numpy as np
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
HERE = '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/gaba_vm/'
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/headline_i'); import dyn2 as H
GROUPS = H.load_groups(H.HERE + 'groups_D42_V1n20_s33333.json'); NP = 96; N = 116
COL = {'sg': '#8c8c8c', '1': '#1f6fb4', '2': '#2a9d5c', '5': '#c4352b'}
LAB = {'sg': 'GABA silenced', '1': 'GABA x1 (build)', '2': 'GABA x2', '5': 'GABA x5 (above natural range)'}
def kern(t, tr, td, d=1.0001):
    tp = tr * td / (td - tr) * np.log(td / tr); nrm = np.exp(-tp / td) - np.exp(-tp / tr); s = t - d
    return np.where(s >= 0, (np.exp(-np.clip(s, 0, None) / td) - np.exp(-np.clip(s, 0, None) / tr)) / nrm, 0.0)
def load(tag):
    r = json.load(open(HERE + 'raw_%s.json' % tag)); z = np.load(HERE + 'vm_%s.npz' % tag)
    return r, z['t'], z['vm']
def gaba_on(r, cell, t):
    g = np.zeros_like(t, dtype=float)
    for k, c in r['gaba_pair_cond'].items():
        a, b = map(int, k.split(','))
        if b != cell or c == 0: continue
        for s in r['spikes'].get(str(a), r['spikes'].get(a, [])):
            g += c * kern(t - s, 0.5, 10.0)
    return g
def sp(r, i): return np.array(r['spikes'].get(str(i), r['spikes'].get(i, [])))
def recall_fig(tags, ev_t, title, fn, win=(-3, 40), second=None, first=0):
    rs = {t: load(t) for t in tags}; base = rs[tags[0]][0]
    mem, cue = GROUPS[first]; nc = [m for m in mem if m not in cue]
    cells2 = []; cue2 = []
    if second is not None:
        mem2, cue2 = GROUPS[second]; nc2 = [m for m in mem2 if m not in cue2]; cells2 = nc2
    fired_ints = sorted({i for t in tags for i in range(NP, N) if any(ev_t + win[0] <= x < ev_t + win[1] for x in sp(rs[t][0], i))})
    nrow = 6 if second is None else 7
    fig, ax = plt.subplots(nrow, 1, figsize=(11, 2.3 * nrow), sharex=True)
    # raster for the first tag of each group (x1)
    main = '1' if any(rs[t][0]['gaba'] == '1' for t in tags) else rs[tags[0]][0]['gaba']
    tm = [t for t in tags if rs[t][0]['gaba'] == main][0]; r0 = rs[tm][0]
    for i in range(N):
        x = sp(r0, i); x = x[(x >= ev_t + win[0]) & (x < ev_t + win[1])] - ev_t
        if len(x) == 0: continue
        c = '#d08c00' if (i in cue or i in cue2) else ('#1f6fb4' if i in nc else ('#7b3fa0' if i >= NP else ('#2a9d5c' if i in cells2 else 'k')))
        ax[0].plot(x, [i] * len(x), '|', color=c, ms=8, mew=1.6)
    leg2 = (', green = G%d non-cue' % second) if second is not None else ''
    ax[0].set_ylabel('cell ID'); ax[0].set_title('%s\nraster (%s): orange = cue (forced), blue = G%d non-cue%s, purple = interneurons, black = other pyramidal' % (title, LAB[main], first, leg2), fontsize=9, loc='left')
    ax[0].axhline(NP - 0.5, color='#ccc', lw=0.8)
    def vm_panel(a, cells, label):
        for t in tags:
            r, tt, vm = rs[t]; m = (tt >= ev_t + win[0]) & (tt < ev_t + win[1])
            for j, cc in enumerate(cells):
                a.plot(tt[m] - ev_t, vm[cc][m], color=COL[r['gaba']], lw=1.1, alpha=0.9, ls=['-', '--', ':', '-.'][j % 4], label='%s cell %d' % (LAB[r['gaba']], cc) if True else None)
        a.axhline(-50, color='#bbb', lw=0.7, ls=':'); a.axhline(-70, color='#bbb', lw=0.7, ls=':')
        a.set_ylabel('Vm (mV)'); a.set_title(label, fontsize=9, loc='left'); a.set_ylim(-95, 35)
    vm_panel(ax[1], cue[:2], 'Vm, G%d cue cells %s (forced spikes at 0 and 0.5 ms); dotted lines: threshold -50, rest = E_GABA -70' % (first, cue[:2]))
    vm_panel(ax[2], nc, 'Vm, G%d non-cue members %s (must be recruited by the cue)' % (first, nc))
    k = 3
    if second is not None:
        vm_panel(ax[3], cells2, 'Vm, G%d non-cue members %s (second cue at %g ms)' % (second, cells2, [e for e in rs[tags[0]][0]['events'] if abs(e['t'] - ev_t) < 1][0]['delta'])); k = 4
    vm_panel(ax[k], fired_ints[:3], 'Vm, interneurons that fire in this window %s (first 3 shown)' % fired_ints)
    a = ax[k + 1]
    tgt = (cells2 if second is not None else nc)
    for t in tags:
        r, tt, vm = rs[t]; m = (tt >= ev_t + win[0]) & (tt < ev_t + win[1])
        if r['gaba'] == 'sg': continue
        for j, cc in enumerate(tgt):
            g = gaba_on(r, cc, tt[m]); a.plot(tt[m] - ev_t, g, color=COL[r['gaba']], lw=1.2, ls=['-', '--'][j % 2], label='%s on cell %d' % (LAB[r['gaba']], cc))
    a.set_ylabel('g_GABA (nS)'); a.set_xlabel('time from first cue onset (ms)'); a.set_title('GABA conductance on %s (reconstructed from interneuron spikes x connectome pair conductance)' % tgt, fontsize=9, loc='left')
    a.legend(fontsize=7, ncol=3, loc='upper right'); a.set_xlabel('')
    a = ax[k + 2]
    for t in tags:
        r, tt, vm = rs[t]; m = (tt >= ev_t + win[0]) & (tt < ev_t + win[1])
        if r['gaba'] == 'sg': continue
        for j, cc in enumerate(tgt):
            g = gaba_on(r, cc, tt[m]); a.plot(tt[m] - ev_t, g * (vm[cc][m] + 70.0), color=COL[r['gaba']], lw=1.2, ls=['-', '--'][j % 2], label='%s on cell %d' % (LAB[r['gaba']], cc))
    a.axhline(0, color='#bbb', lw=0.7); a.set_ylabel('I_GABA (pA)'); a.set_xlabel('time from first cue onset (ms)')
    a.set_title('GABA current on the same cells = g_GABA x (Vm - E_GABA), outward positive; zero whenever Vm = -70 mV (rest = E_GABA)', fontsize=9, loc='left')
    h, l = ax[2].get_legend_handles_labels(); ax[2].legend(h, l, fontsize=7, ncol=3, loc='upper right')
    fig.tight_layout(); fig.savefig(HERE + fn, dpi=130); plt.close(fig); print('wrote', fn)
def runaway_fig(tags, ev_t, title, fn, win=(-3, 120)):
    rs = {t: load(t) for t in tags}
    fig, ax = plt.subplots(len(tags) + 1, 1, figsize=(11, 2.4 * (len(tags) + 1)), sharex=True)
    mem, cue = GROUPS[0]; allmem = {m for mm, _ in GROUPS for m in mm}
    late = None
    for a, t in zip(ax, tags):
        r = rs[t][0]
        for i in range(N):
            x = sp(r, i); x = x[(x >= ev_t + win[0]) & (x < ev_t + win[1])] - ev_t
            if len(x) == 0: continue
            c = '#d08c00' if i in cue else ('#1f6fb4' if i in mem else ('#7b3fa0' if i >= NP else 'k'))
            a.plot(x, [i] * len(x), '|', color=c, ms=6, mew=1.3)
        a.axhline(NP - 0.5, color='#ccc', lw=0.8); a.set_ylabel('cell ID'); a.set_title('%s: raster (orange cue, blue G0 members, black non-member pyramidal, purple interneurons)' % LAB[r['gaba']], fontsize=9, loc='left')
    # Vm of the non-member pyramidal cell that fires most in the SG run
    rsg = rs[tags[0]][0]; cnt = {i: int(((sp(rsg, i) >= ev_t) & (sp(rsg, i) < ev_t + win[1])).sum()) for i in range(NP) if i not in allmem}
    cell = max(cnt, key=cnt.get) if cnt else 0
    a = ax[-1]
    for t in tags:
        r, tt, vm = rs[t]; m = (tt >= ev_t + win[0]) & (tt < ev_t + win[1]); a.plot(tt[m] - ev_t, vm[cell][m], color=COL[r['gaba']], lw=1.0, label=LAB[r['gaba']])
    a.set_title('Vm of non-member pyramidal cell %d (most active non-member with GABA silenced)' % cell, fontsize=9, loc='left'); a.set_ylabel('Vm (mV)'); a.set_xlabel('time from cue onset (ms)'); a.legend(fontsize=7)
    fig.suptitle(title, fontsize=10, x=0.01, ha='left'); fig.tight_layout(); fig.savefig(HERE + fn, dpi=130); plt.close(fig); print('wrote', fn)

def raster_grid(rows, label, title, fn, win=(-3, 150)):
    """rows: list of (tag, row title). Raster of one event (by label) in each run, from spike times (no Vm needed)."""
    fig, ax = plt.subplots(len(rows), 1, figsize=(11, 1.9 * len(rows)), sharex=True)
    allmem = {m for mm, _ in GROUPS for m in mm}
    for a, row in zip(ax, rows):
        tag, rt = row[0], row[1]; lab = row[2] if len(row) > 2 else label
        r = json.load(open(HERE + 'raw_%s.json' % tag)); e = [x for x in r['events'] if x['label'] == lab][0]; t0 = e['t']; rt = '%s, event %s' % (rt, lab)
        m1, c1 = GROUPS[e['first']]; m2, c2 = GROUPS[e['second']] if e['second'] is not None else ([], [])
        n = 0
        for i in range(N):
            x = sp(r, i); x = x[(x >= t0 + win[0]) & (x < t0 + win[1])] - t0
            if len(x) == 0: continue
            n += len(x) if (i < NP and i not in allmem) else 0
            c = '#d08c00' if (i in c1 or i in c2) else ('#1f6fb4' if i in m1 else ('#2a9d5c' if i in m2 else ('#7b3fa0' if i >= NP else 'k')))
            a.plot(x, [i] * len(x), '|', color=c, ms=5, mew=1.1)
        a.axhline(NP - 0.5, color='#ccc', lw=0.8); a.set_ylabel('cell'); a.set_ylim(-2, N + 1)
        a.set_title('%s  (non-member pyramidal spikes in window: %d)' % (rt, n), fontsize=9, loc='left')
    ax[-1].set_xlabel('time from first cue onset (ms)')
    fig.suptitle(title + '\norange = cue cells (forced), blue = first memory, green = second memory, black = other pyramidal, purple = interneurons', fontsize=9.5, x=0.01, ha='left')
    fig.tight_layout(); fig.savefig(HERE + fn, dpi=120); plt.close(fig); print('wrote', fn)

def recall_fig2(tags, ev_t, title, fn, first, second): recall_fig(tags, ev_t, title, fn, win=(-3, 50), second=second, first=first)
if __name__ == '__main__':
    have = lambda t: os.path.exists(HERE + 'raw_%s.json' % t)
    for c in ('0', '1.5', '3.0'):
        tags = [t for t in ('A_sg_c%s' % c, 'A_x1_c%s' % c, 'A_x5_c%s' % c) if have(t)]
        if c == '1.5': tags = [t for t in ('B_sg_c1.5', 'B_x1_c1.5', 'B_x5_c1.5') if have(t)]
        if c == '3.0': tags = [t for t in ('C_sg_c3.0', 'C_x1_c3.0', 'C_x5_c3.0') if have(t)]
        if not tags: continue
        recall_fig(tags, 20.0, 'Recall of memory G0 (E4 model s33333, D42, background c = %s nS): cue 4 cells at 0-1.5 ms' % c, 'fig_recall_c%s.png' % c)
        recall_fig(tags, 520.0, 'Two cues: G0 at 0 ms, then G1 at 10 ms (c = %s nS)' % c, 'fig_twocue_d10_c%s.png' % c, win=(-3, 50), second=1)
        if c == '3.0': runaway_fig(tags, 20.0, 'Recall of G0 at c = 3.0 nS: late activity with GABA silenced, x1, x5', 'fig_late_c3.0.png')
    if have('F2_x1_c0') and have('F_sg_c0'):
        r = json.load(open(HERE + 'raw_F2_x1_c0.json')); evs = [e for e in r['events'] if e['label'] in ('G1>G0 d5',)]
        for e in evs:
            recall_fig_generic = None
            fn = 'fig_discard_%s_c0.png' % e['label'].replace('>', 'to').replace(' ', '_')
            recall_fig2(['F_sg_c0', 'F2_x1_c0'], e['t'], 'Second cue DISCARDED with GABA x1 at c = 0: %s (first G%d at 0 ms, second G%d at %g ms); grey = same event with GABA silenced' % (e['label'], e['first'], e['second'], e['delta']), fn, e['first'], e['second'])
    rows = [r_ for r_ in [('B_sg_c1.5', 'c 1.5, GABA silenced'), ('B_x1_c1.5', 'c 1.5, GABA x1 (build)'), ('B_x5_c1.5', 'c 1.5, GABA x5'),
            ('K_nmda056_sg', 'c 1.5 + NMDA 0.56, GABA silenced'), ('K_nmda056_x1', 'c 1.5 + NMDA 0.56, GABA x1'),
            ('K_nmda100_x1', 'c 1.5 + NMDA 1.0, GABA x1 (runaway in 3 of 6 such events)', 'G1>G0 d5'), ('K_nmda100_x1', 'c 1.5 + NMDA 1.0, GABA x1 (one of the other 3)'), ('K_nmda100_x5', 'c 1.5 + NMDA 1.0, GABA x5')] if have(r_[0])]
    if rows: raster_grid(rows, 'G0>G2 d5', 'Two memories cued 5 ms apart (first at 0 ms, second at 5 ms): does GABA stop the reverberation?', 'fig_runaway_d5.png')
    tags = [t for t in ('K_lat_sg', 'K_lat_x1', 'K_lat_x5') if have(t)]
    if tags: recall_fig(tags, 20.0, 'LATERAL-INHIBITION knob (cue->interneuron cap removed, Pyr->Int AMPA x2), c = 1.5: interneurons fire at ~2 ms, BEFORE the non-cue members', 'fig_recall_lateral.png')
    for kn in ('nmda100', 'nmda056'):
        tags = [t for t in ('K_%s_sg' % kn, 'K_%s_x1' % kn, 'K_%s_x5' % kn) if have(t)]
        if tags: runaway_fig(tags, 20.0, 'Recall of G0 at c = 1.5 nS with NMDA on (NMDA/AMPA %s)' % ('1.0' if kn == 'nmda100' else '0.56'), 'fig_late_%s.png' % kn)

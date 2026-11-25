#!/usr/bin/env python3
"""Vm figures for Randal from the F runs (seed s33333, memory G0 = cue 10,11,34,78 / non-cue 29,63; G1 non-cue 47,50).
Vm is recorded by NES. g_NMDA and g_GABA are RECONSTRUCTED offline from presynaptic spike times and the read-back weights x peak sums,
with the simulator's kernels (NMDA rise 2 / decay 100 ms, GABA 0.5 / 10 ms, onset delay 1.0 ms, peak-normalised, capped at the group's peak sum)
and for NMDA NES's Mg block B(V) = 1 / (1 + 0.33 exp(-0.062 V)) evaluated at the recorded Vm of the postsynaptic cell."""
import json, sys, numpy as np
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
HERE = '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/nmda_gaba_exp/'
NP = 96; N = 116
COL = {0.0: '#8c8c8c', 1.0: '#1f6fb4', 2.0: '#2a9d5c', 5.0: '#c4352b'}
LAB = {0.0: 'GABA off', 1.0: 'GABA x1 (build, ~literature mean)', 2.0: 'GABA x2', 5.0: 'GABA x5 (outside natural range)'}
RLAB = {0.0: 'NMDA off (r 0, old runs)', 0.56: 'NMDA/AMPA r 0.56 (build ratio)', 1.0: 'NMDA/AMPA r 1.0 (upper bound)'}
def kern(t, tr, td, d=1.0001):
    tp = tr * td / (td - tr) * np.log(td / tr); nrm = np.exp(-tp / td) - np.exp(-tp / tr); s = np.clip(t - d, 0, None)
    return np.where(t - d >= 0, (np.exp(-s / td) - np.exp(-s / tr)) / nrm, 0.0)
def load(c, r, f):
    tag = 'F_s33333_c%g_r%g_f%g' % (c, r, f); d = json.load(open(HERE + 'raw_%s.json' % tag)); z = np.load(HERE + 'vm_%s.npz' % tag)
    return d, z['t'].astype(float), z['vm'].astype(float)
def spk(d, i): return np.array(d['spikes'].get(str(i), d['spikes'].get(i, [])))
def cond(d, t, vm, post, typ):
    """reconstructed summed conductance of type typ (2 GABA, 3 NMDA) onto post over time t"""
    tr, td = {2: (0.5, 10.0), 3: (2.0, 100.0)}[typ]; g = np.zeros_like(t)
    for k, (w, gs) in d['eff_cond'].items():
        a, b, ty = map(int, k.split(','))
        if b != post or ty != typ: continue
        s = spk(d, a); s = s[(s < t[-1]) & (s > t[0] - 600)]
        if not len(s): continue
        kk = sum(kern(t - x, tr, td) for x in s)
        gk = np.minimum(gs, min(1.0, w) * gs * kk)
        if typ == 3: gk = np.minimum(gs, (1.0 / (1.0 + 0.33 * np.exp(-0.062 * vm[post]))) * min(1.0, w) * gs * kk)
        g += gk
    return g
def vth(d, cell, t):
    """reconstructed adaptive threshold (LIFCNeuron.cpp update_adaptive_threshold; model-file values VAct -50, dVth 10 mV, dh 0.2/spike, tau_h 50 ms,
    floor +1 mV/spike recovering to VAct with tau 500 ms; h assumed 1 at start). Exact exponential between spikes."""
    sp_ = spk(d, cell); h = np.ones_like(t); fl = np.full_like(t, -50.0)
    for x in sp_[sp_ < t[-1]]:
        a = t >= x
        # each spike adds a decaying deficit: h -= 0.2 e^{-(t-x)/50}, floor += 1 e^{-(t-x)/500} (linear superposition of the linear recovery ODEs)
        h[a] -= 0.2 * np.exp(-(t[a] - x) / 50.0); fl[a] += 1.0 * np.exp(-(t[a] - x) / 500.0)
    return np.maximum(-50.0 + 10.0 * (1 - h), fl)
def panel(runs, ev, win, title, fn, extra_nc=None):
    """runs: list of (c, r, f); ev: event index in the F schedule; one column"""
    data = [(key, *load(*key)) for key in runs]
    d0 = data[0][1]; G = d0['groups']; e = d0['events'][ev]; t0 = e['t']; g0 = G[e['group']]
    cue = [c for c in e['cue']]; nc = g0['noncue']; nc2 = G[e['second']]['noncue'] if e['kind'] == 'pair' else []
    ints = sorted({i for key, d, t, vm in data for i in range(NP, N) if any(t0 + win[0] <= x < t0 + win[1] for x in spk(d, i))})
    fig, ax = plt.subplots(6, 1, figsize=(11, 15), sharex=True)
    for key, d, t, vm in data:
        col = COL[key[2]]; m = (t >= t0 + win[0]) & (t < t0 + win[1]); tt = t[m] - t0; lab = LAB[key[2]] + ('' if len({k[1] for k in runs}) == 1 else ', ' + RLAB[key[1]])
        ls = '-' if len({k[1] for k in runs}) == 1 or key[1] == runs[-1][1] else '--'
        for j, cc in enumerate(cue): ax[0].plot(tt, vm[cc][m], color=col, lw=0.8, ls=ls, label=lab if j == 0 else None)
        for j, n in enumerate(nc):
            ax[1].plot(tt, vm[n][m], color=col, lw=1.1, ls=ls, label=lab if j == 0 else None)
            ax[1].plot(tt, vth(d, n, t[m]), color=col, lw=0.8, ls=':', label='reconstructed adaptive threshold' if (j == 0 and key == runs[0]) else None)
        for j, n in enumerate(nc2): ax[2].plot(tt, vm[n][m], color=col, lw=1.1, ls=ls)
        for j, n in enumerate(ints): ax[3].plot(tt, vm[n][m], color=col, lw=0.6, ls=ls, alpha=0.8)
        tw = t[m]
        gn = sum(cond(d, tw, {n: vm[n][m]}, n, 3) for n in nc) / len(nc); gg = sum(cond(d, tw, None, n, 2) for n in nc) / len(nc)
        ax[4].plot(tt, gn, color=col, lw=1.2, ls=ls); ax[5].plot(tt, gg, color=col, lw=1.2, ls=ls)
    # spike ticks of the first and last run on the cue row
    for tt_, cc in e['cues']:
        if win[0] <= tt_ - t0 < win[1]: ax[0].axvline(tt_ - t0, color='k', lw=0.3, alpha=0.3)
    ax[0].set_ylabel('Vm cue cells\n%s (mV)' % cue); ax[1].set_ylabel('Vm non-cue cells\nof cued memory %s (mV)\n(dotted: adaptive threshold)' % nc)
    ax[2].set_ylabel(('Vm non-cue cells of\nsecond memory %s (mV)' % nc2) if nc2 else '(no second memory\nin this event)')
    ax[3].set_ylabel('Vm of the %d interneurons\nthat fire (mV)' % len(ints)); ax[4].set_ylabel('g_NMDA on non-cue\n(reconstructed, Mg-blocked,\nmean per cell, nS)')
    ax[5].set_ylabel('g_GABA on non-cue\n(reconstructed, mean\nper cell, nS)'); ax[5].set_xlabel('ms after the first cue spike')
    for a in ax[:4]: a.axhline(-50, color='k', lw=0.4, ls=':')
    if not nc2: ax[2].cla(); ax[2].set_yticks([]); ax[2].text(0.5, 0.5, 'no second memory in this event', ha='center', va='center', transform=ax[2].transAxes, color='0.5'); ax[2].set_ylabel('')
    if not ints: ax[3].cla(); ax[3].set_yticks([]); ax[3].text(0.5, 0.5, 'no interneuron fired in this window (any condition)', ha='center', va='center', transform=ax[3].transAxes, color='0.5'); ax[3].set_ylabel('')
    ax[0].legend(fontsize=8, loc='upper right'); ax[1].legend(fontsize=8, loc='upper right')
    fig.suptitle(title, fontsize=11); fig.tight_layout(rect=(0, 0, 1, 0.97)); fig.savefig(HERE + fn, dpi=110); plt.close(fig); print('wrote', fn)
def raster(runs, ev, win, title, fn):
    data = [(key, *load(*key)) for key in runs]; G = data[0][1]['groups']; mem = {x: k for k, g in enumerate(G) for x in g['members']}
    fig, ax = plt.subplots(len(data), 1, figsize=(11, 2.6 * len(data)), sharex=True)
    for a, (key, d, t, vm) in zip(np.atleast_1d(ax), data):
        t0 = d['events'][ev]['t']
        for i in range(N):
            x = spk(d, i); x = x[(x >= t0 + win[0]) & (x < t0 + win[1])] - t0
            a.plot(x, [i] * len(x), '|', ms=4, color='#c4352b' if i >= NP else (['#1f6fb4', '#2a9d5c', '#8a5cc4'][mem[i]] if i in mem else '#555555'))
        a.set_ylabel('cell ID'); a.set_title('%s, %s, c %g nS: %d Pyr spikes' % (LAB[key[2]], RLAB[key[1]], key[0], sum(len(spk(d, i)[(spk(d, i) >= t0 + win[0]) & (spk(d, i) < t0 + win[1])]) for i in range(NP))), fontsize=9)
    np.atleast_1d(ax)[-1].set_xlabel('ms after cue (blue/green/purple = memories G0/G1/G2, grey = other Pyr, red = interneurons)')
    fig.suptitle(title, fontsize=11); fig.tight_layout(rect=(0, 0, 1, 0.97)); fig.savefig(HERE + fn, dpi=110); plt.close(fig); print('wrote', fn)
if __name__ == '__main__':
    W = (-3, 60)
    for r in (0.0, 0.56, 1.0):
        rs = [(1.5, r, 0.0), (1.5, r, 1.0)]; rl = RLAB[r]
        panel(rs, 0, W, 'G0 full cue (4 of 4 cells), c 1.5 nS, %s: GABA off vs x1' % rl, 'fig_full_c1.5_r%g.png' % r)
        panel(rs, 1, W, 'G0 partial cue, 3 of 4 cells (25%% missing), c 1.5 nS, %s' % rl, 'fig_3cell_c1.5_r%g.png' % r)
        panel(rs, 2, W, 'G0 partial cue, 2 of 4 cells (50%% missing), c 1.5 nS, %s' % rl, 'fig_2cell_c1.5_r%g.png' % r)
        panel(rs, 3, W, 'G0 cued, then G1 cued 10 ms later (discard test), c 1.5 nS, %s' % rl, 'fig_pair_d10_c1.5_r%g.png' % r)
        panel(rs, 4, (-3, 120), 'G0 full cue repeated 5 x every 20 ms (pacing), c 1.5 nS, %s' % rl, 'fig_train20_c1.5_r%g.png' % r)
    rs = [(0.0, 0.56, 0.0), (0.0, 0.56, 1.0)]
    panel(rs, 0, W, 'G0 full cue, c 0 (no background), NMDA r 0.56', 'fig_full_c0_r0.56.png')
    panel(rs, 3, W, 'G0 then G1 at 10 ms, c 0, NMDA r 0.56 (discard test)', 'fig_pair_d10_c0_r0.56.png')
    panel(rs, 4, (-3, 120), 'G0 train every 20 ms, c 0, NMDA r 0.56', 'fig_train20_c0_r0.56.png')
    rs = [(3.0, 0.56, 0.0), (3.0, 0.56, 1.0), (3.0, 0.56, 5.0)]
    panel(rs, 0, (-3, 150), 'G0 full cue, c 3.0 nS (strong background), NMDA r 0.56: GABA off / x1 / x5', 'fig_full_c3_r0.56.png')
    raster(rs, 0, (-3, 300), 'Raster, G0 full cue at c 3.0, NMDA r 0.56', 'fig_raster_c3_r0.56.png')
    raster([(1.5, 1.0, 0.0), (1.5, 1.0, 1.0)], 3, (-3, 300), 'Raster, G0 then G1 at 10 ms, c 1.5, NMDA r 1.0', 'fig_raster_pair_c1.5_r1.png')

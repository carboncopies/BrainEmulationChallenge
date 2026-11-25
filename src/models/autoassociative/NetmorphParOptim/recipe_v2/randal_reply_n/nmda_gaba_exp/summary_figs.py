#!/usr/bin/env python3
"""summary plots from scoring.json: discard fraction vs second-cue delay (C) and train completions vs interval (C)."""
import json, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
HERE = '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/nmda_gaba_exp/'
S = json.load(open(HERE + 'scoring.json'))['C']
COL = {'0': '#8c8c8c', '1': '#1f6fb4', '2': '#2a9d5c', '5': '#c4352b'}; LAB = {'0': 'GABA off', '1': 'x1 (build)', '2': 'x2', '5': 'x5 (non-bio)'}
fig, ax = plt.subplots(2, 3, figsize=(14, 7.5), sharey='row')
for i, c in enumerate(('0', '1.5')):
    for j, r in enumerate(('0', '0.56', '1')):
        a = ax[i, j]
        for f in ('0', '1', '2', '5'):
            d = S.get('%s_%s_%s' % (c, r, f))
            if not d: continue
            xs = [];ys = []
            for dl, (n, m, tot) in d['discard'].items():
                if m: xs.append(float(dl)); ys.append(n / m)
            a.plot(xs, ys, 'o-', color=COL[f], label=LAB[f])
        a.set_xscale('log'); a.set_xticks([5, 10, 20, 50, 100]); a.set_xticklabels(['5', '10', '20', '50', '100']); a.set_ylim(-0.05, 1.05)
        a.set_title('c %s nS, NMDA r %s%s' % (c, r, ' (upper bound)' if r == '1' else ''), fontsize=10)
        if j == 0: a.set_ylabel('fraction of valid pairs where\nthe 2nd memory is discarded')
        if i == 1: a.set_xlabel('delay of 2nd cue (ms)')
ax[0, 0].legend(fontsize=8); fig.suptitle('Second-cue discard by GABA (3 E4 models, 24 ordered memory pairs per point; valid = first memory completed, no carry-over)', fontsize=11)
fig.tight_layout(rect=(0, 0, 1, 0.95)); fig.savefig(HERE + 'fig_summary_discard.png', dpi=110)
fig, ax = plt.subplots(1, 3, figsize=(14, 4), sharey=True)
for j, r in enumerate(('0', '0.56', '1')):
    a = ax[j]
    for f in ('0', '1', '2', '5'):
        d = S.get('0_%s_%s' % (r, f)); xs = []; ys = []
        for I, (mn, n) in d['trains'].items():
            if mn is not None: xs.append(float(I)); ys.append(mn)
        a.plot(xs, ys, 'o-', color=COL[f], label=LAB[f])
    a.set_xscale('log'); a.set_xticks([10, 20, 50, 100]); a.set_xticklabels(['10', '20', '50', '100']); a.set_ylim(0, 5.3); a.set_xlabel('interval between repeated full cues (ms)')
    a.set_title('c 0, NMDA r %s' % r, fontsize=10)
ax[0].set_ylabel('recalls completed out of 5'); ax[0].legend(fontsize=8)
fig.suptitle('Same memory cued 5 times in a row (10 memories x 3 models): does GABA set a recall rate?', fontsize=11); fig.tight_layout(rect=(0, 0, 1, 0.92)); fig.savefig(HERE + 'fig_summary_trains.png', dpi=110)
print('ok')

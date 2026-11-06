"""dp_nes_compare.py A B [--log NES_PROF_LOG]: compare two dp_nes_equiv.py runs (output/equiv_<tag>.npz):
force |dF| per tick, per-neuron per-tick spike counts, first differing spike; tick times for ticks 1-50 vs the
last 100 ticks. With --prof LOG: parse the PROF lines of the timing NES build (one per RunFor) into the
per-tick split at early ticks and plateau."""
import argparse
import os
import re

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def load(tag):
    return np.load(os.path.join(HERE, 'output', 'equiv_%s.npz' % tag))


def ms(x):
    return 1000.0 * float(np.mean(x))


def timing(d, name):
    n = len(d['t_total'])
    rows = []
    for lo, hi in ((0, 50), (n - 100, n)):
        rows.append('%s ticks %d-%d: sched %.1f run %.1f read %.1f total %.1f ms' % (
            name, lo + 1, hi, ms(d['t_sched'][lo:hi]), ms(d['t_run'][lo:hi]), ms(d['t_read'][lo:hi]), ms(d['t_total'][lo:hi])))
    return rows


def prof(path):
    keys = ('total_ms', 'cond_ms', 'syn_ms', 'ahp_ms', 'adp_ms', 'syn_calls', 'ahp_calls', 'adp_calls', 'syn_iters', 'ahp_iters', 'adp_iters')
    rows = []
    for line in open(path, errors='replace'):
        i = line.find('PROF ')
        if i < 0:
            continue
        rows.append([float(re.search(k + r'=([0-9.]+)', line[i:]).group(1)) for k in keys])
    a = np.array(rows)
    n = len(a)
    print('PROF lines: %d (dt %s ms)' % (n, re.search(r'Dt_ms=([0-9.]+)', open(path, errors='replace').read()[open(path, errors='replace').read().find('PROF'):]).group(1)))
    for lo, hi in ((0, 50), (n - 100, n)):
        m = a[lo:hi].mean(axis=0)
        tot = m[0]
        print('ticks %d-%d: RunFor-step total %.1f ms; conductance update %.1f (%.0f%%): synapse g_norm %.1f (%.0f%%), fAHP+sAHP %.1f (%.0f%%), ADP %.1f (%.0f%%); other stepping %.1f (%.0f%%)' % (
            lo + 1, hi, tot, m[1], 100 * m[1] / tot, m[2], 100 * m[2] / tot, m[3], 100 * m[3] / tot, m[4], 100 * m[4] / tot,
            tot - m[1], 100 * (tot - m[1]) / tot))
        print('   g_norm iterations per tick: synapse %.2fM (%.0f/call), fAHP+sAHP %.2fM (%.0f/call), ADP %.2fM (%.0f/call)' % (
            m[8] / 1e6, m[8] / m[5], m[9] / 1e6, m[9] / m[6], m[10] / 1e6, m[10] / m[7]))
    return a


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('A', nargs='?')
    ap.add_argument('B', nargs='?')
    ap.add_argument('--prof', default=None)
    a = ap.parse_args()
    if a.prof:
        prof(a.prof)
    if a.A and a.B:
        A, B = load(a.A), load(a.B)
        n = min(len(A['force']), len(B['force']))
        dF = np.abs(A['force'][:n] - B['force'][:n])
        print('ticks %d; force: max |dF| %.6g N, mean |dF| %.6g N, ticks with dF != 0: %d' % (n, dF.max(), dF.mean(), int((dF > 0).sum())))
        def counts(d):
            c = np.zeros((n, 222), dtype=int)
            m = d['sp_tick'] <= n
            np.add.at(c, (d['sp_tick'][m] - 1, d['sp_nidx'][m]), 1)
            return c
        cA, cB = counts(A), counts(B)
        diff = cA - cB
        print('output spikes: %d vs %d (diff %d); per neuron-tick count differences: %d cells, max |d| %d, ticks with any difference %d' % (
            cA.sum(), cB.sum(), cA.sum() - cB.sum(), int((diff != 0).sum()), int(np.abs(diff).max()), int((diff != 0).any(axis=1).sum())))
        la = sorted(zip(A['sp_tick'].tolist(), A['sp_nidx'].tolist(), A['sp_t'].tolist()))
        lb = sorted(zip(B['sp_tick'].tolist(), B['sp_nidx'].tolist(), B['sp_t'].tolist()))
        print('spike lists identical (tick, neuron, time): %s' % (la == lb))
        if la != lb:
            sa, sb = set(la), set(lb)
            print('first spikes only in A:', sorted(sa - sb)[:5])
            print('first spikes only in B:', sorted(sb - sa)[:5])
        for row in timing(A, a.A) + timing(B, a.B):
            print(row)
        for lo, hi in ((0, 50), (n - 100, n)):
            ra, rb = ms(A['t_total'][lo:hi]), ms(B['t_total'][lo:hi])
            print('speedup ticks %d-%d: %.2fx (total), run %.2fx' % (lo + 1, hi, ra / rb, ms(A['t_run'][lo:hi]) / ms(B['t_run'][lo:hi])))
        for name, d in ((a.A, A), (a.B, B)):
            tot = np.asarray(d['t_total'])
            plateau = tot[-100:].mean()
            print('%s projection: 30 s (3000 ticks) %.0f s, 180 s (18000 ticks) %.0f s at plateau %.3f s/tick' % (name, 3000 * plateau, 18000 * plateau, plateau))

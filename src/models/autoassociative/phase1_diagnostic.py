#!/usr/bin/env python3
# phase1_diagnostic.py
# Completion diagnostic AND scorer for the autoassociative LIFC circuit.
#
# Two uses:
#   1. CLI diagnostic:  python phase1_diagnostic.py [/tmp/vbp_<timestamp>]
#      Prints per-cycle recall and a verdict from a saved groundtruth-Vm.pkl.
#   2. Importable scorer: score_recall(t_ms, Vm_cells) -> dict
#      Used by autoassociative_lifc.py to compute its SCORE line inline. Keeping
#      ONE scorer here means the anti-saturation control below is identical in
#      the diagnostic and in the optimization objective.
#
# Does the circuit show GENUINE pattern completion (the uncued half recruited by
# a partial cue via recurrence) or a trivial saturated all-fire attractor? We
# separate them with a control: the uncued neurons must be SILENT in the
# undriven "quiet" gaps. Firing there means saturation/self-sustain, not recall.
#
# Protocol per 1600 ms cycle (50 cycles, T=80000), from the circuit script:
#   train drive : t in [0, 490]     all 8 neurons driven (8 APs @ 70 ms)
#   quiet gap 1 : t in [520, 790]   nothing driven   <- control window
#   cue drive   : t in [800, 1290]  only neurons 0-3 driven (partial cue)
#   quiet gap 2 : t in [1320, 1590] nothing driven   <- control window
# testing_pattern omits neurons 4-7, so any 4-7 firing in the cue window is
# recurrent completion.
import pickle
import sys
import glob
import os

CYCLE = 1600
THRESH = 0.0            # rising crossing of 0 mV counts one spike (peak +30, reset -55)
NUM_CUED = 4            # neurons 0..NUM_CUED-1 are cued; the rest are the recall target
CUE_WIN = (800, 1290)
GAP_WINS = [(520, 790), (1320, 1590)]   # undriven control windows (must stay silent)


def spike_count(trace, lo, hi):
    """Count rising THRESH crossings in sample range [lo, hi] (t_ms is 1 ms/sample)."""
    lo = max(0, lo)
    hi = min(hi, len(trace) - 1)
    c = 0
    prev = trace[lo]
    for v in trace[lo + 1:hi + 1]:
        if prev < THRESH <= v:
            c += 1
        prev = v
    return c


def score_recall(t_ms, Vm_cells):
    """Score autoassociative recall from Vm traces.

    Returns a dict of metrics. The optimization objective is
    ``clean_recall_fraction``: the fraction of cycles in which every uncued
    neuron fires in the cue window AND every neuron is silent in the quiet gaps.
    A saturated all-fire state fails the gap-silence control, so it cannot game
    the objective by simply firing everything.
    """
    n = len(Vm_cells)
    repeats = int(round((t_ms[-1] + 1) / CYCLE))
    uncued = range(NUM_CUED, n)

    full_recall_cycles = 0   # all uncued neurons fire in cue window (ignores gaps)
    clean_recall_cycles = 0  # full recall AND all neurons silent in the quiet gaps
    leak_spikes = 0          # total spikes by ANY neuron in the quiet gaps
    per_cycle_active = []     # how many uncued neurons fired in the cue window, per cycle

    for r in range(repeats):
        base = r * CYCLE
        cue = [spike_count(Vm_cells[c], base + CUE_WIN[0], base + CUE_WIN[1]) for c in uncued]
        gap = 0
        for c in range(n):
            for (glo, ghi) in GAP_WINS:
                gap += spike_count(Vm_cells[c], base + glo, base + ghi)
        leak_spikes += gap
        n_active = sum(1 for x in cue if x > 0)
        per_cycle_active.append(n_active)
        if n_active == len(cue):
            full_recall_cycles += 1
            if gap == 0:
                clean_recall_cycles += 1

    return {
        'num_cycles': repeats,
        'full_recall_cycles': full_recall_cycles,
        'clean_recall_cycles': clean_recall_cycles,
        'clean_recall_fraction': clean_recall_cycles / repeats if repeats else 0.0,
        'leak_spikes': leak_spikes,
        'per_cycle_active': per_cycle_active,
    }


def _load(folder):
    d = pickle.load(open(os.path.join(folder, 'groundtruth-Vm.pkl'), 'rb'))
    return d['t_ms'], d['Vm_cells']


def main():
    folder = sys.argv[1] if len(sys.argv) > 1 else sorted(glob.glob('/tmp/vbp_*'))[-1]
    t_ms, Vm = _load(folder)
    N = len(Vm)
    s = score_recall(t_ms, Vm)
    print(f"folder: {folder}")
    print(f"neurons: {N}, samples: {len(t_ms)}, cycles: {s['num_cycles']}\n")

    print("Per-cycle recall of uncued neurons (4..) in the cue window:")
    print("  cyc | " + " ".join(f"n{c}" for c in range(NUM_CUED, N)) + " | #active")
    for r in range(s['num_cycles']):
        base = r * CYCLE
        cnt = [spike_count(Vm[c], base + CUE_WIN[0], base + CUE_WIN[1]) for c in range(NUM_CUED, N)]
        print(f"  {r+1:3d} | " + " ".join(f"{c:2d}" for c in cnt) + f" | {sum(1 for x in cnt if x>0)}/{N-NUM_CUED}")

    print("\n--- verdict ---")
    print(f"  full-recall cycles (uncued all fire in cue) : {s['full_recall_cycles']}/{s['num_cycles']}")
    print(f"  clean-recall cycles (+ gaps silent)         : {s['clean_recall_cycles']}/{s['num_cycles']}")
    print(f"  clean_recall_fraction (objective)           : {s['clean_recall_fraction']:.3f}")
    print(f"  leak spikes in quiet gaps (saturation)      : {s['leak_spikes']}")
    if s['full_recall_cycles'] == 0:
        print("  => NO completion: recurrence inert, neurons echo only direct input.")
    elif s['clean_recall_cycles'] == 0:
        print("  => AMBIGUOUS/SATURATED: uncued fire but gaps not silent.")
    else:
        print("  => GENUINE completion: uncued recruited by cue, silent when undriven.")


if __name__ == '__main__':
    main()

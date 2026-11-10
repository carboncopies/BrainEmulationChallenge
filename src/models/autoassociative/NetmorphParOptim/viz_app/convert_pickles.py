#!/usr/bin/env python
"""Convert the autoassociative pipeline pickles into visualizer JSON (READ-ONLY on inputs).

Run with a Python that has numpy>=2 (the pickles were written with numpy 2):
  <venv>/bin/python -I convert_pickles.py [--src DIR] [--out data/real-autoassociative.json] [--regions 3]

Pickles used (matrices are [pre][post]):
  cell_positions.pkl                               SomaCenters, SomaRadius, SomaTypes (1 pyr, 2 int, 0 unknown)
  connectionsautoassociative_before_conductance.pkl   AMPA g_peak_sum
  connectionsautoassociative_before_numreceptors.pkl  AMPA receptor counts
  connectionsautoassociative_before_GABA_conductance.pkl  GABA g_peak_sum
NOTE: the pickles contain no brain-region labels, so regions are DERIVED here by splitting
neurons into equal-count slabs along z (a stand-in; flagged in the output 'notes').
"""
import argparse, json, os, pickle
import numpy as np

DEF_SRC = '/home/johnjose/BrainGenix/BrainEmulationChallenge/src/models/autoassociative/output'
TYPES = {1: 'pyramidal', 2: 'interneuron', 0: 'unknown'}

def load(src, name):
    with open(os.path.join(src, name), 'rb') as f:
        return pickle.load(f)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', default=DEF_SRC)
    ap.add_argument('--out', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'real-autoassociative.json'))
    ap.add_argument('--regions', type=int, default=3)
    a = ap.parse_args()

    pos = load(a.src, 'cell_positions.pkl')
    centers = np.array(pos['SomaCenters'], dtype=float)
    radius = np.array(pos['SomaRadius'], dtype=float)
    types = list(pos['SomaTypes'])
    n = len(types)
    ampa_g = np.asarray(load(a.src, 'connectionsautoassociative_before_conductance.pkl'))
    ampa_n = np.asarray(load(a.src, 'connectionsautoassociative_before_numreceptors.pkl'))
    gaba_g = np.asarray(load(a.src, 'connectionsautoassociative_before_GABA_conductance.pkl'))
    for m in (ampa_g, ampa_n, gaba_g):
        assert m.shape == (n, n), m.shape
    try:  # GABA receptor counts are not in the pickles
        gaba_n = np.asarray(load(a.src, 'connectionsautoassociative_before_GABA_numreceptors.pkl'))
    except FileNotFoundError:
        gaba_n = None

    order = np.argsort(centers[:, 2], kind='stable')
    region = [None] * n
    names = ['R%d' % (k + 1) for k in range(a.regions)]
    for rank, idx in enumerate(order):
        region[idx] = names[min(a.regions - 1, rank * a.regions // n)]

    neurons = [dict(id=i, x=centers[i, 0], y=centers[i, 1], z=centers[i, 2], r=radius[i],
                    type=TYPES.get(int(types[i]), 'unknown'), region=region[i]) for i in range(n)]
    conns = []
    for rec, G, N in (('AMPA', ampa_g, ampa_n), ('GABA', gaba_g, gaba_n)):
        for pre, post in zip(*np.nonzero(G)):
            c = dict(pre=int(pre), post=int(post), receptor=rec, g_peak_sum=float(G[pre, post]))
            if N is not None:
                c['n_receptors'] = int(N[pre, post])
            conns.append(c)
    out = dict(
        id=os.path.splitext(os.path.basename(a.out))[0],
        title='Autoassociative reservoir (real pickles, 2026-10-11)',
        kind='real',
        source=a.src,
        notes='Regions are DERIVED z-slabs (pickles have no region labels). GABA n_receptors not available in pickles. Positions in um.',
        regions=[dict(id=r, name='z-slab ' + r) for r in names],
        neurons=neurons, connections=conns)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, 'w') as f:
        json.dump(out, f, indent=1)
    print('wrote', a.out, n, 'neurons', len(conns), 'connections')

if __name__ == '__main__':
    main()

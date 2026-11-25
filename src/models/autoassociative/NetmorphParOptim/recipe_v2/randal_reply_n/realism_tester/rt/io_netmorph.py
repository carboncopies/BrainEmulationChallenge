"""Adapter: NetMorph text output folder (*_net.txt.neurons, .rootnodes, .continuationnodes, .bifurcationnodes, .growthcones, .synapses, *.nibr.clp).
Read-only. Same node logic as recipe_v2/randal_reply_n/morph_e4.py: a segment = node -> parent node (the soma -> root-node stub is not counted).
Synaptic contacts: one per AMPAR line (excitatory presynaptic cell) or GABAR line (inhibitory); NMDAR lines duplicate an AMPAR contact and are skipped."""
import glob, os, re, numpy as np
from .model import Model, AXON, DEND, UNCL

def is_netmorph_dir(path): return os.path.isdir(path) and bool(glob.glob(os.path.join(path, '*_net.txt.neurons')))

def _one(path, ext):
    g = sorted(glob.glob(os.path.join(path, '*_net.txt.' + ext)))
    return g[0] if g else None

def read_region(path):
    """Region geometry from the NetMorph command file (*.nibr.clp); only the 'disc' shape is converted to a volume."""
    g = glob.glob(os.path.join(path, '*.nibr.clp'))
    if not g: return None
    kv = {}
    for line in open(g[0]):
        line = line.strip().rstrip(';')
        if '=' in line: k, v = line.split('=', 1); kv[k.strip()] = v.strip()
    regs = [r for r in kv.get('regions', '').split(',') if r]
    if len(regs) != 1: return dict(shape='unknown', source=os.path.basename(g[0]), note='%d regions; volume not computed' % len(regs))
    r = regs[0]; shape = kv.get(r + '.shape', '')
    c = [float(kv.get(r + '.center' + a, 0.0)) for a in 'XYZ']
    if shape == 'disc':
        rad = float(kv[r + '.shape.radius']); th = float(kv[r + '.shape.thickness'])
        return dict(name=r, shape='disc', center=c, radius=rad, thickness=th, volume_um3=float(np.pi * rad ** 2 * th), source=os.path.basename(g[0]))
    return dict(name=r, shape=shape or 'unknown', center=c, source=os.path.basename(g[0]), note='shape not converted to a volume')

def load(path):
    nfile = _one(path, 'neurons'); assert nfile, 'no *_net.txt.neurons in %s' % path
    labels, types, soma, srad = [], [], [], []
    for l in open(nfile):
        if l[0] == '#' or not l.strip(): continue
        p = l.strip().split(','); labels.append(p[1]); types.append(p[2]); soma.append([float(x) for x in p[4:7]]); srad.append(float(p[7]) if len(p) > 7 else 0.0)
    idx = {lab: i for i, lab in enumerate(labels)}
    pos, par, kind, cell = {}, {}, {}, {}
    for ext in ('rootnodes', 'continuationnodes', 'bifurcationnodes', 'growthcones'):
        f = _one(path, ext)
        if f is None: continue
        for l in open(f):
            if l[0] == '#': continue
            p = l.split(','); i = int(p[0]); pos[i] = (float(p[3]), float(p[4]), float(p[5])); kind[i] = p[2]; cell[i] = p[6]
            if ext != 'rootnodes': par[i] = int(p[7])
    ids = [i for i, j in par.items() if j in pos]
    km = {'axon': AXON, 'dendrite': DEND}
    p1 = np.array([pos[i] for i in ids], float).reshape(-1, 3); p0 = np.array([pos[par[i]] for i in ids], float).reshape(-1, 3)
    seg_cell = np.array([idx[cell[i]] for i in ids], int); seg_kind = np.array([km.get(kind[i], UNCL) for i in ids], int)
    # synapses
    pre, post, xyz, sign = [], [], [], []
    f = _one(path, 'synapses'); n_lines = dict(AMPAR=0, NMDAR=0, GABAR=0, other=0)
    if f:
        for l in open(f):
            if l[0] == '#': continue
            p = l.split(','); rt = p[1]; n_lines[rt if rt in n_lines else 'other'] += 1
            if rt not in ('AMPAR', 'GABAR'): continue
            if p[10] not in idx or p[11] not in idx: continue
            pre.append(idx[p[10]]); post.append(idx[p[11]]); xyz.append([float(x) for x in p[5:8]]); sign.append(1 if rt == 'AMPAR' else -1)
    meta = dict(input_format='netmorph', path=os.path.abspath(path), files=sorted(os.path.basename(x) for x in glob.glob(os.path.join(path, '*_net.txt.*'))),
                synapse_lines=n_lines, contact_rule='one contact per AMPAR or GABAR line (NMDAR lines duplicate AMPAR contacts)',
                radii='not in NetMorph node files: volume fraction not computed (length density only)', cell_labels=labels,
                axon_dendrite_labels='from NetMorph node files (exact)')
    return Model(types, soma, srad, seg_cell, seg_kind, p0, p1, None, pre, post, np.array(xyz).reshape(-1, 3), sign, read_region(path), meta)

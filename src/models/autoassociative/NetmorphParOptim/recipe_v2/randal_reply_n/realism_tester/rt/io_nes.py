"""Adapter: NES saved model file (the converted model, e.g. .../Admonishing/Models/<name>). Read-only (numpy memmap, mode 'r').

Layout (NES Source/Core/Simulator/Structs/Simulation.cpp, Saver::Save):
  SaveLoadPrior (int32) | SaverInfo (9 x size_t: SG, Sph, Cyl, Box, Comp, Rec, Neu, Reg, Circ) | SaverGeometry[SG] (enum + pad + size_t = 16 B)
  | SphereBase[Sph] (40 B) | CylinderBase[Cyl] (64 B) | BoxBase[Box] (56 B) | BSBaseData[Comp] (32 B) | ReceptorBase[Rec] (72 B)
  | RegionBase[Reg] (size not fixed here; skipped) | uint32 flat sizes[Neu] | uint32 circuit sizes[Circ] | neuron flats | circuit flats.
Struct sizes are those of the x86-64 build used here (vtable pointer + fields); they are checked against the file (see _check_layout).
Neuron flat header: 9 x uint32 (FlatBufSize, NameSize, NameOffset, SomaN, SomaOff, DendN, DendOff, AxonN, AxonOff), offsets from the flat start.

Two properties of the converted models found while writing this adapter (2026-11-24, NES nes-linefix build):
  * every neurite cylinder is stored twice: the 'dendrite' and the 'axon' compartment lists of a neuron have equal length and identical geometry,
    and each list holds the neuron's dendrite AND axon segments; receptors reference the second ('axon') copy for both source and target.
  * so the axon/dendrite labels are lost. This adapter de-duplicates (keeps the receptor-referenced copy) and re-labels each neurite tree
    (cylinders joined end-to-start) as axon if it carries presynaptic sites of this cell, dendrite if it carries postsynaptic sites,
    'unclassified' otherwise. Labels are therefore inferred, not read; validate against NetMorph output where available.
Cell type names are not stored: a cell is 'inhibitory' if any of its outgoing receptors is GABA, 'excitatory' if it has outgoing AMPA/NMDA,
'unknown' otherwise, unless types are supplied (--cell-types)."""
import os, struct, collections, numpy as np
from .model import Model, AXON, DEND, UNCL

SG = np.dtype([('Type', '<i4'), ('pad', '<i4'), ('Idx', '<u8')])
SPH = np.dtype([('vp', '<u8'), ('ID', '<i4'), ('Shape', '<i4'), ('C', '<f4', 3), ('R', '<f4'), ('Parent', '<u8')])
CYL = np.dtype([('vp', '<u8'), ('ID', '<i4'), ('Shape', '<i4'), ('C', '<f4', 3), ('R0', '<f4'), ('P0', '<f4', 3), ('R1', '<f4'), ('P1', '<f4', 3), ('pad', '<u4')])
BOX = np.dtype([('vp', '<u8'), ('ID', '<i4'), ('Shape', '<i4'), ('C', '<f4', 3), ('D', '<f4', 3), ('Rot', '<f4', 3), ('pad', '<u4')])
COMP = np.dtype([('ID', '<i4'), ('Shape', '<i4'), ('rest', '<i4', 6)])
REC = np.dtype([('ID', '<i4'), ('Shape', '<i4'), ('Src', '<i4'), ('Dst', '<i4'), ('Erev', '<f4'), ('Rise', '<f4'), ('Decay', '<f4'), ('G', '<f4'), ('W', '<f4'), ('Delay', '<f4'),
                ('vg', 'u1'), ('pad', 'u1', 3), ('STDP', '<i4'), ('Ap', '<f4'), ('An', '<f4'), ('Tp', '<f4'), ('Tn', '<f4'), ('Sh', '<f4'), ('NT', '<i4')])
NT_NAMES = {0: 'AMPA', 1: 'GABA', 2: 'NMDA'}
assert (SPH.itemsize, CYL.itemsize, BOX.itemsize, COMP.itemsize, REC.itemsize) == (40, 64, 56, 32, 72)
KEYS = ['SG', 'Sph', 'Cyl', 'Box', 'Comp', 'Rec', 'Neu', 'Reg', 'Circ']

def header(path):
    with open(path, 'rb') as f: b = f.read(76)
    if len(b) < 76: return None
    cls = struct.unpack('<i', b[:4])[0]; h = dict(zip(KEYS, struct.unpack('<9Q', b[4:76])))
    return cls, h

def is_nes_model(path):
    if not os.path.isfile(path): return False
    try:
        cls, h = header(path)
        need = 76 + 16 * h['SG'] + 40 * h['Sph'] + 64 * h['Cyl'] + 56 * h['Box'] + 32 * h['Comp'] + 72 * h['Rec']
        return 0 <= cls < 16 and h['SG'] == h['Sph'] + h['Cyl'] + h['Box'] and 0 < need <= os.path.getsize(path)
    except Exception: return False

def _arr(mm, off, dt, n):
    return np.frombuffer(mm[off:off + dt.itemsize * n], dtype=dt), off + dt.itemsize * n

def _check_layout(sg, sph, cyl, box, comp, rec, h):
    assert np.array_equal(np.bincount(sg['Type'], minlength=4)[1:4], [h['Sph'], h['Cyl'], h['Box']]), 'geometry map does not match the counts'
    assert (sph['Shape'] == 1).all() and (cyl['Shape'] == 2).all() and (box['Shape'] == 3).all(), 'shape enums wrong: struct sizes differ in this NES build'
    assert np.array_equal(comp['ID'], np.arange(len(comp))), 'compartment IDs not sequential: BSBaseData size differs in this NES build'
    assert np.isin(rec['NT'], [0, 1, 2]).all() and (rec['Src'] >= 0).all() and (rec['Src'] < len(comp)).all(), 'receptor records invalid'

def _neuron_flats(mm, rec_end, h):
    """Region records have no fixed size here, so find the flat-size table: Neu uint32 sizes + Circ sizes followed by flats that end at EOF."""
    n, c = h['Neu'], h['Circ']; L = len(mm)
    for q in range(rec_end, min(rec_end + 65536, L - 4 * (n + c)), 4):
        sz = np.frombuffer(mm[q:q + 4 * (n + c)], dtype='<u4')
        f0 = q + 4 * (n + c)
        if f0 + 4 > L or int(sz[:n].sum()) + int(sz[n:].sum()) != L - f0: continue
        if int(np.frombuffer(mm[f0:f0 + 4], '<u4')[0]) != int(sz[0]): continue
        out = []; o = f0
        for k in range(n):
            hd = np.frombuffer(mm[o:o + 36], '<u4')
            if int(hd[0]) != int(sz[k]): break
            ids = lambda cnt, off: np.frombuffer(mm[o + off:o + off + 4 * cnt], '<i4').astype(np.int64)
            out.append(dict(name=bytes(mm[o + hd[2]:o + hd[2] + hd[1]]).split(b'\0')[0].decode('latin-1'), soma=ids(hd[3], hd[4]), dend=ids(hd[5], hd[6]), axon=ids(hd[7], hd[8])))
            o += int(hd[0])
        if len(out) == n: return out
    raise AssertionError('neuron flat table not found')

def _trees(P0, P1):
    """Union segments whose start point equals another segment's end point (exact float32 bytes). Returns tree id per segment."""
    n = len(P0); parent = np.arange(n)
    def find(i):
        while parent[i] != i: parent[i] = parent[parent[i]]; i = parent[i]
        return i
    end = {P1[i].tobytes(): i for i in range(n)}
    for i in range(n):
        j = end.get(P0[i].tobytes())
        if j is not None and j != i:
            a, b = find(i), find(j)
            if a != b: parent[a] = b
    return np.array([find(i) for i in range(n)])

def load(path, cell_types=None, one_axon_per_cell=True):
    cls, h = header(path); mm = np.memmap(path, dtype='u1', mode='r'); o = 76
    sg, o = _arr(mm, o, SG, h['SG']); sph, o = _arr(mm, o, SPH, h['Sph']); cyl, o = _arr(mm, o, CYL, h['Cyl']); box, o = _arr(mm, o, BOX, h['Box'])
    comp, o = _arr(mm, o, COMP, h['Comp']); rec, o = _arr(mm, o, REC, h['Rec'])
    _check_layout(sg, sph, cyl, box, comp, rec, h)
    nl = _neuron_flats(mm, o, h); N = len(nl)
    c2n = np.full(h['Comp'], -1, np.int64)
    for k, nr in enumerate(nl):
        for a in ('soma', 'dend', 'axon'): c2n[nr[a]] = k
    def geo(cids, kind):
        g = sg[comp['Shape'][cids]]; assert (g['Type'] == kind).all(); return g['Idx'].astype(np.int64)
    soma = np.array([sph['C'][geo(nr['soma'][:1], 1)][0] for nr in nl], float); soma_r = np.array([sph['R'][geo(nr['soma'][:1], 1)][0] for nr in nl], float)
    # duplicated-geometry detection per neuron
    dup = [len(nr['dend']) == len(nr['axon']) and len(nr['dend']) > 0 and np.allclose(cyl['P1'][geo(nr['dend'], 2)], cyl['P1'][geo(nr['axon'], 2)]) for nr in nl]
    mode = 'duplicated' if all(dup) else ('labelled' if not any(dup) else 'mixed')
    seg_cid = []; seg_cell = []; seg_kind = []
    for k, nr in enumerate(nl):
        if dup[k]: cids = nr['axon']; seg_cid.append(cids); seg_cell.append(np.full(len(cids), k)); seg_kind.append(np.full(len(cids), UNCL))
        else:
            for lst, kd in (('dend', DEND), ('axon', AXON)): seg_cid.append(nr[lst]); seg_cell.append(np.full(len(nr[lst]), k)); seg_kind.append(np.full(len(nr[lst]), kd))
    seg_cid = np.concatenate(seg_cid); seg_cell = np.concatenate(seg_cell); seg_kind = np.concatenate(seg_kind)
    ci = geo(seg_cid, 2); P0 = cyl['P0'][ci]; P1 = cyl['P1'][ci]; R = (cyl['R0'][ci] + cyl['R1'][ci]) / 2
    # synaptic contacts: AMPA (0) or GABA (1) receptors; NMDA (2) duplicates an AMPA contact at the same site
    keep = rec['NT'] != 2
    pre = c2n[rec['Src'][keep]]; post = c2n[rec['Dst'][keep]]; nt = rec['NT'][keep]
    sxyz = box['C'][sg['Idx'][rec['Shape'][keep]].astype(np.int64)] if h['Box'] else np.zeros((keep.sum(), 3))
    assert (pre >= 0).all() and (post >= 0).all()
    sign = np.where(nt == 1, -1, 1)
    # re-label trees in duplicated mode
    relabel = None
    if mode != 'labelled':
        pos_of = {int(c): i for i, c in enumerate(seg_cid)}
        votes = collections.defaultdict(lambda: [0, 0])
        tree = np.arange(len(seg_cid), dtype=np.int64)
        for k in range(N):
            m = np.where(seg_cell == k)[0]
            if not len(m) or seg_kind[m[0]] != UNCL: continue
            t = _trees(P0[m], P1[m]); tree[m] = m[t]
        for s, d in zip(rec['Src'][keep], rec['Dst'][keep]):
            i = pos_of.get(int(s)); j = pos_of.get(int(d))
            if i is not None and seg_kind[i] == UNCL: votes[tree[i]][0] += 1
            if j is not None and seg_kind[j] == UNCL: votes[tree[j]][1] += 1
        conflict = 0
        for k in range(N):
            m = np.where((seg_cell == k) & (seg_kind == UNCL))[0]
            for t in np.unique(tree[m]):
                a, d = votes.get(t, [0, 0]); conflict += int(a > 0 and d > 0)
                lab = AXON if a > d else (DEND if d > a else UNCL)
                seg_kind[m[tree[m] == t]] = lab
        n_assumed = 0
        if one_axon_per_cell:   # NetMorph grows one axon per cell: once a cell's axon tree is known, its synapse-free trees are dendrites
            for k in range(N):
                m = np.where(seg_cell == k)[0]
                if (seg_kind[m] == AXON).any():
                    u = m[seg_kind[m] == UNCL]; n_assumed += len(np.unique(tree[u])); seg_kind[u] = DEND
        L = np.linalg.norm(P1 - P0, axis=1)
        relabel = dict(one_axon_per_cell_rule=one_axon_per_cell, trees_set_to_dendrite_by_rule=n_assumed, n_trees=int(sum(len(np.unique(tree[seg_cell == k])) for k in range(N) if dup[k])), trees_with_both_pre_and_post_sites=conflict,
                       unclassified_length_frac=float(L[seg_kind == UNCL].sum() / max(L.sum(), 1e-9)))
    if cell_types is not None:
        types = list(cell_types); assert len(types) == N, 'cell types: %d given, %d cells' % (len(types), N); tsrc = 'supplied (--cell-types)'
    else:
        types = []; pren_all = c2n[rec['Src']]
        for k in range(N):
            out = rec['NT'][pren_all == k]
            types.append('inhibitory' if (out == 1).any() else ('excitatory' if len(out) else 'unknown'))
        tsrc = 'inferred from outgoing receptor type (GABA -> inhibitory, AMPA/NMDA -> excitatory)'
    meta = dict(input_format='nes_model', path=os.path.abspath(path), counts={k: int(v) for k, v in h.items()}, neuron_class=int(cls),
                geometry_mode=mode, n_neurite_cylinders_in_file=int(h['Cyl']), n_neurite_segments_used=int(len(seg_cid)),
                duplicated_neurite_geometry=bool(mode != 'labelled'), relabel=relabel, cell_type_source=tsrc, cell_labels=[nr['name'] for nr in nl],
                receptors=dict({NT_NAMES[t]: int((rec['NT'] == t).sum()) for t in (0, 1, 2)}), contact_rule='one contact per AMPA or GABA receptor record (NMDA records duplicate AMPA contacts)',
                radii='cylinder radii from the NES file (mean of the two end radii)',
                axon_dendrite_labels='read from compartment lists' if mode == 'labelled' else 'inferred per neurite tree from synapse roles (file stores neurites twice without axon/dendrite labels)' + ('; synapse-free trees of a cell with a known axon set to dendrite (one axon per cell)' if one_axon_per_cell else ''))
    return Model(types, soma, soma_r, seg_cell, seg_kind, P0, P1, R, pre, post, sxyz, sign, None, meta)

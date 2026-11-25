"""Common in-memory model used by every check. Adapters (io_netmorph, io_nes) fill it; nothing downstream knows the input format.

Model fields
  cell_type  : list[str], one entry per cell (type name as given by the input, e.g. 'pyramidal' or 'excitatory')
  soma       : (N, 3) float, soma centre in um
  soma_r     : (N,) float, soma radius in um
  seg_cell   : (S,) int, owning cell of every neurite segment
  seg_kind   : (S,) int, 0 = axon, 1 = dendrite, 2 = unclassified
  p0, p1     : (S, 3) float, segment end points in um
  seg_r      : (S,) float radius in um, or None when the input has no radii
  syn_pre, syn_post : (Y,) int, cells of every synaptic contact (one contact per synapse, not per receptor)
  syn_xyz    : (Y, 3) float, contact location
  syn_sign   : (Y,) int, +1 excitatory (AMPA/NMDA), -1 inhibitory (GABA), 0 unknown
  region     : dict or None, e.g. {'shape': 'disc', 'center': [x,y,z], 'radius': r, 'thickness': t, 'volume_um3': v, 'source': '...'}
  meta       : dict, provenance and notes (shown in the report)
"""
import numpy as np
AXON, DEND, UNCL = 0, 1, 2
KIND_NAMES = {AXON: 'axon', DEND: 'dendrite', UNCL: 'unclassified'}

class Model:
    def __init__(self, cell_type, soma, soma_r, seg_cell, seg_kind, p0, p1, seg_r, syn_pre, syn_post, syn_xyz, syn_sign, region=None, meta=None):
        self.cell_type = [str(t) for t in cell_type]
        self.soma = np.asarray(soma, float).reshape(-1, 3); self.soma_r = np.asarray(soma_r, float)
        self.seg_cell = np.asarray(seg_cell, int); self.seg_kind = np.asarray(seg_kind, int)
        self.p0 = np.asarray(p0, float).reshape(-1, 3); self.p1 = np.asarray(p1, float).reshape(-1, 3)
        self.seg_r = None if seg_r is None else np.asarray(seg_r, float)
        self.syn_pre = np.asarray(syn_pre, int); self.syn_post = np.asarray(syn_post, int)
        self.syn_xyz = np.asarray(syn_xyz, float).reshape(-1, 3); self.syn_sign = np.asarray(syn_sign, int)
        self.region = region; self.meta = dict(meta or {})
        self.validate()

    @property
    def n_cells(self): return len(self.cell_type)
    @property
    def types(self): return sorted(set(self.cell_type))
    def seg_len(self): return np.linalg.norm(self.p1 - self.p0, axis=1)

    def validate(self):
        N = self.n_cells; S = len(self.seg_cell); Y = len(self.syn_pre)
        assert self.soma.shape == (N, 3) and self.soma_r.shape == (N,)
        assert self.seg_kind.shape == (S,) and self.p0.shape == (S, 3) and self.p1.shape == (S, 3)
        assert self.seg_r is None or self.seg_r.shape == (S,)
        assert self.syn_post.shape == (Y,) and self.syn_xyz.shape == (Y, 3) and self.syn_sign.shape == (Y,)
        if S: assert self.seg_cell.min() >= 0 and self.seg_cell.max() < N and set(np.unique(self.seg_kind)) <= {AXON, DEND, UNCL}
        if Y: assert self.syn_pre.min() >= 0 and self.syn_pre.max() < N and self.syn_post.min() >= 0 and self.syn_post.max() < N

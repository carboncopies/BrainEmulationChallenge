"""Realism checks (Randal's list, RANDAL_SPEC.md). Every metric is a distribution over cells (or pairs) summarised by n, mean, median, sd, min, max,
p10, p90, so the report can show mean AND median. Metric ids are what profiles refer to (see profiles/README in the main README).

Definitions
  proportion.<T>                fraction of cells of type T (single value)
  cells_per_volume[.<T>]        cells per mm^3 of the model volume (region volume if known, else convex hull of somata; stated in 'volume')
  length.<K>.<T>                total neurite length per cell, K = axon | dendrite (sum of segment lengths, all branches), um
  reach_max.<K>.<T>             spherical range per cell: largest distance from the soma centre to any point of the arbor, um
  reach_mean.<K>.<T>            length-weighted mean distance of the arbor from the soma centre, um
  targets.<T>[.to.<U>]          distinct postsynaptic cells per cell (autapses excluded) [of type U]
  sources.<T>[.from.<U>]        distinct presynaptic cells per cell [of type U]
  conn_prob.<T>.to.<U>          connected ordered pairs / possible ordered pairs (no self pairs), single value
  syn_axon.<T>[.to.<U>]         synaptic contacts made by the cell's axon (outgoing) [onto type U]
  syn_dendrite.<T>[.from.<U>]   synaptic contacts received by the cell (incoming) [from type U]
  syn_per_pair.<T>.to.<U>       contacts per connected ordered pair (distribution over pairs)
  autapses.<T>                  contacts of a cell onto itself
"""
import numpy as np
from .model import AXON, DEND, UNCL, KIND_NAMES

def summ(v):
    v = np.asarray(v, float)
    if v.size == 0: return dict(n=0, mean=None, median=None, sd=None, min=None, max=None, p10=None, p90=None)
    return dict(n=int(v.size), mean=float(v.mean()), median=float(np.median(v)), sd=float(v.std(ddof=1)) if v.size > 1 else 0.0, min=float(v.min()), max=float(v.max()),
                p10=float(np.percentile(v, 10)), p90=float(np.percentile(v, 90)))

def single(x, note=None):
    d = dict(n=1, mean=float(x), median=float(x), sd=None, min=float(x), max=float(x), p10=None, p90=None)
    if note: d['note'] = note
    return d

def model_volume(m):
    if m.region and m.region.get('volume_um3'):
        return float(m.region['volume_um3']), 'region %s (%s, from %s)' % (m.region.get('name', ''), m.region.get('shape'), m.region.get('source'))
    try:
        from scipy.spatial import ConvexHull
        return float(ConvexHull(m.soma).volume), 'convex hull of soma centres (no region geometry in the input; underestimates the tissue volume)'
    except Exception as e:
        return None, 'volume unknown (%s)' % e

def per_cell_arbor(m):
    """returns dict kind -> dict(length, reach_max, reach_mean) arrays over cells (0 / nan where a cell has no such neurite)."""
    L = m.seg_len(); mid = (m.p0 + m.p1) / 2; N = m.n_cells; out = {}
    d1 = np.linalg.norm(m.p1 - m.soma[m.seg_cell], axis=1); d0 = np.linalg.norm(m.p0 - m.soma[m.seg_cell], axis=1); dm = np.linalg.norm(mid - m.soma[m.seg_cell], axis=1)
    dmax = np.maximum(d0, d1)
    for k in (AXON, DEND, UNCL):
        s = m.seg_kind == k; c = m.seg_cell[s]
        length = np.bincount(c, weights=L[s], minlength=N)
        rmax = np.full(N, np.nan); np.fmax.at(rmax, c, dmax[s]) if s.any() else None
        rmean = np.where(length > 0, np.bincount(c, weights=(L * dm)[s], minlength=N) / np.where(length > 0, length, 1), np.nan)
        out[KIND_NAMES[k]] = dict(length=length, reach_max=rmax, reach_mean=rmean, has=length > 0)
    return out

def contact_matrix(m):
    N = m.n_cells; C = np.zeros((N, N), np.int64)
    np.add.at(C, (m.syn_pre, m.syn_post), 1); return C

def compute(m, volume_override=None):
    T = m.types; ct = np.array(m.cell_type); N = m.n_cells; res = {}; notes = {}
    of = {t: np.where(ct == t)[0] for t in T}
    for t in T: res['proportion.%s' % t] = single(len(of[t]) / N)
    vol, vsrc = (volume_override, 'given on the command line') if volume_override else model_volume(m)
    if vol:
        mm3 = vol * 1e-9; res['cells_per_volume'] = single(N / mm3, vsrc)
        for t in T: res['cells_per_volume.%s' % t] = single(len(of[t]) / mm3, vsrc)
    arb = per_cell_arbor(m)
    for kn, a in arb.items():
        if kn == 'unclassified' and not a['has'].any(): continue
        for t in T:
            idx = of[t]
            res['length.%s.%s' % (kn, t)] = summ(a['length'][idx])           # cells with zero length of this kind count as 0
            has = idx[a['has'][idx]]
            res['reach_max.%s.%s' % (kn, t)] = summ(a['reach_max'][has])
            res['reach_mean.%s.%s' % (kn, t)] = summ(a['reach_mean'][has])
            if len(has) < len(idx): notes['length.%s.%s' % (kn, t)] = '%d of %d cells have no %s' % (len(idx) - len(has), len(idx), kn)
    C = contact_matrix(m); auto = np.diag(C).copy(); Cn = C.copy(); np.fill_diagonal(Cn, 0); B = Cn > 0
    for t in T:
        a = of[t]
        res['targets.%s' % t] = summ(B[a].sum(1)); res['sources.%s' % t] = summ(B[:, a].sum(0))
        res['syn_axon.%s' % t] = summ(C[a].sum(1)); res['syn_dendrite.%s' % t] = summ(C[:, a].sum(0)); res['autapses.%s' % t] = summ(auto[a])
        for u in T:
            b = of[u]
            res['targets.%s.to.%s' % (t, u)] = summ(B[np.ix_(a, b)].sum(1)); res['sources.%s.from.%s' % (t, u)] = summ(B[np.ix_(b, a)].sum(0))
            res['syn_axon.%s.to.%s' % (t, u)] = summ(Cn[np.ix_(a, b)].sum(1)); res['syn_dendrite.%s.from.%s' % (t, u)] = summ(Cn[np.ix_(b, a)].sum(0))
            sub = Cn[np.ix_(a, b)]; possible = len(a) * len(b) - (len(a) if t == u else 0)
            res['conn_prob.%s.to.%s' % (t, u)] = single(float((sub > 0).sum()) / possible if possible else 0.0)
            res['syn_per_pair.%s.to.%s' % (t, u)] = summ(sub[sub > 0])
    for k, v in notes.items(): res[k]['note'] = v
    info = dict(n_cells=N, types={t: int(len(of[t])) for t in T}, volume_um3=vol, volume_source=vsrc, n_segments=int(len(m.seg_cell)),
                n_contacts=int(len(m.syn_pre)), n_autapse_contacts=int(auto.sum()), total_length_um={kn: float(a['length'].sum()) for kn, a in arb.items()})
    return res, info

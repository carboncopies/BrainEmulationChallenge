"""3D density grids and radial profiles.

Length density: every segment is cut into pieces no longer than half a voxel; each piece's length goes to the voxel of its midpoint.
Unit km/mm^3 (= um of neurite per um^3). Volume fraction (neurite volume / voxel volume, cylinder pi r^2 L) only when the input has radii.
Soma and synapse grids are counts per mm^3. Grids: (nx, ny, nz) float32, x fastest in the flattened JSON form (index = ix + nx*(iy + ny*iz)).
Radial profile: cylindrical radius r = |(x, y) - centre| in bins; 'column' = length per annulus area (um/um^2, all z);
'slab' = length per annulus volume within |z - zc| <= half thickness (km/mm^3). Ball index = slab density at r < R/3 divided by that at 2R/3 <= r < R."""
import numpy as np
from .model import AXON, DEND, UNCL, KIND_NAMES

def bounds(m, voxel, pad=1):
    pts = np.vstack([m.p0, m.p1, m.soma]) if len(m.p0) else m.soma
    lo = np.floor(pts.min(0) / voxel - pad) * voxel; hi = np.ceil(pts.max(0) / voxel + pad) * voxel
    return lo, np.maximum(1, np.round((hi - lo) / voxel).astype(int))

def pieces(p0, p1, maxlen, w=None):
    L = np.linalg.norm(p1 - p0, axis=1); n = np.maximum(1, np.ceil(L / maxlen).astype(int))
    seg = np.repeat(np.arange(len(L)), n); k = np.arange(n.sum()) - np.repeat(np.cumsum(n) - n, n)
    f = (k + 0.5) / n[seg]; mid = p0[seg] + (p1[seg] - p0[seg]) * f[:, None]
    return mid, (L / n)[seg], seg

def deposit(points, weights, lo, shape, voxel):
    g = np.zeros(shape, np.float64)
    if not len(points): return g.astype(np.float32)
    ix = np.floor((points - lo) / voxel).astype(int); ok = np.all((ix >= 0) & (ix < shape), axis=1)
    np.add.at(g, (ix[ok, 0], ix[ok, 1], ix[ok, 2]), weights[ok]); return g.astype(np.float32)

def centre_and_extent(m):
    if m.region and m.region.get('center') is not None and m.region.get('radius'):
        return np.array(m.region['center'], float), float(m.region['radius']), float(m.region.get('thickness', 0)) / 2 or None, 'region'
    c = m.soma.mean(0); r = float(np.percentile(np.hypot(*(m.soma[:, :2] - c[:2]).T), 95)); hz = float(np.ptp(m.soma[:, 2]) / 2) or None
    return c, r, hz, 'soma centroid; radius = 95th percentile soma distance'

def build(m, voxel=20.0, rbin=10.0):
    lo, shape = bounds(m, voxel); vv = voxel ** 3; ct = np.array(m.cell_type); T = m.types
    grids = {}; meta = dict(origin_um=lo.tolist(), voxel_um=voxel, shape=[int(s) for s in shape], index_order='x fastest: ix + nx*(iy + ny*iz)', units={})
    mid, pl, seg = pieces(m.p0, m.p1, voxel / 2)
    kinds = [k for k in (AXON, DEND, UNCL) if (m.seg_kind == k).any()]
    for k in kinds:
        kn = KIND_NAMES[k]
        for t in T + ['all']:
            s = (m.seg_kind[seg] == k) & ((ct[m.seg_cell[seg]] == t) if t != 'all' else True)
            g = deposit(mid[s], pl[s], lo, shape, voxel) / vv; grids['%s_length.%s' % (kn, t)] = g; meta['units']['%s_length.%s' % (kn, t)] = 'km/mm^3 (um/um^3)'
            if m.seg_r is not None:
                gv = deposit(mid[s], (np.pi * m.seg_r[seg] ** 2 * pl)[s], lo, shape, voxel) / vv
                grids['%s_volfrac.%s' % (kn, t)] = gv; meta['units']['%s_volfrac.%s' % (kn, t)] = 'neurite volume / voxel volume'
    for t in T + ['all']:
        s = (ct == t) if t != 'all' else np.ones(len(ct), bool)
        grids['soma.%s' % t] = deposit(m.soma[s], np.ones(s.sum()), lo, shape, voxel) / (vv * 1e-9); meta['units']['soma.%s' % t] = 'cells/mm^3'
    if len(m.syn_pre):
        grids['synapse.all'] = deposit(m.syn_xyz, np.ones(len(m.syn_pre)), lo, shape, voxel) / (vv * 1e-9); meta['units']['synapse.all'] = 'contacts/mm^3'
    # radial profiles
    c, R, hz, csrc = centre_and_extent(m); r = np.hypot(mid[:, 0] - c[0], mid[:, 1] - c[1]); dz = np.abs(mid[:, 2] - c[2])
    rmax = float(min(np.percentile(r, 99.5) if len(r) else R, 6 * R)); edges = np.arange(0, rmax + rbin, rbin); area = np.pi * (edges[1:] ** 2 - edges[:-1] ** 2)
    hzz = hz or 15.0; prof = dict(centre_um=c.tolist(), centre_source=csrc, R_um=R, slab_half_thickness_um=hzz, r_edges_um=edges.tolist(), series={}, ball_index={})
    for k in kinds:
        kn = KIND_NAMES[k]
        for t in T + ['all']:
            s = (m.seg_kind[seg] == k) & ((ct[m.seg_cell[seg]] == t) if t != 'all' else True)
            col = np.histogram(r[s], edges, weights=pl[s])[0] / area
            sl = np.histogram(r[s & (dz <= hzz)], edges, weights=pl[s & (dz <= hzz)])[0] / (area * 2 * hzz)
            prof['series']['%s.%s' % (kn, t)] = dict(column_um_per_um2=col.tolist(), slab_km_per_mm3=sl.tolist())
            ss = s & (dz <= hzz); inner = ss & (r < R / 3); rim = ss & (r >= 2 * R / 3) & (r < R)
            di = pl[inner].sum() / (np.pi * (R / 3) ** 2 * 2 * hzz); dr = pl[rim].sum() / (np.pi * (R ** 2 - (2 * R / 3) ** 2) * 2 * hzz)
            prof['ball_index']['%s.%s' % (kn, t)] = float(di / dr) if dr > 0 else (float('inf') if di > 0 else None)   # inf: empty rim
    # sanity: total deposited length equals total segment length inside the box
    tot = {KIND_NAMES[k]: float(m.seg_len()[m.seg_kind == k].sum()) for k in kinds}
    dep = {KIND_NAMES[k]: float(grids['%s_length.all' % KIND_NAMES[k]].sum() * vv) for k in kinds}
    meta['length_check_um'] = dict(segments=tot, deposited=dep)
    return grids, meta, prof

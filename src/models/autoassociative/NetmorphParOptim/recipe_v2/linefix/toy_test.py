"""Standalone numeric test of NetMorph's crossing-line-piece test (synapse_formation_model.cc ~200-415).
Faithful numpy port of the C++ arithmetic; compares frac_T_PQ = tx/qx (current) with tx/PQ (proposed)
against an independent ground truth (closest points between the two segments' carrier lines).
No NetMorph/NES involved."""
import numpy as np
rng = np.random.default_rng(12345)

def unit(n):
    v = rng.normal(size=(n, 3)); return v / np.linalg.norm(v, axis=1, keepdims=True)

def netmorph_test(P, Q, R, S, mfd, mode):
    q = Q - P; r = R - P; s = S - P
    qx, qy, qz = q.T; rx, ry, rz = r.T; sx, sy, sz = s.T
    PQ = np.linalg.norm(q, axis=1); l = np.sqrt(PQ**2 - qz**2)
    ry1 = (-rx*qy + ry*qx)/l
    rx2 = (rx*qx + ry*qy + rz*qz)/PQ; ry2 = ry1; CR = rx2; rz2 = (-CR*qz + PQ*rz)/l
    sx2 = (sx*qx + sy*qy + sz*qz)/PQ; CS = sx2; sy2 = (-sx*qy + sy*qx)/l; sz2 = (-CS*qz + PQ*sz)/l
    Or = ry2**2 + rz2**2; Os = sy2**2 + sz2**2
    fv = 0.5*(Or - Os)/((ry2 - sy2)**2 + (rz2 - sz2)**2) + 0.5
    fv = np.where(np.abs(fv) < 1e-10, 0, fv)
    Vy = ry2 + fv*(sy2 - ry2); Vz = rz2 + fv*(sz2 - rz2); lov = np.sqrt(Vy**2 + Vz**2)
    rx3 = CR; rz3 = (ry2*-Vz + rz2*Vy)/lov
    sx3 = CS; sz3 = (sy2*-Vz + sz2*Vy)/lov
    A = rz3*sz3 < 0
    B1 = np.where(rx3 > sx3, (rx3 > 0) & (sx3 < PQ), np.where(sx3 > rx3, (sx3 > 0) & (rx3 < PQ), False))
    ux = (CS*rz3 - CR*sz3)/(rz3 - sz3)
    B2 = (ux >= 0) & (ux <= PQ)
    fT = ux/(qx if mode == 'qx' else PQ)
    fU = (ux - rx3)/(sx3 - rx3)
    T = P + fT[:, None]*(Q - P); U = R + fU[:, None]*(S - R)
    TU = np.linalg.norm(T - U, axis=1)
    return A & B1 & B2 & (TU <= mfd), A & B1 & B2, TU, ux

def truth(P, Q, R, S):
    """Closest points of the two carrier lines; returns line distance and the two parameters."""
    d1 = Q - P; d2 = S - R; w = P - R
    a = (d1*d1).sum(1); b = (d1*d2).sum(1); c = (d2*d2).sum(1); d = (d1*w).sum(1); e = (d2*w).sum(1)
    den = a*c - b*b
    t = (b*e - c*d)/den; u = (a*e - b*d)/den
    dist = np.linalg.norm(P + t[:, None]*d1 - R - u[:, None]*d2, axis=1)
    return dist, t, u

def make(n, axdir=None, seglen=5.0, box=1.5):
    a = unit(n) if axdir is None else np.tile(np.asarray(axdir, float)/np.linalg.norm(axdir), (n, 1))
    P = np.zeros((n, 3)); Q = a*seglen
    mid = Q/2 + rng.uniform(-box, box, size=(n, 3)); b = unit(n)
    R = mid - b*seglen/2; S = mid + b*seglen/2
    return P, Q, R, S

N = 4_000_000
for mfd in (0.1, 0.15, 1.5):
    P, Q, R, S = make(N)
    dist, t, u = truth(P, Q, R, S)
    true_cross = (t >= 0) & (t <= 1) & (u >= 0) & (u <= 1)      # closest points inside both pieces
    true_acc = true_cross & (dist <= mfd)
    cosx = (Q - P)[:, 0]/np.linalg.norm(Q - P, axis=1)
    print(f"\n=== mfd {mfd}: {N} random pairs, true crossings within mfd: {true_acc.sum()}")
    for mode in ('qx', 'PQ'):
        acc, geo, TU, ux = netmorph_test(P, Q, R, S, mfd, mode)
        print(f" mode tx/{mode}: accepted {acc.sum()}  ratio to truth {acc.sum()/true_acc.sum():.3f}  "
              f"accepted&true {np.sum(acc & true_acc)}  accepted-not-true {np.sum(acc & ~true_acc)}  true-not-accepted {np.sum(true_acc & ~acc)}")
        if mode == 'PQ':
            g = geo & true_cross
            print(f"   A&B1&B2 vs true interior crossing: both {g.sum()}, code only {np.sum(geo & ~true_cross)}, truth only {np.sum(true_cross & ~geo)}")
            print(f"   max |TU - line distance| where both: {np.max(np.abs(TU[g]-dist[g])):.2e}; max |ux/PQ - t|: {np.max(np.abs(ux[g]/np.linalg.norm(Q-P,axis=1)[g]-t[g])):.2e}")
        bins = [-1, -0.9, -0.5, 0, 0.5, 0.9, 1.0]
        h_acc, _ = np.histogram(cosx[acc], bins); h_true, _ = np.histogram(cosx[true_acc], bins)
        print("   acceptance / truth by cos(axon,+x) bins", bins)
        print("   ", np.round(h_acc/np.maximum(h_true, 1), 3), " share of accepted with cos>0.9: %.1f%%" % (100*h_acc[-1]/acc.sum()),
              "(isotropic expectation 5.0%)")

print("\n=== fixed axon directions, mfd 0.1, 1e6 pairs each: acceptance relative to truth")
for name, d in [('+x', (1, 0, 0)), ('-x', (-1, 0, 0)), ('+y', (0, 1, 0)), ('+z', (0, 0.001, 1)), ('xy 45deg', (1, 1, 0)), ('xyz diag', (1, 1, 1))]:
    P, Q, R, S = make(1_000_000, axdir=d)
    dist, t, u = truth(P, Q, R, S); ta = (t >= 0) & (t <= 1) & (u >= 0) & (u <= 1) & (dist <= 0.1)
    out = [netmorph_test(P, Q, R, S, 0.1, m)[0].sum()/ta.sum() for m in ('qx', 'PQ')]
    print(f" axon along {name:9s}: tx/qx {out[0]:.3f}   tx/PQ {out[1]:.3f}   (n true {ta.sum()})")

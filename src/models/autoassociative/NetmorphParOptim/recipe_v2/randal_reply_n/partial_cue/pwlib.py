"""arm matrices for addendum C (shared by run_pw.py and analyze_pw.py)."""
import sys
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/fresh_learn')
import numpy as np, fllib as FL
def arm_matrix(net, A, arm):
    if arm == 'LH': return FL.build_F(net, [A], 3.0)
    if arm == 'H2': return FL.build_F(net, [A], 2.0)
    fac = {'W70': 0.7, 'W50': 0.5}[arm]
    X = net.x0.copy(); ix = np.ix_(A, A)
    X[ix] = np.where(net.pos[ix], np.maximum(net.x0[ix], fac * net.U[ix]), X[ix])
    Hv = FL.caps(net, 3.0); info = dict(hubs=[]); tot = X.sum(0)
    for j in np.where(tot > Hv + 1e-9)[0]:
        e = X[:, j] - net.fl[:, j]; room = Hv[j] - net.fl[:, j].sum()
        if room <= 0 or e.sum() <= 0: X[:, j] = net.fl[:, j]; info['hubs'].append(int(j)); continue
        X[:, j] = net.fl[:, j] + min(1.0, room / e.sum()) * e
    return X, info

"""PREREGISTRATION_B allocation + density gate (offline). writes alloc_b.json"""
import sys, json, numpy as np
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/fresh_learn')
import fllib as F
ORDER = ['s33333','s66666','s77777','s44444','s55555','s11111','s22222','s16180','s27182','s31415']
out = {}
for key in ORDER:
    net = F.Net(key); rs = np.random.RandomState(7); res = {}
    sysm = []
    for name, k in (('A17', 17), ('A12', 12)):
        best = None
        for _ in range(300):
            A, ob = F.alloc(net, k, sysm, 0, rs)
            if A is not None and (best is None or ob > best[1]): best = (A, ob)
        if best is None: res[name] = None; break
        res[name] = best[0]; sysm.append(best[0])
    if res.get('A17') is None or res.get('A12') is None: out[key] = dict(gate=False, why='alloc failed'); print(key, 'alloc failed'); continue
    Xl, _ = F.build_F(net, sysm, None); gate = True; info = {}
    for name, A in (('A17', res['A17']), ('A12', res['A12'])):
        ins = [float(net.U[np.ix_(A, [j])].sum() - net.U[j, j]) for j in A]
        frac22 = float(np.mean([i >= 22.0 for i in ins]))
        cs = F.cues_for(A, sysm, 20, 20, 15, 15)
        f75 = F.cascade_batch(Xl, cs['c75']); mask = np.zeros(F.NP, bool); mask[A] = True; c75 = float((f75 == mask).all(1).mean())
        npairs = int((net.pos[np.ix_(A, A)]).sum()); info[name] = dict(frac_in22=frac22, c75=c75, pairs=npairs, density=round(npairs / (len(A) * (len(A) - 1)), 3))
        gate = gate and frac22 >= 0.9 and c75 >= 0.9
    out[key] = dict(gate=gate, A17=res['A17'], A12=res['A12'], info=info); print(key, gate, json.dumps(info))
json.dump(out, open('alloc_b.json', 'w'))

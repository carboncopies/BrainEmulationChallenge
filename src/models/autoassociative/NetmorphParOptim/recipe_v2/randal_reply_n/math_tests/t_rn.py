import sys, json, time, numpy as np
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/loopedwsp_scout/stability')
import rn
alloc = json.load(open('/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/partial_cue/alloc_b.json'))
A = alloc['s77777']['A17']; m = rn.member_matrices('s77777', 'W70', A, r=1.0)
rs = np.random.RandomState(0); cues = []
for q in (13, 9, 4):
    for t in range(4): cues.append([(1.0, int(i)) for i in rs.choice(17, q, replace=False)])
t0 = time.time(); R = rn.sim(m['XA'], m['XN'], cues, T=300., dt=0.1); print('time', time.time() - t0, R.shape)
spk = R.sum(0); print(spk.sum(1)[:12], R.shape)

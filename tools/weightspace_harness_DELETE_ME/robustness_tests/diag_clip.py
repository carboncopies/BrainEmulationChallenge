"""diag_clip.py: LQR whose reading of each state is clipped to +/- range_i (the spiking encoder's
input range) at kick 2x and 4x, delay 2. Tests whether encoder range saturation alone explains
the spiking failures. Diagnostic only; no spiking weights touched.  python3 diag_clip.py"""
from multiprocessing import Pool
import numpy as np
from dp_env import run, DisturbanceCfg
from dp_lqr import dlqr, StateFeedback
from dp_spiking import load_recipe

def one(a):
    k, seed = a
    rng = np.array(load_recipe()['ranges']); K = dlqr(ctrl_dt=0.01)[0]
    inner = StateFeedback(K); b = DisturbanceCfg()
    d = DisturbanceCfg(cart_impulse=b.cart_impulse * k, torque_impulse=b.torque_impulse * k)
    m = run(lambda o: inner(np.clip(o, -rng, rng)), T=180, seed=seed, ctrl_dt=0.01, delay=2, disturbance=d)
    return k, seed, m['upright_frac'], m['fall_time_s']

if __name__ == '__main__':
    with Pool(6) as p:
        for r in p.map(one, [(k, s) for k in (2.0, 4.0) for s in range(3)]):
            print('kick %gx seed %d upr %.3f fall %s' % (r[0], r[1], r[2], r[3]))

"""diag.py: trace spiking kick_2x seed 0 up to the fall: which state clipped, force saturation."""
import math, numpy as np
from dp_env import run, DisturbanceCfg
from dp_spiking import SpikingController, load_recipe
rec=load_recipe(); rng_=np.array(rec['ranges'])
b=DisturbanceCfg(); dist=DisturbanceCfg(cart_impulse=b.cart_impulse*2, torque_impulse=b.torque_impulse*2)
c=SpikingController(rec,seed=0)
m,tr=run(c,T=7.5,seed=0,ctrl_dt=0.01,delay=2,disturbance=dist,trace=True)
S,F,t=tr['s'],tr['F'],tr['t']
print('fall',m['fall_time_s'],'clip ticks',c.enc.n_clipped)
i=int(m['fall_time_s']/0.005)-1
for j in range(i-120,i,10):
    print('t=%.2f F=%6.1f '%(t[j],F[j])+' '.join('%6.2f'%(S[j,k]/rng_[k]) for k in range(6)),' (state/range)')
sat=(np.abs(F[:i])>=19.99); print('saturated frac of steps before fall',sat.mean(), 'last 1 s',sat[-200:].mean())
print('state/range max over run',np.abs(S[:i]/rng_).max(0).round(2))

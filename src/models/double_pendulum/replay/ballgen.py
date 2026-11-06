import sys;sys.path.insert(0,"/home/johnjose/BrainGenix/wt/bec-dpend/src/models/double_pendulum")
from dp_lqr import dlqr
import json,base64
from net8 import *
from ballrun import go as go6
import dp_spiking as sp_
rec=json.load(open('recipe8.json')); K=np.array(rec['K'])
N=1000
def traj(S,F):
    S=np.asarray(S);F=np.asarray(F)
    if len(S)<2*N: S=np.vstack([S,np.repeat(S[-1:],2*N-len(S),0)]);F=np.concatenate([F,np.zeros(2*N-len(F))])
    idx=np.arange(0,2*N,2)+1
    return np.round(S[idx],4).tolist(),np.round(F[idx],3).tolist()
out={'meta':dict(n_out=rec['n_out'],pops=rec['pops'],r0=rec['r0_hz'],n_in=rec['n_in'],N=N,ns=NS,mb=MB,Ls=LS,c=rec['c_N_per_spike'],K=rec['K'],ranges=rec['ranges'])}
SEED=3
def mk(S,F,fell,extra=None):
    s,f=traj(S,F);d=dict(s=s,F=f,fall_s=len(S)*0.005*1 if fell else None)
    d['fall_s']=(len(S)*0.005) if fell else None
    if extra:d.update(extra)
    return d
# env state S has 8 dims at 5ms; first 5ms substeps recorded per tick (rec_[-1]) -> per tick 10ms
def clean(S): return np.asarray(S)
# 1 no control
S,F,fell=go8(lambda o:0.0,N*.01,SEED); out['none']=mk(np.repeat(S,2,0)[:2*N],np.repeat(F,2),fell)
# 2 old LQR (6-state, ball not sensed)
K6=dlqr(ctrl_dt=0.01)[0]
S,F,fell=go8(lambda o:float(-K6@o[[0,1,2,4,5,6]]),N*.01,SEED); out['lqr6']=mk(np.repeat(S,2,0)[:2*N],np.repeat(F,2),fell)
# 3 old hardwired net (6 inputs)
r6=sp_.load_recipe(); r6['c_N_per_spike']=0.08542155329299962
c6=sp_.SpikingController(r6,seed=0)
S,F,fell=go8(lambda o:c6(o[[0,1,2,4,5,6]]),N*.01,SEED); out['net6']=mk(np.repeat(S,2,0)[:2*N],np.repeat(F,2),fell)
# 4 LQR 8
S,F,fell=go8(lambda o:float(-K@o),N*.01,SEED); out['lqr8']=mk(np.repeat(S,2,0)[:2*N],np.repeat(F,2),fell)
# 5 hardwired 8
c=Ctl8(rec,seed=0)
S,F,fell=go8(c,N*.01,SEED); d=mk(np.repeat(S,2,0)[:2*N],np.repeat(F,2),fell)
n=len(c.counts); cnt=np.zeros((N,2*rec['n_out']),np.uint8); cnt[:n]=np.array(c.counts)[:N]
rt=np.zeros((N,2*NS),int); rt[:n]=np.round(np.array(c.rates)[:N]).astype(int)
d['counts']=base64.b64encode(cnt.tobytes()).decode(); d['rates']=rt.tolist(); out['net8']=d
for k in ['none','lqr6','net6','lqr8','net8']:
    print(k,out[k]['fall_s'],np.degrees(np.abs(np.array(out[k]['s'])[:,1:4]).max(0)).round(1))
json.dump(out,open('ball.json','w'),separators=(',',':'))

import sys,json
from ball import *
import dp_spiking as sp_
from dp_lqr import dlqr, StateFeedback
rec=sp_.load_recipe(); rec['c_N_per_spike']=0.08542155329299962
def go(ctrl,T,seed,mb_,dist=True):
    env=BallEnv(None,0.005,0.01,1,DisturbanceCfg() if dist else None,None,seed,mb_=mb_)
    obs=env.reset([0,.0175,.0175,0,0,0,0,0]); S=[];F=[]
    for k in range(int(T/0.01)):
        obs,rec_=env.step(ctrl(obs))
        S.append(rec_[-1][0]);F.append(rec_[-1][1])
        if env.failed(): break
    S=np.array(S); fell=len(S)<int(T/0.01)
    th=np.degrees(np.abs(S[:,1:3]).max(0)) 
    return fell,len(S)*0.01,th,np.degrees(np.abs(S[:,3]).max()),S,np.array(F)
if __name__=='__main__':
    K=dlqr(ctrl_dt=0.01)[0]
    for mb_ in [0.01,0.05,0.1,0.2]:
        for name in ['lqr','net']:
            res=[]
            for seed in range(3):
                c=StateFeedback(K) if name=='lqr' else sp_.SpikingController(rec,seed=seed)
                f,t,th,ph,_,_=go(c,20,seed,mb_)
                res.append((f,round(t,1),th.round(1).tolist(),round(ph)))
            print(mb_,name,res,flush=True)

import sys, json, base64, math, numpy as np
sys.path.insert(0,'/home/johnjose/BrainGenix/wt/bec-dpend/src/models/double_pendulum')
from dp_env import run, DisturbanceCfg
from dp_lqr import dlqr, StateFeedback, ZeroForce
import dp_spiking as sp
rec = sp.load_recipe()
rec['c_N_per_spike']=0.08542155329299962
N=1000  # ticks of 10 ms = 10 s

class Rec(sp.SpikingController):
    def __init__(s,*a,**k):
        super().__init__(*a,**k); s.counts=[]; s.rates=[]
        orig=s.net.run_window
        def rw(spk):
            # replicate run_window but keep per-neuron counts
            net=s.net; P=sp.NEURON
            arr=np.concatenate([net.prev[:,None],spk[:,:-1].astype(np.float32)],axis=1)
            drive=net.W@arr; net.prev=spk[:,-1].astype(np.float32)
            c=np.zeros(2*net.n_out); e1=P['dt_ms']/P['C_pF']
            for t in range(spk.shape[1]):
                net.g=net.a_syn*net.g+drive[:,t]; gt=net.gl+net.g
                Vi=(net.gl*P['EL']+net.g*P['Ee'])/gt
                net.V=Vi+(net.V-Vi)*np.exp(-gt*e1)
                inref=net.ref>0; net.ref[inref]-=1; net.V[inref]=P['Vreset']
                f=(net.V>=P['Vth'])&~inref
                net.V[f]=P['Vreset']; net.ref[f]=net.ref_steps-1; c+=f
            s.counts.append(c.astype(np.uint8))
            return c[:net.n_out].sum(), c[net.n_out:].sum()
        s.net.run_window=rw
    def __call__(s,obs):
        s.rates.append(s.enc.rates(obs,clip=False)); return super().__call__(obs)

def pack(a): return base64.b64encode(np.asarray(a,np.uint8).tobytes()).decode()
def traj(S,F):
    S=np.asarray(S); idx=np.arange(1,2*N+1,2)-1  # state each 10 ms
    return dict(s=np.round(S[idx],4).tolist(), F=np.round(np.asarray(F)[idx],3).tolist())
out={'meta':dict(n_out=rec['n_out'],pops=rec['pops'],ranges=rec['ranges'],r0=rec['r0_hz'],n_in=rec['n_in'],N=N)}
dist=DisturbanceCfg()
# 1 spiking stand-in
c=Rec(rec,seed=0)
m,t=run(c,T=N*0.01,seed=3,ctrl_dt=0.01,delay=1,disturbance=dist,trace=True)
print('spiking',m['upright_frac'],m['rms_th1_deg'],m['fall_time_s'])
r=dict(traj(t['s'],t['F'])); r['counts']=pack(np.array(c.counts)[:N]); r['rates']=np.round(np.array(c.rates)[:N],0).astype(int).tolist(); r['ncount']=len(c.counts)
out['spiking']=r
# 2 LQR
K=dlqr(ctrl_dt=0.01)[0]
m,t=run(StateFeedback(K),T=N*0.01,seed=3,ctrl_dt=0.01,delay=1,disturbance=dist,trace=True); print('lqr',m['upright_frac'])
out['lqr']=traj(t['s'],t['F'])
# 3 no control
m,t=run(ZeroForce(),T=N*0.01,seed=3,ctrl_dt=0.01,delay=1,disturbance=dist,trace=True); print('zero',m['fall_time_s'])
S=t['s']; n=len(S)//2; 
z=traj(np.vstack([S,np.repeat(S[-1:],2*N-len(S),0)]) if len(S)<2*N else S, np.concatenate([t['F'],np.zeros(max(0,2*N-len(S)))]))
z['fall_s']=m['fall_time_s']; out['none']=z
# 4 NES real states 60-70 s, circuit from stand-in
import csv
rows=list(csv.reader(open('/home/johnjose/pendulum_work/long180/run/ticks.csv')))[6000:6000+N]
st=np.array([[float(v) for v in r[2:8]] for r in rows]); F=[float(r[1]) for r in rows]
c=Rec(rec,seed=0)
for s_ in st: c(s_)
out['nes']=dict(s=np.round(st,4).tolist(),F=np.round(F,3).tolist(),counts=pack(np.array(c.counts)),rates=np.round(np.array(c.rates),0).astype(int).tolist())
json.dump(out,open('replay.json','w'),separators=(',',':'))
import os;print(os.path.getsize('replay.json'))

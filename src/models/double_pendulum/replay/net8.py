import math, json, numpy as np
from lqr8 import *
import dp_spiking as sp
NS=8; NAMES=['x','th1','th2','ph','xd','th1d','th2d','phd']
R0=150.0;WMAX=2.0;NIN=256;MARGIN=1.25;V=0.031;TW=0.010
def derive8(T=60.0):
    K=dlqr8()
    S,F,fell=go8(lambda o:float(-K@o),T,100)
    S=S[::2]; assert not fell
    # state order in env: x,t1,t2,ph,xd,w1,w2,wp == NAMES order
    peak=np.abs(S).max(0); rng_=MARGIN*peak; g=R0/rng_
    P=sp.NEURON; nu0=1000/(P['t_ref_ms']+P['dt_ms'])/2
    Gs=np.linspace(2,30,280001); Ge0=float(Gs[np.argmin(np.abs(sp.nu_meanfield(Gs)-nu0))])
    h=1e-4; Sl=float((sp.nu_meanfield(Ge0+h)-sp.nu_meanfield(Ge0-h))[0]/(2*h)); tau=sp.tau_syn_eff_ms(P)
    Kr=np.abs(K)*rng_; C=float(Kr.sum()/(2*Sl*Ge0)); share=Kr/Kr.sum()
    wk=share*Ge0/(R0*1e-3*tau); k=np.ceil(wk/WMAX-1e-9).astype(int); w=wk/k
    n_out=int(math.ceil(2*V*(C/(TW*0.25))**2)); c=C/(n_out*TW)
    pops=[]
    for i in range(NS):
        ps='pull' if K[i]>0 else 'push'; ns='push' if K[i]>0 else 'pull'
        pops.append(dict(index=i,name=NAMES[i]+'+',side=ps,k=int(k[i]),w_nS=float(w[i])))
        pops.append(dict(index=NS+i,name=NAMES[i]+'-',side=ns,k=int(k[i]),w_nS=float(w[i])))
    return dict(K=K.tolist(),ranges=rng_.tolist(),r0_hz=R0,n_in=NIN,n_out=n_out,c_N_per_spike=c,F_max=20.0,pops=pops,connect_seed=12345,peak=peak.tolist(),Ge0=Ge0)
class Enc8:
    def __init__(s,ranges,r0,n_in,seed=0):
        s.g=r0/np.asarray(ranges);s.r0=r0;s.n=n_in;rng=np.random.default_rng(seed)
        s.phase=(np.arange(n_in)[None,:]+rng.random((2*NS,1)))/n_in
    def rates(s,o):
        d=s.g*np.asarray(o);return np.clip(np.concatenate([s.r0+d,s.r0-d]),0,2*s.r0)
    def spikes(s,o,steps=10):
        r=s.rates(o);inc=(r*1e-3)[:,None];out=np.zeros((2*NS,s.n,steps),bool)
        for t in range(steps):
            s.phase+=inc;f=s.phase>=1;out[:,:,t]=f;s.phase-=f
        return out.reshape(2*NS*s.n,steps),r
class Net8(sp.SpikingNet):
    def __init__(s,rec,seed=0):
        n_in,n_out=rec['n_in'],rec['n_out'];s.rec=rec;s.n_in,s.n_out=n_in,n_out
        rng=np.random.default_rng(rec['connect_seed']);W=np.zeros((2*n_out,2*NS*n_in),np.float32)
        for p in rec['pops']:
            row0=0 if p['side']=='push' else n_out;perm=rng.permutation(n_in)
            for j in range(n_out):
                pre=perm[(j*p['k']+np.arange(p['k']))%n_in];W[row0+j,p['index']*n_in+pre]=p['w_nS']
        s.W=W;P=sp.NEURON;s.a_syn=float(np.exp(-P['dt_ms']/P['tau_syn_ms']));s.gl=sp.gL_nS(P)
        s.ref_steps=int(round(P['t_ref_ms']/P['dt_ms']));s.rng=np.random.default_rng(seed+1000);s.reset()
    def reset(s):
        n=2*s.n_out;s.V=s.rng.uniform(-55,-51,n);s.g=np.zeros(n);s.ref=np.zeros(n,int);s.prev=np.zeros(2*NS*s.n_in,np.float32)
    def window(s,spk):
        P=sp.NEURON;arr=np.concatenate([s.prev[:,None],spk[:,:-1].astype(np.float32)],1)
        drive=s.W@arr;s.prev=spk[:,-1].astype(np.float32);c=np.zeros(2*s.n_out);e1=P['dt_ms']/P['C_pF']
        for t in range(spk.shape[1]):
            s.g=s.a_syn*s.g+drive[:,t];gt=s.gl+s.g;Vi=(s.gl*P['EL']+s.g*P['Ee'])/gt
            s.V=Vi+(s.V-Vi)*np.exp(-gt*e1);inr=s.ref>0;s.ref[inr]-=1;s.V[inr]=P['Vreset']
            f=(s.V>=P['Vth'])&~inr;s.V[f]=P['Vreset'];s.ref[f]=s.ref_steps-1;c+=f
        return c
class Ctl8:
    def __init__(s,rec,seed=0,cscale=1.0):
        s.rec=rec;s.enc=Enc8(rec['ranges'],rec['r0_hz'],rec['n_in'],seed);s.net=Net8(rec,seed);s.cs=rec['c_N_per_spike']*cscale
        s.counts=[];s.rates=[]
    def __call__(s,o):
        spk,r=s.enc.spikes(o);c=s.net.window(spk);s.counts.append(c.astype(np.uint8));s.rates.append(r)
        n=s.net.n_out;return float(np.clip(s.cs*(c[:n].sum()-c[n:].sum()),-20,20))
def gain_ratio(rec,seed=7,n_states=30):
    rs=np.random.default_rng(seed);K=np.array(rec['K']);sg=np.array(rec['peak'])/3
    ctl=Ctl8(rec,seed);want=[];got=[]
    for _ in range(n_states):
        s_=rs.normal(0,0.5*sg)
        for _ in range(8): ctl(s_)
        got.append(np.mean([ctl(s_) for _ in range(30)]));want.append(float(-K@s_))
    want,got=np.array(want),np.array(got);return float(want@got/(want@want))
if __name__=='__main__':
    rec=derive8();print({k:rec[k] for k in ['n_out','c_N_per_spike','ranges','Ge0']});print([(p['name'],p['side'],p['k'],round(p['w_nS'],3)) for p in rec['pops'][:8]])
    r=gain_ratio(rec);print('gain ratio',r)
    rec['c_N_per_spike']/=r; rec['gain_ratio_before']=r
    print('after',gain_ratio(rec,seed=8))
    json.dump(rec,open('recipe8.json','w'))

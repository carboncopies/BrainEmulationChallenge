import numpy as np, rn, sys
tag,prefix,arm,key=sys.argv[1:5]; kappa=float(sys.argv[5]); kind=sys.argv[6]
d=rn.load_run(tag,prefix); A=d['A']; M=rn.member_matrices(key,arm,A,d['r']); cl,meta=rn.events_cues(d,A)
sp={int(k):np.array(v) for k,v in d['spikes'].items()}
idx=[i for i,e in enumerate(meta) if e['kind']==kind][:6]
bins=np.arange(0,501,50)
def hist(ts): return np.histogram(ts,bins)[0]
print('stored pop spikes per 50 ms bin (members), events of kind',kind)
for i in idx:
    e=meta[i]; t=e['t']; ts=np.concatenate([sp[m][(sp[m]>=t)&(sp[m]<t+500)]-t for m in A if m in sp]); print(i,hist(ts))
R=rn.sim(M['XA'],M['XN'],cl,kappa=kappa,T=500)
print('model k=%g'%kappa)
dt=0.05
for i in idx:
    ts=np.where(R[:,i,:].any(1))[0]; t_=np.concatenate([np.full(int(R[k,i,:].sum()),k*dt) for k in ts]) if len(ts) else np.array([]); print(i,hist(t_))
# interneuron spikes in stored
ints=[c for c in sp if c>=96]
print('stored interneurons that fired:',ints)
for i in idx[:3]:
    t=meta[i]['t']; print(i,[int(((sp[c]>=t)&(sp[c]<t+450)).sum()) for c in ints])

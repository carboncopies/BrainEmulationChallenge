import numpy as np, rn
d=rn.load_run('s77777_LH_r1_f1','rawB_'); A=d['A']; M=rn.member_matrices('s77777','LH',A,1.0); cl,meta=rn.events_cues(d,A)
sel=[i for i,e in enumerate(meta) if e['kind'] in ('full','p75','p50')]
S=np.array([rn.stored_bins(d,A,i) for i in sel]); print('stored',np.median(S,0).astype(int))
for a in (1.,0.6,0.4):
  for n in (1.,0.5,0.):
    XA=M['XA']*a; XN=M['XN']*n
    R=rn.sim(XA,XN,[cl[i] for i in sel]); B=np.array([rn.pop_bins(R,j) for j in range(len(sel))])
    print('AMPAx%.1f NMDAx%.1f'%(a,n),np.median(B,0).astype(int),' complete frac',np.mean([R[:600,j,:].any(0).all() for j in range(len(sel))]))

import numpy as np, csv, collections
P='/var/lib/BrainGenix/NES/Admonishing/NetmorphOutput/00657198-0d99-4f4c-83f3-92bda8015f7a/202611142317_net.txt.'
def rows(f):
    with open(P+f) as fh:
        for ln in fh:
            if ln[0]=='#' or not ln.strip(): continue
            yield ln.rstrip('\n').split(',')
lab2i={}; ntype=[]; npos=[]
for r in rows('neurons'):
    if r[2] in('pyramidal','interneuron'):
        lab2i[r[1]]=len(ntype); ntype.append(r[2]=='interneuron'); npos.append([float(v) for v in r[4:7]])
ntype=np.array(ntype); npos=np.array(npos); cen=npos.mean(0)
print('n',len(ntype),'int',ntype.sum(),'centre',cen,'soma r max',np.hypot(*(npos[:,:2]-cen[:2]).T).max(),'z range',npos[:,2].min(),npos[:,2].max())
idx=[];xyz=[];par=[];soma=[];ax=[]
for r in rows('rootnodes'):
    idx.append(int(r[0]));xyz.append((float(r[3]),float(r[4]),float(r[5])));par.append(-1);soma.append(lab2i[r[6]]);ax.append(r[2]=='axon')
for f in ['continuationnodes','bifurcationnodes','growthcones']:
    for r in rows(f):
        idx.append(int(r[0]));xyz.append((float(r[3]),float(r[4]),float(r[5])));par.append(int(r[7]));soma.append(lab2i[r[6]]);ax.append(r[2]=='axon')
idx=np.array(idx);xyz=np.array(xyz);par=np.array(par);soma=np.array(soma);ax=np.array(ax)
print('nodes',len(idx),'unique',len(np.unique(idx)),'max idx',idx.max())
pos=np.full(idx.max()+1,-1);pos[idx]=np.arange(len(idx))
m=par>=0; ci=np.where(m)[0]; pi=pos[par[m]]
print('missing parents',(pi<0).sum(),'same soma',(soma[ci]==soma[pi]).mean())
c=xyz[ci];p=xyz[pi];L=np.linalg.norm(c-p,axis=1);cell=soma[ci];isax=ax[ci];isint=ntype[cell]
for nm,mm in [('int axon',isax&isint),('int dend',~isax&isint),('pyr axon',isax&~isint),('pyr dend',~isax&~isint)]:
    n=(48 if 'int' in nm else 96); mid=(c[mm]+p[mm])/2
    rr=np.hypot(mid[:,0]-cen[0],mid[:,1]-cen[1]); zz=mid[:,2]-cen[2]; w=L[mm]
    def wq(v,q):
        o=np.argsort(v); cw=np.cumsum(w[o])/w.sum(); return v[o][np.searchsorted(cw,q)]
    print(nm,'len/cell %.0f'%(w.sum()/n),'seg mean %.2f'%w.mean(),'r q50/90/99 %.0f %.0f %.0f'%tuple(wq(rr,q) for q in(.5,.9,.99)),'z q05/50/95 %.0f %.0f %.0f'%tuple(wq(zz,q) for q in(.05,.5,.95)))
np.savez('segs.npz',c=c,p=p,L=L,cell=cell,isax=isax,isint=isint,npos=npos,cen=cen,ntype=ntype)
seen=set(); S=[]
for r in rows('synapses'):
    k=tuple(r[2:8])+(r[10],r[11])
    if k in seen: continue
    seen.add(k); a=np.array(r[2:5],float); d=np.array(r[5:8],float)
    S.append((lab2i[r[10]],lab2i[r[11]],np.linalg.norm(a-d),a[0],a[1],a[2],float(r[12])))
S=np.array(S); np.save('syn.npy',S)
pt=ntype[S[:,0].astype(int)]; qt=ntype[S[:,1].astype(int)]
for a in (0,1):
  for b in (0,1):
    g=S[(pt==a)&(qt==b)]; pr=len(set(zip(g[:,0],g[:,1])))
    print('IP'[a],'->','IP'[b] if False else ('int' if b else 'pyr'),'pre_int' if a else 'pre_pyr','n',len(g),'pairs',pr,'dmax %.3f'%g[:,2].max(),'q10/25/50/75/90',np.round(np.quantile(g[:,2],[.1,.25,.5,.75,.9]),3))
g=S[(pt==0)&(qt==0)]
h,e=np.histogram(g[:,2],bins=np.arange(0,1.51,0.1)); print('PP dist hist 0.1 bins',h.tolist())
Ds=(0.05,0.1,0.15,0.3,0.5,1.0,1.5); cnt=[(g[:,2]<=D).sum() for D in Ds]
print('PP cum',dict(zip(Ds,cnt))); print('local exponents',np.round(np.diff(np.log(cnt))/np.diff(np.log(Ds)),2))
g=S[(pt==1)&(qt==0)]; print('I->P synapse r from centre q50/90/99',np.round(np.quantile(np.hypot(g[:,3]-cen[0],g[:,4]-cen[1]),[.5,.9,.99]),1),'z-cen q05/50/95',np.round(np.quantile(g[:,5]-cen[2],[.05,.5,.95]),1))
h,e=np.histogram(g[:,2],bins=np.arange(0,0.101,0.02)); print('IP dist hist 0.02 bins',h.tolist())

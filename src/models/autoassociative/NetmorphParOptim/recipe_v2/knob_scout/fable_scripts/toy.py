import numpy as np, sys
z=np.load('toyin.npz'); att=z['att'];attc=z['attc'];npos=z['npos'];ntype=z['ntype'];pathq=z['pathq']
I=np.where(ntype)[0]; rng=np.random.default_rng(7)
REP=6; STEP=5.0; NST=200  # 1000 um
def unit(v): return v/np.linalg.norm(v,axis=1,keepdims=True)
def deflect(u,th,rng):
    # rotate each u by polar angle th about random roll
    a=np.cross(u,rng.normal(size=u.shape)); a=unit(a); return u*np.cos(th)[:,None]+a*np.sin(th)[:,None]
def field(x,own):
    d=att[None,:,:]-x[:,None,:]; r2=(d*d).sum(2); w=1.0/(r2*np.sqrt(r2)+1e-9)
    w[attc[None,:]==own[:,None]]=0
    return (d*w[:,:,None]).sum(1)
def run(w,branch=True,vmin=0.19635,vmax=0.7854,hist=True):
    own=np.repeat(I,REP); x=npos[own].copy(); n=len(own)
    u=unit(rng.normal(size=(n,3))); h1=u.copy();h2=np.zeros_like(u);h3=np.zeros_like(u)
    X=np.zeros((NST+1,n,3)); X[0]=x; al=[]
    for s in range(NST):
        F=field(x,own); Fh=unit(F)
        hv=unit(h1+0.111*h2+0.04*h3) if hist else h1
        pred=unit(hv+w*Fh)
        u=deflect(pred,rng.uniform(vmin,vmax,n),rng)
        if branch:
            b=rng.random(n)<STEP/32.0
            if b.any():
                u[b]=deflect(u[b],np.abs(rng.normal(np.pi/4,0.25,b.sum())),rng); h2[b]=0;h3[b]=0;h1[b]=u[b]
                nb=~b; h3[nb]=h2[nb];h2[nb]=h1[nb];h1[nb]=u[nb]
            else: h3=h2;h2=h1;h1=u
        else: h3=h2;h2=h1;h1=u
        x=x+STEP*u; X[s+1]=x
        if s%10==5:
            al.append(((u*Fh).sum(1)).mean())
    return X,own,np.mean(al)
def summarize(X,own,tag):
    # sample nodes by empirical path distribution
    k=np.clip(np.round(pathq/STEP).astype(int),0,NST); pts=X[k]  # (200,n,3)
    r=np.hypot(pts[...,0],pts[...,1]); zz=pts[...,2]; ds=np.linalg.norm(pts-npos[own][None],axis=2); sr=np.hypot(npos[own][:,0],npos[own][:,1])
    tip=X[int(616/STEP)]; sl=np.linalg.norm(tip-npos[own],axis=1)
    out='%s | r(centre) q50/90/99 %.0f %.0f %.0f | z q05/95 %.0f %.0f | from own soma median by band %.0f %.0f %.0f | reach(q99 of soma dist, mean over cells) %.0f | tip straight/path %.2f | frac r>120 %.3f'%(tag,*np.quantile(r,[.5,.9,.99]),*np.quantile(zz,[.05,.95]),np.median(ds[:,sr<40]),np.median(ds[:,(sr>=40)&(sr<80)]),np.median(ds[:,sr>=80]),np.quantile(ds,.99,axis=0).mean(),sl.mean()/616,(r>120).mean())
    print(out); return pts
res={}
print('DATA    | r(centre) q50/90/99 19 33 55 | z q05/95 -13 14 | from own soma 46 64 107 | reach(max) 133 | tip straight/path 0.14')
for w in (0.9,0.45,0.2,0.1,0.05,0.02,0.0):
    X,own,al=run(w); pts=summarize(X,own,'w=%.2f align<u.F>=%.2f'%(w,al)); res[w]=pts
np.savez('toyout.npz',own=own,**{'w%.2f'%w:v for w,v in res.items()})
# field coherence: cos between field and centre direction vs r at z=0
print('field direction coherence (mean cos to centre direction; and |F| ) by r at z=0:')
for r0 in (5,10,20,30,50,80,120,160):
    th=rng.uniform(0,2*np.pi,300); x=np.c_[r0*np.cos(th),r0*np.sin(th),rng.uniform(-10,10,300)]
    F=field(x,np.full(300,-1)); c=-(F[:,:2]*x[:,:2]).sum(1)/np.linalg.norm(F,axis=1)/r0
    print(r0,'mean cos %.2f  frac cos>0.5 %.2f  |F| median %.3f  Fz/|F| mean %.2f'%(c.mean(),(c>0.5).mean(),np.median(np.linalg.norm(F,axis=1)),(F[:,2]/np.linalg.norm(F,axis=1)).mean()))

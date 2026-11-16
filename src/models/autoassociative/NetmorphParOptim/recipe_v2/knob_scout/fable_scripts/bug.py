import numpy as np
z=np.load('segs.npz'); c=z['c'];p=z['p'];L=z['L'];cell=z['cell'];isax=z['isax'];ntype=z['ntype']
S=np.load('syn.npy'); pre=S[:,0].astype(int); post=S[:,1].astype(int); rng=np.random.default_rng(1)
def seg_of(sub):
    out=[]
    for k in sub:
        i=pre[k]; m=np.where(isax&(cell==i))[0]; x=S[k,3:6]
        a=p[m]; b=c[m]; ab=b-a; t=np.clip(((x-a)*ab).sum(1)/(ab*ab).sum(1),0,1); dist=np.linalg.norm(a+ab*t[:,None]-x,axis=1)
        j=dist.argmin(); out.append((dist[j],ab[j,0]/L[m[j]],ab[j,1]/L[m[j]],ab[j,2]/L[m[j]],t[j]*L[m[j]],L[m[j]]))
    return np.array(out)
pt=ntype[pre];qt=ntype[post]
allax=isax
cx=(c[allax]-p[allax])[:,0]/L[allax]; w=L[allax]
print('ALL axon segments: length-weighted mean cos to +x %.3f, frac cos>0.9: %.3f, cos>0.96: %.3f'%((cx*w).sum()/w.sum(),w[cx>0.9].sum()/w.sum(),w[cx>0.96].sum()/w.sum()))
for nm,m,n in [('I->P (D=0.1)',(pt==1)&(qt==0),1616),('P->I (D=0.1)',(pt==0)&(qt==1),348),('P->P d<=0.1',(pt==0)&(qt==0)&(S[:,2]<=0.1),800),('P->P 1.0<d<=1.5',(pt==0)&(qt==0)&(S[:,2]>1.0),800),('P->P all',(pt==0)&(qt==0),1500)]:
    idx=np.where(m)[0]; 
    if len(idx)>n: idx=rng.choice(idx,n,replace=False)
    o=seg_of(idx); ok=o[:,0]<0.01
    cxs=o[ok,1]; ux=o[ok,4]; err=ux*np.abs(1/cxs-1)
    print(nm,'n',ok.sum(),'/',len(idx),'| cos_x: mean %.2f q10/50/90 %.2f %.2f %.2f | frac cos_x>0.9 %.2f | cos_y mean %.2f cos_z mean %.2f | ux median %.2f (seg L median %.2f) | err=ux|1/cx-1| q50/90/99 %.3f %.3f %.3f | max sqrt(d^2+err^2) %.3f'%(cxs.mean(),*np.quantile(cxs,[.1,.5,.9]),(cxs>0.9).mean(),o[ok,2].mean(),o[ok,3].mean(),np.median(ux),np.median(o[ok,5]),*np.quantile(err,[.5,.9,.99]),np.sqrt(S[idx][ok][:,2]**2+err**2).max()))
# predicted acceptance from the T-misplacement hypothesis using actual axon segment lengths and isotropic directions
Ls=rng.choice(L[isax],400000); cs=rng.uniform(-1,1,400000); ux=rng.uniform(0,1,400000)*Ls; err=ux*np.abs(1/cs-1)
for D in (0.05,0.1,0.15,0.3,0.5,1.0,1.5):
    d=rng.uniform(0,D,400000); acc=(d**2+err**2<=D**2).mean(); print('D',D,'acceptance %.4f  -> count ~ D*acc = %.5f'%(acc,D*acc))
for D,dm in ((1.5,0.1),(1.5,0.5)):
    d=rng.uniform(0,dm,400000); print('D=1.5, restricted to true d<=%.1f: acceptance %.3f'%(dm,(d**2+err**2<=D**2).mean()))

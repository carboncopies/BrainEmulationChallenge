import numpy as np, scipy.sparse as sp
z=np.load('segs.npz'); c=z['c'];p=z['p'];L=z['L'];cell=z['cell'];isax=z['isax'];isint=z['isint'];npos=z['npos'];cen=z['cen'];ntype=z['ntype']
S=np.load('syn.npy')
h=5.0; HX=300; HZ=80
nx=int(2*HX/h); nz=int(2*HZ/h); V=nx*nx*nz
def field(mask,K=4):
    # returns sparse (144 x V) length per voxel
    rows=[];cols=[];vals=[]
    for k in range(K):
        f=(k+0.5)/K; pt=p[mask]+(c[mask]-p[mask])*f-cen
        ix=np.floor((pt[:,0]+HX)/h).astype(int);iy=np.floor((pt[:,1]+HX)/h).astype(int);iz=np.floor((pt[:,2]+HZ)/h).astype(int)
        ok=(ix>=0)&(ix<nx)&(iy>=0)&(iy<nx)&(iz>=0)&(iz<nz)
        rows.append(cell[mask][ok]);cols.append((ix[ok]*nx+iy[ok])*nz+iz[ok]);vals.append(L[mask][ok]/K)
    return sp.csr_matrix((np.concatenate(vals),(np.concatenate(rows),np.concatenate(cols))),shape=(144,V))
A=field(isax); Dn=field(~isax)
I=np.where(ntype)[0]; Pq=np.where(~ntype)[0]
print('axon len in grid frac',A.sum()/L[isax].sum(),'dend in grid frac',Dn.sum()/L[~isax].sum())
pre=S[:,0].astype(int);post=S[:,1].astype(int)
def obs(a,b,dmax): 
    m=np.isin(pre,a)&np.isin(post,b)&(S[:,2]<=dmax); return m.sum()
for nm,a,b,d in [('I->P',I,Pq,0.1),('I->I',I,I,0.1),('P->I',Pq,I,0.1),('P->P d<=0.5',Pq,Pq,0.5),('P->P d<=0.1',Pq,Pq,0.1)]:
    M=(A[a]@Dn[b].T).toarray()/h**3*(np.pi/2)*d
    if nm[0]==nm[3]: np.fill_diagonal(M,0)
    o=obs(a,b,d); print(nm,'pred %.0f obs %d kappa=obs/pred %.2f'%(M.sum(),o,o/M.sum()))
    if nm=='I->P':
        Mip=M; kap=o/M.sum()
# finer voxel sensitivity central only is skipped; per-pair structure
lam=Mip*kap
print('pred targets/int (Poisson on lam) %.1f  obs %.1f ; pred syn/pair %.2f'%((1-np.exp(-lam)).sum(1).mean(),1007/48,lam.sum()/(1-np.exp(-lam)).sum()))
# total pyr dendrite density field
rho=np.asarray(Dn[Pq].sum(0)).ravel()/h**3   # um/um^3
G=rho.reshape(nx,nx,nz)
xs=(np.arange(nx)+.5)*h-HX; zs=(np.arange(nz)+.5)*h-HZ
X,Y=np.meshgrid(xs,xs,indexing='ij'); R=np.hypot(X,Y)
print('pyr dend density (um/um^3) by r band, |z|<15 and 15<|z|<40:')
for r0,r1 in [(0,20),(20,40),(40,60),(60,80),(80,100),(100,120),(120,160),(160,220)]:
    m=(R>=r0)&(R<r1)
    print(r0,r1,'%.4f %.4f'%(G[m][:,np.abs(zs)<15].mean(),G[m][:,(np.abs(zs)>=15)&(np.abs(zs)<40)].mean()))
print('max voxel density %.3f ; 99.9 pct %.3f; mean over slab r<120,|z|<15 %.4f'%(rho.max(),np.quantile(rho,.999),G[R<120][:,np.abs(zs)<15].mean()))
# density experienced by actual int axons
Aint=np.asarray(A[I].sum(0)).ravel()
print('axon-weighted pyr dend density experienced by int axons %.4f'%((Aint*rho).sum()/Aint.sum()))
print('implied from obs: %.4f'%(1616/(48*74624)/(np.pi/2*0.1)))
# density near pyramidal somata: mean rho in voxels within 15um of any pyr soma vs not
# counterfactual Gaussian soma-centred arbors
Rp=Dn[Pq]  # 96 x V per-cell length
vx=np.repeat(xs,nx*nz); vy=np.tile(np.repeat(xs,nz),nx); vz=np.tile(zs,nx*nx)
def scen(sig,sigz,La,d,centre_on='soma'):
    lam=np.zeros((48,96))
    for k,i in enumerate(I):
        cx,cy=(npos[i,0]-cen[0],npos[i,1]-cen[1]) if centre_on=='soma' else (0,0)
        w=np.exp(-((vx-cx)**2+(vy-cy)**2)/(2*sig**2)-(vz**2)/(2*sigz**2)); w/=w.sum()
        lam[k]=kap*(np.pi/2)*d*La*(Rp@w)/h**3
    t=(1-np.exp(-lam)).sum(1).mean(); return lam.sum(),t,lam.sum()/(48*t)
print('kappa',kap)
print('scenario: sigma_xy sigma_z La d -> I->P total, targets/int, syn/pair(Poisson)')
for cen_on in ('centre','soma'):
  for sig in (15,25,40,60,90):
    for (La,d) in ((45500,0.1),(45500,0.15),(74624,0.1)):
        r=scen(sig,8,La,d,cen_on); print(cen_on,sig,8,La,d,'-> %.0f %.1f %.2f'%r)
r=scen(40,25,45500,0.1,'soma'); print('soma sig40 sigz25 -> %.0f %.1f %.2f'%r)
np.save('rho.npy',G)

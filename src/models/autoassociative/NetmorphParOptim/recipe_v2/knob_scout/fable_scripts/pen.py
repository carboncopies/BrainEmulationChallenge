import numpy as np, scipy.sparse as sp
z=np.load('segs.npz'); c=z['c'];p=z['p'];L=z['L'];cell=z['cell'];isax=z['isax'];npos=z['npos'];cen=z['cen'];ntype=z['ntype']
T=np.load('toyout.npz'); own=T['own']; I=np.where(ntype)[0]; Pq=np.where(~ntype)[0]
h=5.0;HX=350;HZ=250;nx=int(2*HX/h);nz=int(2*HZ/h);V=nx*nx*nz
def vox(pt):
    ix=np.floor((pt[:,0]+HX)/h).astype(int);iy=np.floor((pt[:,1]+HX)/h).astype(int);iz=np.floor((pt[:,2]+HZ)/h).astype(int)
    ok=(ix>=0)&(ix<nx)&(iy>=0)&(iy<nx)&(iz>=0)&(iz<nz); return ok,(ix*nx+iy)*nz+iz
m=(~isax)&(~ntype[cell]); rows=[];cols=[];vals=[]
for k in range(4):
    pt=p[m]+(c[m]-p[m])*((k+.5)/4)-cen; ok,v=vox(pt); rows.append(cell[m][ok]);cols.append(v[ok]);vals.append(L[m][ok]/4)
Dn=sp.csr_matrix((np.concatenate(vals),(np.concatenate(rows),np.concatenate(cols))),shape=(144,V))[Pq]
print('pyr dend in grid frac %.2f'%(Dn.sum()/L[m].sum()))
rowmap=np.full(144,-1); rowmap[I]=np.arange(48)
base=None
print('w | rel I->P total | V1-length: I->P, targets/int, syn/pair | S1-length: I->P, targets/int, syn/pair | at D=0.15 V1: I->P, targets, syn/pair')
for w in ('0.90','0.45','0.20','0.10','0.05','0.00'):
    pts=T['w'+w]; n=pts.shape[1]; pp=pts.reshape(-1,3); oo=np.tile(own,pts.shape[0])
    ok,v=vox(pp); A=sp.csr_matrix((np.full(ok.sum(),1.0/(pts.shape[0]*6)),(rowmap[oo[ok]],v[ok])),shape=(48,V))  # each int row sums to <=1
    M=(A@Dn.T).toarray()   # mean dend density per pair /h^3 later
    if base is None: base=M.sum()
    rel=M.sum()/base
    def st(tot0): 
        lam=M/base*tot0; t=(1-np.exp(-lam)).sum(1).mean(); return lam.sum(),t,lam.sum()/(48*t)
    print(w,'| %.2f | %.0f %.1f %.2f | %.0f %.1f %.2f | %.0f %.1f %.2f'%(rel,*st(926),*st(1462),*st(926*1.94)), '| in-grid frac %.2f'%ok.mean())
# acceptance under the T-misplacement test vs mean axon segment length
rng=np.random.default_rng(3); n=600000; Ls0=rng.choice(L[isax],n); cs=rng.uniform(-1,1,n); f=rng.uniform(0,1,n)
print('acceptance of true crossings (isotropic axon segments), by D and segment-length scale:')
for sc in (1.0,0.6,0.4,0.2,0.1):
    out=[]
    for D in (0.1,0.15,1.5):
        d=rng.uniform(0,D,n); err=f*Ls0*sc*np.abs(1/cs-1); out.append((d*d+err*err<=D*D).mean())
    print('mean seg %.1f um: D=0.1 %.3f  D=0.15 %.3f  D=1.5 %.3f'%(Ls0.mean()*sc,*out))

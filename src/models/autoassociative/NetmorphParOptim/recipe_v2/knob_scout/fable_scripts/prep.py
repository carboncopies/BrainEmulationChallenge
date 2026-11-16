import numpy as np
P='/var/lib/BrainGenix/NES/Admonishing/NetmorphOutput/00657198-0d99-4f4c-83f3-92bda8015f7a/202611142317_net.txt.'
def rows(f):
    with open(P+f) as fh:
        for ln in fh:
            if ln[0]=='#' or not ln.strip(): continue
            yield ln.rstrip('\n').split(',')
lab2i={};ntype=[];npos=[]
for r in rows('neurons'):
    if r[2] in('pyramidal','interneuron'): lab2i[r[1]]=len(ntype);ntype.append(r[2]=='interneuron');npos.append([float(v) for v in r[4:7]])
ntype=np.array(ntype);npos=np.array(npos);cen=npos.mean(0)
N=1601332; xyz=np.zeros((N,3));par=np.full(N,-1);soma=np.zeros(N,int);ax=np.zeros(N,bool);kind=np.zeros(N,int)
for r in rows('rootnodes'):
    i=int(r[0]);xyz[i]=[float(r[3]),float(r[4]),float(r[5])];soma[i]=lab2i[r[6]];ax[i]=r[2]=='axon'
for kk,f in enumerate(['continuationnodes','bifurcationnodes','growthcones']):
    for r in rows(f):
        i=int(r[0]);xyz[i]=[float(r[3]),float(r[4]),float(r[5])];par[i]=int(r[7]);soma[i]=lab2i[r[6]];ax[i]=r[2]=='axon';kind[i]=kk+1
# attractor points: dendritic bifurcation nodes
m=(kind==2)&(~ax); att=xyz[m]-cen; attc=soma[m]
print('attractor pts',m.sum(),'pyr',(~ntype[attc]).sum(),'int',ntype[attc].sum())
r=np.hypot(att[:,0],att[:,1]); print('attractor r q10/50/90/99',np.round(np.quantile(r,[.1,.5,.9,.99]),0),'z q05/50/95',np.round(np.quantile(att[:,2],[.05,.5,.95]),0))
# path length from soma for int axon nodes
seglen=np.zeros(N); h=par>=0; seglen[h]=np.linalg.norm(xyz[h]-xyz[par[h]],axis=1)
path=np.full(N,-1.0); path[par<0]=0
todo=np.where(h)[0]
while len(todo):
    ok=path[par[todo]]>=0; path[todo[ok]]=path[par[todo[ok]]]+seglen[todo[ok]]; todo=todo[~ok]
ia=ax&ntype[soma]
print('int axon node path q10/25/50/75/90',np.round(np.quantile(path[ia],[.1,.25,.5,.75,.9]),0),'tips q50/90',np.round(np.quantile(path[ia&(kind==3)],[.5,.9]),0))
print('int axon bifurcations per cell',(ia&(kind==2)).sum()/48,' => bif per um of path along a root-tip path: ', )
# bifurcations along a root-to-tip path: count for sample of tips
tips=np.where(ia&(kind==3))[0][::50]; nb=[]
for t in tips:
    k=0;j=t
    while par[j]>=0:
        j=par[j]; k+=(kind[j]==2)
    nb.append(k)
print('bifurcations on root-tip path: mean %.1f; tip path mean %.0f -> one per %.0f um'%(np.mean(nb),path[tips].mean(),path[tips].mean()/np.mean(nb)))
d=xyz[ia]-cen; ds=np.linalg.norm(xyz[ia]-npos[soma[ia]],axis=1); sr=np.hypot(*(npos[soma[ia]][:,:2]-cen[:2]).T)
for a,b in ((0,40),(40,80),(80,125)):
    mm=(sr>=a)&(sr<b); print('soma band',a,b,'median node dist from centre(xy) %.0f, from own soma %.0f'%(np.median(np.hypot(d[mm,0],d[mm,1])),np.median(ds[mm])))
np.savez('toyin.npz',att=att,attc=attc,npos=npos-cen,ntype=ntype,pathq=np.quantile(path[ia],np.linspace(0.005,0.995,200)))

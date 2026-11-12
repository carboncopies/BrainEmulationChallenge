from common import *
import json,itertools
from scipy.optimize import minimize
from scipy.stats import ks_2samp,spearmanr
rng=np.random.default_rng(0)
R={};NN={};PD={}
for s in SIMS:
    R[s],NN[s]=load(s)
    for p in PATHS: PD[s,p]=pairs(R[s],NN[s],p)
out={};L=[]
def w(x=''): L.append(x)
def table(rows,hdr):
    w('| '+' | '.join(hdr)+' |');w('|'+'---|'*len(hdr))
    for r in rows: w('| '+' | '.join(str(x) for x in r)+' |')
    w()
def dev(n,mu):
    mu=np.maximum(mu,1e-12);t=np.where(n>0,n*np.log(np.where(n>0,n,1)/mu),0)
    return float(2*np.sum(t-(n-mu)))
def fit(d,n,form):
    f=(lambda d,A,l:A*np.exp(-d/l)) if form=='exp' else (lambda d,A,l:A*np.exp(-(d/l)**2))
    def nll(q):
        mu=f(d,np.exp(q[0]),np.exp(q[1]));return float(np.sum(mu-n*np.log(np.maximum(mu,1e-300))))
    best=None
    for l0 in (30,60,120):
        res=minimize(nll,[np.log(max(n.mean(),1e-3)),np.log(l0)],method='Nelder-Mead',options={'xatol':1e-6,'fatol':1e-9,'maxiter':4000})
        if best is None or res.fun<best.fun: best=res
    A,l=np.exp(best.x);return dict(A=float(A),scale=float(l),dev=dev(n,f(d,A,l)),form=form)
def predf(fp,d):
    A,l=fp['A'],fp['scale'];return A*np.exp(-d/l) if fp['form']=='exp' else A*np.exp(-(d/l)**2)
def bestfit(d,n):
    a=fit(d,n,'exp');b=fit(d,n,'gauss');return (a if a['dev']<=b['dev'] else b),a,b
BW=25
def binmodel(d,n):
    mx=d.max();nb=int(mx//BW)+1;idx=np.minimum((d//BW).astype(int),nb-1)
    m=np.array([n[idx==k].mean() if (idx==k).any() else 0 for k in range(nb)]);return m
def binpred(m,d): return m[np.minimum((d//BW).astype(int),len(m)-1)]
# K1
w('# RESULTS (offline, scope B)\n');w('## K0 loader validation\nConvention: PP = AMPA num_receptors summed over pyr->pyr ordered pairs (NMDA entries separate, excluded); PI = AMPA pyr->int; IP = GABA int->pyr; II = GABA int->int; no self pairs. Interneuron conductance = 0.98 nS * AMPA synapse count (threshold >=13.84 nS means >=15 synapses). All validation numbers from the task reproduced exactly (133: 1208/3331/543, 10 ints; 127: 92/217/33; 141: 955/2951 ->6; 145: 1399/2585 ->8; 146: 927/3575 ->5).\n')
rows=[]
for s in SIMS:
    g=0.98*NN[s]['PI'].sum(0)
    rows.append([s,SIMS[s][1],SIMS[s][2]]+[int(NN[s][p].sum()) for p in PATHS]+[int((NN[s][p]>0).sum()) for p in PATHS]+[int((g>=13.84-1e-9).sum())])
table(rows,['sim','seed','D','syn PP','syn PI','syn IP','syn II','pairs PP','pairs PI','pairs IP','pairs II','#int>=13.84nS'])
out['K0']=rows
w('## K1 distance kernel (3D soma distance, 25 um bins)\n')
F={}
for p in PATHS:
    w(f'### {p}: binned stats per sim (npairs / mean n / P(n>=1) / var-over-mean)\n')
    for s in SIMS:
        d,n,_,_=PD[s,p];nb=int(d.max()//BW)+1;idx=np.minimum((d//BW).astype(int),nb-1)
        w(f'sim {s}: '+'; '.join(f'{k*BW}-{(k+1)*BW}: {int((idx==k).sum())}/{n[idx==k].mean():.3g}/{(n[idx==k]>0).mean():.2f}/{(n[idx==k].var()/n[idx==k].mean() if n[idx==k].mean()>0 else float("nan")):.2f}' for k in range(nb) if (idx==k).any()))
    w()
rows=[]
for s in SIMS:
    for p in PATHS:
        d,n,_,_=PD[s,p];b,a,g=bestfit(d,n);F[s,p]=(b,a,g)
        rows.append([s,SIMS[s][1],SIMS[s][2],p,f"{a['A']:.4g}",f"{a['scale']:.1f}",f"{a['dev']:.0f}",f"{g['A']:.4g}",f"{g['scale']:.1f}",f"{g['dev']:.0f}",b['form']])
w('### Poisson ML fits: exp = A exp(-d/lambda), gauss = A exp(-(d/sigma)^2)\n')
table(rows,['sim','seed','D','path','A_exp','lambda','dev_exp','A_gauss','sigma','dev_gauss','better'])
out['K1_fits']=rows
w('### Kernel shape across D (seed 20240628) and across seeds at D=0.5; A ratio vs sim133\n')
rows=[]
for p in PATHS:
    for s in (127,147,133,151,134):
        a=F[s,p][1];a0=F[133,p][1];D=SIMS[s][2]
        rows.append([p,s,D,f"{a['scale']:.1f}",f"{a['A']:.4g}",f"{a['A']/a0['A']:.3f}",f"{(D/0.5)**1.6:.3f}"])
table(rows,['path','sim','D','lambda_exp','A_exp','A/A133','(D/0.5)^1.6'])
rows=[]
for p in PATHS:
    ls=[F[s,p][1]['scale'] for s in (133,141,145,146)];rows.append([p]+[f'{x:.1f}' for x in ls]+[f'{np.std(ls)/np.mean(ls):.3f}'])
table(rows,['path','lam133','lam141','lam145','lam146','CV'])
# K2
def mc(mu_pair_by_post,nb_k,draws=1000,thr=13.84):
    # mu: (npre,npost) matrix. returns mean totals and counts>=thr
    tot=[];cnt=[]
    for _ in range(draws):
        x=rng.poisson(mu_pair_by_post) if nb_k is None else rng.poisson(rng.gamma(nb_k,mu_pair_by_post/nb_k))
        tot.append(x.sum());cnt.append(int((0.98*x.sum(0)>=thr-1e-9).sum()))
    return np.mean(tot),np.mean(cnt),np.std(cnt)
def mumat(fn,s,p):
    r=R[s];a,b={'PP':(r.pyr,r.pyr),'PI':(r.pyr,r.int),'IP':(r.int,r.pyr),'II':(r.int,r.int)}[p]
    d=np.linalg.norm(r.pos[a][:,None]-r.pos[b][None],axis=2);mu=fn(d)
    if p in('PP','II'):np.fill_diagonal(mu,0)
    return mu
def overk(d,n,mu): # NB size k: var=mu+mu^2/k
    v=np.sum((n-mu)**2-mu);q=np.sum(mu**2);return (q/v if v>0 else 1e6)
def makefns(sims,p):
    d=np.concatenate([PD[s,p][0] for s in sims]);n=np.concatenate([PD[s,p][1] for s in sims])
    b,a,g=bestfit(d,n);m=binmodel(d,n)
    return b,m,(lambda D,b=b:predf(b,D)),(lambda D,m=m:binpred(m,D)),d,n
w('## K2 seed transfer (fit on 133 only)\n')
K2=[];rows=[]
fit133={p:makefns([133],p) for p in PATHS}
for p in PATHS:
    b,m,fp,fb,d,n=fit133[p]
    k=overk(d,n,fp(d));w(f'{p}: best form {b["form"]} A={b["A"]:.4g} scale={b["scale"]:.1f}; NB size k (param kernel) = {k:.3g}')
w()
def evaluate(train,test,label,rows):
    for p in PATHS:
        b,m,fp,fb,d,n=makefns(train,p);k=overk(d,n,fp(d))
        naive=np.mean([NN[t][p].sum() for t in train])
        for t in test:
            act=int(NN[t][p].sum());row=[label,t,p,act,f'{naive:.0f}']
            for nm,fn in (('param',fp),('bin',fb)):
                mu=mumat(fn,t,p);row.append(f'{mu.sum():.0f}')
            rows.append(row)
tot=[]
evaluate([133],[141,145,146],'133->',tot)
w('(a) totals: label,target,path,actual,naive(133),kernel-param,kernel-bin\n')
table(tot,['fit','target','path','actual','naive','param','bin']);out['K2_totals']=tot
rows=[]
def intpred(train,test,label,rows):
    b,m,fp,fb,d,n=makefns(train,'PI');k=overk(d,n,fp(d))
    nv=np.mean([int((0.98*NN[t]['PI'].sum(0)>=13.84-1e-9).sum()) for t in train])
    for t in test:
        act=int((0.98*NN[t]['PI'].sum(0)>=13.84-1e-9).sum());row=[label,t,act,f'{nv:.1f}']
        for fn in (fp,fb):
            mu=mumat(fn,t,'PI')
            for kk in (None,k):
                tt,c,sd=mc(mu,kk,1000);row.append(f'{c:.2f}+-{sd:.2f}')
        rows.append(row)
    return k
k=intpred([133],[141,145,146],'133->',rows)
w(f'(b) #ints>=13.84 nS from MC (1000 draws), PI NB size k={k:.3g} (fit on 133)\n')
table(rows,['fit','target','actual','naive','param-Poisson','param-NB','bin-Poisson','bin-NB']);out['K2_ints']=rows
w('Leave-one-seed-out over the four D=0.5 sims\n')
tot=[];rows=[];S4=[133,141,145,146]
for t in S4:
    tr=[x for x in S4 if x!=t];evaluate(tr,[t],f'LOSO',tot);intpred(tr,[t],'LOSO',rows)
table(tot,['fit','target','path','actual','naive(mean of 3)','param','bin']);table(rows,['fit','target','actual','naive','param-Poisson','param-NB','bin-Poisson','bin-NB'])
out['LOSO_totals']=tot;out['LOSO_ints']=rows
# K3
w('## K3 geometry vs seed spread (kernel pooled over 4 D=0.5 sims)\n')
rows=[];rows2=[]
for p in PATHS:
    b,m,fp,fb,d,n=makefns(S4,p)
    w(f'{p} pooled: {b["form"]} A={b["A"]:.4g} scale={b["scale"]:.1f}')
    cvs={}
    for s in S4:
        mu=mumat(fp,s,p);act=NN[s][p].astype(float)
        rows.append([p,s,int(act.sum()),f'{mu.sum():.0f}'])
        if p in('PP','II'):pass
        def cv(a,m_,ax):
            ra=a.sum(ax);rm=m_.sum(ax);ok=rm>0;r=ra[ok]/rm[ok];return r.std()/r.mean()
        # Poisson-expected CV
        sims=[];
        for _ in range(100):
            x=rng.poisson(mu);sims.append((cv(x,mu,1),cv(x,mu,0)))
        sm=np.mean(sims,0)
        rows2.append([p,s,f'{cv(act,mu,1):.3f}',f'{sm[0]:.3f}',f'{cv(act,mu,0):.3f}',f'{sm[1]:.3f}'])
w()
table(rows,['path','sim','actual total','kernel-pred total']);
w('Per-neuron ratio actual/predicted (CV across neurons); "pois" = CV expected from pure Poisson noise around kernel\n')
table(rows2,['path','sim','CV pre(out)','pois pre','CV post(in)','pois post']);out['K3']=[rows,rows2]
for p in PATHS:
    a=[r[2] for r in rows if r[0]==p];pr=[float(r[3]) for r in rows if r[0]==p]
    w(f'{p}: actual mean {np.mean(a):.0f} sd {np.std(a,ddof=1):.0f} (CV {np.std(a,ddof=1)/np.mean(a):.3f}); predicted mean {np.mean(pr):.0f} sd {np.std(pr,ddof=1):.0f}; corr(actual,pred)={np.corrcoef(a,pr)[0,1]:.2f}')
w()
# K4
w('## K4 soma placement\n')
rows=[]
for s in S4:
    r=R[s];p=r.pos;c=p.mean(0)[:2]
    rr=np.hypot(p[:,0],p[:,1]);fr=np.histogram((rr/124)**2,bins=np.linspace(0,1,6))[0]/len(rr)
    D_=np.linalg.norm(p[:,None]-p[None],axis=2);np.fill_diagonal(D_,1e9)
    pp=r.pos[r.pyr];ii=r.pos[r.int]
    kr=ks_2samp(np.hypot(*pp[:,:2].T)**2,np.hypot(*ii[:,:2].T)**2).pvalue;kz=ks_2samp(pp[:,2],ii[:,2]).pvalue
    rows.append([s,' / '.join(f'{x:.2f}' for x in fr),f'{p[:,2].min():.1f}..{p[:,2].max():.1f} (range {np.ptp(p[:,2]):.1f})',f'{rr.max():.1f}',f'{D_.min():.2f}',f'{kr:.2f}',f'{kz:.2f}'])
table(rows,['sim','frac in 5 equal-area annuli (expect 0.20 each)','z range','max r','min pair dist','KS p r^2 pyr vs int','KS p z pyr vs int'])
out['K4_geom']=rows
def place(n,rad,th,ms,rng,maxtry=2000):
    P_=np.zeros((0,3))
    while len(P_)<n:
        for _ in range(maxtry):
            r_=rad*np.sqrt(rng.random());a=2*np.pi*rng.random();q=np.array([r_*np.cos(a),r_*np.sin(a),th*rng.random()])
            if len(P_)==0 or np.min(np.linalg.norm(P_-q,axis=1))>=ms:break
        else: pass
        P_=np.vstack([P_,q])
    return P_
def kernel_totals(Pos,npyr,fns):
    out_={}
    pp,ii=Pos[:npyr],Pos[npyr:]
    for p,(a,b) in {'PP':(pp,pp),'PI':(pp,ii),'IP':(ii,pp),'II':(ii,ii)}.items():
        d=np.linalg.norm(a[:,None]-b[None],axis=2);mu=fns[p](d)
        if p in('PP','II'):np.fill_diagonal(mu,0)
        out_[p]=mu.sum()
    return out_
fns4={p:makefns(S4,p)[2] for p in PATHS}
sim=[kernel_totals(place(94,124,42,15,rng),67,fns4) for _ in range(200)]
rows=[]
for p in PATHS:
    x=np.array([q[p] for q in sim]);a=[int(NN[s][p].sum()) for s in S4];kp=[float(mumat(fns4[p],s,p).sum()) for s in S4]
    rows.append([p,f'{x.mean():.0f}',f'{x.std(ddof=1):.0f}',f'{np.std(x,ddof=1)/x.mean():.3f}',' / '.join(map(str,a)),f'{np.mean(a):.0f}',f'{np.std(a,ddof=1):.0f}',' / '.join(f'{v:.0f}' for v in kp)])
w('Simulated placements (200; uniform in cylinder r=124, thickness 42, rejection minsep 15), kernel-predicted totals:\n')
table(rows,['path','sim mean','sim sd','sim CV','actual 133/141/145/146','actual mean','actual sd','kernel-pred on actual pos'])
out['K4_sim']=rows
# K5
import pandas as pd
df=pd.read_excel(P+'/batchB_labels_all.xlsx')
fns127={p:makefns([127],p)[2] for p in PATHS}
G=[]
for _,r in df.iterrows():
    acc={p:[] for p in PATHS}
    for _ in range(30):
        q=kernel_totals(place(int(r.pyramidal+r.interneuron),r['shape.radius'],r['shape.thickness'],r.minneuronseparation,rng),int(r.pyramidal),fns127)
        for p in PATHS:acc[p].append(q[p])
    G.append({p:np.mean(acc[p]) for p in PATHS})
gd=pd.DataFrame(G);gd.columns=['G_'+c for c in PATHS]
gd.insert(0,'sample',df['sample'].values);gd.to_csv('geom_terms.csv',index=False)
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import PoissonRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import RepeatedKFold
from sklearn.metrics import r2_score,mean_absolute_error,mean_poisson_deviance
raw=['days','pyramidal','interneuron','minneuronseparation','shape.radius','shape.thickness','dm.weight']
Xr=df[raw].values
lab={'usable_pyr_int':'G_PI','usable_int_pyr':'G_IP','usable_int_int':'G_II','usable_conns2':'G_PP'}
w('## K5 cross-config geometry-only (batch B)\n');w('G terms in scope_offline/B/geom_terms.csv. KERN3 = Poisson GLM on log(G_path), log(dm.weight), days. For usable_conns2 (not a pathway count) G_PP is used per the spec; note label definition differs, so this is a loose test.\n')
rows=[]
for l,g in lab.items():
    y=df[l].values.astype(float);Xk=np.column_stack([np.log(gd[g].values),np.log(df['dm.weight'].values),df['days'].values])
    res={m:dict(p=np.zeros(len(y)),n=np.zeros(len(y))) for m in('RF','KERN3','mean')}
    st={m:[] for m in res}
    rk=RepeatedKFold(n_splits=5,n_repeats=10,random_state=0)
    for tr,te in rk.split(Xr):
        preds={'RF':RandomForestRegressor(500,random_state=0,n_jobs=-1).fit(Xr[tr],y[tr]).predict(Xr[te]),
         'KERN3':make_pipeline(StandardScaler(),PoissonRegressor(alpha=1e-6,max_iter=2000)).fit(Xk[tr],y[tr]).predict(Xk[te]),
         'mean':np.full(len(te),y[tr].mean())}
        for m,pr in preds.items():
            pr=np.maximum(pr,1e-6);dm=mean_poisson_deviance(y[te],pr);d0=mean_poisson_deviance(y[te],np.full(len(te),max(y[tr].mean(),1e-6)))
            sp=spearmanr(y[te],pr)[0] if np.std(pr)>0 else 0
            st[m].append([r2_score(y[te],pr),mean_absolute_error(y[te],pr),sp,1-dm/d0 if d0>0 else np.nan])
    for m in st:
        a=np.nanmean(np.array(st[m]),0);rows.append([l,m,f'{a[0]:.3f}',f'{a[1]:.3f}',f'{a[2]:.3f}',f'{a[3]:.3f}'])
table(rows,['label','model','R2','MAE','Spearman','Poisson dev explained (vs fold-mean)']);out['K5']=rows
w('Label means: '+', '.join(f'{l}={df[l].mean():.2f}' for l in lab))
open('RESULTS.md','w').write('\n'.join(L));json.dump(out,open('results.json','w'),default=str,indent=1)

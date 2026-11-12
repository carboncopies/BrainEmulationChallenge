from common import *
from multiprocessing import Pool
MODELS=['RF7','POIS7','M1','M2']
T3=['usable_int_pyr','usable_pyr_int','usable_int_int','usable_conns2']+[r for r in RAW]
df,_=load()
def one(args):
    t,n,rep=args
    rng=np.random.default_rng(1000*rep+n); perm=rng.permutation(len(df)); tr=perm[:n]; te=perm[n:]
    y=df[t].values.astype(float); out={}
    for m in MODELS:
        try:
            if y[tr].sum()==0 and m!='RF7': raise ValueError('allzero')
            p=fit_predict(m,t,tr,te,df,ntrees=100); b=fit_predict('BASE',t,tr,te,df)
            out[m]=metrics(y[te],p,b)
        except Exception as e: out[m]=None
    return (t,n,rep,out)
def agg(rs):
    S={}
    for t,n,rep,out in rs:
        for m,v in out.items():
            d=S.setdefault(t,{}).setdefault(str(n),{}).setdefault(m,dict(fail=0,R2=[],rho=[],D2=[]))
            if v is None: d['fail']+=1
            else:
                for k in ['R2','rho','D2']: d[k].append(v[k])
    for t in S:
        for n in S[t]:
            for m,d in S[t][n].items():
                for k in ['R2','rho','D2']:
                    a=np.array(d[k],float); a=a[~np.isnan(a)]
                    d[k]=dict(med=float(np.median(a)) if len(a) else None,q25=float(np.percentile(a,25)) if len(a) else None,q75=float(np.percentile(a,75)) if len(a) else None,n=len(a))
    return S
def t4():
    s=(df.pyramidal+df.interneuron).values; med=np.median(s)
    tr=np.where(s<=med)[0]; te=np.where(s>med)[0]; out={'median_size':float(med),'n_train':len(tr),'n_test':len(te),
      'wall_low':float(df.wall_s.values[tr].mean()),'wall_high':float(df.wall_s.values[te].mean()),'res':{}}
    for t in T3:
        y=df[t].values.astype(float); b=fit_predict('BASE',t,tr,te,df); out['res'][t]={'ytest_mean':float(y[te].mean()),'ytrain_mean':float(y[tr].mean())}
        for m in MODELS:
            try: out['res'][t][m]=metrics(y[te],fit_predict(m,t,tr,te,df),b)
            except Exception as e: out['res'][t][m]=None
    return out
if __name__=='__main__':
    jobs=[(t,n,r) for t in T3 for n in [5,10,20,40,80] for r in range(100)]
    with Pool(40) as p: rs=p.map(one,jobs,chunksize=20)
    json.dump(dict(t3=agg(rs),t4=t4()),open('t3_results.json','w'),default=float)

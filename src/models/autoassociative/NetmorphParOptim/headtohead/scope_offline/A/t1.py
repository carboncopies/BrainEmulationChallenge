from common import *
from sklearn.model_selection import RepeatedKFold
from multiprocessing import Pool
MODELS=['BASE','RF7','POIS7','M1','M2']
TG=LAB+RAW
df,_=load()
folds=list(RepeatedKFold(n_splits=5,n_repeats=10,random_state=0).split(df))
def top10(yt,yp):
    k=10; a=set(np.argsort(-yt,kind='stable')[:k]); b=set(np.argsort(-yp,kind='stable')[:k]); return len(a&b)/k
def run(t):
    out={}
    y=df[t].values.astype(float)
    for m in MODELS:
        if not applicable(m,t): continue
        oof=np.full((10,len(df)),np.nan); fm=[]
        for i,(tr,te) in enumerate(folds):
            try: p=fit_predict(m,t,tr,te,df)
            except Exception as e: p=np.full(len(te),np.nan)
            pb=back(p,df.iloc[te],t); base=back(fit_predict('BASE',t,tr,te,df),df.iloc[te],t)
            oof[i//5,te]=pb
            fm.append(metrics(y[te],pb,base) if not np.isnan(pb).any() else dict(R2=np.nan,MAE=np.nan,rho=np.nan,D2=np.nan))
        # pooled per repeat; base oof = fold train mean
        pooled=[];t10=[]
        baseoof=np.full((10,len(df)),np.nan)
        for i,(tr,te) in enumerate(folds): baseoof[i//5,te]=back(fit_predict('BASE',t,tr,te,df),df.iloc[te],t)[0]
        for r in range(10):
            pooled.append(metrics(y,oof[r],baseoof[r])); t10.append(top10(y,oof[r]) if np.std(oof[r])>0 else np.nan)
        res={}
        for k in ['R2','MAE','rho','D2']:
            a=np.array([x[k] for x in fm]); b=np.array([x[k] for x in pooled])
            res[k]=dict(fold_mean=float(np.nanmean(a)),fold_sd=float(np.nanstd(a)),pool_mean=float(np.nanmean(b)),pool_sd=float(np.nanstd(b)),nan_folds=int(np.isnan(a).sum()))
        res['top10']=dict(mean=float(np.nanmean(t10)),sd=float(np.nanstd(t10)))
        out[m]=res
    return t,out
if __name__=='__main__':
    with Pool(32) as p: R=dict(p.map(run,TG))
    # coefficients + bootstrap
    coefs={}; rng=np.random.default_rng(0)
    names=['intercept','log(n_pre*n_post)','log V','log dm.weight','days','log minsep']
    for t in TG:
        if isfrac(t): continue
        y=df[t].values.astype(float); X=M1X(df,t)
        c=Pois().fit(X,y).coef(); bs=[]
        for _ in range(500):
            ix=rng.integers(0,len(df),len(df))
            try: bs.append(Pois().fit(X[ix],y[ix]).coef())
            except Exception: pass
        bs=np.array(bs); coefs[t]=dict(names=names,coef=c.tolist(),boot_se=bs.std(0).tolist(),nboot=len(bs))
    # T2
    t2={}
    for t in TG:
        if isfrac(t) or t.endswith('_g'): continue
        y=df[t].values.astype(float); X=M1X(df,t); m=Pois().fit(X,y); mu=m.predict(X)
        t2[t]=dict(mean=y.mean(),var=y.var(ddof=1),R2max=1-mu.mean()/y.var(ddof=1),R2max_pearson_resid=None,
                   disp=float(((y-mu)**2/np.maximum(mu,1e-9)).sum()/(len(y)-6)),insample_R2=float(r2_score(y,mu)))
    json.dump(dict(cv=R,coefs=coefs,t2=t2),open('t1_results.json','w'),default=float)

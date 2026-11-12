from common import *
import statsmodels.api as sm
from statsmodels.discrete.discrete_model import NegativeBinomial
from sklearn.model_selection import RepeatedKFold
from multiprocessing import Pool
TG=['raw_pyr_int_n','raw_int_int_n','raw_int_pyr_n','raw_pyr_pyr_n','usable_conns2','usable_pyr_int','usable_int_int','usable_int_pyr']
df,_=load(); folds=list(RepeatedKFold(n_splits=5,n_repeats=10,random_state=0).split(df))
def nbfit(X,y,alpha_fb=None):
    mu=X.mean(0); sd=X.std(0); Z=sm.add_constant((X-mu)/sd)
    p0=Pois(alpha=1e-8).fit(X,y); st=np.append(p0.m.intercept_,p0.m.coef_)
    for meth in ['newton','bfgs','nm']:
        try:
            r=NegativeBinomial(y,Z,loglike_method='nb2').fit(start_params=np.append(st,0.5),method=meth,maxiter=500,disp=0)
            a=r.params[-1]
            if r.mle_retvals.get('converged',True) and np.isfinite(r.params).all() and 1e-6<a<1e3: return ('ok',r.params[:-1],a,mu,sd)
        except Exception: pass
    if alpha_fb is None: return None
    r=sm.GLM(y,Z,family=sm.families.NegativeBinomial(alpha=alpha_fb)).fit()
    return ('fb',r.params,alpha_fb,mu,sd)
def nbpred(f,X): return np.exp(sm.add_constant((X-f[3])/f[4],has_constant='add')@f[1])
def top10(yt,yp): return len(set(np.argsort(-yt,kind='stable')[:10])&set(np.argsort(-yp,kind='stable')[:10]))/10
def run(t):
    y=df[t].values.astype(float); X=M1X(df,t); a_full=nbfit(X,y)[2]
    oof={m:np.full((10,100),np.nan) for m in ['NB','RF7','BASE']}; fb=0; alphas=[]
    for i,(tr,te) in enumerate(folds):
        f=nbfit(X[tr],y[tr],a_full)
        if f[0]=='fb': fb+=1
        alphas.append(f[2]); oof['NB'][i//5,te]=nbpred(f,X[te])
        oof['RF7'][i//5,te]=fit_predict('RF7',t,tr,te,df); oof['BASE'][i//5,te]=y[tr].mean()
    res={'fallbacks':fb,'alpha_fold_median':float(np.median(alphas)),'oof_spearman':{}}
    pr={m:[] for m in ['NB','RF7']}
    for m in ['NB','RF7']:
        for r in range(10): pr[m].append(metrics(y,oof[m][r],oof['BASE'][r]))
        res[m]={k:[float(np.mean([x[k] for x in pr[m]])),float(np.std([x[k] for x in pr[m]]))] for k in ['rho','R2','D2','MAE']}
        res[m]['top10']=[float(np.mean([top10(y,oof[m][r]) for r in range(10)])),float(np.std([top10(y,oof[m][r]) for r in range(10)]))]
    d=np.array([a['rho']-b['rho'] for a,b in zip(pr['NB'],pr['RF7'])]); res['diff']=[float(d.mean()),float(d.min()),float(d.max())]
    # full fit coefs with SEs on raw scale
    Z=sm.add_constant(X); p0=Pois(alpha=1e-8).fit(X,y).coef()
    r=NegativeBinomial(y,Z,loglike_method='nb2').fit(start_params=np.append(p0,0.5),method='newton',maxiter=500,disp=0)
    res['full']={'alpha':float(r.params[-1]),'alpha_se':float(r.bse[-1]),'coef':r.params[:-1].tolist(),'se':r.bse[:-1].tolist(),'converged':bool(r.mle_retvals.get('converged'))}
    return t,res
if __name__=='__main__':
    with Pool(8) as p: R=dict(p.map(run,TG))
    json.dump(R,open('g1_results.json','w'),default=float,indent=1)

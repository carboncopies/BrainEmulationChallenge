import json,glob,re,warnings,numpy as np,pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import PoissonRegressor
from sklearn.metrics import r2_score,mean_absolute_error,mean_poisson_deviance
from scipy.stats import spearmanr
warnings.filterwarnings('ignore')
D='/home/johnjose/cos/netmorph_work/bec/src/models/autoassociative/NetmorphParOptim/'
F=['days','pyramidal','interneuron','minneuronseparation','shape.radius','shape.thickness','dm.weight']
LAB=['usable_conns2','usable_pyr_int','usable_int_pyr','usable_int_int','frac_int_driven','frac_pyr_inhibited','frac_pyr_inhibited_w05']
ALPHA=0.01
def load():
    df=pd.read_excel(D+'batchB_labels_all.xlsx')
    rows=[]
    for f in glob.glob(D+'batchB/out*-rawcounts.json'):
        if '/vout' in f: continue
        n=int(re.search(r'out(\d+)-',f).group(1)); j=json.load(open(f))['0']
        c=j['rawcounts']['classes']
        def s(keys,fld): return sum(c[k][fld] for k in keys if k in c)
        r={'sample':n+1,'_pars':j['pars'],'_lab':j['labels'],
         'raw_pyr_int_n':s(['pyr->int:1'],'connections'),'raw_pyr_int_g':s(['pyr->int:1'],'g_peak_sum_nS'),
         'raw_int_pyr_n':s(['int->pyr:2'],'connections'),'raw_int_pyr_g':s(['int->pyr:2'],'g_peak_sum_nS'),
         'raw_int_int_n':s(['int->int:2'],'connections'),'raw_int_int_g':s(['int->int:2'],'g_peak_sum_nS'),
         'raw_pyr_pyr_n':s(['pyr->pyr:1','pyr->pyr:3'],'connections'),'raw_pyr_pyr_g':s(['pyr->pyr:1','pyr->pyr:3'],'g_peak_sum_nS')}
        rows.append(r)
    R=pd.DataFrame(rows).set_index('sample'); df=df.set_index('sample').loc[R.index].copy()
    ok=True
    for s,r in R.iterrows():
        if np.abs(np.array(r['_pars'])-df.loc[s,F].values.astype(float)).max()>1e-9: ok=False
        for l in LAB:
            if abs(r['_lab'][l]-df.loc[s,l])>1e-9: ok=False
    R=R.drop(columns=['_pars','_lab'])
    df=df.join(R).reset_index(drop=True)
    return df,ok
RAW=[f'raw_{p}_{k}' for p in ['pyr_int','int_pyr','int_int','pyr_pyr'] for k in ['n','g']]
# pathway: (pre,post) for each target
PATH={'usable_conns2':('P','P'),'usable_pyr_int':('P','I'),'usable_int_pyr':('I','P'),'usable_int_int':('I','I'),
 'frac_int_driven':('P','I'),'frac_pyr_inhibited':('I','P'),'frac_pyr_inhibited_w05':('I','P')}
for p,(a,b) in {'pyr_int':('P','I'),'int_pyr':('I','P'),'int_int':('I','I'),'pyr_pyr':('P','P')}.items():
    for k in 'ng': PATH[f'raw_{p}_{k}']=(a,b)
def isfrac(t): return t.startswith('frac_')
def npost(df,t): return (df['interneuron'] if PATH[t][1]=='I' else df['pyramidal']).values.astype(float)
def y_model(df,t):  # modelled quantity
    y=df[t].values.astype(float)
    return y*npost(df,t) if isfrac(t) else y
def back(pred,df,t):
    return np.clip(pred/npost(df,t),0,1) if isfrac(t) else pred
def cnt(df,a):
    return df['pyramidal'].values.astype(float) if a=='P' else df['interneuron'].values.astype(float)
def lg(x): return np.log(np.maximum(x,1e-12))
def M1X(df,t):
    a,b=PATH[t]; npre=cnt(df,a); npo=cnt(df,b)
    V=np.pi*df['shape.radius'].values.astype(float)**2*df['shape.thickness'].values
    if isfrac(t): pair=[lg(npre),lg(npo)]
    else:
        pr=npre*(npo-1) if a==b else npre*npo
        pair=[lg(pr)]
    X=np.column_stack(pair+[lg(V),lg(df['dm.weight'].values.astype(float)),df['days'].values.astype(float),lg(df['minneuronseparation'].values.astype(float))])
    return X
def offset(df,t):
    a,b=PATH[t]; npre=cnt(df,a); npo=cnt(df,b); pr=npre*(npo-1) if a==b else npre*npo
    V=np.pi*df['shape.radius'].values.astype(float)**2*df['shape.thickness'].values
    return lg(pr)-lg(V)
def M2X(df):
    return np.column_stack([lg(df['dm.weight'].values.astype(float)),df['days'].values.astype(float)])
class Pois:
    def __init__(s,alpha=ALPHA): s.alpha=alpha
    def fit(s,X,y,off=None):
        s.mu=X.mean(0); s.sd=X.std(0)+1e-9; Z=(X-s.mu)/s.sd
        if off is None: m=PoissonRegressor(alpha=s.alpha,max_iter=2000,tol=1e-8).fit(Z,y)
        else:
            w=np.exp(off); m=PoissonRegressor(alpha=s.alpha,max_iter=2000,tol=1e-8).fit(Z,y/w,sample_weight=w)
        s.m=m; return s
    def predict(s,X,off=None):
        p=s.m.predict((X-s.mu)/s.sd); return p if off is None else p*np.exp(off)
    def coef(s):  # raw-scale coefficients
        b=s.m.coef_/s.sd; return np.append(s.m.intercept_-(b*s.mu).sum(),b)
def fit_predict(model,t,tr,te,df,ntrees=500,seed=0):
    """tr, te: index arrays into df. returns prediction of modelled quantity (count scale) for te."""
    y=y_model(df,t)
    d_tr=df.iloc[tr]; d_te=df.iloc[te]
    if model=='BASE': return np.full(len(te),y[tr].mean())
    if model=='RF7':
        m=RandomForestRegressor(n_estimators=ntrees,random_state=seed,n_jobs=1).fit(df.iloc[tr][F],y[tr]); return m.predict(d_te[F])
    if model=='POIS7':
        m=Pois().fit(d_tr[F].values.astype(float),y[tr]); return m.predict(d_te[F].values.astype(float))
    if model=='M1':
        m=Pois().fit(M1X(d_tr,t),y[tr]); return m.predict(M1X(d_te,t))
    if model=='M2':
        m=Pois().fit(M2X(d_tr),y[tr],offset(d_tr,t)); return m.predict(M2X(d_te),offset(d_te,t))
def metrics(yt,yp,ybase):
    yp=np.maximum(yp,1e-6); yb=np.maximum(ybase,1e-6)
    r2=r2_score(yt,yp); mae=mean_absolute_error(yt,yp)
    rho=spearmanr(yt,yp)[0] if np.std(yp)>0 and np.std(yt)>0 else np.nan
    db=mean_poisson_deviance(yt,yb) if True else 0
    d2=1-mean_poisson_deviance(yt,yp)/db if db>0 else np.nan
    return dict(R2=r2,MAE=mae,rho=rho,D2=d2)
def applicable(model,t): return not (model=='M2' and isfrac(t))

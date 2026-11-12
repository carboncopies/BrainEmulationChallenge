from common import *
df,_=load(); rng=np.random.default_rng(0); N=20000
S=pd.DataFrame({'days':rng.integers(20,26,N),'pyramidal':rng.integers(16,71,N),'interneuron':rng.integers(16,31,N),
 'minneuronseparation':rng.integers(10,16,N),'shape.radius':rng.integers(100,201,N),'shape.thickness':rng.integers(20,51,N),
 'dm.weight':np.round(rng.integers(1,11,N)/10,1)})
def dens(d): return (d.pyramidal+d.interneuron)/(np.pi*d['shape.radius']**2*d['shape.thickness']*1e-9)
def con(d):
    de=dens(d); pf=d.pyramidal/(d.pyramidal+d.interneuron); return ((de>=10000)&(de<=50000)&(pf>=.7)&(pf<=.8)).values
cS=con(S); cD=con(df); print('constraint frac in sample',cS.mean(),'observed rows satisfying',cD.sum())
out={'frac_sample_ok':float(cS.mean()),'n_obs_ok':int(cD.sum())}
for t in ['usable_int_pyr','usable_pyr_int','usable_conns2']:
    y=df[t].values.astype(float); m=Pois().fit(M1X(df,t),y); pin=m.predict(M1X(df,t)); ps=m.predict(M1X(S,t))
    r={'insample_spearman':float(spearmanr(pin,y)[0])}
    def rec(i,p): return {'config':{k:float(S[k].iloc[i]) for k in F},'pred':float(p[i])}
    r['argmax_uncon']=rec(int(np.argmax(ps)),ps); 
    ix=np.where(cS)[0]; j=ix[np.argmax(ps[ix])]; r['argmax_con']=rec(int(j),ps)
    r['pred_top1pct_uncon_median']=float(np.median(np.sort(ps)[-200:]))
    b=int(np.argmax(y)); r['best_obs']={'config':{k:float(df[k].iloc[b]) for k in F},'value':float(y[b]),'M1_insample_pred':float(pin[b]),'meets_constraint':bool(cD[b])}
    if cD.any():
        yy=np.where(cD,y,-1); b=int(np.argmax(yy)); r['best_obs_con']={'config':{k:float(df[k].iloc[b]) for k in F},'value':float(y[b]),'M1_pred':float(pin[b])}
    r['coef']=m.coef().tolist(); out[t]=r
# T6
y=np.log(df.wall_s.values.astype(float)); n=(df.pyramidal+df.interneuron).values.astype(float); V=np.pi*df['shape.radius']**2*df['shape.thickness']; d=df.days.values.astype(float)
def ols(X,y):
    X1=np.column_stack([np.ones(len(y)),X]); b=np.linalg.lstsq(X1,y,rcond=None)[0]; res=y-X1@b
    return b,1-res.var()/y.var()
t6={}
b,r2=ols(np.column_stack([np.log(n),d]),y); t6['A']={'terms':['icpt','log(n)','days'],'coef':b.tolist(),'R2':r2,'pred':{k:float(np.exp(b@[1,np.log(s),dd])) for k,(s,dd) in {'67+27,d25':(94,25),'48+20,d22':(68,22),'24+16,d20':(40,20)}.items()}}
b,r2=ols(np.column_stack([np.log(n),d,np.log(V)]),y); Vm=float(np.median(V))
t6['B']={'terms':['icpt','log(n)','days','logV'],'coef':b.tolist(),'R2':r2,'V_used_median_um3':Vm,'pred':{k:float(np.exp(b@[1,np.log(s),dd,np.log(Vm)])) for k,(s,dd) in {'67+27,d25':(94,25),'48+20,d22':(68,22),'24+16,d20':(40,20)}.items()}}
t6['wall_s_mean']=float(df.wall_s.mean()); t6['wall_s_range']=[float(df.wall_s.min()),float(df.wall_s.max())]
out['t6']=t6; json.dump(out,open('t5_results.json','w'),indent=1)
print(json.dumps(out,indent=1))

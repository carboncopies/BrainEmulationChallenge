import json, numpy as np, pandas as pd
from scipy.stats import spearmanr
H='/home/johnjose/cos/netmorph_work/headtohead/'
COMP=['raw_pyr_int_n','raw_int_pyr_n','raw_int_int_n','usable_conns2']; TG=COMP+['J']
REF=dict(zip(COMP,[42.0,97.25,18.25,460.0])); T1,T2=1.041,1.534
r=pd.read_csv(H+'runs.csv'); r['sc']=r.soft_clean.astype(str)=='True'
out={}; md=[]
def f(x):
    if x is None or (isinstance(x,float) and np.isnan(x)): return 'nan'
    return '%.3g'%x if isinstance(x,(float,np.floating)) else str(x)
def table(hdr,rows):
    md.append('| '+' | '.join(hdr)+' |'); md.append('|'+'---|'*len(hdr))
    for x in rows: md.append('| '+' | '.join(f(v) for v in x)+' |')
    md.append('')
# recompute J check
Jc=np.minimum.reduce([r[c]/REF[c] for c in COMP]); out['J_recompute_maxabsdiff']=float(np.abs(Jc-r.J).max())
r['lim']=pd.DataFrame({c:r[c]/REF[c] for c in COMP}).idxmin(axis=1)
r['seed']=r.netmorph_seed
r['kind']=np.where(r.run_id.str.startswith('H-'),'H',np.where(r.run_id.str.startswith('N-'),'N','T'))
# A
md.append('# SCORE_FINAL\n\n## A. Sanity'); a={}
a['rows_per_queue']=r.groupby('queue').size().to_dict(); a['all_rc0']=bool((r.rc==0).all()); a['sim_id_min']=int(r.NES_SIM_ID.min()); a['sim_id_max']=int(r.NES_SIM_ID.max()); a['sim_id_unique']=bool(r.NES_SIM_ID.is_unique)
a['wall_s']=dict(min=r.wall_s.min(),median=r.wall_s.median(),max=r.wall_s.max())
q3=r[r.queue=='queue3']; rt=q3.wall_s/q3.pred_wall_s
a['q3_ratio']=dict(median=rt.median(),max=rt.max()); a['runs_over_2x_all']=r[r.wall_s>2*r.pred_wall_s].run_id.tolist()
a['q3_over_2x']=q3[rt>2].run_id.tolist(); a['J_recompute_maxabsdiff']=out['J_recompute_maxabsdiff']; a['nan_cells_in_key_cols']=int(r[COMP+['J','wall_s','pred_wall_s']].isna().sum().sum())
out['A']=a
table(['item','value'],[[k,json.dumps(v,default=float) if isinstance(v,(dict,list)) else v] for k,v in a.items()])
# B
Hr=r[r.kind=='H'].copy(); cm=Hr.groupby('config_id')[TG].mean()
P={'ml':pd.read_csv(H+'preds_heldout_ml.csv').set_index('config_id'),'mech':pd.read_csv(H+'preds_heldout_mech.csv').set_index('config_id')}
def pcol(P,t): return P['J_pred'] if t=='J' else P[t+'_mean']
def pdev(y,p,b):
    p=np.maximum(p,1e-9);b=max(b,1e-9)
    def dv(y,m): 
        t=np.where(y>0,y*np.log(np.where(y>0,y,1)/m),0); return np.mean(2*(t-(y-m)))
    return 1-dv(y,p)/dv(y,np.full(len(y),b))
def met(y,p,t,lo=None,hi=None):
    y=np.asarray(y,float);p=np.asarray(p,float)
    d=dict(n=len(y),spearman=spearmanr(y,p)[0],R2=1-((y-p)**2).sum()/((y-y.mean())**2).sum(),MAE=np.abs(y-p).mean(),
      med_abs_rel_err=float(np.median(np.abs(y-p)/np.abs(y))),
      poisson_D2=pdev(y,p,y.mean()) if t!='J' else None,
      cov80=float(np.mean((y>=lo)&(y<=hi))) if lo is not None else None)
    return {k:(float(v) if v is not None else None) for k,v in d.items()}
B={}; md.append('## B. Held-out prediction error')
gen=['H%02d'%i for i in range(1,9)]; cor=['H%02d'%i for i in range(9,13)]
for lvl in ['config_mean','per_run','general_H01-H08','corner_H09-H12']:
    B[lvl]={}; rows=[]
    for arm in ['ml','mech']:
        B[lvl][arm]={}
        for t in TG:
            if lvl=='per_run':
                y=Hr[t].values; cfg=Hr.config_id.values
            else:
                idx=cm.index if lvl=='config_mean' else (gen if lvl.startswith('gen') else cor)
                y=cm.loc[idx,t].values; cfg=np.array(idx)
            Pp=P[arm].loc[cfg]
            lo=Pp[t+'_lo80'].values if t!='J' else None; hi=Pp[t+'_hi80'].values if t!='J' else None
            m=met(y,pcol(Pp,t).values,t,lo,hi); B[lvl][arm][t]=m
            rows.append([arm,t]+[m[k] for k in ['n','spearman','R2','poisson_D2','MAE','med_abs_rel_err','cov80']])
    md.append('### vs '+lvl+(' (12 config means over 2 seeds)' if lvl=='config_mean' else ' (24 runs)' if lvl=='per_run' else ' (config means)'))
    table(['arm','target','n','Spearman','R2','PoissonD2','MAE','MedAbsRelErr','cov80'],rows)
rng=np.random.default_rng(0); bs={}; cfgs=list(cm.index)
def sp(a,b):
    return np.nan if np.std(a)==0 or np.std(b)==0 else spearmanr(a,b)[0]
rows=[]
for t in TG:
    y=cm[t].values; pm=pcol(P['mech'].loc[cfgs],t).values; pl=pcol(P['ml'].loc[cfgs],t).values; d=[]
    rng=np.random.default_rng(0)
    for _ in range(2000):
        i=rng.integers(0,12,12); d.append(sp(y[i],pm[i])-sp(y[i],pl[i]))
    d=np.array(d); v=d[~np.isnan(d)]
    bs[t]=dict(point_diff=sp(y,pm)-sp(y,pl),ci90_lo=float(np.percentile(v,5)),ci90_hi=float(np.percentile(v,95)),frac_mech_gt_ml=float((v>0).mean()),frac_tie=float((v==0).mean()),frac_ml_gt_mech=float((v<0).mean()),n_valid=int(len(v)),n_nan=int(np.isnan(d).sum()))
    rows.append([t]+list(bs[t].values()))
B['bootstrap_spearman_mech_minus_ml']=bs
md.append('### Bootstrap (2000 resamples of 12 config means, seed 0; Spearman mech - ml; NaN resamples dropped)')
table(['target','point diff','CI90 lo','CI90 hi','frac mech>ml','frac tie','frac ml>mech','n valid','n NaN'],rows)
out['B']=B
# C
md.append('## C. Held-out seed spread'); C={}; rows=[]
for t in TG:
    w=Hr.pivot(index='config_id',columns='seed',values=t); a_,b_=w[2001],w[2002]
    s=(a_-b_).abs()/((a_+b_)/2)
    C[t]=dict(median_rel_spread=float(s.median()),max_rel_spread=float(s.max()),spearman_2001_vs_2002=float(spearmanr(a_,b_)[0]),pearson_2001_vs_2002=float(np.corrcoef(a_,b_)[0,1]))
    rows.append([t]+list(C[t].values()))
out['C']=C; table(['target','median |a-b|/mean','max','Spearman s2001 vs s2002','Pearson'],rows)
# D
md.append('## D. Nominations'); N=r[r.kind=='N'].copy(); N['arm_']=N.arm
N['cfg']=N.config_id; rows=[]
for _,x in N.iterrows(): rows.append([x.arm,x.cfg,x.seed]+[x[c] for c in COMP]+[x.J,x.sc,x.lim])
table(['arm','config','seed']+COMP+['J','soft_clean','limiting'],rows)
D={}; rows=[]
for (arm,c),g in N.groupby(['arm','cfg'],sort=False):
    d={}
    for t in TG: d[t]=dict(mean=float(g[t].mean()),sd=float(g[t].std(ddof=1)),cv=float(g[t].std(ddof=1)/g[t].mean()))
    D.setdefault('per_config',{})[c]=d
    rows.append([arm,c]+[v for t in TG for v in (d[t]['mean'],d[t]['sd'],d[t]['cv'])])
md.append('Per config mean / SD (ddof=1) / CV'); table(['arm','config']+[f'{t} {s}' for t in TG for s in ('mean','sd','cv')],rows)
rows=[]; D['per_arm']={}
for arm,g in N.groupby('arm'):
    d=dict(n=len(g),mean_J=g.J.mean(),median_J=g.J.median(),T1_hits=int(((g.J>=T1)&g.sc).sum()),T2_hits=int(((g.J>=T2)&g.sc).sum()),best_J=g.J.max())
    D['per_arm'][arm]={k:float(v) for k,v in d.items()}; rows.append([arm]+list(d.values()))
table(['arm','n','mean J','median J','T1 hits','T2 hits','best J'],rows)
lc=N.lim.value_counts().to_dict(); D['limiting_counts_18']=lc; D['limiting_counts_by_arm']={a:g.lim.value_counts().to_dict() for a,g in N.groupby('arm')}
md.append('Limiting component counts over 18 runs: '+json.dumps(lc)+'; by arm: '+json.dumps(D['limiting_counts_by_arm'])+'\n')
pn={'ml':pd.read_csv(H+'preds_nom_ml.csv').set_index('config_id'),'mech':pd.read_csv(H+'preds_nom_mech.csv').set_index('config_id')}
obs=N.groupby('cfg').J.mean(); order=['ML-NOM-1','ML-NOM-2','ML-NOM-3','M1','M7','M9']; rows=[]; D['pred_vs_obs']={}
for c in order: rows.append([c,obs[c],pn['ml'].loc[c,'J_pred'],pn['mech'].loc[c,'J_pred']])
table(['config','obs mean J','ml pred J','mech pred J'],rows)
for arm in pn:
    p=pn[arm].loc[order,'J_pred'].values; y=obs[order].values
    D['pred_vs_obs'][arm]=dict(MAE=float(np.abs(p-y).mean()),bias_pred_minus_obs=float((p-y).mean()),spearman6=float(spearmanr(y,p)[0]),rank_obs=pd.Series(y,order).rank(ascending=False).tolist(),rank_pred=pd.Series(p,order).rank(ascending=False).tolist())
    md.append(f"{arm}: MAE={f(D['pred_vs_obs'][arm]['MAE'])}, bias(pred-obs)={f(D['pred_vs_obs'][arm]['bias_pred_minus_obs'])}, Spearman(6)={f(D['pred_vs_obs'][arm]['spearman6'])}, obs rank (order {order})={D['pred_vs_obs'][arm]['rank_obs']}, pred rank={D['pred_vs_obs'][arm]['rank_pred']}")
md.append(''); out['D']=D
# E
md.append('## E. Training recap (queues 1-2, run order in file)'); E={}; rows=[]
for arm in ['ML','MECH']:
    g=r[(r.kind=='T')&(r.arm==arm)].reset_index(drop=True); sc=g[g.sc]
    h1=np.where((g.J>=T1)&g.sc)[0]; h2=np.where((g.J>=T2)&g.sc)[0]
    d=dict(n=len(g),n_soft_clean=len(sc),best_softclean_J=sc.J.max(),best_J_any=g.J.max(),mean_J=g.J.mean(),n_T1=len(h1),n_T2=len(h2),first_T1=int(h1[0])+1 if len(h1) else None,first_T2=int(h2[0])+1 if len(h2) else None)
    E[arm]={k:(float(v) if v is not None else None) for k,v in d.items()}; rows.append([arm]+list(d.values()))
    E[arm]['J_sequence']=g.J.round(3).tolist(); E[arm]['soft_clean_sequence']=g.sc.tolist()
out['E']=E; table(['arm','n','n soft_clean','best soft-clean J','best J any','mean J','n T1','n T2','first T1 idx','first T2 idx'],rows)
for arm in E: md.append(f'{arm} J sequence: {E[arm]["J_sequence"]}; soft_clean: {E[arm]["soft_clean_sequence"]}')
md.append('')
# F
md.append('## F. Training vs nomination re-runs'); F={}; rows=[]
T=r[r.kind=='T']
for arm in ['MECH','ML']:
    for c in sorted(N[N.arm==arm].cfg.unique()):
        t=T[(T.arm==arm)&(T.config_id==c)]
        if len(t)==0: F[c]=None; continue
        nj=N[(N.arm==arm)&(N.cfg==c)].sort_values('seed').J.tolist()
        F[c]=dict(train_J=float(t.J.iloc[0]),nom_J=nj,nom_mean=float(np.mean(nj)),train_minus_nom_mean=float(t.J.iloc[0]-np.mean(nj)))
        rows.append([arm,c,t.J.iloc[0],nj[0],nj[1],nj[2],np.mean(nj),t.J.iloc[0]-np.mean(nj)])
table(['arm','config','train J (seed 20240628)','nom J s3001','s3002','s3003','nom mean','train - nom mean'],rows)
md.append('ML nominations matching an ML training config_id: '+str([c for c in N[N.arm=="ML"].cfg.unique() if c in set(T[T.arm=="ML"].config_id)])+'\n')
out['F']=F
# anomalies
an=[]
an.append('soft_clean False rows by kind: '+json.dumps(r[~r.sc].groupby('kind').size().to_dict()))
an.append('soft_clean False run_ids: '+', '.join(r[~r.sc].run_id))
an.append('heldout_configs.csv soft_clean flag vs observed runs agree: '+str(bool((Hr.groupby('config_id').sc.first()==pd.read_csv(H+'heldout_configs.csv').set_index('config_id').soft_clean.astype(str).eq('True')).all())))
an.append('N- and H- run params match nominations.csv and heldout_configs.csv on all 7 params (checked separately: 0 mismatches)')
out['anomalies']=an
md.append('## Anomalies / notes'); md+=['- '+x for x in an]
md.append('- soft_clean reasons are not stored in runs.csv beyond the boolean; frac_* columns exist but the criterion is not re-derived here.')
open(H+'SCORE_FINAL.md','w').write('\n'.join(md)+'\n')
json.dump(out,open(H+'score_final.json','w'),indent=1,default=lambda o:float(o) if isinstance(o,(np.floating,np.integer)) else str(o))

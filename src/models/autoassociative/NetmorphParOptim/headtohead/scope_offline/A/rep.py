import json,numpy as np
a=json.load(open('t1_results.json')); b=json.load(open('t3_results.json')); c=json.load(open('t5_results.json'))
M=['BASE','RF7','POIS7','M1','M2']; L=[]
def P(s=''): L.append(s)
cv=a['cv']; T=list(cv)
for k,nm in [('R2','R2'),('MAE','MAE'),('rho','Spearman rho'),('D2','Poisson D2 vs BASE')]:
    for kind in ['fold','pool']:
        P(f'### T1 {nm} -- {"mean±sd over 50 folds" if kind=="fold" else "pooled OOF per repeat, mean±sd over 10 repeats"}'); P('| target | '+' | '.join(M)+' |'); P('|'+'---|'*(len(M)+1))
        for t in T:
            r=[]
            for m in M:
                v=cv[t].get(m)
                if v is None: r.append('-'); continue
                d=v[k]; r.append(f"{d[kind+'_mean']:.3f}±{d[kind+'_sd']:.3f}")
            P(f'| {t} | '+' | '.join(r)+' |')
        P()
P('### T1 top-10 precision (OOF per repeat, mean±sd over 10 repeats; chance=0.10)'); P('| target | '+' | '.join(M)+' |'); P('|'+'---|'*(len(M)+1))
for t in T: P(f'| {t} | '+' | '.join('-' if cv[t].get(m) is None else f"{cv[t][m]['top10']['mean']:.2f}±{cv[t][m]['top10']['sd']:.2f}" for m in M)+' |')
P(); P('### M1 coefficients on all 100 rows (log link, raw feature scale; bootstrap-500 SE)')
for t,d in a['coefs'].items():
    P(f'- {t}: '+', '.join(f"{n}={c_:.3f}±{s:.3f}" for n,c_,s in zip(d['names'],d['coef'],d['boot_se']))+f" (nboot={d['nboot']})")
P(); P('### T2 noise ceiling (M1, all rows; dispersion=Pearson chi2/(n-6))'); P('| target | mean | var | R2max Poisson | dispersion | M1 in-sample R2 |'); P('|---|---|---|---|---|---|')
for t,d in a['t2'].items(): P(f"| {t} | {d['mean']:.3f} | {d['var']:.3f} | {d['R2max']:.3f} | {d['disp']:.2f} | {d['insample_R2']:.3f} |")
P(); P('### T3 learning curves, 100 random subsets each (median [IQR]); fail = fits skipped')
for t,S in b['t3'].items():
    P(f'**{t}**'); P('| n_train | metric | '+' | '.join(['RF7','POIS7','M1','M2'])+' |'); P('|---|---|---|---|---|---|')
    for n in ['5','10','20','40','80']:
        for k in ['rho','D2','R2']:
            r=[]
            for m in ['RF7','POIS7','M1','M2']:
                d=S[n][m]; x=d[k]
                r.append('n/a' if x['med'] is None else f"{x['med']:.2f} [{x['q25']:.2f},{x['q75']:.2f}]"+(f" f{d['fail']}" if d['fail'] and k=='rho' else ''))
            P(f'| {n} | {k} | '+' | '.join(r)+' |')
    P()
t4=b['t4']; P(f"### T4 extrapolation: train size<= {t4['median_size']} (n={t4['n_train']}), test size> (n={t4['n_test']}); mean wall_s low={t4['wall_low']:.0f}, high={t4['wall_high']:.0f}")
P('| target | train mean | test mean | metric | RF7 | POIS7 | M1 | M2 |'); P('|---|---|---|---|---|---|---|---|')
for t,d in t4['res'].items():
    for k in ['rho','D2','R2','MAE']:
        P(f"| {t} | {d['ytrain_mean']:.2f} | {d['ytest_mean']:.2f} | {k} | "+' | '.join('-' if d[m] is None or d[m][k] is None or d[m][k]!=d[m][k] else f"{d[m][k]:.3f}" for m in ['RF7','POIS7','M1','M2'])+' |')
P(); P(f"### T5 inversion (20000 uniform samples; fraction passing density+pyr-fraction constraint={c['frac_sample_ok']:.3f}; observed rows passing={c['n_obs_ok']}/100)")
f=lambda d:', '.join(f"{k.replace('shape.','')}={v:g}" for k,v in d.items())
for t in ['usable_int_pyr','usable_pyr_int','usable_conns2']:
    r=c[t]; P(f"- **{t}** in-sample Spearman(M1,obs)={r['insample_spearman']:.3f}")
    P(f"  - argmax unconstrained: {f(r['argmax_uncon']['config'])} -> pred {r['argmax_uncon']['pred']:.1f}")
    P(f"  - argmax constrained: {f(r['argmax_con']['config'])} -> pred {r['argmax_con']['pred']:.1f}")
    P(f"  - best observed: {f(r['best_obs']['config'])} -> obs {r['best_obs']['value']:g} (M1 in-sample pred {r['best_obs']['M1_insample_pred']:.1f}; meets constraint={r['best_obs']['meets_constraint']})")
    if 'best_obs_con' in r: P(f"  - best observed among constraint-satisfying rows: {f(r['best_obs_con']['config'])} -> obs {r['best_obs_con']['value']:g} (M1 pred {r['best_obs_con'].get('M1_pred',0):.1f})")
t6=c['t6']; P(); P('### T6 runtime log(wall_s) OLS (all 100 rows, in-sample R2); wall_s mean=%.0f range=%s'%(t6['wall_s_mean'],t6['wall_s_range']))
for k in 'AB':
    d=t6[k]; P(f"- {k}: "+', '.join(f"{n}={v:.4f}" for n,v in zip(d['terms'],d['coef']))+f"; R2={d['R2']:.3f}; pred wall_s: "+', '.join(f"{n}: {v:.0f}" for n,v in d['pred'].items())+(f" (logV at median V={d['V_used_median_um3']:.3g} um3)" if 'V_used_median_um3' in d else ''))
open('RESULTS_tables.md','w').write('\n'.join(L)); print('\n'.join(L))

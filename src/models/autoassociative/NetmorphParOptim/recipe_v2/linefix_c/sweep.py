"""Read-only D_synmax sweep on the three patched seed-16180 runs by thresholding stored pre-post synapse distance.
Adds: finer Pyr->Pyr thresholds, drivable 8-cell from synapse counts x 0.98 nS (validated at D 0.1 against the viz-dump value),
inhibitory fraction A for combinations, negative-binomial extrapolation of interneuron pairs to D 0.15. -> sweep_results.json"""
import json, numpy as np, os, sys
sys.path.insert(0,'.'); import pairs
from scipy.optimize import brentq
W='/home/johnjose/cos/netmorph_work/recipe_v2'; fx=json.load(open(W+'/linefix/pv_results.json'))
def best8(v):
    v=sorted(v,reverse=True); return max(min(sum(v[4:8]),10.0)+sum(v[0:4]),min(sum(v[0:4]),10.0)+sum(v[4:8]))
def nbfit(mean,p0):  # NB with P(0)=p0: (r/(r+mean))^r = p0
    f=lambda r:(r/(r+mean))**r-p0
    return brentq(f,1e-4,1e4) if np.exp(-mean)<p0 else np.inf
def nb(mean,r):  # returns p_conn, syn per connected
    p0=np.exp(-mean) if np.isinf(r) else (r/(r+mean))**r
    return 1-p0, mean/(1-p0)
out={}
for v in('S1','V1','V3'):
    t,xyz,pre,post,dist=pairs.load(pairs.RUNS[('fix',v)]); n=len(t); P=np.where(t)[0]; I=np.where(~t)[0]
    def M(a,b,th):
        m=np.isin(pre,a)&np.isin(post,b)&(dist<=th); X=np.zeros((n,n),int); np.add.at(X,(pre[m],post[m]),1); return X[np.ix_(a,b)]
    r={'PP':{},'int':{},'A':{},'nb015':{}}
    for th in(1.5,0.5,0.3,0.15,0.1,0.075,0.05,0.03,0.02,0.01,0.005):
        S=M(P,P,th); c=S[S>0]; r['PP'][th]=dict(syn=int(S.sum()),p_conn=round(len(c)/9120,3),spc_mean=round(float(c.mean()),2),spc_median=float(np.median(c)),in_mean=round(float(S.sum(0).mean()),1),in_median=float(np.median(S.sum(0))),in_max=int(S.sum(0).max()),zero_in=int((S.sum(0)==0).sum()),top5_in_share=round(float(np.sort(S.sum(0))[-5:].sum()/S.sum()),3))
    for th in(0.1,0.075,0.05,0.03):
        PI=M(P,I,th); IP=M(I,P,th); II=M(I,I,th)
        d8=int(sum(best8(PI[:,k]*0.98)>=13.84 for k in range(len(I))))
        st=lambda S,npair:(int(S.sum()),round(float((S>0).sum()/npair),3),round(float(S.sum()/max(1,(S>0).sum())),2))
        r['int'][th]=dict(PI=st(PI,PI.size),IP=st(IP,IP.size),II=st(II,II.size-len(I)),drivable8=d8,drivable_simple=int((PI.sum(0)*0.98>=13.84).sum()),zero_in=int((PI.sum(0)==0).sum()),targets_per_int=round(float((IP>0).sum(1).mean()),1),viz_drivable8=fx[v+'_s16180_fix']['drivable_8cell_capaware'] if th==0.1 else None)
        for tp in(1.5,0.5,0.3,0.15,0.1,0.05):
            r['A']['int%g_pp%g'%(th,tp)]=round(float(IP.sum()/(IP.sum()+r['PP'][tp]['syn'])),3)
    # NB extrapolation to 0.15, with check: fit at 0.05, predict 0.1
    for k,(a,b) in dict(PI=(P,I),IP=(I,P),II=(I,I)).items():
        S5=M(a,b,0.05); S10=M(a,b,0.1); npair=S10.size-(len(I) if k=='II' else 0)
        m5=S5.sum()/npair; m10=S10.sum()/npair
        r5=nbfit(m5,1-(S5>0).sum()/npair); chk=nb(m10,r5); r10=nbfit(m10,1-(S10>0).sum()/npair); pr=nb(1.5*m10,r10)
        r['nb015'][k]=dict(check_pred_p_spc_at_0p1=[round(chk[0],3),round(chk[1],2)],actual_at_0p1=[round(float((S10>0).sum()/npair),3),round(float(S10.sum()/(S10>0).sum()),2)],pred_0p15=dict(syn=int(1.5*S10.sum()),p_conn=round(pr[0],3),spc=round(pr[1],2)))
    r['K_overlap_IP_over_PP']=round((r['int'][0.1]['IP'][0]/0.1)/(r['PP'][1.5]['syn']/1.5),2)
    out[v]=r; print('==',v,'K',r['K_overlap_IP_over_PP'])
    for th,x in r['PP'].items(): print('  PP',th,x)
    for th,x in r['int'].items(): print('  int',th,x)
    print('  A',r['A']); print('  nb',r['nb015'])
json.dump(out,open('sweep_results.json','w'),indent=1)

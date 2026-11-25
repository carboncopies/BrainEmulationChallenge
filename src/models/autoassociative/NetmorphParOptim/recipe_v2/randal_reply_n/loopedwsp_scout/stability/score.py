"""Score the no-inhibition reduced model (rn.py) against ALL stored addendum B/C runs (except LI) as fixed in PROTOCOL.md."""
import numpy as np, rn, glob, os, json, statistics as st
from summ import summarize
def spearman(a,b):
    ra=np.argsort(np.argsort(a)); rb=np.argsort(np.argsort(b)); return float(np.corrcoef(ra,rb)[0,1]) if len(a)>2 else float('nan')
cells=[]; runs=[]; tab=['| run | class | n | stored c/rec/rv | model c/rec/rv | stored m450 / last | model m450 / last | counts within 1 | m450 within x2 | last within 100 ms |','|'+'---|'*10]
for pre in ('rawB_','rawC_'):
    for fn in sorted(glob.glob(rn.HERE+pre+'s*.json')):
        tag=os.path.basename(fn)[len(pre):-5]; d=rn.load_run(tag,pre)
        if d['arm']=='LI': continue
        A=d['A']; M=rn.member_matrices('s%d'%d['seed'],d['arm'],A,d['r']); cl,meta=rn.events_cues(d,A)
        mm=rn.sim_measures(rn.sim(M['XA'],M['XN'],cl),meta,A); sm=rn.stored_measures(d,A)
        for r in mm: r['cont']=False
        S=summarize(sm); Mo=summarize(mm); runs.append((tag,d['arm'],d['seed'],S,Mo))
        for k in ('full','p75','p50','p25','p1','unrel'):
            if k not in S: continue
            s=S[k]; m=Mo[k]; ok_c=all(abs(s[i]-m[i])<=1 for i in (0,1,2)); ok_m=max(s[4]+5,m[4]+5)/min(s[4]+5,m[4]+5)<=2; ok_l=abs(s[5]-m[5])<=100
            cells.append((tag,k,ok_c,ok_m,ok_l,s[3]))
            tab.append('| %s | %s | %d | %d/%d/%d | %d/%d/%d | %.0f / %.0f | %.0f / %.0f | %s | %s | %s |'%(tag,k,s[3],s[0],s[1],s[2],m[0],m[1],m[2],s[4],s[5],m[4],m[5],'Y' if ok_c else 'N','Y' if ok_m else 'N','Y' if ok_l else 'N'))
n=len(cells); print('cells',n,'counts within 1: %d (%.0f%%)  m450 x2: %d (%.0f%%)  last 100 ms: %d (%.0f%%)'%(sum(c[2] for c in cells),100*np.mean([c[2] for c in cells]),sum(c[3] for c in cells),100*np.mean([c[3] for c in cells]),sum(c[4] for c in cells),100*np.mean([c[4] for c in cells])))
# restricted to the arms that are the point of the question (LH, W70, W50, H2)
sub=[c for c in cells if any(a in c[0] for a in ('_LH_','_W70_','_W50_','_H2_'))]
print('LH/W70/W50/H2 only: cells',len(sub),'counts %.0f%% m450 %.0f%% last %.0f%%'%tuple(100*np.mean([c[i] for c in sub]) for i in (2,3,4)))
# termination call per run: median last of 75% events <100 ms ?
print('\nTERMINATION CALL (p75 median last < 100 ms) per run; "stored" uses non-contaminated stored events')
agree=0
for tag,arm,seed,S,Mo in runs:
    if 'p75' not in S: continue
    st_t=S['p75'][5]<100; mo_t=Mo['p75'][5]<100; agree+=(st_t==mo_t); print('%-22s stored last %.0f (%s)  model last %.0f (%s) %s'%(tag,S['p75'][5],'ends' if st_t else 'reverb',Mo['p75'][5],'ends' if mo_t else 'reverb','OK' if st_t==mo_t else 'MISS'))
print('termination agreement %d/%d'%(agree,len([r for r in runs if 'p75' in r[3]])))
# ordering of arms by median p75 member spikes within each model
for seed in (77777,66666):
    rr=[(t,S['p75'][4],Mo['p75'][4]) for t,a,s,S,Mo in runs if s==seed and 'p75' in S]
    print(seed,'Spearman(stored m450, model m450) over %d runs: %.2f'%(len(rr),spearman([x[1] for x in rr],[x[2] for x in rr])))
    rr2=[x for x in rr if '_L0_' not in x[0]]; print(seed,'  without L0 (%d runs): %.2f'%(len(rr2),spearman([x[1] for x in rr2],[x[2] for x in rr2])))
open('score_table.md','w').write('\n'.join(tab)+'\n')

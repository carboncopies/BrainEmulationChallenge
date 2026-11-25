import numpy as np, rn, glob, os, statistics as st, json
from summ import summarize
runs=[]
for pre in ('rawB_','rawC_'):
    for fn in sorted(glob.glob(rn.HERE+pre+'s*.json')):
        tag=os.path.basename(fn)[len(pre):-5]; runs.append((tag,pre))
out={}
for tag,pre in runs:
    d=rn.load_run(tag,pre); arm=d['arm']; key='s%d'%d['seed']
    if arm=='LI': continue
    A=d['A']; M=rn.member_matrices(key,arm,A,d['r']); cl,meta=rn.events_cues(d,A)
    R=rn.sim(M['XA'],M['XN'],cl); mm=rn.sim_measures(R,meta,A); sm=rn.stored_measures(d,A)
    for r in mm: r['cont']=False
    sS=summarize(sm); sM=summarize(mm); out[tag]=dict(stored=sS,model=sM)
    print(tag); 
    for k in ('full','p75','p50','p25'):
        if k in sS: print('   %-5s stored c%d rv%d/%d m450=%3.0f last=%3.0f | model c%d rv%d/%d m450=%4.0f last=%3.0f'%((k,sS[k][0],sS[k][2],sS[k][3],sS[k][4],sS[k][5],sM[k][0],sM[k][2],sM[k][3],sM[k][4],sM[k][5])))
json.dump(out,open('t5_noinh.json','w'))

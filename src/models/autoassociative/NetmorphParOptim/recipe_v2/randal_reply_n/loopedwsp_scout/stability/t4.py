import numpy as np, rn, statistics as st
d=rn.load_run('s77777_LH_r1_f1','rawB_'); A=d['A']; M=rn.member_matrices('s77777','LH',A,1.0); cl,meta=rn.events_cues(d,A)
sm=rn.stored_measures(d,A); sel=[i for i,e in enumerate(meta) if e['kind'] in ('p75','p50','full') and not sm[i]['cont']]
for a in (0.95,0.9,0.85,0.8,0.75,0.7):
  for nm in (1.0,):
    R=rn.sim(M['XA']*a,M['XN']*a,[cl[i] for i in sel]); mm=rn.sim_measures(R,[meta[i] for i in sel],A)
    print('c=%.2f mem450 %s last %s complete %d/%d'%(a,sorted(x['mem450'] for x in mm)[::3],sorted(round(x['last']) for x in mm)[::3],sum(x['complete'] for x in mm),len(mm)))

"""Inhibition sensitivity: 7 explicit interneurons (the 7 that fire in the stored runs), all-to-all, Pyr->Int AMPA gPI nS/pair, Int->Pyr GABA gIP nS/pair (both free: not stored).
Question: is there an Int->Pyr strength at which the ignited state ends while 75% (and 50%) cues still complete?"""
import numpy as np, rn, json
from summ import summarize
res={}
for tag,pre in [('s77777_LH_r1_f1','rawB_'),('s66666_LH_r1_f1','rawB_'),('s77777_W70_r1_f1','rawC_'),('s66666_W70_r1_f1','rawC_')]:
    d=rn.load_run(tag,pre); A=d['A']; M=rn.member_matrices('s%d'%d['seed'],d['arm'],A,d['r']); cl,meta=rn.events_cues(d,A)
    for gPI in (1.,3.):
        for gIP in (0.,0.25,0.5,0.75,1.,1.5,2.,4.):
            R=rn.run_model(M,cl,gPI=gPI,gIP=gIP); s=summarize(rn.sim_measures(R[:,:,:],meta,A)); res['%s|%g|%g'%(tag,gPI,gIP)]=s
            print('%-18s gPI %g gIP %-4g'%(tag,gPI,gIP),' '.join('%s c%d rv%d L%.0f'%(k,v[0],v[2],v[5]) for k,v in s.items() if k in ('full','p75','p50')),flush=True)
json.dump(res,open('inh_scan.json','w'))

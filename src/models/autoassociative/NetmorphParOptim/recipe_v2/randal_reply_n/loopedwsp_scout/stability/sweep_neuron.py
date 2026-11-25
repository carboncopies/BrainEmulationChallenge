"""Predicted effect of reset and sAHP changes (fable-knobs arms and a wider grid) on the LH assembly of both models, r = 1, no inhibition term (see README for why).
Each arm simulated on all 27 stored events (fresh cell state per event: carry-over from the previous event is NOT modelled)."""
import numpy as np, rn, json, sys
from summ import summarize
arms={'N0':dict(reset='TOVM',sahp=(30.,300.,1.,2.)),'R(-55)':dict(reset='AFTER',Vreset=-55.),'R(-60)':dict(reset='AFTER',Vreset=-60.),'R(-52)':dict(reset='AFTER',Vreset=-52.),
 'S2':dict(reset='TOVM',sahp=(30.,1000.,2.,4.)),'RS2':dict(reset='AFTER',Vreset=-55.,sahp=(30.,1000.,2.,4.)),'RS3':dict(reset='AFTER',Vreset=-55.,sahp=(30.,1500.,3.,6.)),
 'S4':dict(reset='TOVM',sahp=(30.,1000.,4.,8.)),'S6':dict(reset='TOVM',sahp=(30.,1000.,6.,12.)),'S3d3':dict(reset='TOVM',sahp=(30.,1500.,3.,6.)),'S8':dict(reset='TOVM',sahp=(30.,1500.,8.,16.)),
 'S3_300':dict(reset='TOVM',sahp=(30.,300.,3.,6.)),'S6_300':dict(reset='TOVM',sahp=(30.,300.,6.,12.))}
out={}
for tag,pre in [('s77777_LH_r1_f1','rawB_'),('s66666_LH_r1_f1','rawB_'),('s77777_LH_r0.56_f1','rawB_'),('s66666_LH_r0.56_f1','rawB_')]:
    d=rn.load_run(tag,pre); A=d['A']; M=rn.member_matrices('s%d'%d['seed'],'LH',A,d['r']); cl,meta=rn.events_cues(d,A)
    for name,kw in arms.items():
        R=rn.sim(M['XA'],M['XN'],cl,**kw); mm=rn.sim_measures(R,meta,A); s=summarize(mm); out['%s|%s'%(tag,name)]=s
        print('%-20s %-8s'%(tag,name),' '.join('%s c%d rv%d m%.0f L%.0f'%(k,v[0],v[2],v[4],v[5]) for k,v in s.items() if k in ('full','p75','p50','p25')),flush=True)
json.dump(out,open('sweep_neuron.json','w'))

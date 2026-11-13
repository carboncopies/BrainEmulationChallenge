"""Probe: does ModelLoad honour per-pair AMPA W>1 / PeakG / kinetics edits and GABA kinetics? Sims A (original model) and B (patched probe copy). Deletes its own sims and the saved/patched models."""
import sys, json, os, numpy as np
sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe'); sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe_v2/inhibition_timing')
import recipelib as L
from patch_inh import *
OUTD='/home/johnjose/cos/netmorph_work/recipe_v2/inhibition_timing/'
pp=json.load(open(OUTD+'probe_pairs.json')); PI=pp['pi']
edits=[((a,b,0),e) for (a,b),e in zip(PI,[{}, {'W':1.0}, {'W':2.0}, {'G':2.94}, {'G':2.94,'W':1.0}, {'W':1.0,'Rise':0.2,'Decay':1.2}, {'W':1.0,'Rise':0.5,'Decay':6.0}, {'W':5.0}])]
spec=dict(gaba_W=2.5,gaba_rise=0.3,gaba_decay=3.3,ii_W=13.0,ii_decay=1.2)
PM='v2-arbor-S1-inh-probe'; RT='v2-arbor-S1-inh-probe-rt'
patch(PM,spec,edits)
NES,client=L.connect(); sims=[]; out=dict(spec=spec,edits=[[list(k),v] for k,v in edits])
def mk(n):
    c=NES.Simulation.Configuration(); c.Name=n; c.Seed=0; s=client.CreateSimulation(c); assert s.ID>=0; sims.append(s.ID); return s
def conn_pairs(sim,keys):
    conn=sim.GetConnectome(Pause_s=0.1); r={}
    for pre in range(len(conn['ConnectionTargets'])):
        for i,post in enumerate(conn['ConnectionTargets'][pre]):
            if (pre,int(post)) in keys: r.setdefault((pre,int(post)),[]).append((int(conn['ConnectionTypes'][pre][i]),round(float(conn['ConnectionWeights'][pre][i]),4),round(float(conn['ConnectionGPeakSum'][pre][i]),4)))
    return r
keys={tuple(p) for p in PI}
res={}; objs=[]
try:
  for tag,model in (('A_orig','v2-arbor-S10000'),('B_patched',PM)):
    s=mk('inhprobe-'+tag); objs.append(s)
    s.SetLIFCAbstractedFunctional(_AbstractedFunctional=True); s.SetLIFCPreciseSpikeTimes(_UsePreciseSpikeTimes=True); s.SetSTDP(_DoSTDP=False)
    s.ModelLoad(model)
    out['connectome_'+tag]={str(k):v for k,v in conn_pairs(s,keys).items()}
    if tag=='B_patched':
        try: out['modelsave']=str(s.ModelSave(RT))[:150]
        except Exception as e: out['modelsave']='ERR '+str(e)
    cues=[(float(20+40*i),int(a)) for i,(a,b) in enumerate(PI)]
    gt=pp['gaba_target']; t0=20+40*len(PI)
    cues.append((float(t0),gt)); cues+= [(float(t0+2.0),int(i)) for i in pp['gaba_pre']]
    r=s.SetSpecificAPTimes(cues); assert r.get('StatusCode',1)==0,r
    s.RecordAll(-1); s.RunAndWait(Runtime_ms=float(t0+60),Dt_ms=0.1,timeout_s=1500.0)
    rec=s.GetRecording()['Recording']; t=np.array(rec['t_ms'],float)
    sp=s.GetSpikeTimes()['SpikeTimes']
    res[tag]=dict(t=t,vm={int(k):np.array(v['Vm_mV'] if isinstance(v,dict) else v,float) for k,v in rec['neurons'].items() if int(k) in [b for a,b in PI]+[gt]},spk={int(k):[float(x) for x in v['tSpike_ms']] for k,v in sp.items() if len(v['tSpike_ms'])})
finally:
  for fn in (PM,RT):
    try: os.remove(D+fn); print('removed model',fn)
    except Exception as e: print('rm',fn,e)
  for s in objs:
    try: print('deleted',s.ID,s.DeleteResidentByID(),flush=True)
    except Exception as e: print('DELETE FAILED',s.ID,e)
out['sim_ids']=sims
# analysis (early window only, before recurrent cascades can reach the target)
A,B=res['A_orig'],res['B_patched']; t=A['t']
np.savez(OUTD+'probe_traces.npz',t=t,**{'%s_%d'%(k,n):v for k,R in (('A',A),('B',B)) for n,v in R['vm'].items()})
rows=[]
for i,(a,b) in enumerate(PI):
    t00=20+40*i; w=(t>=t00-0.05)&(t<t00+12); tt=t[w]-t00; row=dict(pair=[a,b],edit=edits[i][1])
    for nm,R in (('A',A),('B',B)):
        v=R['vm'][b][w]; d=v-v[0]
        row[nm+'_dV_at_3ms']=float(np.interp(3.0,tt,d)); row[nm+'_dV_at_4ms']=float(np.interp(4.0,tt,d)); row[nm+'_dV_at_2ms']=float(np.interp(2.0,tt,d)); row[nm+'_first_dV_gt_0.05ms']=float(tt[np.argmax(d>0.05)]) if (d>0.05).any() else None
        row[nm+'_ts_to_half_of_4ms']=None
    rows.append(row)
out['ampa_rows']=rows
gt=pp['gaba_target']; w=(t>=t0-2)&(t<t0+40)
out['gaba_post_vm']=dict(t=[round(float(x-t0),2) for x in t[w][::5]],A=[round(float(x),2) for x in A['vm'][gt][w][::5]],B=[round(float(x),2) for x in B['vm'][gt][w][::5]])
json.dump(out,open(OUTD+'probe_result.json','w'),indent=1,default=str)
for r in rows: print({k:(round(v,3) if isinstance(v,float) else v) for k,v in r.items()})
print('sims',sims,'modelsave',out['modelsave'])
print('gaba post t,A,B'); [print(a,b,c) for a,b,c in list(zip(out['gaba_post_vm']['t'],out['gaba_post_vm']['A'],out['gaba_post_vm']['B']))]

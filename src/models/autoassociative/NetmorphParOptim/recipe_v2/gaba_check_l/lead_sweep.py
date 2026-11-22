#!/usr/bin/env python3
"""Timing sweep on E4 s33333 (R3-programmed, D42 group 0, c=0): k interneurons (strongest summed GABA onto the group's non-cue members first) are forced to spike at DELTA ms after cue onset;
does the programmed non-cue member still fire (within 10 ms of cue onset)? Variants: GABA weight x1 / x2 / x2.5 (DIAGNOSTIC copies of the model file, GABA Weight only, deleted afterwards). PATCHED instance only.
usage: lead_sweep.py FACTOR   (1, 2, 2.5)"""
import sys, os, shutil, json, numpy as np
sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe_v2/headline_i'); sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe'); sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe_v2/gaba_patch')
import dyn2 as H, recipelib as L
from gabafile import RDT, locate
HERE='/home/johnjose/cos/netmorph_work/recipe_v2/gaba_check_l/'
MD='/home/johnjose/BrainGenix/wt/linefix-instance/out/Admonishing/Models/'
SEED='V1n20_s33333'; NP=96; W=0.2
f=float(sys.argv[1]); model=H.MODELS[SEED]; copy=None
if f!=1.0:
    copy='v2-gabachk-s33333-x%s'%str(f).replace('.','p'); assert not os.path.exists(MD+copy)
    shutil.copyfile(MD+model,MD+copy); cls,h,off=locate(MD+copy)
    rec=np.memmap(MD+copy,dtype=RDT,mode='r+',offset=off,shape=(h['Rec'],)); m=rec['NT']==1; rec['W'][m]=(rec['W'][m]*np.float32(f)).astype('<f4'); rec.flush(); print('patched',int(m.sum()),'GABA records x',f,flush=True)
    model=copy
D=L.Dump(H.DUMPS[SEED]); GA=D.GA[NP:,:NP]*W
groups=H.load_groups(H.HERE+'groups_D42_%s.json'%SEED); mem,cue=groups[0]; nc=[m for m in mem if m not in cue]
rank=np.argsort(-GA[:,nc].sum(1))
plist=H.pair_list(D,groups,0.0)
DELTAS=[0,1,2,3,4,5,6,8]; KS=[1,3,20]
NES,client=H.connect(); cf=NES.Simulation.Configuration(); cf.Name='gabachk-lead-x%s'%f; cf.Seed=0; sim=client.CreateSimulation(cf); sid=sim.ID; assert sid>=0
out=dict(factor=f,model=model,sim_id=sid,group=dict(members=mem,cue=cue,noncue=nc),int_rank=[int(i) for i in rank])
try:
    sim.SetLIFCAbstractedFunctional(_AbstractedFunctional=True); sim.SetLIFCPreciseSpikeTimes(_UsePreciseSpikeTimes=True); sim.SetSTDP(_DoSTDP=False)
    sim.ModelLoad(model)
    conn=sim.GetConnectome(Pause_s=0.1); gw=sorted({round(float(w_),3) for pre in D.its for w_,t in zip(conn['ConnectionWeights'][pre],conn['ConnectionTypes'][pre]) if int(t)==2}); out['gaba_weights_on_load']=gw
    rep=L.apply_pairs(sim,plist); assert rep['n_readback_mismatch']==0,rep
    sim.SetSTDP(_DoSTDP=False)
    ev=[]; cues=[]; t=100.0
    ev.append(dict(k=0,delta=None,t=t,ints=[])); 
    for o,cc in zip(H.CUE_OFFS,cue): cues.append((t+o,cc))
    t+=400.0
    for k in KS:
        for d in DELTAS:
            ev.append(dict(k=k,delta=d,t=t,ints=[int(NP+i) for i in rank[:k]]))
            for o,cc in zip(H.CUE_OFFS,cue): cues.append((t+o,cc))
            for i in rank[:k]: cues.append((t+d,NP+int(i)))
            t+=400.0
    out['events']=ev
    r=sim.SetSpecificAPTimes([(float(a),int(b)) for a,b in cues]); assert r.get('StatusCode',1)==0,r
    sim.RecordAll(-1); sim.RunAndWait(Runtime_ms=float(t+100),Dt_ms=1.0,timeout_s=3000.0)
    sp=sim.GetSpikeTimes()['SpikeTimes']; spikes={int(k):sorted(float(x) for x in v['tSpike_ms']) for k,v in sp.items()}
    res=[]
    for e in ev:
        t0=e['t']; fired=[m for m in nc if any(t0<=x<t0+10 for x in spikes.get(m,[]))]
        first=[round(min(x-t0 for x in spikes[m] if t0<=x<t0+10),2) for m in fired]
        ints=sorted((i-NP,round(min(x-t0 for x in spikes[i] if t0<=x<t0+100),2)) for i in range(NP,D.N) if any(t0<=x<t0+100 for x in spikes.get(i,[])))
        res.append(dict(k=e['k'],delta=e['delta'],noncue_fired=len(fired),first_ms=first,ints_in_window=ints))
        print('k',e['k'],'delta',e['delta'],'noncue fired',len(fired),'/',len(nc),first,flush=True)
    out['res']=res
    json.dump(out,open(HERE+'lead_sweep_x%s.json'%str(f).replace('.','p'),'w'),default=float)
finally:
    try: print('deleted',sid,sim.DeleteResidentByID(),flush=True)
    except Exception as e: print('DELETE FAILED',sid,e,flush=True)
    if copy and os.path.exists(MD+copy): os.remove(MD+copy); print('removed model copy',copy,flush=True)

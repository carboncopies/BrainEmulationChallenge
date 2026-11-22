#!/usr/bin/env python3
"""Unit tests on a grown E4 model (s33333, headline_i), PATCHED instance only (API 8010). usage: unit_e4.py MODE SG   MODE = nat | prog ; SG = 0 (GABA x1) | 1 (GABA silenced as in dyn2.py)
nat  : unprogrammed network. W1 (t=100): ONE interneuron i* (largest single Int->Pyr pair) fires 10 spikes at 100 Hz, record Vm of all its Pyr targets (IPSP at rest).
       W2 (t=600): the targets' Pyr presynaptic cells fire 3 spikes (0,3,6 ms) to depolarise them, and i* fires the same 10-spike train from t=600 (IPSP on a depolarised cell).
prog : R3-programmed network (dyn2.pair_list, c=0, design D42 group 0). Cue 4 cells (0..1.5 ms) + k interneurons forced to spike AT the cue onset (strongest summed GABA onto the group's non-cue members first), k in KS. Does the programmed non-cue member still fire?"""
import sys, json, numpy as np
sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe_v2/headline_i'); sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe')
import dyn2 as H, recipelib as L
HERE='/home/johnjose/cos/netmorph_work/recipe_v2/gaba_check_l/'
SEED='V1n20_s33333'; NP=96; W=0.2
mode=sys.argv[1]; sg=sys.argv[2]=='1'
D=L.Dump(H.DUMPS[SEED]); N=D.N
GA=D.GA[NP:,:NP]*W           # interneuron x pyr pair conductance (nS)
KS=[0,1,2,3,5,8,12,20]
NES,client=H.connect()
cf=NES.Simulation.Configuration(); cf.Name='gabachk-%s-%d'%(mode,int(sg)); cf.Seed=0
sim=client.CreateSimulation(cf); sid=sim.ID; assert sid>=0; print('sim',sid,flush=True)
out=dict(mode=mode,sg=sg,seed=SEED,sim_id=sid)
try:
    sim.SetLIFCAbstractedFunctional(_AbstractedFunctional=True); sim.SetLIFCPreciseSpikeTimes(_UsePreciseSpikeTimes=True); sim.SetSTDP(_DoSTDP=False)
    sim.ModelLoad(H.MODELS[SEED])
    if mode=='prog':
        groups=H.load_groups(H.HERE+'groups_D42_%s.json'%SEED); plist=H.pair_list(D,groups,0.0)
        rep=L.apply_pairs(sim,plist); assert rep['n_readback_mismatch']==0,rep
    if sg:
        conn=sim.GetConnectome(Pause_s=0.1); gp=[]
        for pre in D.its:
            for post,t in zip(conn['ConnectionTargets'][pre],conn['ConnectionTypes'][pre]):
                if int(t)==2: gp.append((pre,int(post)))
        for a,b in gp: sim.SetPrePostStrength(a,b,0.0)
    conn=sim.GetConnectome(Pause_s=0.1)
    gw=[float(w_) for pre in D.its for w_,t in zip(conn['ConnectionWeights'][pre],conn['ConnectionTypes'][pre]) if int(t)==2]
    out['gaba_pairs_in_connectome']=len(gw); out['gaba_nonzero_weights']=sum(1 for w_ in gw if w_!=0); out['gaba_weight_set']=sorted({round(w_,3) for w_ in gw})
    print(out,flush=True)
    sim.SetSTDP(_DoSTDP=False)
    cues=[]
    if mode=='nat':
        istar=int(np.argmax(GA.max(1))); ii=NP+istar; tg=[int(p) for p in np.where(GA[istar]>0)[0]]; tg=sorted(tg,key=lambda p:-GA[istar,p])
        top=tg[:6]; pre=sorted({int(a) for p in top for a in np.argsort(-D.G[:NP,p])[:12] if D.G[a,p]>0 and a not in top})
        out.update(istar=ii,targets=tg,top_targets=top,top_pair_g=[float(GA[istar,p]) for p in top],pre_cells=pre)
        for k in range(10): cues.append((100.0+10*k,ii))
        for t0 in (600.0,): 
            for k in range(10): cues.append((t0+10*k,ii))
            for a in pre:
                for o in (0,3,6): cues.append((t0+o,a))
        run_ms=900.0
    else:
        mem,cue=groups[0]; nc=[m for m in mem if m not in cue]
        rank=np.argsort(-GA[:,nc].sum(1)); out.update(group=dict(members=mem,cue=cue,noncue=nc),int_rank=[int(i) for i in rank],ceiling_gaba_on_noncue=[float(GA[:,m].sum()) for m in nc],
             gaba_pair_g_onto_noncue=[[float(GA[i,m]) for m in nc] for i in rank])
        t=1200.0; ev=[]
        for k in KS:
            ev.append(dict(k=k,t=t,ints=[int(NP+i) for i in rank[:k]]))
            for o,cc in zip(H.CUE_OFFS,cue): cues.append((t+o,cc))
            for i in rank[:k]: cues.append((t,NP+int(i)))
            t+=400.0
        out['events']=ev; run_ms=t+100
    r=sim.SetSpecificAPTimes([(float(a),int(b)) for a,b in [(x[0],x[1]) for x in cues]]); assert r.get('StatusCode',1)==0,r
    sim.RecordAll(-1); sim.RunAndWait(Runtime_ms=float(run_ms),Dt_ms=0.1,timeout_s=3000.0)
    rec=sim.GetRecording()['Recording']; sp=sim.GetSpikeTimes()['SpikeTimes']; tt=np.array(rec['t_ms'],float)
    spikes={int(k):sorted(float(x) for x in v['tSpike_ms']) for k,v in sp.items()}
    out['spikes']={k:v for k,v in spikes.items() if v}
    if mode=='nat':
        vm={}
        for p in out['targets']:
            v=rec['neurons'][str(p)]['Vm_mV'] if str(p) in rec['neurons'] else rec['neurons'][p]['Vm_mV']
            vm[p]=np.array(v,float)
        out['vm_sample']={str(p):[round(float(x),3) for x in vm[p][(tt>=95)&(tt<215)][::10]] for p in top}
        out['vm_sample2']={str(p):[round(float(x),3) for x in vm[p][(tt>=595)&(tt<715)][::10]] for p in top}
        rows=[]
        for p in out['targets']:
            for nm,t0 in (('W1',100.0),('W2',600.0)):
                w_=(tt>=t0-5)&(tt<t0+110); base=float(vm[p][(tt>=t0-20)&(tt<t0-2)].mean()); mn=float(vm[p][w_].min()); mx=float(vm[p][w_].max())
                rows.append(dict(target=p,win=nm,pair_g=float(GA[istar,p-0]),baseline=round(base,3),min=round(mn,3),max=round(mx,3),dmin=round(mn-base,3),dmax=round(mx-base,3),spikes=[round(x,2) for x in spikes.get(p,[]) if t0-5<=x<t0+110]))
        out['rows']=rows
    json.dump(out,open(HERE+'unit_e4_%s_sg%d.json'%(mode,int(sg)),'w'),default=float)
    if mode=='prog':
        for e in ev:
            fired=[m for m in nc if any(e['t']<=x<e['t']+10 for x in spikes.get(m,[]))]
            print('k',e['k'],'noncue fired',len(fired),'/',len(nc),'ints spiking in window',sum(1 for i in range(NP,N) if any(e['t']<=x<e['t']+100 for x in spikes.get(i,[]))),flush=True)
    else:
        for r_ in out['rows'][:40]: print(r_)
finally:
    try: print('deleted',sid,sim.DeleteResidentByID(),flush=True)
    except Exception as e: print('DELETE FAILED',sid,e,flush=True)

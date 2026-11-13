"""usage: run_inh.py TAG VARIANT PAIRSCFG MODE KIND   VARIANT in P1,P2,P3,P1u ; PAIRSCFG = c0|c0.15|c0.25|c0.5 ; MODE = full|SG|IS ; KIND as ripple_S1_R3/run_r3.py.
Programs R3 pair lists (groups of the variant), with Pyr->Int g_peak_sum scaled by s (weight 1 => conductance = s*g). SG: zero all GABA weights; IS: Pyr->Int weight 0."""
import sys, json, os
sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe_v2/ripple_S1_R3')
import r3lib
from r3lib import *
HERE='/home/johnjose/cos/netmorph_work/recipe_v2/inhibition_timing/'
KIN=dict(gaba_rise=0.3,gaba_decay=3.3)
VAR={'P1':dict(model='v2-arbor-S1-inhP1',spec=dict(pi_G=0.6494,pi_W=1.0,gaba_W=2.5,**KIN),s=0.6494,groups='P1'),
     'P2':dict(model='v2-arbor-S1-inhP2',spec=dict(pi_G=0.6494,pi_W=1.0,gaba_W=5.0,**KIN),s=0.6494,groups='P1'),
     'P3':dict(model='v2-arbor-S1-inhP3',spec=dict(pi_G=1.9481,pi_W=1.0,gaba_W=2.5,**KIN),s=1.9481,groups='P3'),
     'P1u':dict(model='v2-arbor-S1-inhP1u',spec=dict(pi_G=1.0,pi_W=1.0,gaba_W=2.5,**KIN),s=1.0,groups='R3')}
tag,vn,cfg,mode,kind=sys.argv[1:6]; V=VAR[vn]; s=V['s']; gx=V['spec']['gaba_W']
def load_pairs_inh(_name):
    fn=(('/home/johnjose/cos/netmorph_work/recipe_v2/fable_design_S1/pairs_R3_%s.json'%cfg) if V['groups']=='R3' else HERE+'pairs_%s_%s.json'%(V['groups'],cfg))
    d=json.load(open(fn)); groups=[(sorted(g['members']),sorted(g['cue'])) for g in d['groups']]; raw=[]
    for a,b,c,g,r in d['pairs']:
        if b>=96: g=g*s; c=0.0 if mode=='IS' else g
        raw.append([a,b,c,g,r])
    return groups,[(int(a),int(b),float(c),float(g)) for a,b,c,g,r in raw],raw
r3lib.load_pairs=load_pairs_inh
def fresh_copy_i(NES, client, name, ref_pairs):
    c=NES.Simulation.Configuration(); c.Name=name; c.Seed=0
    sim=client.CreateSimulation(c); assert sim.ID>=0
    sim.SetLIFCAbstractedFunctional(_AbstractedFunctional=True); sim.SetLIFCPreciseSpikeTimes(_UsePreciseSpikeTimes=True); sim.SetSTDP(_DoSTDP=False)
    sim.ModelLoad(V['model'])
    n=len(sim.GetSomaPositions().get('SomaCenters',[]))
    conn=sim.GetConnectome(Pause_s=0.1); ampa={}; wa=set(); wg=set(); piw=set()
    for pre in range(len(conn['ConnectionTargets'])):
        for i,post in enumerate(conn['ConnectionTargets'][pre]):
            t=int(conn['ConnectionTypes'][pre][i]); w=round(float(conn['ConnectionWeights'][pre][i]),3)
            if t==2: wg.add(w)
            else: wa.add(w)
            if t==1:
                ampa[(pre,int(post))]=float(conn['ConnectionGPeakSum'][pre][i])
                if post>=96: piw.add(w)
    miss=[k for k in ref_pairs if k not in ampa]
    gbad=[k for k in ref_pairs if k in ampa and abs(ampa[k]-ref_pairs[k])>1e-3*max(1.0,ref_pairs[k])]
    ok=(n==N and not miss and not gbad and wa=={0.2,1.0} and wg=={round(0.2*gx,3)} and piw=={1.0})
    return sim, dict(sim_id=sim.ID,model=V['model'],n_neurons=n,ampa_nmda_weights_on_load=sorted(wa),gaba_weights_on_load=sorted(wg),pyrint_w_on_load=sorted(piw),pairs_missing=len(miss),g_mismatch=len(gbad),loaded_ok=bool(ok))
r3lib.fresh_copy=fresh_copy_i
NES,client=L.connect()
p=kind.split(':'); sg=(mode=='SG')
if p[0]=='single': e=single_run(NES,client,tag,'x',sg)
else:
    rec='rec' in p[1:]; q=[x for x in p if x!='rec']
    e=ripple_run(NES,client,tag,'x',sg,[int(c) for c in q[1]],float(q[2]),float(q[3]),cue3=(int(q[4]) if len(q)>4 else None),record=rec)
e.update(name=tag,variant=vn,cfg=cfg,mode=mode,scale=s,gaba_x=gx,spec=V['spec'])
json.dump(e,open(HERE+'raw_%s.json'%tag,'w'),separators=(',',':'))

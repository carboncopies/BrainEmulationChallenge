"""usage: runB.py TAG MODEL S GX BGW C SG(0|1) KIND [SRC]  -- R3 recipe with background weight BGW and per-pair cap C (nS); Pyr->Int programmed conductance = S x g_peak(R3 weight 1).
KIND as ripple_S1_R3/run_r3.py (single | rip:order:spacing:dt[:cue3grp]). Groups = original R3 groups unless env GROUPS=path (pairs groups json) . -> raw_TAG.json"""
import sys, json, os
sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe_v2/ripple_S1_R3')
sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe_v2/fable_design_S1'); sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import r3lib
from r3lib import *
import design as dz
HERE='/home/johnjose/cos/netmorph_work/recipe_v2/option_B_scaled/'
tag,model,s,gx,bgw,c,sg,kind=sys.argv[1],sys.argv[2],float(sys.argv[3]),float(sys.argv[4]),float(sys.argv[5]),float(sys.argv[6]),sys.argv[7]=='1',sys.argv[8]
SEED=os.environ.get('SEED')
if SEED:   # second seed network: swap dump/groups in all modules that cached the S1 ones
    RB='/home/johnjose/cos/netmorph_work/recipe_v2/robustness_S1/'
    nd=dz.L.Dump(RB+'grow_S1-seed%s/viz/sample_0000.json'%SEED)
    import slib
    for m in (dz,r3lib,slib):
        for k,v in (('D',nd),('G',nd.G),('dump',nd),('N',nd.N),('NP',len(nd.pyr)),('G_',None)):
            if v is not None and hasattr(m,k): setattr(m,k,v)
    if os.environ.get('OVL'):
        import ovl_build; ovl_build.install(dz); groups=dz.load_groups(os.environ['OVL'])
    else: groups=dz.load_groups(RB+'designs/groups_s%s_K4.json'%SEED)
elif os.environ.get('OVL'):
    import ovl_build; ovl_build.install(dz); groups=dz.load_groups(os.environ['OVL'])
else: groups=dz.load_groups()
kw=dict(T=16.5,Lnn=8,Lnc=8); 
if c>0: kw.update(bg=bgw,pc=c)
pf=HERE+'pairs_tmp_%s.json'%tag; dz.export_pairs(groups,pf,**kw)
def load_pairs_B(_n):
    d=json.load(open(pf)); gr=[(sorted(g['members']),sorted(g['cue'])) for g in d['groups']]; raw=[]
    for a,b,cc,g,r in d['pairs']:
        if b>=96: g=g*s; cc=g
        raw.append([a,b,cc,g,r])
    return gr,[(int(a),int(b),float(cc),float(g)) for a,b,cc,g,r in raw],raw
r3lib.load_pairs=load_pairs_B
gw=min(gx,5.0)
def fresh_copy_B(NES, client, name, ref_pairs):
    cf=NES.Simulation.Configuration(); cf.Name=name; cf.Seed=0
    sim=client.CreateSimulation(cf); assert sim.ID>=0
    sim.SetLIFCAbstractedFunctional(_AbstractedFunctional=True); sim.SetLIFCPreciseSpikeTimes(_UsePreciseSpikeTimes=True); sim.SetSTDP(_DoSTDP=False)
    try: sim.ModelLoad(model)
    except Exception:
        sim.DeleteResidentByID(); raise
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
    ok=(n==N and not miss and not gbad and wa=={0.2,1.0} and wg=={round(0.2*gw,3)} and piw=={1.0})
    return sim, dict(sim_id=sim.ID,model=model,n_neurons=n,ampa_nmda_weights_on_load=sorted(wa),gaba_weights_on_load=sorted(wg),pyrint_w_on_load=sorted(piw),pairs_missing=len(miss),g_mismatch=len(gbad),loaded_ok=bool(ok))
r3lib.fresh_copy=fresh_copy_B
NES,client=L.connect()
p=kind.split(':')
try:
    if p[0]=='single': e=single_run(NES,client,tag,'x',sg)
    else:
        rec='rec' in p[1:]; q=[x for x in p if x!='rec']
        e=ripple_run(NES,client,tag,'x',sg,[int(x) for x in q[1]],float(q[2]),float(q[3]),cue3=(int(q[4]) if len(q)>4 else None),record=rec)
    e.update(name=tag,s=s,gaba_x=gx,bgw=bgw,c=c,sg=sg,model=model,kind_arg=kind)
    json.dump(e,open(HERE+'raw_%s.json'%tag,'w'),separators=(',',':'))
finally:
    os.remove(pf)

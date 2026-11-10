import json, sys, time
MODE=sys.argv[1]; assert MODE in ('off','on')
W='/home/johnjose/cos/netmorph_work'
OUT=W+'/fable_loop/r2_it2/stdp_%s/'%MODE
sys.path.insert(0, W+'/bec/src/models/autoassociative/NetmorphParOptim/weight_space')
from reservoir import Reservoir
import BrainGenix.NES as NES
DUMP=W+'/fable_loop/it1/viz_a/sample_0000.json'
r=Reservoir(DUMP); G=r.G[1]
pyr=[int(i) for i in r.pyr]; its=[int(i) for i in r.int]
assert pyr==list(range(67)) and its==list(range(67,94))
PP=[(a,b) for a in pyr for b in pyr if a!=b and G[a,b]>0]
PI=[(a,b) for a in pyr for b in its if G[a,b]>0]
groups=[([4,18,20,22,29,51,59,63],[22,29,51,63]),([8,27,33,39,41,42,44,60],[8,27,33,44]),([0,12,17,19,21,37,49,50],[12,17,19,50])]
grp={m:k for k,(mem,_) in enumerate(groups) for m in mem}
wpost={}
for k,(mem,cue) in enumerate(groups):
    for m in [m for m in mem if m not in cue]:
        S=sum(float(G[c,m]) for c in cue); wpost[m]=1.0 if S==0 else min(1.0,27.44/S)
        for c in cue:
            if G[c,m]>0: assert G[c,m]>=4.5
cueset={c:k for k,(mem,cue) in enumerate(groups) for c in cue}
def Cgi(k,i): return sum(float(G[c,i]) for c in groups[k][1])
def inhw(p,i):
    if p in cueset:
        C=Cgi(cueset[p],i); assert C>0; return min(1.0,10.0/C)
    return 1.0
T4=18; bg=0
ops=[]
for a,b in PP:
    g=float(G[a,b])
    if a in grp and b in grp and grp[a]==grp[b]:
        cue=groups[grp[a]][1]; ac=a in cue; bc=b in cue
        if ac and not bc: v=T4/4
        elif not ac and not bc: v=wpost[b]*g
        elif not ac and bc: v=g
        else: v=0.0
    else: v=bg*g
    ops.append([a,b,float(v)])
for a,b in PI: ops.append([a,b,float(G[a,b])*inhw(a,b)])
dump=json.load(open(DUMP)); pd={(x['pre'],x['post'],x['type']):x['g_peak_sum'] for x in dump['connections']}
N=len(dump['neurons'])
for a,b,v in ops: assert (a,b,1) in pd and 0<=v<=pd[(a,b,1)]+1e-9
assert len(ops)==len(PP)+len(PI)
pat={1:lambda c:c[:3],2:lambda c:c,3:lambda c:c[:3],4:lambda c:c[1:],5:lambda c:c[:2],6:lambda c:c,7:lambda c:c[:3],8:lambda c:c[:2],9:lambda c:c,10:lambda c:c,11:lambda c:c,12:lambda c:c[:2]}
EV=[]; t=20
for gi in range(3):
    for k in range(1,13):
        EV.append((t,gi,'e%d'%k,pat[k](groups[gi][1]))); t+=2000
assert EV[-1][0]==70020 or True
t=72020
for gi in range(3): EV.append((t,gi,'final',list(groups[gi][1]))); t+=2000
assert len(EV)==39
json.dump(EV,open(OUT+'events.json','w'))
SEG=[(0,4000),(4000,24000),(24000,48000),(48000,72000),(72000,78000)]
cfg=NES.Client.Configuration(); cfg.Mode=NES.Client.Modes.Remote; cfg.Host='localhost'; cfg.Port=8000; cfg.UseHTTPS=False
cfg.AuthenticationMethod=NES.Client.Authentication.Password; cfg.Username='Admonishing'; cfg.Password='Instruction'
client=NES.Client.Client(cfg); assert client.IsReady()
def snap(sim):
    conn=sim.GetConnectome(Pause_s=0.1); L=[]
    for pre in range(len(conn['ConnectionTargets'])):
        for i,post in enumerate(conn['ConnectionTargets'][pre]):
            L.append([pre,int(post),int(conn['ConnectionTypes'][pre][i]),float(conn['ConnectionWeights'][pre][i]),float(conn['ConnectionGPeakSum'][pre][i])])
    return L
def verify(sim):
    n=len(sim.GetSomaPositions().get('SomaCenters',[])); L=snap(sim); mism=0; w=set()
    for pre,post,ty,wt,g in L:
        w.add(round(wt,3))
        if (pre,post,ty) not in pd or abs(pd[(pre,post,ty)]-g)>1e-3*max(1.0,g): mism+=1
    ok=n==N==94 and mism==0 and len(L)==len(pd)==7370 and w=={0.2}
    print('VERIFY neurons',n,'connections',len(L),'mismatches',mism,'weights',sorted(w),'OK' if ok else 'FAIL',flush=True); return ok
c=NES.Simulation.Configuration(); c.Name='fable-r2it2-stdp%s-copy133'%MODE; c.Seed=0
sim=client.CreateSimulation(c); ID=sim.ID; print('NEW SIM ID',ID,flush=True)
open(OUT+'sim_id.txt','w').write(str(ID)); assert ID>140
sim.SetLIFCAbstractedFunctional(_AbstractedFunctional=True)
sim.SetLIFCPreciseSpikeTimes(_UsePreciseSpikeTimes=True)
print('ModelLoad',sim.ModelLoad('fable-it1a-sim133'),flush=True)
assert verify(sim)
assert sim.ID==ID>140
codes=[]
for s in range(0,len(ops),500):
    ch=ops[s:s+500]; r_=sim.BatchSetPrePostStrength([o[0] for o in ch],[o[1] for o in ch],[o[2] for o in ch])
    assert r_.get('StatusCode',1)==0,r_; codes.append(r_['StatusCode'])
print('ops',len(ops),'codes',codes,flush=True)
print('SetSTDP',sim.SetSTDP(_DoSTDP=(MODE=='on')),flush=True)
snaps={'W0':snap(sim)}
print('RecordAll',sim.RecordAll(-1),flush=True)
out={'sim_id':ID,'segments':[],'ops_codes':codes}
t00=time.time()
for k,(s,e) in enumerate(SEG,1):
    assert sim.ID==ID
    pairs=[(float(t),int(n)) for t,gi,lab,cs in EV if s<=t<e for n in cs]
    r2=sim.SetSpecificAPTimes(pairs); print('seg',k,'SetSpecificAPTimes',r2,'n',len(pairs),flush=True)
    sim.RunAndWait(Runtime_ms=float(e-s),Dt_ms=1.0,timeout_s=900.0)
    st=sim.GetStatus(); sp=sim.GetSpikeTimes()
    print(' simtime',st['InSimulationTime_ms'],flush=True)
    snaps['W%d'%k]=snap(sim)
    out['segments'].append({'k':k,'cue_resp':r2,'sim_time_ms':st['InSimulationTime_ms'],'spikes':sp})
    json.dump(out,open(OUT+'out.json','w')); json.dump(snaps,open(OUT+'snaps.json','w'))
out['wall_s']=time.time()-t00; json.dump(out,open(OUT+'out.json','w')); print('wall_s',out['wall_s'])

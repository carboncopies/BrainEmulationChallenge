import argparse, json, time
import BrainGenix.NES as NES
P=argparse.ArgumentParser(); P.add_argument('-SimID',type=int,required=True); P.add_argument('-dump',required=True)
P.add_argument('-phases',required=True); P.add_argument('-out',required=True); P.add_argument('-stop_after',type=int,default=99); P.add_argument('-start',type=int,default=0)
A=P.parse_args()
C3_ID=int(open('/home/johnjose/cos/netmorph_work/fable_loop/it3/C3_id.txt').read().strip())
assert C3_ID>135 and A.SimID==C3_ID, 'refusing: only C3 allowed'
cfg=NES.Client.Configuration(); cfg.Mode=NES.Client.Modes.Remote; cfg.Host='localhost'; cfg.Port=8000; cfg.UseHTTPS=False
cfg.AuthenticationMethod=NES.Client.Authentication.Password; cfg.Username='Admonishing'; cfg.Password='Instruction'
client=NES.Client.Client(cfg); assert client.IsReady()
c=NES.Simulation.Configuration(); c.Name='attach'; c.Seed=0
sim=client.CreateSimulation(c,_Create=False); sim.ID=A.SimID
dump=json.load(open(A.dump)); pd={(x['pre'],x['post'],x['type']):x['g_peak_sum'] for x in dump['connections']}
ph=json.load(open(A.phases))['phases']
for p in ph:
    for a,b,v in p['ops']: assert (a,b,1) in pd and 0<=v<=pd[(a,b,1)]+1e-9
out={'sim_id':A.SimID,'phases':[]}
if A.start>0:
    out=json.load(open(A.out)); out['phases']=out['phases'][:A.start]
def save(): json.dump(out,open(A.out,'w'))
print('STDP',sim.SetSTDP(_DoSTDP=False))
if A.start==0: print('RecordAll',sim.RecordAll(-1))
t00=time.time(); prev_end=0
if A.start>0: prev_end=ph[A.start-1]['end_ms']
for k,p in enumerate(ph):
    if k<A.start: continue
    ops=p['ops']; codes=[]
    for s in range(0,len(ops),500):
        ch=ops[s:s+500]
        r=sim.BatchSetPrePostStrength([o[0] for o in ch],[o[1] for o in ch],[o[2] for o in ch])
        assert r.get('StatusCode',1)==0,'batch failed %r'%r; codes.append(r['StatusCode'])
    pairs=[(float(t),int(n)) for t,ids in p['cues'] for n in ids]
    r2=sim.SetSpecificAPTimes(pairs); print(p['name'],'ops',len(ops),'codes',codes,'cues',r2,flush=True)
    dur=p['end_ms']-prev_end; prev_end=p['end_ms']
    sim.RunAndWait(Runtime_ms=float(dur),Dt_ms=1.0,timeout_s=600.0)
    st=sim.GetStatus(); sp=sim.GetSpikeTimes()
    print(' simtime',st['InSimulationTime_ms'],flush=True)
    out['phases'].append({'name':p['name'],'n_ops':len(ops),'codes':codes,'cue_resp':r2,'sim_time_ms':st['InSimulationTime_ms'],'spikes':sp}); save()
    if k+1>=A.stop_after: print('stopping after phase',k+1); break
if len(out['phases'])==len(ph):
    conn=sim.GetConnectome(Pause_s=0.1); cls={}
    for pre in range(len(conn['ConnectionTargets'])):
        for i,post in enumerate(conn['ConnectionTargets'][pre]):
            t=int(conn['ConnectionTypes'][pre][i]); pp=pre<67; qp=int(post)<67
            key=('pyr' if pp else 'int')+'->'+('pyr' if qp else 'int')+' type%d'%t
            cls.setdefault(key,set()).add(round(float(conn['ConnectionWeights'][pre][i]),4))
    out['final_weights']={k:sorted(v) for k,v in cls.items()}; print(out['final_weights'])
out['wall_s']=time.time()-t00; save()

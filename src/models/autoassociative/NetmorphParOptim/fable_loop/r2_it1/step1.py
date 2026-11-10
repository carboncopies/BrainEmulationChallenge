import json, sys, time
ARM='a'
W='/home/johnjose/cos/netmorph_work/fable_loop/'
import BrainGenix.NES as NES
DUMP=W+'it1/viz_%s/sample_0000.json'%ARM
cfg = NES.Client.Configuration()
cfg.Mode = NES.Client.Modes.Remote; cfg.Host='localhost'; cfg.Port=8000; cfg.UseHTTPS=False
cfg.AuthenticationMethod = NES.Client.Authentication.Password; cfg.Username='Admonishing'; cfg.Password='Instruction'
client = NES.Client.Client(cfg); assert client.IsReady()
dump=json.load(open(DUMP)); N=len(dump['neurons'])
pd={(c['pre'],c['post'],c['type']):c['g_peak_sum'] for c in dump['connections']}
def verify(sim,label):
    somas=sim.GetSomaPositions(); n=len(somas.get('SomaCenters',[]))
    conn=sim.GetConnectome(Pause_s=0.1); mism=0;nc=0;w=set()
    for pre in range(len(conn['ConnectionTargets'])):
        for i,post in enumerate(conn['ConnectionTargets'][pre]):
            key=(pre,int(post),int(conn['ConnectionTypes'][pre][i])); nc+=1
            w.add(round(float(conn['ConnectionWeights'][pre][i]),3)); g=float(conn['ConnectionGPeakSum'][pre][i])
            if key not in pd or abs(pd[key]-g)>1e-3*max(1.0,g): mism+=1
    ok = n==N==94 and mism==0 and nc==len(pd) and w=={0.2}
    print(label,'neurons',n,'conns',nc,'dump_conns',len(pd),'mismatch',mism,'weights',sorted(w),'OK' if ok else 'FAIL',flush=True)
    return ok
MODEL={'a':'fable-it1a-sim133','b':'fable-it1b-sim134'}[ARM]
c=NES.Simulation.Configuration(); c.Name='fable-r2it1-jitter-copy133'; c.Seed=0
C=client.CreateSimulation(c); print('NEW SIM ID',C.ID,flush=True); assert C.ID>140
open(W+'r2_it1/C_id.txt','w').write(str(C.ID))
C.SetLIFCAbstractedFunctional(_AbstractedFunctional=True)
C.SetLIFCPreciseSpikeTimes(_UsePreciseSpikeTimes=True)
C.SetSTDP(_DoSTDP=False)
r=C.ModelLoad(MODEL); print('ModelLoad',r,flush=True)
print('verify C', verify(C,'simC'))

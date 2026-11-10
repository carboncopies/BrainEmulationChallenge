import json, sys, time
import BrainGenix.NES as NES
DUMP='/home/johnjose/cos/netmorph_work/fable_loop/it1/viz_a/sample_0000.json'
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
c=NES.Simulation.Configuration(); c.Name='fable-it3-copy133'; c.Seed=0
C=client.CreateSimulation(c); print('NEW SIM ID',C.ID,flush=True)
C.SetLIFCAbstractedFunctional(_AbstractedFunctional=True)
C.SetLIFCPreciseSpikeTimes(_UsePreciseSpikeTimes=True)
C.SetSTDP(_DoSTDP=False)
r=C.ModelLoad('fable-it1a-sim133'); print('ModelLoad',r,flush=True)
print('verify C', verify(C,'simC'))

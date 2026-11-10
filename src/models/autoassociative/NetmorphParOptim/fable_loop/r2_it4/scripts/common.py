import json
import BrainGenix.NES as NES
W='/home/johnjose/cos/netmorph_work/fable_loop/r2_it4/'
def client():
    cfg = NES.Client.Configuration()
    cfg.Mode = NES.Client.Modes.Remote; cfg.Host='localhost'; cfg.Port=8000; cfg.UseHTTPS=False
    cfg.AuthenticationMethod = NES.Client.Authentication.Password; cfg.Username='Admonishing'; cfg.Password='Instruction'
    c = NES.Client.Client(cfg); assert c.IsReady(); return c
def attach(cl,i):
    c=NES.Simulation.Configuration(); c.Name='attach'; c.Seed=0
    s=cl.CreateSimulation(c,_Create=False); s.ID=i; return s
def verify(sim,dumppath,label):
    dump=json.load(open(dumppath)); N=len(dump['neurons'])
    pd={(c['pre'],c['post'],c['type']):c['g_peak_sum'] for c in dump['connections']}
    somas=sim.GetSomaPositions(); n=len(somas.get('SomaCenters',[]))
    conn=sim.GetConnectome(Pause_s=0.1); mism=0;nc=0;w=set()
    for pre in range(len(conn['ConnectionTargets'])):
        for i,post in enumerate(conn['ConnectionTargets'][pre]):
            key=(pre,int(post),int(conn['ConnectionTypes'][pre][i])); nc+=1
            w.add(round(float(conn['ConnectionWeights'][pre][i]),3)); g=float(conn['ConnectionGPeakSum'][pre][i])
            if key not in pd or abs(pd[key]-g)>1e-3*max(1.0,g): mism+=1
    ok = n==N==94 and mism==0 and nc==len(pd) and w=={0.2}
    print(label,'neurons',n,'dumpN',N,'conns',nc,'dump_conns',len(pd),'mismatch',mism,'weights',sorted(w),'OK' if ok else 'FAIL',flush=True)
    return ok

import json, sys
import BrainGenix.NES as NES
D='/home/johnjose/cos/netmorph_work/fable_loop/r2_seeds/'
cfg = NES.Client.Configuration()
cfg.Mode = NES.Client.Modes.Remote; cfg.Host='localhost'; cfg.Port=8000; cfg.UseHTTPS=False
cfg.AuthenticationMethod = NES.Client.Authentication.Password; cfg.Username='Admonishing'; cfg.Password='Instruction'
client = NES.Client.Client(cfg); assert client.IsReady()
def attach(i):
    c=NES.Simulation.Configuration(); c.Name='attach'; c.Seed=0
    s=client.CreateSimulation(c,_Create=False); s.ID=i; return s
for S,sid in ((1001,141),(1002,145),(1003,146)):
    dump=json.load(open(D+'viz_%d/sample_0000.json'%S)); N=len(dump['neurons'])
    pd={(c['pre'],c['post'],c['type']):c['g_peak_sum'] for c in dump['connections']}
    sim=attach(sid)
    somas=sim.GetSomaPositions(); n=len(somas.get('SomaCenters',[]))
    conn=sim.GetConnectome(Pause_s=0.1); mism=0;nc=0;w=set()
    for pre in range(len(conn['ConnectionTargets'])):
        for i,post in enumerate(conn['ConnectionTargets'][pre]):
            key=(pre,int(post),int(conn['ConnectionTypes'][pre][i])); nc+=1
            w.add(round(float(conn['ConnectionWeights'][pre][i]),3)); g=float(conn['ConnectionGPeakSum'][pre][i])
            if key not in pd or abs(pd[key]-g)>1e-3*max(1.0,g): mism+=1
    ok = n==N==94 and mism==0 and nc==len(pd) and w=={0.2}
    print('seed',S,'sim',sid,'neurons',n,'dumpN',N,'conns',nc,'dump_conns',len(pd),'mismatch',mism,'weights',sorted(w),'OK' if ok else 'FAIL',flush=True)
    if ok:
        print(' ModelSave',sim.ModelSave('fable-r2-seed%d'%S),flush=True)

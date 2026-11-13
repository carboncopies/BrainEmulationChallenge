import sys, json
sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe')
import recipelib as L
L.guard_memory()
NES, client = L.connect()
def mk(name):
    c = NES.Simulation.Configuration(); c.Name = name; c.Seed = 0
    s = client.CreateSimulation(c); assert s.ID >= 0; return s
def conn_map(sim):
    conn = sim.GetConnectome(Pause_s=0.1); m = {}
    for pre in range(len(conn['ConnectionTargets'])):
        for i, post in enumerate(conn['ConnectionTargets'][pre]):
            m.setdefault((pre,int(post)),[]).append((int(conn['ConnectionTypes'][pre][i]), round(float(conn['ConnectionWeights'][pre][i]),5), round(float(conn['ConnectionGPeakSum'][pre][i]),4)))
    return m
out = {}
A = mk('v2-rt-a'); sims = [A]
try:
    A.SetLIFCAbstractedFunctional(_AbstractedFunctional=True); A.SetSTDP(_DoSTDP=False)
    A.ModelLoad('fable-it1a-sim133')
    m0 = conn_map(A)
    pyr = set(range(67))
    pp = [k for k,v in m0.items() if k[0] in pyr and k[1] in pyr and any(t==1 for t,_,_ in v)][:5]       # Pyr->Pyr AMPA
    pi = [k for k,v in m0.items() if k[0] in pyr and k[1] not in pyr and any(t==1 for t,_,_ in v)][:3]  # Pyr->Int AMPA
    ip = [k for k,v in m0.items() if k[0] not in pyr and k[1] in pyr and all(t==2 for t,_,_ in v)][:3]  # Int->Pyr GABA only
    out['before'] = {str(k): m0[k] for k in pp+pi+ip}
    pairs = []
    for k in pp+pi:
        g = [x for x in m0[k] if x[0]==1][0][2]; pairs.append((k[0],k[1],0.5*g,g))
    r = A.BatchSetPrePostStrength([p[0] for p in pairs],[p[1] for p in pairs],[p[2] for p in pairs]); out['set_ampa_response']=r
    gi = [(k[0],k[1],0.1) for k in ip]
    r2 = A.BatchSetPrePostStrength([p[0] for p in gi],[p[1] for p in gi],[p[2] for p in gi]); out['set_gaba_response']=r2
    m1 = conn_map(A); out['after_set_live'] = {str(k): m1[k] for k in pp+pi+ip}
    A.ModelSave('v2-roundtrip-test')
    B = mk('v2-rt-b'); sims.append(B)
    B.SetLIFCAbstractedFunctional(_AbstractedFunctional=True)
    B.ModelLoad('v2-roundtrip-test')
    m2 = conn_map(B); out['after_save_load'] = {str(k): m2.get(k) for k in pp+pi+ip}
    out['ampa_edit_survived_saveload'] = all(m2.get(k)==m1[k] for k in pp+pi)
    out['gaba_state_live_vs_loaded_equal'] = all(m2.get(k)==m1[k] for k in ip)
finally:
    for s in sims:
        try: s.DeleteResidentByID(Pause_s=0.1)
        except Exception as e: print('delete failed', e)
json.dump(out, open('roundtrip_result.json','w'), indent=1, default=str)
print(json.dumps({k:v for k,v in out.items() if k in ('set_ampa_response','set_gaba_response','ampa_edit_survived_saveload','gaba_state_live_vs_loaded_equal')}, default=str)[:800])
for k in ['before','after_set_live','after_save_load']:
    print(k); [print(' ',a,b) for a,b in list(out[k].items())[:11]]

"""ModelLoad -> ModelSave roundtrip of patched model P1: parse the saved file and compare every receptor record (all 113,267 fields) with the patched file."""
import sys, os, json, numpy as np
sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe'); sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe_v2/inhibition_timing')
import recipelib as L
from patch_inh import *
NES,client=L.connect(); RT='v2-arbor-S1-inhP1-rt'; out={}
c=NES.Simulation.Configuration(); c.Name='inh-rt'; c.Seed=0; s=client.CreateSimulation(c); sid=s.ID
try:
    s.SetLIFCAbstractedFunctional(_AbstractedFunctional=True); s.SetSTDP(_DoSTDP=False)
    s.ModelLoad('v2-arbor-S1-inhP1'); out['save']=str(s.ModelSave(RT))
finally:
    print('deleted',sid,s.DeleteResidentByID(),flush=True)
try:
    c1,h1,o1,r1=load(D+'v2-arbor-S1-inhP1'); c2,h2,o2,r2=load(D+RT); a=np.array(r1); b=np.array(r2)
    out['n_records']=[len(a),len(b)]
    out['fields_equal']={k:bool(np.array_equal(a[k],b[k])) for k in ['Src','Dst','Erev','Rise','Decay','G','W','Delay','NT']}
    out['same_after_sort']=None
    M,pre,post=masks(r1)
    for nm in ('pi','gaba','pp'): out[nm]={f:sorted(set(np.round(np.array(r2[f])[M[nm]],4).tolist()))[:6] for f in ('G','W','Rise','Decay')}
finally:
    os.remove(D+RT); out['rt_model_removed']=not os.path.exists(D+RT)
json.dump(out,open('rt_result.json','w'),indent=1); print(json.dumps(out,indent=1)[:2500])

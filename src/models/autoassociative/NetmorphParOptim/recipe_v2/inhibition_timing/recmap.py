import sys, json, numpy as np, collections
sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe_v2/inhibition_timing')
from comp2neuron import *
MODEL='/var/lib/BrainGenix/NES/Admonishing/Models/v2-arbor-S10000'
def pre_post(rec, path=MODEL):
    o=comp_map(path); mx=max(max(a.max() if len(a) else 0, b.max() if len(b) else 0, c.max() if len(c) else 0) for a,b,c in o)
    lut=np.full(mx+1,-1,np.int32)
    for k,(s,d,a) in enumerate(o):
        lut[s]=k; lut[d]=k; lut[a]=k
    return lut[np.array(rec['Src'])], lut[np.array(rec['Dst'])]
if __name__=='__main__':
    cls,h,off,rec=load(MODEL); pre,post=pre_post(rec)
    print('unmapped',(pre<0).sum(),(post<0).sum())
    d=json.load(open('/home/johnjose/cos/netmorph_work/recipe_v2/dendrite_rerun/grow_S1/viz/sample_0000.json'))
    cnt=collections.Counter(); 
    for c in d['connections']: cnt[(c['pre'],c['post'],{1:0,2:1,3:2}[c['type']])]+=c['num_receptors']
    got=collections.Counter(zip(pre.tolist(),post.tolist(),np.array(rec['NT']).tolist()))
    print('pairs dump',len(cnt),'file',len(got),'identical',cnt==got)
    typ=np.array([n['soma_type'] for n in d['neurons']])
    nt=np.array(rec['NT'])
    for a,b,nm in [(1,1,'PP'),(1,2,'PI'),(2,1,'IP'),(2,2,'II')]:
        m=(typ[pre]==a)&(typ[post]==b)
        print(nm,{k:int((m&(nt==k)).sum()) for k in (0,1,2)})

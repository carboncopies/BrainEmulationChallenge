import sys, json, numpy as np
sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe_v2/inhibition_timing')
from recmap import *
cls,h,off,rec=load(MODEL); pre,post=pre_post(rec); nt=np.array(rec['NT'])
pyr=lambda x:x<96
# single-synapse Pyr->Int pairs, distinct pre and distinct post, pre has no NMDA/AMPA to anything strong (any)
import collections
pi=collections.Counter(); 
m=(nt==0)&pyr(pre)&~pyr(post)
for a,b in zip(pre[m],post[m]): pi[(int(a),int(b))]+=1
sing=[k for k,v in pi.items() if v==1]
used_a=set(); used_b=set(); pick=[]
for a,b in sorted(sing):
    if a not in used_a and b not in used_b: pick.append((a,b)); used_a.add(a); used_b.add(b)
    if len(pick)==8: break
print('pyr->int single-syn picks',pick)
# post pyr with most GABA input from ints; its presyn ints
m2=(nt==1)&~pyr(pre)&pyr(post); ci=collections.Counter(post[m2].tolist()); tgt=ci.most_common(1)[0]; print('GABA target pyr',tgt, sorted({int(a) for a in pre[m2&(post==tgt[0])]}))
json.dump(dict(pi=[list(map(int,p)) for p in pick],gaba_target=int(tgt[0]),gaba_pre=sorted({int(a) for a in pre[m2&(post==tgt[0])]})),open('probe_pairs.json','w'))

import sys; sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe_v2/fable_design_S1')
from design import *
import numpy as np, random
Gp=G[:96,:96]; S=(Gp>=4.5)
print('strong pairs',S.sum(),'per source mean',S.sum(1).mean(),'max',S.sum(1).max())
rng=random.Random(1); found=0; best=None
for t in range(400000):
    cueA=rng.sample(range(96),4); cueB=rng.sample([x for x in range(96) if x not in cueA],4)
    ca=[n for n in range(96) if n not in cueA+cueB and S[cueA,n].all()]
    cb=[n for n in range(96) if n not in cueA+cueB and S[cueB,n].all()]
    sh=[n for n in ca if n in cb]
    if len(ca)>=4 and len(cb)>=4 and len(sh)>=1:
        found+=1
        if best is None or len(sh)>best[0]: best=(len(sh),cueA,cueB,ca,cb,sh)
print(found,best)

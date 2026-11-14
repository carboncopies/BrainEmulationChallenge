import json
from emu_scan import *
g=load_groups(); R=[]
def red(o): return dict(full=o['full'],f3=o['false3'],spur=o['spur'],last=float(max(o['last'])),pyr=sum(o['pyr']),int=sum(o['int']))
for c in (1.8,1.85,1.9,1.95,2.0,2.5,3.0):
    sg=red(one(g,s=1,gx=1,bgw=0.5,c=c,SG=True)); print(c,'SG',sg,flush=True)
    for s,gx in ((1,1),(3,5),(5,5),(7,5)):
        a=red(one(g,s=s,gx=gx,bgw=0.5,c=c)); R.append(dict(c=c,s=s,gx=gx,on=a,SG=sg)); print(' ',s,gx,a,flush=True)
json.dump(R,open('scan4.json','w'))

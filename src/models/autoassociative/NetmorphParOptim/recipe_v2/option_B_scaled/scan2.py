import json
from emu_scan import *
g=load_groups(); R=[]
def red(o): return dict(full=o['full'],f3=o['false3'],spur=o['spur'],last=float(max(o['last'])),pyr=sum(o['pyr']),int=sum(o['int']))
bgw,c=0.5,2.0
sg=red(one(g,s=1,gx=1,bgw=bgw,c=c,SG=True)); print('SG',sg)
for s in (2,3,5,7):
    for gx in (1,2.5,5,10):
        a=red(one(g,s=s,gx=gx,bgw=bgw,c=c)); R.append(dict(s=s,gx=gx,on=a)); print(s,gx,a,flush=True)
json.dump(R,open('scan2.json','w'))

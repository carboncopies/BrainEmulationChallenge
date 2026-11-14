import json
from emu_scan import *
g=load_groups(); R=[]
def red(o): return dict(full=o['full'],f3=o['false3'],spur=o['spur'],last=float(max(o['last'])),pyr=sum(o['pyr']),int=sum(o['int']))
for bgw in (0.5,):
  for c in (1.0,1.25,1.5,1.75):
    sg=red(one(g,s=1,gx=1,bgw=bgw,c=c,SG=True)); print(bgw,c,'SG',sg,flush=True)
    for s,gx in ((1,1),(3,5),(5,5),(7,5),(10,5),(7,10),(10,10)):
        a=red(one(g,s=s,gx=gx,bgw=bgw,c=c)); R.append(dict(bgw=bgw,c=c,s=s,gx=gx,on=a,SG=sg)); print(' ',s,gx,a,flush=True)
json.dump(R,open('scan3.json','w'))

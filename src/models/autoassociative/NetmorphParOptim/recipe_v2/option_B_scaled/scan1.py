import json, itertools, sys
from emu_scan import *
if __name__!="__main__": raise SystemExit
g=load_groups(); R=[]
def red(o): return dict(full=o['full'],f3=o['false3'],spur=o['spur'],last=max(o['last']),pyr=sum(o['pyr']),int=sum(o['int']))
for bgw,c in [(0.2,0.5),(0.5,1.0),(0.5,2.0),(1.0,2.0),(1.0,4.0)]:
    for s,gx in [(1,1),(10,10),(20,10)]:
        a=red(one(g,s=s,gx=gx,bgw=bgw,c=c)); b=red(one(g,s=s,gx=gx,bgw=bgw,c=c,SG=True))
        R.append(dict(bgw=bgw,c=c,s=s,gx=gx,on=a,SG=b)); print(bgw,c,s,gx,'ON',a,'SG',b,flush=True)
json.dump(R,open('scan1.json','w'))

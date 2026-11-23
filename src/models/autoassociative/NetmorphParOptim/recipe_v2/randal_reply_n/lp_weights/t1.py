import time, sys
import lpw_lib as L, numpy as np
sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe_v2/ripple_overlap_j'); import ovlib as O
key=sys.argv[1] if len(sys.argv)>1 else 's16180'
G=L.load(key); cfg=L.Cfg(G,**L.PRIMARY)
t=time.time(); cands=L.candidates(cfg,2); print(key,'cands m=2',len(cands),time.time()-t)
D,P=O.load(key); c2=O.candidates(P,2); print('ovlib cands',len(c2))
for k in (0,1,2,3):
    t=time.time(); mem,F=L.pack(cfg,cands,2,k,0); print('k',k,'n_mem',len(mem),'t',round(time.time()-t,1))
    t=time.time(); res=L.solve(cfg,mem); print('  LP status',res['status'], round(time.time()-t,1), (res.get('wsum'),res.get('nrow')))
    if res['status']==0:
        print('  ',{a:round(b,3) for a,b in L.wstats(cfg,res,mem).items()})

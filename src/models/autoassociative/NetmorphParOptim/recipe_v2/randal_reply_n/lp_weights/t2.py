import time, sys, lpw_lib as L, numpy as np
key=sys.argv[1]
for vn in ('primary','hubs_waived'):
    cfg=L.Cfg(L.load(key),**L.VARIANTS[vn]); cands=L.candidates(cfg,2); print(key,vn,'cands',len(cands),flush=True)
    for k in (0,1,2,3):
        t=time.time(); mem,F=L.pack(cfg,cands,2,k,0); res=L.solve(cfg,mem)
        print(' k',k,'n_mem',len(mem),'pack s',round(time.time()-t,1),'LP',res['status'],res.get('stageB'),flush=True)
        if res['status']==0: st=L.wstats(cfg,res,mem); print('   ',{a:(round(b,3) if not isinstance(b,str) else b) for a,b in st.items()},flush=True)

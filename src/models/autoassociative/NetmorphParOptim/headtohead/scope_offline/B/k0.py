from common import *
for s in SIMS:
    r,N=load(s)
    cnt={p:int(N[p].sum()) for p in PATHS}; prs={p:int((N[p]>0).sum()) for p in PATHS}
    g=0.98*N['PI'].sum(0)
    print(s,SIMS[s][1:],len(r.pyr),len(r.int),cnt,prs,int((g>=13.84-1e-9).sum()),'NMDA PP',int(r.NR[NMDA][np.ix_(r.pyr,r.pyr)].sum()),'NMDA PI',int(r.NR[NMDA][np.ix_(r.pyr,r.int)].sum()))

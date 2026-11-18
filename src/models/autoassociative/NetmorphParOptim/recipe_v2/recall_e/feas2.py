"""Capacity packing, same method as dynamics_c/feas.py (cue-sets with >=m common strong in-neighbours, 300 random-restart greedy packings of disjoint memories, pair threshold 4.125 nS),
plus network stats. If the full enumeration of 4-subsets would exceed 3e6 combinations the candidate list is built by sampling (<=400 subsets per target): then the result is a LOWER BOUND ('LB').
usage: feas2.py TAG DUMP  -> feas_<TAG>.json"""
import sys,itertools,random,json,math
from collections import defaultdict
import numpy as np
sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe')
import recipelib as L
THR=4.125
def main(tag,dump):
    if dump.endswith('.npy'): P=np.load(dump); nint=-1
    else: D=L.Dump(dump); P=D.G[:96,:96]; nint=D.N-96
    out=dict(tag=tag,dump=dump,n_int=nint)
    nz=P[P>0]; out.update(pairs=int(len(nz)),p_conn=round(len(nz)/9120,4),g_mean=float(nz.mean()),g_median=float(np.median(nz)),pairs_ge_thr=int((P>=THR).sum()),
        targets_ge4=int(sum(1 for n in range(96) if (np.delete(P[:,n],n)>=THR).sum()>=4)))
    nb={n:[c for c in range(96) if c!=n and P[c,n]>=THR] for n in range(96)}
    full=sum(math.comb(len(v),4) for v in nb.values() if len(v)>=4)
    sampled=full>3e6; out['sampled_LB']=sampled; out['n_4subsets_full']=full
    A=(P>=THR)
    def cands_for(m):
        if not sampled:
            byC=defaultdict(set)
            for n,v in nb.items():
                if len(v)>=4:
                    for C in itertools.combinations(sorted(v),4): byC[C].add(n)
            return [(C,sorted(t for t in T if t not in C)) for C,T in byC.items() if len([t for t in T if t not in C])>=m]
        # vectorised random cue sets (4 distinct cells), 3e6 samples; keep those with >=m common strong targets outside the cue
        rs=np.random.RandomState(1); out_c=[]
        for _ in range(6):
            idx=np.argsort(rs.rand(500000,96),axis=1)[:,:4]
            common=A[idx[:,0]]&A[idx[:,1]]&A[idx[:,2]]&A[idx[:,3]]
            for r in range(4): common[np.arange(len(idx)),idx[:,r]]=False
            ok=np.where(common.sum(1)>=m)[0]
            if len(ok)>40000: ok=ok[:40000]
            for i in ok: out_c.append((tuple(sorted(idx[i])),[int(t) for t in np.where(common[i])[0]]))
        return out_c
    for m in (4,2):
        cs=cands_for(m)
        rr=random.Random(0); best=[]
        for _ in range(300):
            order=cs[:]; rr.shuffle(order); used=set(); ch=[]
            for C,T in order:
                if used&set(C): continue
                Tf=[t for t in T if t not in used]
                if len(Tf)>=m:
                    Tf=rr.sample(Tf,m); ch.append((list(C),sorted(Tf))); used|=set(C)|set(Tf)
            if len(ch)>len(best): best=ch
        out['cands_m%d'%m]=len(cs); out['max_disjoint_m%d'%m]=len(best); out['groups_m%d'%m]=best
        print(tag,m,len(cs),len(best),flush=True)
    json.dump(out,open('feas_%s.json'%tag,'w'),default=int)
if __name__=='__main__': main(sys.argv[1],sys.argv[2])

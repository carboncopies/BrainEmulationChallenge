"""Offline feasibility: how many disjoint memories (4 cue + m noncue, every cue->noncue pair g_peak_sum >= thr) exist in the V1n30 dumps. Read-only."""
import sys,itertools,random
from collections import defaultdict
sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe')
import recipelib as L
C='/home/johnjose/cos/netmorph_work/recipe_v2/linefix_c/grow_V1n30_s%d_p0d0175_i0d0495/viz/sample_0000.json'
def cands(P,thr,m):
    nb={n:[c for c in range(96) if c!=n and P[c,n]>=thr] for n in range(96)}
    byC=defaultdict(set)
    for n in nb:
        if len(nb[n])>=4:
            for Cc in itertools.combinations(sorted(nb[n]),4): byC[Cc].add(n)
    out=[]
    for Cc,T in byC.items():
        T=sorted(t for t in T if t not in Cc)
        if len(T)>=m: out.append((Cc,T))
    return out
def pack(cs,m,tries=300,seed=0):
    rnd=random.Random(seed); best=[]
    for _ in range(tries):
        order=cs[:]; rnd.shuffle(order); used=set(); ch=[]
        for Cc,T in order:
            if used&set(Cc): continue
            Tf=[t for t in T if t not in used]
            if len(Tf)>=m:
                Tf=rnd.sample(Tf,m); ch.append((Cc,sorted(Tf))); used|=set(Cc)|set(Tf)
        if len(ch)>len(best): best=ch
    return best
if __name__=='__main__':
    for s in (16180,27182):
        P=L.Dump(C%s).G[:96,:96]
        for thr in (4.125,3.5):
            for m in (4,3,2):
                cs=cands(P,thr,m); b=pack(cs,m)
                print(s,'thr',thr,'noncue',m,'cue-sets with >=m targets',len(cs),'max disjoint memories found',len(b),b,flush=True)

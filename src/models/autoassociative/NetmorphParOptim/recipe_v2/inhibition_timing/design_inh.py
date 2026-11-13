"""Offline redesign of 4 memories (4 cue + 4 non-cue, disjoint, cue->noncue pair >= 4.5 nS as R3) for Pyr->Int drive scale s: maximise inhibition that
the 8-cell volley can deliver onto own non-cue cells (self) and other memories' non-cue cells (cross). Heuristic only (no NES). usage: design_inh.py s tag seed"""
import sys, json, time, random, numpy as np
sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe_v2/fable_design_S1')
from design import *
s=float(sys.argv[1]); tag=sys.argv[2]; seed=int(sys.argv[3]) if len(sys.argv)>3 else 1
rng=random.Random(seed); nP=96; K=4; THR=13.84
Gpp=G[:nP,:nP]; Gpi=G[:nP,nP:]*s; GAip=D.GA[nP:,:nP]   # GAip[k,n]: GABA g_peak_sum int k -> pyr n
def nsp(d): return 2 if d>=20 else (1 if d>=THR else 0)
def mats(groups):
    S=np.zeros(K); C=np.zeros((K,K)); nint=[]
    for i,(mem,cue) in enumerate(groups):
        d=Gpi[mem,:].sum(0); w=np.array([nsp(x) for x in d]); nint.append(int((w>0).sum()))
        for j,(mj,cj) in enumerate(groups):
            ncj=[m for m in mj if m not in cj]
            v=(w[:,None]*GAip[:,ncj]).sum(0)
            if i==j: S[i]=v.mean()
            else: C[i,j]=v.max()
    return S,C,nint
def cost(groups):
    S,C,ni=mats(groups); off=C[~np.eye(K,dtype=bool)]
    pen=sum(4*max(0,2-n) for n in ni)+2*max(0,off.max()-70)
    return float(-S.min()-S.mean()-0.5*off.mean()+pen)
def valid(g):
    used=[m for mem,_ in g for m in mem]
    if len(set(used))!=len(used): return False
    return all(Gpp[c,n]>=4.5 for mem,cue in g for c in cue for n in mem if n not in cue)
def init():
    avail=set(range(nP)); gs=[]
    for _ in range(K):
        for _t in range(3000):
            cue=rng.sample(sorted(avail),4); cand=[n for n in sorted(avail) if n not in cue and all(Gpp[c,n]>=4.5 for c in cue)]
            if len(cand)>=4:
                nc=rng.sample(cand,4); gs.append((sorted(cue+nc),sorted(cue))); avail-=set(cue+nc); break
        else: return None
    return gs
best=None; t0=time.time()
while time.time()-t0<float(sys.argv[4]) if len(sys.argv)>4 else 100:
    g=init()
    if g is None: continue
    c=cost(g); NIT=4000
    for it in range(NIT):
        T=3.0*(1-it/NIT)+0.05; gi=rng.randrange(K); used={m for m2,_ in g for m in m2}; free=[p for p in range(nP) if p not in used]
        new=[(list(m),list(c2)) for m,c2 in g]; m,cu=new[gi]
        if rng.random()<0.7:
            old=rng.choice(m); nw=rng.choice(free); m[m.index(old)]=nw
            if old in cu: cu[cu.index(old)]=nw
        else:
            a,b=rng.sample(m,2)
            if (a in cu)==(b in cu): continue
            if a in cu: cu[cu.index(a)]=b
            else: cu[cu.index(b)]=a
        new[gi]=(sorted(m),sorted(cu))
        if not valid(new): continue
        c2=cost(new)
        if c2<c or rng.random()<np.exp((c-c2)/T): g,c=new,c2
        if best is None or c<best[0]: best=(c,[(list(a),list(b)) for a,b in g])
groups=best[1]; S,C,ni=mats(groups)
# reference: original R3 groups under the same measure
g0=load_groups(); S0,C0,n0=mats(g0)
out=dict(scale=s,cost=best[0],groups=[dict(members=m,cue=c,noncue=[x for x in m if x not in c]) for m,c in groups],self_inh_nS=S.round(2).tolist(),cross_max_nS=C.round(1).tolist(),n_driven_ints=ni,
  ref_R3=dict(self_inh_nS=S0.round(2).tolist(),cross_max_nS=C0.round(1).tolist(),n_driven_ints=n0))
json.dump(out,open('groups_%s.json'%tag,'w'),indent=1); print(json.dumps({k:v for k,v in out.items() if k!='groups'}),groups)

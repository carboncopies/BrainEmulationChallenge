"""Overlapping-engram designs on S1 (offline, no NES). M0 and M1 share k non-cue cells (k=0..3 of 8 = 0/12.5/25/37.5 %); M2 and M3 are disjoint controls.
Rule as R3: every cue->noncue pair >= 4.5 nS (all 4 cues of a memory onto every non-cue of that memory, shared cells included).
usage: ovl_design.py -> groups_ovl_k{0..3}.json   (format of fable_design_S1 groups: [{members,cue}])"""
import sys, json, random
sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe_v2/fable_design_S1')
from design import *
import os
SEED=os.environ.get('SEED'); PFX='groups_ovl'
if SEED:
    G=L.Dump('/home/johnjose/cos/netmorph_work/recipe_v2/robustness_S1/grow_S1-seed%s/viz/sample_0000.json'%SEED).G; PFX='groups_ovl%s'%SEED
Gp=G[:96,:96]; S=(Gp>=4.5)
def cands(cue,excl): return [n for n in range(96) if n not in excl and S[cue,n].all()]
rng=random.Random(7)
for k in range(4):
  for t in range(200000):
    used=set(); gs=[]
    cA=rng.sample(range(96),4); cB=rng.sample([x for x in range(96) if x not in cA],4); used|=set(cA+cB)
    ca=cands(cA,used); cb=cands(cB,used); sh=[n for n in ca if n in cb]
    if len(sh)<k: continue
    shared=rng.sample(sh,k); rest=[n for n in ca if n not in shared]; restb=[n for n in cb if n not in shared]
    if len(rest)<4-k or len(restb)<4-k: continue
    ra=rng.sample(rest,4-k); rb_=rng.sample([n for n in restb if n not in ra],4-k) if len(restb)>=4-k else None
    if rb_ is None or set(ra)&set(rb_): continue
    gs=[(sorted(cA+shared+ra),sorted(cA)),(sorted(cB+shared+rb_),sorted(cB))]; used|=set(shared+ra+rb_)
    ok=True
    for _ in range(2):
        for _t in range(2000):
            cue=rng.sample([x for x in range(96) if x not in used],4); cd=cands(cue,used|set(cue))
            if len(cd)>=4: nc=rng.sample(cd,4); gs.append((sorted(cue+nc),sorted(cue))); used|=set(cue+nc); break
        else: ok=False
    if ok and len(gs)==4: break
  else: raise SystemExit('fail k=%d'%k)
  json.dump(dict(k=k,overlap_cells=sorted(set(gs[0][0])&set(gs[1][0])),groups=[dict(members=m,cue=c,noncue=[x for x in m if x not in c]) for m,c in gs]),open('%s_k%d.json'%(PFX,k),'w'),indent=1)
  print(k,gs[0],gs[1],'shared',sorted(set(gs[0][0])&set(gs[1][0])))

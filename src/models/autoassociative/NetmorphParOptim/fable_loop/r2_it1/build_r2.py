import json, sys
ARM='a'
W='/home/johnjose/cos/netmorph_work'
sys.path.insert(0, W+'/bec/src/models/autoassociative/NetmorphParOptim/weight_space')
from reservoir import Reservoir
r=Reservoir(W+'/fable_loop/it1/viz_a/sample_0000.json')
G=r.G[1]; GA=r.G[2]; pyr=[int(i) for i in r.pyr]; its=[int(i) for i in r.int]
assert pyr==list(range(67)) and its==list(range(67,94))
PP=[(a,b) for a in pyr for b in pyr if a!=b and G[a,b]>0]
PI=[(a,b) for a in pyr for b in its if G[a,b]>0]
print('ARM',ARM,'PP pairs',len(PP),'PI pairs',len(PI))
groups=[([4,18,20,22,29,51,59,63],[22,29,51,63]),([8,27,33,39,41,42,44,60],[8,27,33,44]),([0,12,17,19,21,37,49,50],[12,17,19,50])]
grp={m:k for k,(mem,_) in enumerate(groups) for m in mem}
wpost={}
for k,(mem,cue) in enumerate(groups):
    nc=[m for m in mem if m not in cue]
    for m in nc:
        S=sum(float(G[c,m]) for c in cue)
        wpost[m]=1.0 if S==0 else min(1.0,27.44/S)
        for c in cue:
            if G[c,m]>0: assert G[c,m]>=4.5,(c,m,float(G[c,m]))
cueset={}
for k,(mem,cue) in enumerate(groups):
    for c in cue: cueset[c]=k
def Cgi(k,i): return sum(float(G[c,i]) for c in groups[k][1])
def inhw(p,i):
    if p in cueset:
        k=cueset[p]; C=Cgi(k,i); assert C>0
        return min(1.0,10.0/C)
    return 1.0
nlow=[(p,i,inhw(p,i)) for p,i in PI if inhw(p,i)<1]
print('DESIGN TABLE (INHfb)')
for k,(mem,cue) in enumerate(groups):
    rows=[]
    for i in its:
        full=sum(float(G[m,i])*inhw(m,i) for m in mem if G[m,i]>0)
        if full>=14:
            cd=sum(float(G[c,i])*inhw(c,i) for c in cue if G[c,i]>0); f1=sum(float(G[m,i]) for m in mem)
            rows.append('%d: %.2f / %.2f / %.2f'%(i,cd,full,f1))
    print(' G%d int id: cue-only INHfb / full8 INHfb / full8 w=1 : %s'%(k,'; '.join(rows) if rows else 'none'))
print(' pyr->int pairs with weight<1: %d ; min such weight %.4f'%(len(nlow),min([x[2] for x in nlow],default=1.0)))
T4=18
def build(bg,inh):
    d={}
    for a,b in PP:
        g=float(G[a,b])
        if a in grp and b in grp and grp[a]==grp[b]:
            cue=groups[grp[a]][1]; ac=a in cue; bc=b in cue
            if ac and not bc: assert g>=T4/4-1e-9; v=T4/4
            elif not ac and not bc: v=wpost[b]*g
            elif not ac and bc: v=g
            else: v=0.0
        else: v=bg*g
        d[(a,b)]=v
    for p in PI: d[p]=float(G[p])*inhw(*p) if inh else 0.0
    return d

OFFS=[(0,0,0,0),(0,1,2,3),(0,2,4,6),(0,3,6,9),(0,4,8,12),(0,5,10,15)]
JS=[0,3,6,9,12,15]
def events(phase):
    E=[]  # (time, gi, J, [(cell,off)])
    t=20 if phase==1 else 48020
    for gi,(mem,cue) in enumerate(groups):
        if phase==1:
            for J,o in zip(JS,OFFS): E.append((t,gi,str(J),list(zip(cue,o)))); t+=2000
            E.append((t,gi,'3cell',list(zip(cue[0:3],(0,2,4))))); t+=2000
            E.append((t,gi,'3cell',list(zip(cue[1:4],(0,2,4))))); t+=2000
        else:
            E.append((t,gi,'9',list(zip(cue,(9,6,3,0))))); t+=2000
            E.append((t,gi,'12',list(zip(cue,(12,8,4,0))))); t+=2000
    return E
E1=events(1); E2=events(2); assert len(E1)==24 and len(E2)==6 and E1[-1][0]==46020 and E2[-1][0]==58020
d=build(0,1); o=[]
for (a,b),v in d.items():
    assert G[a,b]>0 and 0<=v<=G[a,b]+1e-9; o.append([a,b,float(v)])
assert len(o)==len(PP)+len(PI)
print('ops',len(o),'nonzero',sum(1 for x in o if x[2]>0))
lab='ENG18 BG0 INHfb'
out=[]
for k,(E,s,e) in enumerate([(E1,0,48000),(E2,48000,60000)],1):
    out.append({'name':'P%d %s'%(k,lab),'label':lab,'ops':o,
      'cues':[[t+off,[c]] for t,gi,J,cs in E for c,off in cs],
      'events':[[t,gi,J,cs] for t,gi,J,cs in E],'start_ms':s,'end_ms':e})
json.dump({'phases':out,'w_post':{str(k):v for k,v in wpost.items()}},open('r2it1_phases.json','w'))

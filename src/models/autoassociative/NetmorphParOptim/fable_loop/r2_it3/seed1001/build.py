import json, sys
S=int(sys.argv[1])
W='/home/johnjose/cos/netmorph_work'
sys.path.insert(0, W+'/bec/src/models/autoassociative/NetmorphParOptim/weight_space')
from reservoir import Reservoir
r=Reservoir(W+'/fable_loop/r2_seeds/viz_%d/sample_0000.json'%S)
G=r.G[1]
pyr=[int(i) for i in r.pyr]; its=[int(i) for i in r.int]
assert pyr==list(range(67)) and its==list(range(67,94))
dz=json.load(open(W+'/fable_loop/r2_seeds/design_%d.json'%S))['groups']
EXP={1001:[([17,19,59,62],[3,32,55,61]),([11,13,38,65],[4,20,54,63]),([21,44,45,53],[6,12,16,18])],
1002:[([12,15,24,38],[0,7,9,25]),([18,42,43,58],[30,31,33,60]),([17,36,53,55],[34,44,50,65])],
1003:[([14,25,31,63],[7,9,26,58]),([5,33,53,59],[4,8,56,57]),([15,29,40,66],[1,3,44,51])]}[S]
for g,(c,n) in zip(dz,EXP): assert sorted(g['cue'])==c and sorted(g['noncue'])==n,(g,c,n)
groups=[(sorted(g['cue']+g['noncue']),sorted(g['cue'])) for g in dz]
json.dump(groups,open('groups.json','w'))
PP=[(a,b) for a in pyr for b in pyr if a!=b and G[a,b]>0]
PI=[(a,b) for a in pyr for b in its if G[a,b]>0]
print('PP',len(PP),'PI',len(PI))
grp={m:k for k,(mem,_) in enumerate(groups) for m in mem}; assert len(grp)==24
wpost={}
for k,(mem,cue) in enumerate(groups):
    for m in [m for m in mem if m not in cue]:
        Sm=sum(float(G[c,m]) for c in cue)
        wpost[m]=1.0 if Sm==0 else min(1.0,27.44/Sm)
        for c in cue:
            if G[c,m]>0: assert G[c,m]>=4.5,(c,m,float(G[c,m]))
cueset={c:k for k,(mem,cue) in enumerate(groups) for c in cue}
def Cgi(k,i): return sum(float(G[c,i]) for c in groups[k][1])
def inhw(p,i):
    if p in cueset:
        C=Cgi(cueset[p],i); assert C>0
        return min(1.0,10.0/C)
    return 1.0
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
EV12=[]; t=20
for gi,(mem,cue) in enumerate(groups):
    c1,c2,c3,c4=cue
    for s in [[c1,c2],[c1,c2,c3],[c2,c3,c4],[c1,c2,c3,c4]]: EV12.append((t,gi,s)); t+=1000
assert EV12[-1][0]==11020
EV3=[(20,0,groups[0][1]),(3020,1,groups[1][1]),(6020,2,groups[2][1])]
spec=[(0,1,EV12),(0.01,1,EV3),(0.01,0,EV3),(0.02,1,EV3),(0.02,0,EV3),(0.03,1,EV3),(0.03,0,EV3),(0.05,1,EV3),(0.05,0,EV3)]
out=[]; cur=0
for i,(bg,inh,EV) in enumerate(spec,1):
    dur=12000 if EV is EV12 else 9000
    lab='BG%g %s'%(bg,'INHfb' if inh else 'INHoff')
    d=build(bg,inh); o=[]
    for (a,b),v in d.items():
        assert G[a,b]>0 and 0<=v<=G[a,b]+1e-9; o.append([a,b,float(v)])
    print('P%d'%i,lab,'ops',len(o))
    out.append({'name':'P%d %s'%(i,lab),'label':lab,'ops':o,'cues':[[cur+t,s] for t,gi,s in EV],'events':[[cur+t,gi,s] for t,gi,s in EV],'start_ms':cur,'end_ms':cur+dur}); cur+=dur
json.dump({'phases':out},open('phases.json','w'))

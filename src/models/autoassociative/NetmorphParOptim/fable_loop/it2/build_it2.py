import json, sys
W='/home/johnjose/cos/netmorph_work'
sys.path.insert(0, W+'/bec/src/models/autoassociative/NetmorphParOptim/weight_space')
from reservoir import Reservoir
r=Reservoir(W+'/fable_loop/it1/viz_a/sample_0000.json')
G=r.G[1]; pyr=[int(i) for i in r.pyr]; its=[int(i) for i in r.int]
assert pyr==list(range(67)) and its==list(range(67,94))
PP=[(a,b) for a in pyr for b in pyr if a!=b and G[a,b]>0]
PI=[(a,b) for a in pyr for b in its if G[a,b]>0]
print('PP',len(PP),'PI',len(PI))
g0=[4,18,20,22,29,51,59,63]; c0=[22,29,51,63]; g1=[8,27,33,39,41,42,44,60]; c1=[8,27,33,44]; g2=[0,12,17,19,21,37,49,50]
def ops(ppw=None, piw=0.0):
    d={}
    for p in PP: d[p]=0.0
    for p in PI: d[p]=piw*G[p]
    if ppw: 
        for p,v in ppw.items(): d[p]=v
    return d
# phase A
A={}
for cues,mem,T in [(c0,g0,{4:12,18:14,20:16,59:18}),(c1,g1,{39:20,41:22,42:24,60:28})]:
    for m,t in T.items():
        for c in cues:
            if G[c,m]>0: A[(c,m)]=t/4.0
            else: print('WARN no AMPA calib pair',c,m)
# phase C
Cw={}; wm={}
for mem,cues in [(g0,c0),(g1,c1)]:
    for m in mem:
        S=sum(G[c,m] for c in cues if c!=m)
        w=1.0 if S==0 else min(1.0,27.44/S); wm[m]=w
        for p in mem:
            if p!=m and G[p,m]>0: Cw[(p,m)]=w*G[p,m]
print('w_m',{k:round(v,4) for k,v in wm.items()})
pa=ops(A,0.0); pb=ops(None,1.0); pc=ops(Cw,1.0); pd=ops(Cw,0.0)
phases=[("A pyr threshold calibration",pa,[(20,c0),(520,c1)],1000),
("B interneuron drive",pb,[(1020,c0),(1270,g0),(1520,g1),(1770,g2)],2000),
("C recall with inhibition",pc,[(2020,c0),(2770,c1)],3500),
("D recall inhibition off",pd,[(3520,c0),(4270,c1)],5000),
("E recall with inhibition repeat",pc,[(5020,c0),(5770,c1)],6500)]
out=[]
for name,d,cues,end in phases:
    o=[]
    for (a,b),v in d.items():
        assert G[a,b]>0 and 0<=v<=G[a,b]+1e-9
        o.append([a,b,float(v)])
    assert len(o)==len(PP)+len(PI)
    print(name,'ops',len(o),'nonzero',sum(1 for x in o if x[2]>0))
    out.append({'name':name,'ops':o,'cues':[[t,list(ids)] for t,ids in cues],'end_ms':end})
json.dump({'phases':out,'w_m':{str(k):v for k,v in wm.items()}},open('it2_phases.json','w'))

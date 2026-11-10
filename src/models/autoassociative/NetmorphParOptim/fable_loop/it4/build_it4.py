import json, sys
ARM=sys.argv[1]
W='/home/johnjose/cos/netmorph_work'
sys.path.insert(0, W+'/bec/src/models/autoassociative/NetmorphParOptim/weight_space')
from reservoir import Reservoir
r=Reservoir(W+'/fable_loop/it1/viz_%s/sample_0000.json'%ARM)
G=r.G[1]; GA=r.G[2]; pyr=[int(i) for i in r.pyr]; its=[int(i) for i in r.int]
assert pyr==list(range(67)) and its==list(range(67,94))
PP=[(a,b) for a in pyr for b in pyr if a!=b and G[a,b]>0]
PI=[(a,b) for a in pyr for b in its if G[a,b]>0]
print('ARM',ARM,'PP pairs',len(PP),'PI pairs',len(PI))
groups=[([4,18,20,22,29,51,59,63],[22,29,51,63]),([8,27,33,39,41,42,44,60],[8,27,33,44]),([0,12,17,19,21,37,49,50],[12,17,19,50])]
grp={m:k for k,(mem,_) in enumerate(groups) for m in mem}
wpost={}; mincue={}; Spost={}; bad=[]
for k,(mem,cue) in enumerate(groups):
    nc=[m for m in mem if m not in cue]; mn=1e9
    for m in nc:
        S=sum(float(G[c,m]) for c in cue); Spost[m]=S; wpost[m]=1.0 if S==0 else min(1.0,27.44/S)
        for c in cue:
            if G[c,m]>0:
                mn=min(mn,float(G[c,m]))
                if G[c,m]<4.5: bad.append((c,m,float(G[c,m])))
    mincue[k]=mn
print('DESIGN TABLE')
for k,(mem,cue) in enumerate(groups):
    nc=[m for m in mem if m not in cue]
    print(' G%d min G cue->noncue = %.4f ; noncue w_post: %s ; S_post: %s'%(k,mincue[k],{m:round(wpost[m],4) for m in nc},{m:round(Spost[m],3) for m in nc}))
for k,(mem,cue) in enumerate(groups):
    rows=[]
    for i in its:
        a8=sum(float(G[m,i]) for m in mem)
        if a8>=14: rows.append('%d: %.2f / %.2f'%(i,sum(float(G[c,i]) for c in cue),a8))
    print(' G%d interneurons >=14 nS from 8 members (id: cue4 / all8): %s'%(k,'; '.join(rows) if rows else 'none'))
for k,(mem,cue) in enumerate(groups):
    print(' G%d per-member total GABA g_peak_sum from all interneurons: %s'%(k,{m:round(float(sum(GA[i,m] for i in its)),3) for m in mem}))
if bad:
    print('STOP: cue->noncue pairs with G<4.5:',bad); sys.exit(2)
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
    for p in PI: d[p]=float(G[p]) if inh else 0.0
    return d
def ev12():
    E=[]; t=20
    for gi,subs in [(0,[[22,29],[22,29,51],[29,51,63],[22,29,51,63]]),(1,[[8,27],[8,27,33],[27,33,44],[8,27,33,44]]),(2,[[12,17],[12,17,19],[17,19,50],[12,17,19,50]])]:
        for s in subs: E.append((t,gi,s)); t+=1000
    return E
EV12=ev12(); assert EV12[-1][0]==11020
EV3=[(20,0,[22,29,51,63]),(1520,1,[8,27,33,44]),(3020,2,[12,17,19,50])]
spec=[(0,1,EV12),(0,0,EV12)]
for bg in (0.01,0.02,0.03,0.05): spec+=[(bg,1,EV3),(bg,0,EV3)]
out=[]; cur=0
for i,(bg,inh,EV) in enumerate(spec,1):
    dur=12000 if EV is EV12 else 4500
    lab='ENG%d BG%g INH%s'%(T4,bg,'on' if inh else 'off')
    d=build(bg,inh); o=[]
    for (a,b),v in d.items():
        assert G[a,b]>0 and 0<=v<=G[a,b]+1e-9; o.append([a,b,float(v)])
    assert len(o)==len(PP)+len(PI)
    print('P%d'%i,lab,'ops',len(o),'nonzero',sum(1 for x in o if x[2]>0))
    out.append({'name':'P%d %s'%(i,lab),'label':lab,'ops':o,'cues':[[cur+t,s] for t,gi,s in EV],'events':[[cur+t,gi,s] for t,gi,s in EV],'start_ms':cur,'end_ms':cur+dur}); cur+=dur
json.dump({'phases':out,'w_post':{str(k):v for k,v in wpost.items()}},open('it4_phases.json','w'))

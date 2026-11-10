import json, sys
X=sys.argv[1]
W='/home/johnjose/cos/netmorph_work'
sys.path.insert(0, W+'/bec/src/models/autoassociative/NetmorphParOptim/weight_space')
from reservoir import Reservoir
r=Reservoir(W+'/fable_loop/r2_it4/viz_%s/sample_0000.json'%X)
G=r.G[1]; GA=r.G[2]; pyr=[int(i) for i in r.pyr]; its=[int(i) for i in r.int]
assert pyr==list(range(67)) and its==list(range(67,94))
PP=[(a,b) for a in pyr for b in pyr if a!=b and G[a,b]>0]
PI=[(a,b) for a in pyr for b in its if G[a,b]>0]
print('ARM',X,'PP pairs',len(PP),'PI pairs',len(PI))
groups=[([4,18,20,22,29,51,59,63],[22,29,51,63]),([8,27,33,39,41,42,44,60],[8,27,33,44]),([0,12,17,19,21,37,49,50],[12,17,19,50])]
grp={m:k for k,(mem,_) in enumerate(groups) for m in mem}
cueset={c:k for k,(mem,cue) in enumerate(groups) for c in cue}
bad=[]; zero=[]; mins=[]
wpost={}
for k,(mem,cue) in enumerate(groups):
    nc=[m for m in mem if m not in cue]; gs=[]
    for m in nc:
        S=sum(float(G[c,m]) for c in cue)
        wpost[m]=1.0 if S==0 else min(1.0,27.44/S)
        for c in cue:
            gs.append(float(G[c,m]))
            if G[c,m]==0: zero.append((c,m))
            elif G[c,m]<4.5: bad.append((c,m,float(G[c,m])))
    mins.append(min(gs))
    print('G%d min cue->non-cue G over all 16 pairs: %.4f ; min over existing pairs %.4f'%(k,min(gs),min(x for x in gs if x>0)))
print('cue->non-cue pairs with no AMPA (not programmable):',zero)
if bad:
    print('ASSERT FAIL cue->noncue G<4.5 pairs:',bad); sys.exit(3)
def Cgi(k,i): return sum(float(G[c,i]) for c in groups[k][1])
def inhw(p,i):
    if p in cueset:
        k=cueset[p]; C=Cgi(k,i); assert C>0
        return min(1.0,10.0/C)
    return 1.0
nlow=[(p,i,inhw(p,i)) for p,i in PI if inhw(p,i)<1]
print('DESIGN TABLE')
for k,(mem,cue) in enumerate(groups):
    rows=[]
    for i in its:
        full1=sum(float(G[m,i]) for m in mem if G[m,i]>0)
        if full1>=14:
            cd1=sum(float(G[c,i]) for c in cue if G[c,i]>0)
            cdf=sum(float(G[c,i])*inhw(c,i) for c in cue if G[c,i]>0)
            fullf=sum(float(G[m,i])*inhw(m,i) for m in mem if G[m,i]>0)
            rows.append('%d: %.2f / %.2f / %.2f / %.2f'%(i,cd1,full1,cdf,fullf))
    print(' G%d int id: cue-only w1 / all8 w1 / cue-only INHfb / all8 INHfb : %s'%(k,'; '.join(rows) if rows else 'none'))
print(' member total GABA g_peak_sum from all interneurons:')
for k,(mem,cue) in enumerate(groups):
    print('  G%d: %s'%(k,', '.join('%d:%.2f'%(m,float(GA[its,m].sum())) for m in mem)))
print(' pyr->int pairs with weight<1 under INHfb: %d ; min such weight %.4f'%(len(nlow),min([x[2] for x in nlow],default=1.0)))
T4=18
def build(bg,inh):
    d={}
    for a,b in PP:
        g=float(G[a,b])
        if a in grp and b in grp and grp[a]==grp[b]:
            cue=groups[grp[a]][1]; ac=a in cue; bc=b in cue
            if ac and not bc: v=T4/4
            elif not ac and not bc: v=wpost[b]*g
            elif not ac and bc: v=g
            else: v=0.0
        else: v=bg*g
        d[(a,b)]=v
    for p in PI:
        d[p]=0.0 if inh=='off' else (float(G[p]) if inh=='uni' else float(G[p])*inhw(*p))
    return d
def ev12():
    E=[]; t=20
    for gi,subs in [(0,[[22,29],[22,29,51],[29,51,63],[22,29,51,63]]),(1,[[8,27],[8,27,33],[27,33,44],[8,27,33,44]]),(2,[[12,17],[12,17,19],[17,19,50],[12,17,19,50]])]:
        for s in subs: E.append((t,gi,s)); t+=1000
    return E
EV12=ev12(); assert len(EV12)==12 and EV12[-1][0]==11020
EV3=[(20,0,[22,29,51,63]),(3020,1,[8,27,33,44]),(6020,2,[12,17,19,50])]
spec=[(0,'uni',EV12),(0,'off',EV3),(0,'fb',EV3),(0.02,'fb',EV3),(0.03,'fb',EV3),(0.05,'fb',EV3),(0.03,'off',EV3)]
out=[]; cur=0
for i,(bg,inh,EV) in enumerate(spec,1):
    dur=12000 if EV is EV12 else 9000
    lab='BG%g INH%s'%(bg,inh if inh=='off' else {'uni':'uni','fb':'fb'}[inh])
    d=build(bg,inh); o=[]
    for (a,b),v in d.items():
        assert G[a,b]>0 and 0<=v<=G[a,b]+1e-9; o.append([a,b,float(v)])
    assert len(o)==len(PP)+len(PI)
    print('P%d'%i,lab,'ops',len(o),'nonzero',sum(1 for x in o if x[2]>0))
    out.append({'name':'P%d %s'%(i,lab),'label':lab,'bg':bg,'inh':'INH'+inh,'ops':o,'cues':[[cur+t,s] for t,gi,s in EV],'events':[[cur+t,gi,s] for t,gi,s in EV],'start_ms':cur,'end_ms':cur+dur}); cur+=dur
json.dump({'phases':out,'w_post':{str(k):v for k,v in wpost.items()}},open(W+'/fable_loop/r2_it4/%s/phases.json'%X,'w'))

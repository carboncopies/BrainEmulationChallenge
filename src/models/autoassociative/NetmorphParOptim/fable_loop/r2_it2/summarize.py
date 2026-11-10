import json, sys, statistics as S
MODE=sys.argv[1]; D='stdp_%s/'%MODE
EV=json.load(open(D+'events.json')); out=json.load(open(D+'out.json')); snaps=json.load(open(D+'snaps.json'))
G=[([4,18,20,22,29,51,59,63],[22,29,51,63]),([8,27,33,39,41,42,44,60],[8,27,33,44]),([0,12,17,19,21,37,49,50],[12,17,19,50])]
ingrp={m:k for k,(mm,_) in enumerate(G) for m in mm}
cum=[sum(len(v['tSpike_ms']) for v in s['spikes']['SpikeTimes'].values()) for s in out['segments']]
sp={int(k):sorted(v['tSpike_ms']) for k,v in out['segments'][-1]['spikes']['SpikeTimes'].items()}
L=[]
# forced check seg1
sp1={int(k):v['tSpike_ms'] for k,v in out['segments'][0]['spikes']['SpikeTimes'].items()}
miss=0;tot=0;offs=[]
for t,gi,lab,cs in EV:
    if t<4000:
        for n in cs:
            near=[x for x in sp1.get(n,[]) if abs(x-t)<=3]; tot+=1
            if near: offs.append(round(min(near,key=lambda x:abs(x-t))-t,2))
            else: miss+=1
L.append('FORCED SPIKE CHECK (segment 1): found %d/%d near expected absolute times; offsets ms min %s max %s'%(tot-miss,tot,min(offs),max(offs)))
L.append('cumulative spikes per segment: '+', '.join('S%d=%d'%(i+1,c) for i,c in enumerate(cum)))
L.append('')
used=set()
for t,gi,lab,cs in EV:
    mem,cue=G[gi]; nc=[m for m in mem if m not in cue]
    def w(i): return [x-t for x in sp.get(i,[]) if t<=x<t+300]
    for i in sp:
        for x in sp[i]:
            if t<=x<t+300: used.add((i,x))
    ncf=[m for m in nc if w(m)]
    unc=[c for c in cue if c not in cs and w(c)]
    lat=min((x for m in ncf for x in w(m)),default=None)
    pm=' '.join('%d:%d'%(m,len(w(m))) for m in mem)
    tm=sum(len(w(m)) for m in mem)
    og=sum(1 for m in ingrp if ingrp[m]!=gi and w(m))
    op=sum(1 for i in range(67) if i not in ingrp and w(i))
    ints=[i for i in range(67,94) if w(i)]; isp=sum(len(w(i)) for i in ints)
    fi=min((x for i in ints for x in w(i)),default=None)
    lp=max((x for i in range(67) for x in w(i)),default=None)
    L.append('G%d %s %d-cell cue=%s | noncue_fired=%d/4 %s | first_noncue_latency_ms=%s | target_member_spikes=%d | per-member spikes [%s] | uncued_cue_fired=%s | other_group_members_fired=%d | other_pyr_fired=%d | int_fired=%d spikes=%d first_int_spike_ms=%s | last_pyr_spike_ms=%s'%(
      gi,lab,len(cs),cs,len(ncf),ncf,'%.2f'%lat if lat is not None else '-',tm,pm,unc,og,op,len(ints),isp,'%.2f'%fi if fi is not None else '-','%.2f'%lp if lp is not None else '-'))
L.append('')
def amp(s): return {(a,b):(w,g) for a,b,ty,w,g in snaps[s] if ty==1}
A={k:amp(k) for k in snaps}
gps=A['W0']
def tbl(s,rows,cols,nS=False):
    o=['      cols '+' '.join('%8d'%c for c in cols)]
    for r in rows: o.append('  row %3d '%r+' '.join('%8.4f'%(A[s][(r,c)][0]*(A[s][(r,c)][1] if nS else 1)) if (r,c) in A[s] else '%8s'%'-' for c in cols))
    return o
L.append('B. WEIGHT TABLES (AMPA weight, pre rows -> post cols; "-" = no AMPA connection)')
g0c=G[0][1]; g0n=[4,18,20,59]
for s in ['W0','W1','W2','W5']:
    L.append(' G0 cue->noncue weight @%s'%s); L+=tbl(s,g0c,g0n)
for s in ['W0','W1','W2','W5']:
    L.append(' G0 cue->noncue nS (weight x g_peak_sum) @%s'%s); L+=tbl(s,g0c,g0n,True)
for gi,(pre,post) in [(1,('W2','W3')),(2,('W3','W4'))]:
    cue=G[gi][1]; ncs=[m for m in G[gi][0] if m not in cue]
    for s in ['W0',pre,post,'W5']:
        L.append(' G%d cue->noncue weight @%s'%(gi,s)); L+=tbl(s,cue,ncs)
def st(s,P):
    v=[A[s][p][0] for p in P if p in A[s]]
    return 'n=%d min %.4f mean %.4f max %.4f'%(len(v),min(v),S.mean(v),max(v)) if v else 'n=0'
for gi,(mem,cue) in enumerate(G):
    nc=[m for m in mem if m not in cue]
    for s in ['W0','W5']:
        L.append(' G%d @%s noncue->noncue: %s'%(gi,s,st(s,[(a,b) for a in nc for b in nc if a!=b])))
        L.append(' G%d @%s cue->cue: %s'%(gi,s,st(s,[(a,b) for a in cue for b in cue if a!=b])))
        L.append(' G%d @%s noncue->cue: %s'%(gi,s,st(s,[(a,b) for a in nc for b in cue])))
L.append('')
PP=[p for p in A['W0'] if p[0]<67 and p[1]<67]; PI=[p for p in A['W0'] if p[0]<67 and p[1]>=67]
def within(p): return p[0] in ingrp and p[1] in ingrp and ingrp[p[0]]==ingrp[p[1]]
def df(s,P):
    d=[(A[s][p][0]-A['W0'][p][0],p) for p in P]
    inc=[x for x in d if x[0]>1e-9]; dec=[x for x in d if x[0]<-1e-9]
    return len(inc),len(dec),max([x[0] for x in inc],default=0),min([x[0] for x in dec],default=0),max([abs(x[0]) for x in d if abs(x[0])>1e-9],default=0),len(inc)+len(dec)
for s in ['W1','W2','W3','W4','W5']:
    i,d_,mi,md,_,_=df(s,PP); L.append('%s vs W0 AMPA pyr->pyr (%d pairs): increased=%d decreased=%d largest_increase=%.4f largest_decrease=%.4f'%(s,len(PP),i,d_,mi,md))
    i,d_,mi,md,ma,n=df(s,[p for p in PP if not within(p)]); L.append('%s vs W0 AMPA pyr->pyr NOT within one group: changed=%d max_abs_change=%.4f'%(s,n,ma))
    i,d_,mi,md,ma,n=df(s,PI); L.append('%s vs W0 AMPA pyr->int (%d pairs): increased=%d decreased=%d largest_increase=%.4f largest_decrease=%.4f max_abs_change=%.4f'%(s,len(PI),i,d_,mi,md,ma))
cues=sorted(c for _,cu in G for c in cu)
L.append('cue cells -> interneuron 89 AMPA pairs (W0, W5):')
for c in cues:
    if (c,89) in A['W0']: L.append('  %d->89: W0=%.4f W5=%.4f'%(c,A['W0'][(c,89)][0],A['W5'][(c,89)][0]))
gb=sorted({round(w,4) for a,b,ty,w,g in snaps['W5'] if ty!=1 and ty!=2 and False} | {round(w,4) for a,b,ty,w,g in snaps['W5'] if ty not in (1,2)})
types=sorted({ty for a,b,ty,w,g in snaps['W5']}); L.append('connection types present: %s'%types)
L.append('unique GABA (non-AMPA/NMDA types, i.e. types not in {1,2}) weights at W5: %s'%gb)
for ty in types:
    L.append('  type %d unique weights W5: %s'%(ty,sorted({round(w,4) for a,b,t,w,g in snaps['W5'] if t==ty})[:12]))
L.append('')
n=sum(1 for i in sp for x in sp[i] if (i,x) not in used)
L.append('C. spikes outside all windows: %d ; total spikes: %d'%(n,sum(len(v) for v in sp.values())))
open(D+'summary.txt','w').write('\n'.join(L)+'\n')

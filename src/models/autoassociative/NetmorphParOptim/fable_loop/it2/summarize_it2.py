import json
d=json.load(open('it2_out.json'))
st=d['phases'][-1]['spikes']['SpikeTimes']
sp={int(k):sorted(v['tSpike_ms']) for k,v in st.items()}
g0=[4,18,20,22,29,51,59,63]; c0=[22,29,51,63]; g1=[8,27,33,39,41,42,44,60]; c1=[8,27,33,44]; g2=[0,12,17,19,21,37,49,50]
def lab(i):
    if i>=67: return 'int'
    if i in c0: return 'G0cue'
    if i in g0: return 'G0'
    if i in c1: return 'G1cue'
    if i in g1: return 'G1'
    if i in g2: return 'G2'
    return 'pyr-other'
ph=json.load(open('it2_phases.json'))['phases']
ev=[(t,ids,p['name']) for p in ph for t,ids in p['cues']]
L=[]; used=set()
# check cumulativeness
L.append('cumulative spike count per phase snapshot: '+str([sum(len(v['tSpike_ms']) for v in p['spikes']['SpikeTimes'].values()) for p in d['phases']]))
for t,ids,name in ev:
    L.append('\n=== cue t=%g ms cells=%s (phase %s) window [%g,%g)'%(t,ids,name,t,t+240))
    tot={k:0 for k in ['G0','G1','G2','pyr-other','int']}; ints=set(); lastp=None
    for i in sorted(sp):
        ts=[x for x in sp[i] if t<=x<t+240]
        for x in sp[i]:
            if t<=x<t+240: used.add((i,x))
        if not ts: continue
        rel=[x-t for x in ts]; l=lab(i)
        L.append('  %d(%s): %d [%s] last=%.2f'%(i,l,len(ts),', '.join('%.2f'%x for x in rel[:6]),rel[-1]))
        k='G0' if l in('G0','G0cue') else 'G1' if l in('G1','G1cue') else l
        tot[k]+=len(ts)
        if i>=67: ints.add(i)
        else: lastp=max(lastp,rel[-1]) if lastp is not None else rel[-1]
    L.append('  TOTALS: G0 members %d, G1 members %d, G2 members %d, other pyr %d, interneurons %d; distinct interneurons firing %d; last pyramidal spike rel cue: %s'%(tot['G0'],tot['G1'],tot['G2'],tot['pyr-other'],tot['int'],len(ints),'%.2f'%lastp if lastp is not None else 'none'))
L.append('\n=== spikes outside all cue windows')
n=0
for i in sorted(sp):
    for x in sp[i]:
        if (i,x) not in used: L.append('  %d(%s) t=%.2f'%(i,lab(i),x)); n+=1
L.append('  count: %d'%n)
open('it2_summary.txt','w').write('\n'.join(L)); print('\n'.join(L))

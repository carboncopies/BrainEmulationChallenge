import json
d=json.load(open('r2it1_out.json')); ph=json.load(open('r2it1_phases.json'))['phases']
cum=[sum(len(v['tSpike_ms']) for v in p['spikes']['SpikeTimes'].values()) for p in d['phases']]
st=d['phases'][-1]['spikes']['SpikeTimes']; sp={int(k):sorted(v['tSpike_ms']) for k,v in st.items()}
G=[([4,18,20,22,29,51,59,63],[22,29,51,63]),([8,27,33,39,41,42,44,60],[8,27,33,44]),([0,12,17,19,21,37,49,50],[12,17,19,50])]
ingrp={m for mem,_ in G for m in mem}
L=[]; used=set()
for pi,p in enumerate(ph,1):
    for t,gi,J,cs in p['events']:
        mem,cue=G[gi]; nc=[m for m in mem if m not in cue]; forced=[c for c,o in cs]
        def w(i): return [x-t for x in sp.get(i,[]) if t<=x<t+300]
        for i in sp:
            for x in sp[i]:
                if t<=x<t+300: used.add((i,x))
        ncf=[m for m in nc if w(m)]
        unc=[c for c in cue if c not in forced and w(c)]
        tm=sum(len(w(m)) for m in mem)
        og=sum(1 for k,(mm,_) in enumerate(G) if k!=gi for m in mm if w(m))
        op=[i for i in range(67) if i not in ingrp and w(i)]; ops_=sum(len(w(i)) for i in op)
        ints=[i for i in range(67,94) if w(i)]; isp=sum(len(w(i)) for i in ints)
        lat=min((x for m in ncf for x in w(m)),default=None)
        fi=min((x for i in ints for x in w(i)),default=None)
        lp=max((x for i in range(67) for x in w(i)),default=None)
        f=lambda v:'%.2f'%v if v is not None else '-'
        L.append('P%d G%d J=%s offsets=%s | noncue_fired=%d/4 %s | first_noncue_latency_from_first_cue_ms=%s | per-noncue first-spike latencies=[%s] | target_member_spikes=%d | uncued_cue_fired=%s | other_group_members_fired=%d | other_pyr_fired=%d spikes=%d | int_fired=%d spikes=%d first_int_spike_ms=%s | last_pyr_spike_ms=%s'%(
            pi,gi,J,'('+','.join('%d:%d'%(c,o) for c,o in cs)+')',len(ncf),ncf,f(lat),' '.join('%d:%.2f'%(m,w(m)[0]) for m in ncf),tm,unc,og,len(op),ops_,len(ints),isp,f(fi),f(lp)))
n=sum(1 for i in sp for x in sp[i] if (i,x) not in used)
L.append(''); L.append('spikes outside all windows: %d'%n)
L.append('total spikes: %d (cumulative per phase: %s)'%(cum[-1],', '.join('P%d=%d'%(i+1,c) for i,c in enumerate(cum))))
open('r2it1_summary.txt','w').write('\n'.join(L)+'\n')

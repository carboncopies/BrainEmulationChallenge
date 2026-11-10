import json
d=json.load(open('out.json')); ph=json.load(open('phases.json'))['phases']; G=json.load(open('groups.json'))
cum=[sum(len(v['tSpike_ms']) for v in p['spikes']['SpikeTimes'].values()) for p in d['phases']]
st=d['phases'][-1]['spikes']['SpikeTimes']; sp={int(k):sorted(v['tSpike_ms']) for k,v in st.items()}
ingrp={m for mem,_ in G for m in mem}
L=[]; used=set()
for pi,p in enumerate(ph,1):
    for t,gi,forced in p['events']:
        mem,cue=G[gi]; nc=[m for m in mem if m not in cue]
        def w(i): return [x-t for x in sp.get(i,[]) if t<=x<t+300]
        for i in sp:
            for x in sp[i]:
                if t<=x<t+300: used.add((i,x))
        ncf=[m for m in nc if w(m)]
        unc=[c for c in cue if c not in forced and w(c)]
        tm=sum(len(w(m)) for m in mem)
        og=[(k,m,len(w(m))) for k,(mm,_) in enumerate(G) if k!=gi for m in mm if w(m)]
        op=[i for i in range(67) if i not in ingrp and w(i)]; ops_=sum(len(w(i)) for i in op)
        ints=[i for i in range(67,94) if w(i)]; isp=sum(len(w(i)) for i in ints)
        lat=min((x for m in ncf for x in w(m)),default=None)
        fi=min((x for i in ints for x in w(i)),default=None)
        lp=max((x for i in range(67) for x in w(i)),default=None)
        f=lambda v:'%.2f'%v if v is not None else '-'
        L.append('P%d %s | G%d cue=%s | noncue_fired=%d/4 %s | first_noncue_latency_ms=%s | target_member_spikes=%d | uncued_cue_fired=%s | other_group_members_fired=%d [%s] | other_pyr_fired=%d spikes=%d %s | int_fired=%d spikes=%d first_int_spike_ms=%s | last_pyr_spike_ms=%s'%(
            pi,p['label'],gi,forced,len(ncf),ncf,f(lat),tm,unc,len(og),' '.join('G%d:%d:%d'%x for x in og),len(op),ops_,op,len(ints),isp,f(fi),f(lp)))
n=sum(1 for i in sp for x in sp[i] if (i,x) not in used)
L.append(''); L.append('spikes outside all windows: %d'%n)
L.append('cumulative spike totals per phase: '+', '.join('P%d=%d'%(i+1,c) for i,c in enumerate(cum)))
open('summary.txt','w').write('\n'.join(L)+'\n'); print('\n'.join(L))

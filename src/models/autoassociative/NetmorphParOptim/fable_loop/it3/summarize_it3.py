import json
d=json.load(open('it3_out.json')); ph=json.load(open('it3_phases.json'))['phases']
cum=[sum(len(v['tSpike_ms']) for v in p['spikes']['SpikeTimes'].values()) for p in d['phases']]
st=d['phases'][-1]['spikes']['SpikeTimes']; sp={int(k):sorted(v['tSpike_ms']) for k,v in st.items()}
G=[([4,18,20,22,29,51,59,63],[22,29,51,63]),([8,27,33,39,41,42,44,60],[8,27,33,44]),([0,12,17,19,21,37,49,50],[12,17,19,50])]
ingrp={m for mem,_ in G for m in mem}
L=[]; used=set(); intblock=[]
for pi,p in enumerate(ph,1):
    for t,gi,forced in p['events']:
        mem,cue=G[gi]; nc=[m for m in mem if m not in cue]
        def w(i): return [x-t for x in sp.get(i,[]) if t<=x<t+240]
        for i in sp:
            for x in sp[i]:
                if t<=x<t+240: used.add((i,x))
        ncf=[m for m in nc if w(m)]
        unc=[c for c in cue if c not in forced and w(c)]
        tm=sum(len(w(m)) for m in mem)
        og=[(m,len(w(m))) for k,(mm,_) in enumerate(G) if k!=gi for m in mm if w(m)]
        op=[i for i in range(67) if i not in ingrp and w(i)]; ops_=sum(len(w(i)) for i in op)
        ints=[i for i in range(67,94) if w(i)]; isp=sum(len(w(i)) for i in ints)
        lat=min((x for m in ncf for x in w(m)),default=None)
        lp=max((x for i in range(67) for x in w(i)),default=None)
        L.append('P%d %s | G%d cue=%s | noncue_fired=%d/4 %s | uncued_cue_fired=%s | target_member_spikes=%d | other_group_members_fired=%d [%s] | other_pyr_fired=%d spikes=%d %s | int_fired=%d spikes=%d | first_noncue_latency_ms=%s | last_pyr_spike_ms=%s'%(
            pi,p['label'],gi,forced,len(ncf),ncf,unc,tm,len(og),' '.join('%d:%d'%x for x in og),len(op),ops_,op[:10],len(ints),isp,'%.2f'%lat if lat is not None else '-','%.2f'%lp if lp is not None else '-'))
        if pi in(1,2) and gi==0:
            intblock.append('P%d t=%g cue=%s'%(pi,t,forced))
            for i in ints: intblock.append('  int %d: %s'%(i,', '.join('%.2f'%x for x in w(i))))
            if not ints: intblock.append('  (no interneuron spikes)')
L.append(''); L.append('Interneuron spike times (ms rel. cue), phases 1 and 2, G0 events:'); L+=intblock
n=sum(1 for i in sp for x in sp[i] if (i,x) not in used)
L.append(''); L.append('spikes outside all windows: %d'%n)
L.append('cumulative spike totals per phase: '+', '.join('P%d=%d'%(i+1,c) for i,c in enumerate(cum)))
open('it3_summary.txt','w').write('\n'.join(L)+'\n'); print('\n'.join(L))

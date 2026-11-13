import sys, json, glob, os
import numpy as np
H='/home/johnjose/cos/netmorph_work/recipe_v2/inhibition_timing/'
S={}
for f in sorted(glob.glob(H+'raw_*.json')):
    e=json.load(open(f)); n=os.path.basename(f)[4:-5]
    base=dict(variant=e['variant'],cfg=e['cfg'],mode=e['mode'],loaded_ok=e['load']['loaded_ok'],readback_mismatch=e['readback']['n_mismatch'])
    if e['kind']=='single':
        ev=e['events']; fu=[x for x in ev if x['expect_complete']]; t3=[x for x in ev if not x['expect_complete']]
        ints=sorted({i for x in ev for i in x['ints_fired']})
        S[n]=dict(base,kind='single',complete=[x['noncue_fired'] for x in fu],latency=[round(x['latency_ms'],2) for x in fu if x['latency_ms'] is not None],member_spikes=[x['member_spikes'] for x in fu],
          burst_end=[round(x['burst_end_ms'],2) for x in fu],last_pyr=[round(x['last_pyr_spike_ms'],1) for x in fu if x['last_pyr_spike_ms'] is not None],int_spikes_full=[x['interneuron_spikes'] for x in fu],
          false3_events=sum(x['noncue_fired']>0 for x in t3),false3_cells=sum(x['noncue_fired'] for x in t3),spurious=sum(x['other_pyr_fired'] for x in ev),crosstalk=sum(x['other_group_members_fired'] for x in ev),
          int_spikes_3cell=[x['interneuron_spikes'] for x in t3],ints=ints,all_clean=all(x['clean'] for x in ev))
    else:
        a=e['analysis']; m=a['memories']
        S[n]=dict(base,kind='ripple',dt=e['dt_ms'],order=[g for g,_ in e['events']],complete=[x['n_noncue_fired_10ms'] for x in m],lat=[round(x['latency_last_noncue_ms'],2) if x['latency_last_noncue_ms'] else None for x in m],
          burst_end=[round(x['last_member_spike_after_cue_ms'],2) for x in m],member_spikes=[x['member_spikes_total'] for x in m],int_spikes=[x['int_spikes_in_window'] for x in m],crosstalk=len(a['crosstalk_events']),
          spurious=a['spurious_nonmember_pyr_spikes'],last=round(a['activity_end_after_first_cue_ms'],2),ints=a['ints_that_fired'],success=a['ripple_success'])
json.dump(S,open(H+'summary.json','w'),indent=0)
for n,s in S.items(): print(n,{k:v for k,v in s.items() if k not in('variant','cfg','mode')})

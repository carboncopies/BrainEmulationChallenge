import json, glob, os
D='/home/johnjose/cos/netmorph_work/recipe_v2/gaba_patch/'
S={}; ids=[]
for f in sorted(glob.glob(D+'raw_*.json')):
    e=json.load(open(f)); n=e['name']; ids.append(e['load']['sim_id'])
    if e['kind']=='single':
        ev=e['events']; fl=[x for x in ev if x['expect_complete']]; t=[x for x in ev if not x['expect_complete']]
        S[n]=dict(factor=e['factor'],kind='single',pairs=e['pairs'],sg=e['sg'],complete=[x['noncue_fired'] for x in fl],latency=[round(x['latency_ms'],2) for x in fl],member_spikes=[x['member_spikes'] for x in fl],burst_end=[round(x['burst_end_ms'],2) for x in fl],int_spikes=[x['interneuron_spikes'] for x in fl],false3cell=sum(x['noncue_fired']>0 for x in t),spurious=sum(x['other_pyr_fired'] for x in ev),crosstalk=sum(x['other_group_members_fired'] for x in ev),all_clean=all(x['clean'] for x in ev),loaded_ok=e['load']['loaded_ok'],sim_id=e['load']['sim_id'])
    else:
        a=e['analysis']; m=a['memories']
        S[n]=dict(factor=e['factor'],kind='ripple',pairs=e['pairs'],sg=e['sg'],order=[g for g,_ in e['events']],complete=[x['n_noncue_fired_10ms'] for x in m],burst_end=[round(x['last_member_spike_after_cue_ms'],2) for x in m],member_spikes=[x['member_spikes_total'] for x in m],int_spikes=[x['int_spikes_in_window'] for x in m],crosstalk=len(a['crosstalk_events']),spurious=a['spurious_nonmember_pyr_spikes'],last=round(a['activity_end_after_first_cue_ms'],2),pyr_spk=a['total_pyr_spikes'],int_total=a['total_interneuron_spikes'],success=a['ripple_success'],loaded_ok=e['load']['loaded_ok'],sim_id=e['load']['sim_id'])
json.dump(S,open(D+'summary.json','w'),indent=0)
for n,s in S.items(): print(n,{k:v for k,v in s.items() if k not in('pairs','kind','factor','order')})
print('sim ids',sorted(ids))

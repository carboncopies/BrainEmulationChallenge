import json, glob, os
H = '/home/johnjose/cos/netmorph_work/recipe_v2/robustness_S1/'
S = {}
for f in sorted(glob.glob(H + 'raw/raw_*.json')):
    d = json.load(open(f)); n = d['name']; rb = d['readback']
    if d['kind'] == 'single':
        ev = d['events']; full = [e for e in ev if e['expect_complete']]; sub = [e for e in ev if not e['expect_complete']]
        S[n] = dict(kind='single', pairs=d['pairs'], sg=d['sg'], complete=[e['noncue_fired'] for e in full], full_clean=all(e['clean'] for e in full),
            false_completions_3cell=sum(1 for e in sub if e['noncue_fired'] > 0), noncue_fired_in_3cell=sum(e['noncue_fired'] for e in sub),
            three_cell_clean=all(e['clean'] for e in sub), member_spikes_full=[e['member_spikes'] for e in full], burst_end_full=[round(e['burst_end_ms'], 2) for e in full],
            int_spikes_full=[e['interneuron_spikes'] for e in full], ints_fired=sorted({i for e in ev for i in e['ints_fired']}),
            crosstalk_or_spurious=sum(e['other_group_members_fired'] + e['other_pyr_fired'] for e in ev), pyr_spikes_total=d['pyr_spikes_total'],
            readback_mismatch=rb['n_mismatch'], nmda_nonzero=rb['nmda_nonzero_after'], gaba_nonzero_after=rb['gaba_nonzero_after'], sim_id=rb['sim_id'],
            pass_=bool(all(e['clean'] for e in ev) and all(e['burst_end_ms'] <= 40 for e in full)))
    else:
        a = d['analysis']; m = a['memories']
        S[n] = dict(kind='ripple', pairs=d['pairs'], sg=d['sg'], dt=d['dt_ms'], order=[e[0] for e in d['events']], spacing=d['events'][1][1] - d['events'][0][1], cue3=a['cue3_group'],
            complete=[x['n_noncue_fired_10ms'] for x in m], burst_end_ms=[round(x['last_member_spike_after_cue_ms'], 2) for x in m], member_spikes=[x['member_spikes_total'] for x in m],
            int_spikes=[x['int_spikes_in_window'] for x in m], crosstalk=len(a['crosstalk_events']), spurious=a['spurious_nonmember_pyr_spikes'],
            pyr_spikes_total=a['total_pyr_spikes'], last_spike_ms=a['last_any_spike_ms'], last_after_first_cue=a['activity_end_after_first_cue_ms'],
            within100=a['activity_ends_within_100ms'], bursts_over_40=a['burst_over_40ms_groups'], success=a['ripple_success'], ints=a['ints_that_fired'],
            gaba_nonzero_after=rb['gaba_nonzero_after'], readback_mismatch=rb['n_mismatch'], nmda_nonzero=rb['nmda_nonzero_after'], sim_id=rb['sim_id'])
json.dump(S, open(H + 'summary.json', 'w'), indent=1)
for n, s in S.items():
    if s['kind'] == 'single': print(n, 'full', s['complete'], 'clean', s['full_clean'], '3cell false', s['false_completions_3cell'], 'spk', s['member_spikes_full'], 'end', s['burst_end_full'], 'int', s['int_spikes_full'], 'xt/spur', s['crosstalk_or_spurious'], 'PASS', s['pass_'])
    else: print(n, 'cue3', s['cue3'], 'compl', s['complete'], 'ends', s['burst_end_ms'], 'pyrspk', s['pyr_spikes_total'], 'last', s['last_spike_ms'], 'xt', s['crosstalk'], 'spur', s['spurious'], 'b>40', s['bursts_over_40'], 'ints', s['ints'], 'SUCC', s['success'])

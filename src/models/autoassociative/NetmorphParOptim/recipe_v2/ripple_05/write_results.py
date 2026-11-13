import json
D='/home/johnjose/cos/netmorph_work/recipe_v2/ripple_05/'
S=json.load(open(D+'mech_summary.json'))
def f(x): return 'fail' if x is None else ('%.1f'%x)
def fl(xs): return ', '.join(f(x) if x is not None else 'x' for x in xs)
titles={'E1':'E1: re-selected groups R0..R3, standard Pyr->Int rule','E2':'E2: original G0..G3, Pyr->Int scaling (fix B)','E3':'E3: re-selected R0..R3 + Pyr->Int scaling','E4':'E4: K=3 original G0,G1,G2 + Pyr->Int scaling','E4b':'E4b: K=3 re-selected set, standard rule (run because E1 and E3 both completed all memories in all 4 runs at Dt 1)'}
o=[]
for n,T in titles.items():
    s=S[n]; o.append('### %s\n'%T)
    o.append('Label: sensitivity study, D_synmax 0.5, not bio-realistic. Groups (members; cue first 4 of each listed in JSON `groups`): '+'; '.join('G%d cue %s non-cue %s'%(i,g['cue'],[m for m in g['members'] if m not in g['cue']]) for i,g in enumerate(s['groups']))+'.\n')
    o.append('Weight set: %d pairs programmed; vs weights.json: %d Pyr->Int and %d Pyr->Pyr pairs differ (matches mech_experiments.json); read-back mismatches in all %d sims: %d.\n'%(s['set_info']['n_pairs'],s['set_info']['n_pyr_int_diff_vs_weights_json'],s['set_info']['n_pyr_pyr_diff_vs_weights_json'],s['n_sims'],s['readback_mismatches_total']))
    o.append('**Verdict: %s** (Dt 1 ms all memories complete in all 4 runs: %s; Dt 0.1 ms: %s; singles all complete: %s).\n'%(s['verdict'],s['all_complete_all4_dt1'],s['all_complete_all4_dt0.1'],all(v['complete'] for v in s['singles'].values())))
    o.append('Single-memory baselines (Dt 1): '+'; '.join('G%s %s, latency %s ms, %d interneuron spikes (%d cells), last member spike %s ms, last activity %s ms'%(g,'4/4' if v['complete'] else 'FAIL',f(v['latency']),v['int_spikes'],v['ints_fired'],f(v['last_member_spike']),f(v['last_activity'])) for g,v in s['singles'].items())+'.\n')
    o.append('Per-run observations (columns follow the cue order; "x" = no value). Burst end = last member pyramidal spike after its own cue; interneuron spikes counted from a memory\'s cue to the next cue (last: to run end); last activity = last spike of any cell, relative to first cue.\n')
    o.append('| run | order | non-cue fired /4 | latency last non-cue (ms) | burst end after cue (ms) | int spikes per window | cross-talk | non-member pyr spikes | last pyr spike (ms) | last activity (ms) | burst not terminated | robust ok |\n|---|---|---|---|---|---|---|---|---|---|---|---|')
    for r,v in s['runs'].items():
        o.append('| %s | %s | %s | %s | %s | %s | %d | %d | %s | %s | %s | %s |'%(r,''.join(str(x) for x in v['order']),','.join(map(str,v['n_noncue'])),fl(v['latency']),fl(v['burst_end_after_cue']),','.join(map(str,v['int_spikes_window'])),v['crosstalk'],v['spurious'],f(v['last_pyr']),f(v['last_any']),v['not_terminated'],v['robust_ok']))
    o.append('\nPredicted (copied from MECH_DESIGN.md section 6 / mech_experiments.json) versus observed. Mark rule: ranges are HIT when inside; for probability predictions P, HIT when the outcome agrees with the side P>=0.5 favours, MISS otherwise (a coarse mechanical rule, not calibration).\n')
    o.append('| quantity | predicted | observed | mark |\n|---|---|---|---|')
    for c in s['comparisons']: o.append('| %s | %s | %s | %s |'%(c['quantity'],str(c['predicted']).replace('|','/'),str(c['observed']).replace('|','/'),c['mark']))
    g=s['gaba_observed_from_singles']
    o.append('\nObserved GABA matrix from the single-memory runs (rows = recalled memory, columns = target memory non-cue members; nS g_peak_sum at weight 1, observed interneuron spike counts x dump GABA conductance; same convention as predictions). Spike-weighted max: %s. Binary mean (cells that fired at least once): %s.\n'%(g['spike_weighted_max'],g['binary_mean']))
    o.append('Score: %d HIT of %d scored.\n'%(s['n_hit'],s['n_scored']))
open(D+'mech_tables.md','w').write('\n'.join(o))

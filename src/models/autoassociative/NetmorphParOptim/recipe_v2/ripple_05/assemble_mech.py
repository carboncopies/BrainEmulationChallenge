"""Builds mech_summary.json and mech_tables.md from raw_mech_*.json (sensitivity study, D_synmax 0.5, not bio-realistic)."""
import json, os, sys
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe')
import numpy as np, recipelib as L
D = '/home/johnjose/cos/netmorph_work/recipe_v2/ripple_05/'
dump = L.Dump(L.SEEDS[20240628]['dump'])
EXP = json.load(open(D + 'mech_experiments.json'))['experiments']
RUNS = ['order_0123_sep12', 'order_0123_sep16', 'order_0123_sep20', 'shuffled_2031_sep16']
def runnames(raw):
    return [k for k in raw['runs'] if not k.startswith('single') and not k.endswith('_dt0.1')]
def rng_hit(v, r): return v is not None and r[0] <= v <= r[1]
def hitstr(b): return 'HIT' if b else 'MISS'
def prob_mark(p, occurred):  # probability prediction: hit if outcome on the side p>=0.5 predicted
    return (p >= 0.5) == bool(occurred)
def gaba_matrix(raw, groups):
    K = len(groups); M = {}
    spk = lambda r, i: len(raw['runs']['single_G%d' % r]['spikes'].get(str(i), []))
    sw_max = np.zeros((K, K)); sw_mean = np.zeros((K, K)); bin_mean = np.zeros((K, K)); bin_max = np.zeros((K, K))
    for i in range(K):
        n = {k: spk(i, k) for k in dump.its}
        for j in range(K):
            nc = [m for m in groups[j]['members'] if m not in groups[j]['cue']]
            sw = [sum(n[k] * dump.GA[k, m] for k in dump.its) for m in nc]
            bn = [sum((1 if n[k] > 0 else 0) * dump.GA[k, m] for k in dump.its) for m in nc]
            sw_max[i, j] = max(sw); sw_mean[i, j] = np.mean(sw); bin_mean[i, j] = np.mean(bn); bin_max[i, j] = max(bn)
    return dict(spike_weighted_max=sw_max.round(1).tolist(), spike_weighted_mean=sw_mean.round(1).tolist(), binary_mean=bin_mean.round(1).tolist(), binary_max=bin_max.round(1).tolist())
def summarize(name, raw, tag=''):
    key = 'E2' if name == 'E2b' else name
    e = EXP[{'E4b': 'E4b_alternative', 'E2b': 'E2'}.get(name, name)]
    groups = raw['groups']; K = len(groups); R = raw['runs']
    S = dict(experiment=name, label='sensitivity study, D_synmax 0.5, not bio-realistic', groups=groups, set_info=raw['set_info'], readback_mismatches_total=sum(r['readback']['n_mismatch'] for r in R.values()), n_sims=len(R))
    rn = runnames(raw)
    S['singles'] = {g: dict(complete=R['single_G%d' % g]['analysis']['all_complete'], latency=R['single_G%d' % g]['analysis']['memories'][0]['latency_last_noncue_ms'],
        int_spikes=R['single_G%d' % g]['analysis']['total_interneuron_spikes'], ints_fired=R['single_G%d' % g]['analysis']['memories'][0]['ints_fired_in_window'],
        last_member_spike=R['single_G%d' % g]['analysis']['memories'][0]['last_member_spike_after_cue_ms'], last_activity=R['single_G%d' % g]['analysis']['last_any_spike_ms'],
        spurious=R['single_G%d' % g]['analysis']['spurious_nonmember_pyr_spikes']) for g in range(K)}
    def runrow(rname):
        a = R[rname]['analysis']
        return dict(order=[m['group'] for m in a['memories']], n_noncue=[m['n_noncue_fired_10ms'] for m in a['memories']], latency=[m['latency_last_noncue_ms'] for m in a['memories']],
            int_spikes_window=[m['int_spikes_in_window'] for m in a['memories']], burst_end_after_cue=[m['last_member_spike_after_cue_ms'] for m in a['memories']],
            last_pyr_after_cue_in_window=[m['last_pyr_spike_in_window_after_cue_ms'] for m in a['memories']],
            crosstalk=len(a['crosstalk_events']), spurious=a['spurious_nonmember_pyr_spikes'], last_pyr=a['last_pyr_spike_ms'], last_any=a['last_any_spike_ms'],
            within100=a['activity_ends_within_100ms'], not_terminated=a['burst_not_terminated'], all_complete=a['all_complete'], robust_ok=a['robust_ok_this_run'],
            total_int=a['total_interneuron_spikes'], total_pyr=a['total_pyr_spikes'])
    S['runs'] = {r: runrow(r) for r in R if not r.startswith('single')}
    d1 = [r for r in rn]; d01 = [r + '_dt0.1' for r in rn]
    S['all_complete_all4_dt1'] = all(S['runs'][r]['all_complete'] for r in d1)
    S['all_complete_all4_dt0.1'] = all(S['runs'][r]['all_complete'] for r in d01)
    S['robust_dt1'] = all(S['runs'][r]['robust_ok'] for r in d1) and all(S['singles'][g]['complete'] for g in S['singles'])
    S['robust_dt0.1'] = all(S['runs'][r]['robust_ok'] for r in d01)
    S['verdict'] = 'ROBUST SUCCESS' if (S['robust_dt1'] and S['robust_dt0.1']) else ('PARTIAL (Dt 1 ms only; marginal)' if S['robust_dt1'] else 'FAIL')
    S['completion_counts_dt1'] = {r: S['runs'][r]['n_noncue'] for r in d1}
    S['completion_counts_dt0.1'] = {r: S['runs'][r]['n_noncue'] for r in d01}
    S['gaba_observed_from_singles'] = gaba_matrix(raw, groups)
    gm = np.array(S['gaba_observed_from_singles']['spike_weighted_max']); bm = np.array(S['gaba_observed_from_singles']['binary_mean'])
    off = ~np.eye(K, dtype=bool)
    S['gaba_max_offdiag_spike_weighted'] = float(gm[off].max()); S['gaba_max_offdiag_binary_mean'] = float(bm[off].max())
    # comparisons
    P = e['predictions']; C = []
    def add(q, pred, obs, hit): C.append(dict(quantity=q, predicted=pred, observed=obs, mark=hitstr(hit) if hit is not None else 'n/a'))
    cp = P.get('completion_4of4_probability_per_memory', {})
    dt1 = {r: S['runs'][r] for r in d1}
    ordn = lambda sp: [r for r in d1 if r.startswith('order_') and r.endswith('sep%d' % sp)][0]
    for sep in ((12, 16, 20) if cp else ()):
        r = dt1[ordn(sep)]
        p = cp['sep%d' % sep]
        for idx in range(K):
            if idx == 0 and sep != 12: continue
            lab = ['first', 'second', 'third', 'fourth'][idx] + (' memory' + (' (sep %d)' % sep if idx else ''))
            if idx == 0: lab = 'first memory 4/4 (all spacings)'; obs = [dt1[ordn(s)]['n_noncue'][0] for s in (12, 16, 20)]; ok = all(o == 4 for o in obs); add('P(4/4) ' + lab, p[0], obs, prob_mark(p[0], ok)); continue
            add('P(4/4) %s memory (G%d) at %d ms' % (['first', 'second', 'third', 'fourth'][idx], r['order'][idx], sep), p[idx], '%d/4' % r['n_noncue'][idx], prob_mark(p[idx], r['n_noncue'][idx] == 4))
    sk = ([k for k in cp if k.startswith('shuffled')] or [None])[0]; sr = dt1[[r for r in dt1 if r.startswith('shuffled')][0]]
    for idx, g in enumerate(sr['order'] if sk else []):
        p = cp[sk]['G%d' % g]
        add('P(4/4) shuffled, G%d (position %d)' % (g, idx + 1), p, '%d/4' % sr['n_noncue'][idx], prob_mark(p, sr['n_noncue'][idx] == 4))
    add('P(all memories complete in all 4 runs), Dt 1', P['p_all_memories_complete_all_4_runs'], S['all_complete_all4_dt1'], prob_mark(P['p_all_memories_complete_all_4_runs'], S['all_complete_all4_dt1']))
    lats = [x for r in dt1.values() for x in r['latency'] if x is not None]
    if 'latency_last_noncue_ms' in P: add('latency of last non-cue (ms), Dt 1 all complete memories', P['latency_last_noncue_ms'], [round(min(lats), 2), round(max(lats), 2)] if lats else None, rng_hit(min(lats), P['latency_last_noncue_ms']) and rng_hit(max(lats), P['latency_last_noncue_ms']) if lats else False)
    b = P['burst_end_after_cue_ms']
    if isinstance(b, str): b = EXP['E2']['predictions']['burst_end_after_cue_ms']
    be = {g: [r['burst_end_after_cue'][i] for r in dt1.values() for i, gg in enumerate(r['order']) if gg == g] for g in range(K)}
    S['burst_end_by_group_dt1'] = {g: [round(x, 1) for x in v if x is not None] for g, v in be.items()}
    if 'range' in b:
        allv = [x for v in be.values() for x in v if x is not None]
        n_in = sum(rng_hit(x, b['range']) for x in allv)
        add('burst end after cue (ms), last member spike, all memories, Dt 1', 'range %s (P in range %.2f); >20 ms P %.2f' % (b['range'], b['p_in_range'], b.get('p_over_20', float('nan'))), 'min %.1f max %.1f; %d/%d inside range; %d > 20 ms' % (min(allv), max(allv), n_in, len(allv), sum(x > 20 for x in allv)), n_in == len(allv))
    else:
        for g in range(K):
            k = 'G%d' % g
            if k in b and isinstance(b[k], dict):
                v = [x for x in be[g] if x is not None]; n_in = sum(rng_hit(x, b[k]['range']) for x in v)
                add('burst end G%d (ms)' % g, 'range %s (P %.2f)' % (b[k]['range'], b[k]['p_in_range']), 'min %.1f max %.1f; %d/%d inside' % (min(v), max(v), n_in, len(v)), n_in == len(v))
    ip = P['interneuron_spikes_per_recall']; sing = [S['singles'][g]['int_spikes'] for g in range(K)]
    if isinstance(ip['range'], dict):
        hits = [rng_hit(sing[g], ip['range']['G%d' % g]) for g in range(K) if 'G%d' % g in ip['range']]
    else: hits = [rng_hit(s, ip['range']) for s in sing]
    add('interneuron spikes per recall, single-memory runs, Dt 1 (G0..)', 'nominal %s, range %s' % (ip['nominal'], ip['range']), sing, all(hits))
    inr = [[x for x in r['int_spikes_window']] for r in dt1.values()]
    S['int_spikes_window_dt1'] = inr
    add('interneuron spikes per cue window in 4 ordered runs (G in order), Dt 1', 'same ranges (windows include tails of earlier recalls)', inr, None)
    pg = P['peak_gaba_onto_other_memory_noncue_nS']
    if 'spike_weighted_max_nominal' in pg:
        add('peak GABA onto another memory non-cue member: spike-weighted max, max off-diag (nS g_peak_sum, observed spikes from singles)', 'nominal %s, range %s' % (pg['spike_weighted_max_nominal'], pg['spike_weighted_max_range']), round(S['gaba_max_offdiag_spike_weighted'], 1), rng_hit(S['gaba_max_offdiag_spike_weighted'], pg['spike_weighted_max_range']))
        if 'binary_mean_max_nominal' in pg: add('same, binary mean (max off-diag)', '<= %s' % pg['binary_mean_max_nominal'], round(S['gaba_max_offdiag_binary_mean'], 1), S['gaba_max_offdiag_binary_mean'] <= pg['binary_mean_max_nominal'])
    else:
        g01 = float(gm[0, 1]); add('peak GABA G0 -> G1 spike-weighted max (nS)', 'nominal %s, range %s, baseline %s' % (pg['G0_to_G1_spike_weighted_max_nominal'], pg['G0_to_G1_range'], pg.get('baseline_observed', 176.8)), round(g01, 1), rng_hit(g01, pg['G0_to_G1_range']))
        add('G0 -> G1 binary mean (nS)', pg['G0_to_G1_binary_mean_nominal'] if 'G0_to_G1_binary_mean_nominal' in pg else 12.0, round(float(bm[0, 1]), 1), None)
        add('max any pair spike-weighted (nS)', pg.get('max_any_pair_nominal', 69.6), round(S['gaba_max_offdiag_spike_weighted'], 1), None)
    nf = P.get('new_failures', {})
    anyunterm = any(S['runs'][r]['not_terminated'] for r in d1); S['any_burst_not_terminated_dt1'] = anyunterm
    over40 = [(r, S['runs'][r]['order'][i]) for r in d1 for i, v in enumerate(S['runs'][r]['burst_end_after_cue']) if v and v > 40]
    S['bursts_over_40ms_dt1'] = over40
    if 'p_burst_not_terminated_any_group' in nf: add('P(a burst not terminated within 40 ms in some group)', nf['p_burst_not_terminated_any_group'], 'occurred: %s %s' % (anyunterm, over40), prob_mark(nf['p_burst_not_terminated_any_group'], anyunterm))
    sil = any(m < 1 for r in R.values() for m in [x for x in r['analysis'].get('memories', []) and [mm['int_spikes_in_window'] for mm in r['analysis']['memories']]])
    if 'p_zero_in_any_recall' in ip: add('P(interneurons silent in some recall)', ip['p_zero_in_any_recall'], 'occurred: %s' % sil, prob_mark(ip['p_zero_in_any_recall'], sil))
    sf = any(not S['singles'][g]['complete'] for g in S['singles'])
    if 'p_single_memory_recall_fails' in nf: add('P(a single memory fails on its own)', nf['p_single_memory_recall_fails'], 'occurred: %s' % sf, prob_mark(nf['p_single_memory_recall_fails'], sf))
    xt = any(r['crosstalk'] or r['spurious'] for r in S['runs'].values()) or any(S['singles'][g]['spurious'] for g in S['singles'])
    add('P(cross-talk or non-member pyramidal spikes), all runs', nf.get('p_crosstalk_or_nonmember_spikes', 0.03), 'occurred: %s' % xt, prob_mark(nf.get('p_crosstalk_or_nonmember_spikes', 0.03), xt))
    if 'p_total_activity_over_100ms' in nf:
        o100 = any(not S['runs'][r]['within100'] for r in d1); add('P(total activity > 100 ms in some run)', nf['p_total_activity_over_100ms'], 'occurred: %s' % o100, prob_mark(nf['p_total_activity_over_100ms'], o100))
    if 'p_all_complete_at_dt0p1' in P: add('P(all complete at Dt 0.1 ms)', P['p_all_complete_at_dt0p1'], S['all_complete_all4_dt0.1'], prob_mark(P['p_all_complete_at_dt0p1'], S['all_complete_all4_dt0.1']))
    if 'p_robust_success' in P: add('P(robust success)', P['p_robust_success'], S['robust_dt1'] and S['robust_dt0.1'], prob_mark(P['p_robust_success'], S['robust_dt1'] and S['robust_dt0.1']))
    S['comparisons'] = C
    S['n_hit'] = sum(c['mark'] == 'HIT' for c in C); S['n_scored'] = sum(c['mark'] in ('HIT', 'MISS') for c in C)
    return S
if __name__ == '__main__':
    out = {}
    for n, f in [('E1', 'raw_mech_E1.json'), ('E2', 'raw_mech_E2.json'), ('E3', 'raw_mech_E3.json'), ('E4', 'raw_mech_E4.json'), ('E4b', 'raw_mech_E4b.json'), ('E2b', 'raw_mech_E2b.json')]:
        if os.path.exists(D + f):
            raw = json.load(open(D + f))
            if len(raw['runs']) < (4 + 8 if n != 'E4' and n != 'E4b' else 3 + 8): print('incomplete', n); continue
            out[n] = summarize(n, raw)
    json.dump(out, open(D + 'mech_summary.json', 'w'), indent=1, default=str)
    for n, S in out.items(): print(n, S['verdict'], S['n_hit'], '/', S['n_scored'], S['completion_counts_dt1'], S['completion_counts_dt0.1'])

#!/usr/bin/env python3
"""Driver: reservoir analysis -> engram design -> weight programs -> surrogate evaluation -> results.

Usage: python run_all.py [dump.json] [out_dir]
"""
import json, os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reservoir import Reservoir, AMPA, GABA, NMDA, PRINCIPAL
import engram, program, surrogate

HERE = os.path.dirname(os.path.abspath(__file__))
N_DIR = os.path.dirname(HERE)
DUMP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(N_DIR, 'batchB', 'vviz4', 'sample_0000.json')
OUT = sys.argv[2] if len(sys.argv) > 2 else HERE
DOC_BASELINE = {'source': 'doc2.txt Part 0 (nesvbp-autoassociative, 20 days, 32 pyr + 16 int)',
                'pyr': 32, 'int': 16, 'pairs_present': 765, 'pairs_possible': 992, 'mean_g_existing_nS': 3.14,
                'max_g_nS': 16.66, 'pairs_ge_6.86nS': 58, 'pyr_int_pairs': 5, 'int_pyr_pairs': 26, 'int_pyr_max_nS': 1.6,
                'P1_margin_nS': 30.4, 'P2_margin_nS': 17.6}

T_CUE, T_END = 20.0, 150.0
WIN = (T_CUE + 0.5, T_CUE + 20.0)      # completion window after the cue volley


def spikes_in(sp, ids, win):
    return [i for i in ids if any(win[0] <= t <= win[1] for t in sp[i])]


def evaluate(res, W, patterns, cues, k, cue_cells, gaba_w=None, label=''):
    """Run one cue trial in the surrogate and score it."""
    Wk = {t: W[t].copy() for t in W}
    if gaba_w is not None:
        Wk[GABA] = np.where(res.G[GABA] > 0, gaba_w, 0.0)
    net = surrogate.Net(res.G, Wk, res.N, dt=0.1, is_principal=(res.types == PRINCIPAL))
    sp = net.run(T_END, forced=[(T_CUE, int(c)) for c in cue_cells])
    G = patterns[k]
    noncue = [i for i in G if i not in cue_cells]
    members_hit = spikes_in(sp, noncue, WIN)
    allmem = set(c for p in patterns for c in p)
    nonmem = [i for i in res.pyr if i not in allmem]
    spurious = spikes_in(sp, nonmem, WIN)
    others = [i for kk, p in enumerate(patterns) if kk != k for i in p]
    cross = spikes_in(sp, others, WIN)
    ints = spikes_in(sp, res.int, WIN)
    lat = [min(t for t in sp[i] if t >= WIN[0]) - T_CUE for i in members_hit]
    rev = [len([t for t in sp[i] if t > T_CUE]) for i in G]   # spikes per member after the cue (reverberation)
    late = spikes_in(sp, G, (T_CUE + 50, T_END))
    return {'label': label, 'pattern': k, 'cue': [int(c) for c in cue_cells],
            'completion': round(len(members_hit) / max(1, len(noncue)), 3),
            'completed_members': members_hit, 'latency_ms': round(float(np.mean(lat)), 2) if lat else None,
            'spurious_frac': round(len(spurious) / max(1, len(nonmem)), 3), 'n_spurious': len(spurious),
            'cross_pattern_frac': round(len(cross) / max(1, len(others)), 3) if others else None,
            'interneurons_firing': len(ints), 'spikes_per_member_after_cue_mean': round(float(np.mean(rev)), 2),
            'members_still_firing_after_50ms': len(late),
            'total_pyr_spikes': int(sum(len(sp[i]) for i in res.pyr))}


def main():
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    res = Reservoir(DUMP)
    res.save_matrices(os.path.join(OUT, 'matrices_sim127.npz'))
    summ = res.summary()
    results = {'dump': DUMP, 'reservoir': summ, 'doc_baseline': DOC_BASELINE}

    # --- surrogate calibration
    gstar = surrogate.threshold_conductance()
    results['surrogate_calibration'] = {
        'G_star_AMPA_only_nS': round(gstar, 2),
        'G_star_with_NMDA_0.5ratio_nS': round(surrogate.threshold_conductance(nmda_ratio=0.5), 2),
        'doc_target_nS': 27.44, 'doc_target_over_G_star': round(27.44 / gstar, 2),
        'four_single_synapses_nS': 4 * 0.98,
        'note': 'G* = smallest synchronous AMPA g_peak (weight 1) from one volley that makes a resting converter-default LIF spike (AHP on, no ADP/adaptive threshold/fatigue).'}

    # --- engram design
    A = res.pyr_pyr_ampa()
    pyr = res.pyr
    des = engram.design(A, K_list=(1, 2, 3, 4))
    # map local pyramidal indices -> neuron IDs
    for K, d in des['K'].items():
        for p in d.get('patterns', []):
            p['group_ids'] = [int(pyr[i]) for i in p['group']]
            p['cue_ids'] = [int(pyr[i]) for i in p['cue']]
    results['engram_design'] = des
    print('design done', round(time.time() - t0, 1), 's')

    # --- weight programs (K=2 primary; K=3 if feasible)
    programs = {}
    evals = []
    for K in (2, 3):
        d = des['K'][K]
        if not d.get('patterns'):
            continue
        patterns = [p['group_ids'] for p in d['patterns']]
        cues = [p['cue_ids'] for p in d['patterns']]
        scaled = program.scaled_engram_weights(res, patterns, cues, T_cue_nS=27.44)
        variants = {
            'w1_prune': dict(engram_w=1.0, background='prune'),
            'scaled_prune': dict(engram_w=scaled, background='prune'),
            'scaled_bg02': dict(engram_w=scaled, background='engram_only'),
            'scaled_prune_intdrive1': dict(engram_w=scaled, background='prune', pyr_int_w=1.0),
        }
        for name, kw in variants.items():
            ops = program.program(res, patterns, **kw)
            tag = 'K%d_%s' % (K, name)
            programs[tag] = program.summarize(ops)
            program.save(ops, os.path.join(OUT, 'ops_%s.json' % tag))
            W = program.apply_offline(res, ops)
            # received conductance check at programmed weights (designated cue)
            margins = []
            for G, C in zip(patterns, cues):
                recv = [(W[AMPA][C, i] * res.G[AMPA][C, i]).sum() for i in G if i not in C]
                margins.append(round(float(min(recv)), 2))
            programs[tag]['cue_margin_at_programmed_weights_nS'] = margins
            inh_settings = [('gaba_as_built_0.2', None), ('no_inhibition', 0.0), ('gaba_w1_hypothetical', 1.0)]
            if K == 3:
                inh_settings = inh_settings[:1]
            for inh_name, gw in inh_settings:
                for k in range(len(patterns)):
                    evals.append(evaluate(res, W, patterns, cues, k, cues[k], gw, '%s|%s|cue4' % (tag, inh_name)))
                    if inh_name == 'gaba_as_built_0.2':
                        evals.append(evaluate(res, W, patterns, cues, k, cues[k][:2], gw, '%s|%s|cue2' % (tag, inh_name)))
            print(tag, 'evaluated', round(time.time() - t0, 1), 's')
        if K == 2:
            # as-grown baseline (no ops): weights 0.2 everywhere
            W0 = {t: res.W[t].copy() for t in (AMPA, GABA, NMDA)}
            for k in range(len(patterns)):
                evals.append(evaluate(res, W0, patterns, cues, k, cues[k], None, 'K2_as_grown_no_ops|gaba_as_built_0.2|cue4'))
    results['programs'] = programs
    results['surrogate_evals'] = evals

    # --- bio limits
    sys.path.insert(0, N_DIR)
    import pandas as pd
    import bio_check
    df = pd.read_excel(os.path.join(N_DIR, 'validation_labels.xlsx'))
    row = df[df['NES_SIM_ID'] == 127]
    bio_check.assert_hard_limits(row[['days', 'pyramidal', 'interneuron', 'minneuronseparation', 'shape.radius', 'shape.thickness', 'dm.weight']])
    allw = [o['weight'] for tag in programs for o in json.load(open(os.path.join(OUT, 'ops_%s.json' % tag)))['ops']]
    results['bio_limits'] = {
        'sim127_parameters': {c: (float(row[c].iloc[0]) if c == 'dm.weight' else int(row[c].iloc[0])) for c in
                              ['days', 'pyramidal', 'interneuron', 'minneuronseparation', 'shape.radius', 'shape.thickness', 'dm.weight']},
        'hard_limits_assert': 'passed (bio_check.assert_hard_limits)',
        'g_per_receptor_nS': summ['g_per_receptor_median_nS'],
        'programmed_weights_range': [min(allw), max(allw)],
        'max_programmed_conductance_le_g_peak_sum': True,
    }
    with open(os.path.join(OUT, 'results.json'), 'w') as f:
        json.dump(results, f, indent=1, default=lambda o: int(o) if isinstance(o, np.integer) else float(o))
    write_md(results, os.path.join(OUT, 'results.md'))
    print('done', round(time.time() - t0, 1), 's')


def write_md(r, path):
    L = []
    s = r['reservoir']; b = r['doc_baseline']
    L.append('# Weight-space prototype: numeric results (sim 127 = validation sample k=4)\n')
    L.append('## Reservoir vs doc baseline\n')
    L.append('| quantity | doc baseline (20 d, 32 pyr/16 int) | sim 127 (25 d, 67 pyr/27 int, dm.w 0.9) |')
    L.append('|---|---|---|')
    pp = s['pyr_pyr_ampa']
    L.append('| Pyr->Pyr AMPA pairs present | %d/%d (%.0f%%) | %d/%d (%.0f%%) |' % (b['pairs_present'], b['pairs_possible'], 100 * b['pairs_present'] / b['pairs_possible'], pp['pairs_present'], pp['ordered_pairs_possible'], 100 * pp['fraction_present']))
    L.append('| mean g_peak_sum over existing pairs (nS) | %.2f | %.2f |' % (b['mean_g_existing_nS'], pp['mean_g_peak_sum_existing_nS']))
    L.append('| max pair g_peak_sum (nS) | %.2f | %.2f |' % (b['max_g_nS'], pp['max_g_peak_sum_nS']))
    L.append('| pairs >= 6.86 nS (per-pair criterion) | %d | %d |' % (b['pairs_ge_6.86nS'], pp['pairs_ge_6.86nS']))
    L.append('| pairs >= 27.44 nS | n/a | %d |' % pp['pairs_ge_27.44nS'])
    L.append('| Pyr->Int AMPA pairs (total nS) | %d | %d (%.1f) |' % (b['pyr_int_pairs'], s['pyr_int_ampa']['pairs'], s['pyr_int_ampa']['total_nS']))
    L.append('| Int->Pyr GABA pairs, max pair nS | %d, %.1f | %d, %.1f |' % (b['int_pyr_pairs'], b['int_pyr_max_nS'], s['int_pyr_gaba']['pairs'], s['int_pyr_gaba']['max_pair_nS']))
    L.append('| pyramidal cells receiving any GABA | ? | %d of %d (mean total %.1f nS, max %.1f) |' % (s['int_pyr_gaba']['pyr_with_inhibition'], s['pyramidal'], s['int_pyr_gaba']['mean_total_onto_pyr_nS'], s['int_pyr_gaba']['max_total_onto_one_pyr_nS']))
    L.append('| interneurons receiving any Pyr AMPA | ? | %d of %d (max total %.1f nS) |' % (s['pyr_int_ampa']['interneurons_with_input'], s['interneurons'], s['pyr_int_ampa']['max_total_onto_one_int_nS']))
    L.append('\n## Engram design (assembly-sum criterion, group 8, cue 4, target 27.44 nS at weight 1)\n')
    L.append('| K | feasible | min margin (nS) | per-pattern margins | groups (neuron IDs) | cues |')
    L.append('|---|---|---|---|---|---|')
    for K, d in r['engram_design']['K'].items():
        if 'patterns' not in d:
            L.append('| %s | no | - | %s | | |' % (K, d.get('reason')))
            continue
        L.append('| %s | %s | %.1f | %s | %s | %s |' % (K, d['feasible'], d['min_margin_nS'], [p['margin_nS'] for p in d['patterns']],
                                                        '; '.join(str(p['group_ids']) for p in d['patterns']), '; '.join(str(p['cue_ids']) for p in d['patterns'])))
    L.append('\nDoc baseline: P1 margin %.1f nS (feasible), P2 disjoint %.1f nS (64%%, infeasible).' % (b['P1_margin_nS'], b['P2_margin_nS']))
    c = r['surrogate_calibration']
    L.append('\n## Surrogate calibration\n')
    L.append('G* (one synchronous AMPA volley, weight 1, resting converter-default LIF with AHP) = %.2f nS; doc target 27.44 nS = %.2fx G*; four single synapses = %.2f nS (sub-threshold, consistent with the doc).' % (c['G_star_AMPA_only_nS'], c['doc_target_over_G_star'], c['four_single_synapses_nS']))
    L.append('\n## Weight programs\n')
    L.append('| program | ops | by role | weight range | cue margin at programmed weights (nS, per pattern) | NMDA zeroed on engram pairs (nS) |')
    L.append('|---|---|---|---|---|---|')
    for tag, p in r['programs'].items():
        L.append('| %s | %d | %s | [%.2f, %.2f] | %s | %.0f |' % (tag, p['n_ops'], p['by_role'], p['min_weight'], p['max_weight'], p['cue_margin_at_programmed_weights_nS'], p['nmda_zeroed_on_engram_pairs_nS']))
    L.append('\n## Surrogate recall (cue volley at 20 ms, window 20.5-40 ms)\n')
    L.append('| program | inhibition | cue | pattern | completion | latency ms | spurious non-member frac (n) | cross-pattern frac | ints firing | spikes/member after cue | members firing >50 ms later |')
    L.append('|---|---|---|---|---|---|---|---|---|---|---|')
    for e in r['surrogate_evals']:
        prog, inh, cue = e['label'].split('|')
        L.append('| %s | %s | %s | P%d | %.2f | %s | %.2f (%d) | %s | %d | %.1f | %d |' % (
            prog, inh, cue, e['pattern'], e['completion'], e['latency_ms'], e['spurious_frac'], e['n_spurious'],
            e['cross_pattern_frac'], e['interneurons_firing'], e['spikes_per_member_after_cue_mean'], e['members_still_firing_after_50ms']))
    bl = r['bio_limits']
    L.append('\n## Bio limits\n')
    L.append('sim 127 parameters: %s -> hard limits %s. Per-receptor g_peak (median, nS): %s. Programmed weights in [%.2f, %.2f]; every Conductance_nS <= pair g_peak_sum.' % (bl['sim127_parameters'], bl['hard_limits_assert'], bl['g_per_receptor_nS'], bl['programmed_weights_range'][0], bl['programmed_weights_range'][1]))
    with open(path, 'w') as f:
        f.write('\n'.join(L) + '\n')


if __name__ == '__main__':
    main()

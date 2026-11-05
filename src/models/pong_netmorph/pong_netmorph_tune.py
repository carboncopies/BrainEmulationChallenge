#!/usr/bin/env python3
"""pong_netmorph_tune.py: write calibrated strengths onto a grown model's EXISTING pairs.

  python pong_netmorph_tune.py -Model johnjose-pong-g1 -Out output [-Tuned johnjose-pong-g1-tuned]

For every neuron pair that has a synapse in the grown connectome:
  intended AMPA edge   -> set total conductance (nS): B->U/D -GB, P->U/D -GP (excitatory variant), U->UP/D->DOWN -GOut
  intended GABA edge   -> CANNOT be set: NES BatchSetPrePostStrength/SetPrePostStrength only write
                          the first AMPA receptor of a pair (LIFCNeuron::UpdatePrePostStrength), so a
                          GABA-only pair is left at its grown strength. Reported.
  unintended pair      -> -Unintended zero (default): set to 0 (a GABA-only pair is zeroed by the 'clear the
                          others' branch although the call returns an error status); 'keep': untouched.
Missing intended edges cannot be restored by tuning; they are listed in the summary.

Two NES facts found while doing this (see README):
  * ModelSave writes the receptor structs as built by Netmorph, NOT the edited per-pair weights, so a
    reloaded '-tuned' model is identical to the grown one. The tuning is therefore saved as a RECIPE
    (output/<tuned>_recipe.json) that apply_recipe() re-applies after ModelLoad (pong_handwired -Model does this).
  * The effective conductance of a pair is min(g_peak_sum, weight*g_peak_sum*g_norm): a set value above
    the grown g_peak_sum of that pair is capped at it. The recipe records the achievable value.
"""
import argparse
import json
import os
import sys

import nes_loop as NL
import pong_spec as S
import pong_netmorph_analyze as AN

STEP1 = dict(B=10.0, OUT=20.0)      # step-1 calibrated AMPA conductances (nS)


def parse_args(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument('-Host', default='localhost')
    p.add_argument('-Port', default=8100, type=int)
    p.add_argument('-Model', default='johnjose-pong-grown')
    p.add_argument('-Tuned', default=None, help='default <Model>-tuned')
    p.add_argument('-Out', default='output')
    p.add_argument('-GB', default=STEP1['B'], type=float, help='B_i -> U_i/D_i total AMPA conductance (nS)')
    p.add_argument('-GP', default=None, type=float,
                   help='P_j -> U/D total AMPA conductance (nS), pyramidal-paddle variant only (default GB)')
    p.add_argument('-GOut', default=STEP1['OUT'], type=float, help='U->UP, D->DOWN (nS)')
    p.add_argument('-Unintended', default='zero', choices=['zero', 'keep'])
    p.add_argument('-Calibrate', action='store_true',
                   help='excitatory (pyramidal-paddle) variant: choose a per-comparator-cell input scale k_i '
                        '(B_i and P_j incoming g = min(k_i, g_peak_sum)) from measured responses, see calibrate()')
    p.add_argument('-KGrid', default='1,1.5,2,2.5,3,3.5,4,5,6,8,10', help='comma list of k values (nS) to try')
    p.add_argument('-Rm', default=None, type=float,
                   help='optional: MembraneResistance_MOhm for the two output cells UP and DOWN only. '
                        'A neuron edit, NOT a weight edit: reported separately in the README.')
    p.add_argument('-Vth', default=None, type=float, help='optional: SpikeThreshold_mV for UP and DOWN only')
    return p.parse_args(argv)


def load_summary(sim, model, ptype):
    summ = dict(model=model, ptype=ptype)
    ab = sim.GetAbstractConnectome(Sparse=True)
    summ['Regions'], summ['PrePostNumReceptors'] = ab['Regions'], ab['PrePostNumReceptors']
    summ['Connectome'] = sim.GetConnectome()
    return summ


def compute_recipe(summ, GB, GP, GOut, unintended='zero', Rm=None, Vth=None):
    role = AN.role_of(summ)
    pairs = AN.pair_table(summ)
    paddle = 'gaba' if summ['ptype'] == 'interneuron' else 'ampa'
    intended = {(pre, post): (cls, sg) for cls, pre, post, sg in S.edges(paddle=paddle)}
    gp = GP if GP is not None else GB
    rec = dict(ptype=summ['ptype'], regions=summ['Regions'], params=dict(GB=GB, GP=gp, GOut=GOut, unintended=unintended),
               ampa=[], zero_gaba=[], left_gaba=[], capped=[], neuron_edit=None)
    pars = {}
    if Rm is not None:
        pars['MembraneResistance_MOhm'] = Rm
    if Vth is not None:
        pars['SpikeThreshold_mV'] = Vth
    if pars:
        ids = [summ['Regions'][r_][0] for r_ in ('UP', 'DOWN')]
        rec['neuron_edit'] = dict(ids=sorted(ids), pars=pars)
        rec['params'].update(pars)
    for (a, b), v in sorted(pairs.items()):
        key = (role[a], role[b])
        gsum = v['ampa']
        if key in intended:
            cls, sg = intended[key]
            if sg > 0 and gsum > 0:
                g = {'B->U': GB, 'B->D': GB, 'P->U': gp, 'P->D': gp, 'U->UP': GOut, 'D->DOWN': GOut}[cls]
                rec['ampa'].append([a, b, g, min(g, gsum)])
                if g > gsum:
                    rec['capped'].append([role[a], role[b], g, gsum])
            elif sg < 0 and v['gaba'] > 0:
                rec['left_gaba'].append([role[a], role[b], v['gaba']])
            elif unintended == 'zero':
                (rec['ampa'] if v['ampa'] > 0 else rec['zero_gaba']).append([a, b, 0.0, 0.0] if v['ampa'] > 0 else [a, b])
        elif unintended == 'zero':
            (rec['ampa'] if v['ampa'] > 0 else rec['zero_gaba']).append([a, b, 0.0, 0.0] if v['ampa'] > 0 else [a, b])
    return rec


def apply_recipe(sim, rec):
    """Apply a recipe to a freshly loaded grown model (in-memory only, see module docstring)."""
    regions = sim.GetAbstractConnectome(Sparse=True)['Regions']
    assert regions == rec['regions'], 'neuron/role mapping of the loaded model differs from the recipe'
    if rec['ampa']:
        r = sim.BatchSetPrePostStrength([x[0] for x in rec['ampa']], [x[1] for x in rec['ampa']],
                                        [x[2] for x in rec['ampa']])
        assert r.get('StatusCode', 0) == 0, r
    ne = rec.get('neuron_edit')
    if ne:
        r = sim.EditLIFCNeuron(ne['ids'], dict(ne['pars']))
        assert r.get('StatusCode', 0) == 0, r
    for a, b in rec['zero_gaba']:
        sim.SetPrePostStrength(a, b, 0.0)   # error status for GABA-only pairs, but the pair is zeroed


def calibrate(sim, summ, rec, kgrid, spacing=100):
    """Per-cell input-scale calibration for the excitatory coincidence variant.

    For each k in kgrid every incoming B/P pair of every comparator cell X (U_i, D_i) is set to
    min(k, g_peak_sum of that pair) and one probe run presents, 100 ms apart: B_i alone (8 trials),
    P_j alone (8), and every (B_i, P_j) combination (64). Cell X_i scores a point for
      - silence on B_i alone, silence on each P_j alone that feeds it,
      - at least one spike on (B_i, P_j) for each intended (existing) P_j -> X_i edge.
    The k with the most points (middle of ties) is kept per cell. Only response measurements are used, no
    knowledge of the NES internals; unintended pairs are already zeroed in rec.
    Returns (per-cell k dict role->k, per-cell score table).
    """
    import numpy as np
    import pong_handwired as H
    role = AN.role_of(summ)
    ids = {r: v[0] for r, v in summ['Regions'].items()}
    gsum = {}
    pairs = AN.pair_table(summ)
    for (a, b), v in pairs.items():
        gsum[(a, b)] = v['ampa']
    inc = {}   # post id -> list of (pre id, pre role)
    for a, b, g, geff in rec['ampa']:
        if g > 0 and role[b][0] in 'UD' and role[b] not in ('UP', 'DOWN'):
            inc.setdefault(b, []).append((a, role[a]))
    cells = sorted(inc)
    n = S.N
    net = H.Net()
    net.B = {i: H.Role(ids['B%d' % i]) for i in range(n)}
    net.P = {i: H.Role(ids['P%d' % i]) for i in range(n)}
    base_pairs = [x for x in rec['ampa']]
    # trials: (name, ball or None, paddle or None)
    trials = [('B', b, None) for b in range(n)] + [('P', None, p) for p in range(n)] + \
             [('BP', b, p) for b in range(n) for p in range(n)]
    score = {c: {} for c in cells}
    for k in kgrid:
        pre_l, post_l, g_l = [], [], []
        for a, b, g, geff in base_pairs:
            if b in inc and any(a == x[0] for x in inc[b]) and g > 0:
                g = min(k, gsum[(a, b)])
            pre_l.append(a); post_l.append(b); g_l.append(g)
        r = sim.BatchSetPrePostStrength(pre_l, post_l, g_l)
        assert r.get('StatusCode', 0) == 0, r
        st = sim.GetStatus()
        t0 = st['InSimulationTime_ms'] + 10
        pairs_t, starts = [], {}
        for q, (nm, b, p) in enumerate(trials):
            s0 = t0 + q * spacing
            starts[(nm, b, p)] = s0
            for kk in range(H.BURST_SPIKES):
                if p is not None:
                    pairs_t.append([s0 + H.PADDLE_OFFSET_MS + kk * H.BURST_ISI_MS, net.P[p].ID])
                if b is not None:
                    pairs_t.append([s0 + H.BALL_OFFSET_MS + kk * H.BURST_ISI_MS, net.B[b].ID])
        pairs_t.sort(key=lambda x: x[0])
        sim.SetSpecificAPTimes([[float(t), int(i)] for t, i in pairs_t])
        end = t0 + len(trials) * spacing + spacing
        sim.RunFor(end - st['InSimulationTime_ms'], 1.0)
        while sim.GetStatus()['IsSimulating']:
            import time; time.sleep(0.05)
        data = sim.GetSpikeTimes()['SpikeTimes'] or {}
        for c in cells:
            v = data.get(str(c), data.get(c, []))
            v = np.array(v['tSpike_ms'] if isinstance(v, dict) else v)
            def fired(key):
                s0 = starts[key]
                return bool(v.size and ((v >= s0) & (v < s0 + spacing)).any())
            pts, tot = 0, 0
            feeding_B = [x for x in inc[c] if x[1][0] == 'B']
            feeding_P = [x for x in inc[c] if x[1][0] == 'P']
            for _, rb in feeding_B:
                bi = int(rb[1:])
                tot += 1; pts += (not fired(('B', bi, None)))
                for _, rp in feeding_P:
                    pj = int(rp[1:])
                    tot += 2
                    pts += (not fired(('P', None, pj)))
                    pts += fired(('BP', bi, pj))
            score[c][k] = (pts, tot)
    chosen, table = {}, {}
    for c in cells:
        best = max(v[0] for v in score[c].values())
        ks = sorted(k for k, v in score[c].items() if v[0] == best)
        chosen[role[c]] = ks[len(ks) // 2]
        table[role[c]] = {str(k): score[c][k] for k in kgrid}
    return chosen, table


def effective_strengths(sim, role):
    """Per role pair: sum of min(weight*g_peak_sum, g_peak_sum) (sign by transmitter) after tuning, read back from the server."""
    c = sim.GetConnectome()
    eff = {}
    for pre, (tg, ty, gp_, w) in enumerate(zip(c['ConnectionTargets'], c['ConnectionTypes'],
                                               c['ConnectionGPeakSum'], c['ConnectionWeights'])):
        for post, k, g, ww in zip(tg, ty, gp_, w):
            if k == AN.NMDA:
                continue
            key = '%s>%s' % (role[pre], role[post])
            eff[key] = eff.get(key, 0.0) + min(g * ww, g) * (-1 if k == AN.GABA else 1)  # peak capped at g_peak_sum (Neuron.cpp:152-155)
    return eff, c


def main(argv=None):
    A = parse_args(argv)
    tuned = A.Tuned or A.Model + '-tuned'
    ptype = json.load(open(os.path.join(A.Out, '%s_connectome.json' % A.Model))).get('ptype', 'interneuron')
    client = NL.connect(A.Host, A.Port)
    sim = NL.new_simulation(client, 'tune-' + A.Model)
    sim.SetLIFCAbstractedFunctional(_AbstractedFunctional=True)
    sim.SetSTDP(_DoSTDP=False)
    sim.ModelLoad(A.Model)
    summ = load_summary(sim, A.Model, ptype)
    rec = compute_recipe(summ, A.GB, A.GP, A.GOut, A.Unintended, A.Rm, A.Vth)
    role = AN.role_of(summ)
    if A.Calibrate:
        kgrid = [float(x) for x in A.KGrid.split(',')]
        ks, table = calibrate(sim, summ, rec, kgrid)
        rec['calibration'] = dict(k_per_cell=ks, scores=table, kgrid=kgrid)
        pairs = AN.pair_table(summ)
        for x in rec['ampa']:
            a, b = x[0], x[1]
            if x[2] > 0 and role[b] in ks:
                x[2] = min(ks[role[b]], pairs[(a, b)]['ampa']) if role[a][0] in 'BP' else x[2]
                x[3] = x[2]
        print('calibrated per-cell k:', ks)
    apply_recipe(sim, rec)
    eff, conn = effective_strengths(sim, role)
    rec['effective_strength_nS'] = eff
    json.dump(rec, open(os.path.join(A.Out, '%s_recipe.json' % tuned), 'w'))
    sim.ModelSave(tuned)   # NOTE: stores the grown receptor structs, not the edit (see docstring)
    nz = {k: v for k, v in eff.items() if abs(v) > 1e-9}
    print('recipe: %d AMPA pairs set/zeroed (%d at target, %d capped by g_peak_sum), %d GABA-only pairs zeroed, '
          '%d intended GABA pairs left at grown strength'
          % (len(rec['ampa']), sum(1 for x in rec['ampa'] if x[2] > 0), len(rec['capped']),
             len(rec['zero_gaba']), len(rec['left_gaba'])))
    print('nonzero effective pairs after tuning: %d (saved %s, recipe %s_recipe.json)' % (len(nz), tuned, tuned))
    # summary of the tuned state for the analysis (zero-weight pairs are dropped from the connectome view)
    summ_t = dict(summ, model=tuned, Connectome=conn, effective_strength_nS=eff, tuning=rec['params'])
    json.dump(summ_t, open(os.path.join(A.Out, '%s_connectome.json' % tuned), 'w'))
    return 0


if __name__ == '__main__':
    sys.exit(main())

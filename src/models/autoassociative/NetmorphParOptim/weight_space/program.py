#!/usr/bin/env python3
"""Weight-space programming: turn engram designs into BatchSetPrePostStrength operations.

Server semantics (PROVEN from BrainGenix-NES source, Simulation.cpp:1358-1391 and
LIFCNeuron.cpp:543-559): BatchSetPrePostStrength(PreSyn[], PostSyn[], Conductance_nS[]) sets, on the
POST neuron, the first AMPA receptor-data from PRE to  weight = Conductance_nS / g_peak_sum_nS  and sets
every other receptor-data from that PRE (i.e. the pair's NMDA) to weight 0. It returns false (and the
batch stops at that element, earlier elements already applied) if PRE has no AMPA onto POST. There is
NO clamp in this call, so staying inside [0,1] is the caller's job: we require Conductance_nS <= g_peak_sum.

Weights cannot create synapses: a pair with no grown AMPA cannot be programmed (doc B4), and GABA
pairs cannot be touched at all by this API (interneuron as PRE fails the batch).
"""
import json
import numpy as np
from reservoir import AMPA, GABA, NMDA, PRINCIPAL

W_MIN, W_MAX = 0.0, 1.0


def scaled_engram_weights(res, patterns, cues, T_cue_nS=27.44):
    """Per-postsynaptic-cell weight scaling so that the designated 4-cell cue delivers ~T_cue to every
    non-cue member and the full group delivers ~T_cue*(|G|-1)/|C| (keeps recurrent drive bounded instead
    of using weight 1.0 everywhere). Returns dict (pre, post) -> weight in [0,1]."""
    A = res.G[AMPA]
    w = {}
    for G, C in zip(patterns, cues):
        for i in G:
            others = [j for j in G if j != i and A[j, i] > 0]
            tot = A[others, i].sum() if others else 0.0
            s = min(1.0, T_cue_nS * (len(G) - 1) / len(C) / tot) if tot > 0 else 1.0
            if i not in C:
                cue_tot = A[[j for j in C if A[j, i] > 0], i].sum()
                if cue_tot > 0:
                    s = max(s, min(1.0, T_cue_nS / cue_tot))
            for j in others:
                w[(j, i)] = s
    return w


def program(res, patterns, engram_w=1.0, background='prune', pyr_int_w=None):
    """Return list of op dicts.
    patterns: list of lists of pyramidal neuron IDs (disjoint groups).
    engram_w: float weight for all within-engram pairs, or dict (pre, post) -> weight.
    background: 'prune' -> every Pyr->Pyr AMPA pair not inside one engram is set to 0;
                'engram_only' -> only pairs touching an engram cell are pruned, others untouched (0.2 as built);
                'none' -> no pruning at all.
    pyr_int_w: if not None, set every existing Pyr->Int AMPA pair to this weight (in [0,1]).
    """
    A = res.G[AMPA]
    member_of = {}
    for k, G in enumerate(patterns):
        for c in G:
            assert res.types[c] == PRINCIPAL, 'engram cells must be pyramidal'
            assert c not in member_of, 'patterns must be disjoint'
            member_of[c] = k
    ops = []
    pyr = res.pyr
    for pre in pyr:
        for post in pyr:
            if pre == post or A[pre, post] <= 0:
                continue  # no grown AMPA synapse: cannot be programmed (and the API would fail)
            kp, kq = member_of.get(pre), member_of.get(post)
            if kp is not None and kp == kq:
                w = engram_w[(pre, post)] if isinstance(engram_w, dict) else engram_w
                role = 'engram_P%d' % kp
            elif kp is not None or kq is not None:
                w, role = 0.0, 'prune_cross' if (kp is not None and kq is not None) else 'prune_offpattern'
            else:
                if background == 'prune':
                    w, role = 0.0, 'prune_background'
                else:
                    continue
            if background == 'none' and w == 0.0:
                continue
            ops.append(_op(res, pre, post, w, role))
    if pyr_int_w is not None:
        for pre in pyr:
            for post in res.int:
                if A[pre, post] > 0:
                    ops.append(_op(res, pre, post, pyr_int_w, 'pyr_int_drive'))
    validate(res, ops)
    return ops


def _op(res, pre, post, w, role):
    g = float(res.G[AMPA][pre, post])
    return {'pre': int(pre), 'post': int(post), 'weight': float(w), 'g_peak_sum_nS': g,
            'conductance_nS': float(w * g), 'nmda_zeroed_nS': float(res.G[NMDA][pre, post]), 'role': role}


def validate(res, ops):
    A = res.G[AMPA]
    seen = set()
    for o in ops:
        assert W_MIN <= o['weight'] <= W_MAX, o
        assert A[o['pre'], o['post']] > 0, 'pair has no AMPA: %r' % o
        assert res.types[o['pre']] == PRINCIPAL, 'interneuron as PRE would fail the batch: %r' % o
        assert o['conductance_nS'] <= o['g_peak_sum_nS'] + 1e-9, o
        assert (o['pre'], o['post']) not in seen, 'duplicate pair'
        seen.add((o['pre'], o['post']))
    return True


def to_batch_args(ops):
    """The three parallel lists BatchSetPrePostStrength(PreSyn, PostSyn, Conductance_nS) takes."""
    return [o['pre'] for o in ops], [o['post'] for o in ops], [o['conductance_nS'] for o in ops]


def apply_offline(res, ops):
    """Effective weight matrices after the ops (what the server state would be)."""
    W = {t: res.W[t].copy() for t in (AMPA, GABA, NMDA)}
    for o in ops:
        W[AMPA][o['pre'], o['post']] = o['weight']
        W[NMDA][o['pre'], o['post']] = 0.0  # side effect of the API (gap C2)
    return W


def summarize(ops):
    from collections import Counter
    c = Counter(o['role'] for o in ops)
    return {'n_ops': len(ops), 'by_role': dict(c),
            'max_weight': max((o['weight'] for o in ops), default=0.0),
            'min_weight': min((o['weight'] for o in ops), default=0.0),
            'engram_conductance_total_nS': round(sum(o['conductance_nS'] for o in ops if o['role'].startswith('engram')), 2),
            'nmda_zeroed_on_engram_pairs_nS': round(sum(o['nmda_zeroed_nS'] for o in ops if o['role'].startswith('engram')), 2)}


def save(ops, path):
    pre, post, g = to_batch_args(ops)
    with open(path, 'w') as f:
        json.dump({'ops': ops, 'BatchSetPrePostStrength': {'PreSyn': pre, 'PostSyn': post, 'Conductance_nS': g}}, f)

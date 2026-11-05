#!/usr/bin/env python3
"""pong_netmorph_analyze.py: wiring fidelity of a grown model vs the step-1 spec.

Reads the connectome summary JSON written by pong_netmorph_grow.py (or
pong_netmorph_tune.py) -- no server needed.

  python pong_netmorph_analyze.py output/johnjose-pong-g1_connectome.json [-json out.json]

Definitions (neuron-pair level, as in the abstract connectome):
  intended edge      (pre role, post role, sign) from pong_spec.edges()
  present            the pair has at least one synapse of the intended sign
  wrong_sign         the pair exists but only with the opposite transmitter
  missing            no synapse between the pair
  unintended pair    pair present that is not an intended edge; broken down by
                     pre class -> post class (B,P,U,D,UP,DOWN); 'recurrent/backward'
                     = target is in an earlier stage (B/P) or the same pair reversed.
Precision = correct-sign intended pairs / all pairs present. Recall = correct-sign / intended.
"""
import argparse
import json
import sys
from collections import Counter, defaultdict

import pong_spec as S

AMPA, GABA, NMDA = 1, 2, 3   # ConnectionTypes codes in the client connectome


def pair_table(summ):
    """{(pre_id, post_id): {'ampa':g, 'gaba':g, 'nmda':g, 'n': numreceptors(non-NMDA)}}"""
    c = summ['Connectome']
    t = {}
    for pre, (tg, ty, gp) in enumerate(zip(c['ConnectionTargets'], c['ConnectionTypes'], c['ConnectionGPeakSum'])):
        for post, k, g in zip(tg, ty, gp):
            d = t.setdefault((pre, post), dict(ampa=0.0, gaba=0.0, nmda=0.0, n=0))
            d[{AMPA: 'ampa', GABA: 'gaba', NMDA: 'nmda'}[k]] += g
    for pre, post, cnt in summ['PrePostNumReceptors']:
        if (pre, post) in t:
            t[(pre, post)]['n'] = cnt
    return t


def role_of(summ):
    return {nid: r for r, ids in summ['Regions'].items() for nid in ids}


def analyze(summ, effective=False):
    """effective=True: only count pairs whose tuned strength is non-zero (needs 'effective_strength_nS')."""
    role = role_of(summ)
    pairs = pair_table(summ)
    pairs_by_role = {(role[a], role[b]): v for (a, b), v in pairs.items()}
    if effective:
        eff = summ['effective_strength_nS']
        pairs_by_role = {k: v for k, v in pairs_by_role.items() if abs(eff.get('%s>%s' % k, 0.0)) > 1e-9}
    paddle = 'gaba' if summ.get('ptype', 'interneuron') == 'interneuron' else 'ampa'
    intended = {(pre, post): (cls, sg) for cls, pre, post, sg in S.edges(paddle=paddle)}
    per_cls = {c: Counter() for c in S.EDGE_CLASSES}
    missing, wrong = [], []
    for (pre, post), (cls, sg) in intended.items():
        v = pairs_by_role.get((pre, post))
        if v is None:
            per_cls[cls]['missing'] += 1
            missing.append((pre, post))
        else:
            have = v['ampa'] > 0 if sg > 0 else v['gaba'] > 0
            if have:
                per_cls[cls]['present'] += 1
            else:
                per_cls[cls]['wrong_sign'] += 1
                wrong.append((pre, post))
        per_cls[cls]['intended'] += 1
    unint = Counter()
    unint_list = []
    for (pre, post), v in pairs_by_role.items():
        if (pre, post) in intended:
            continue
        pc, qc = S.role_class(pre), S.role_class(post)
        sign = 'AMPA' if v['ampa'] > 0 else 'GABA'
        stage = {'B': 0, 'P': 0, 'U': 1, 'D': 1, 'UP': 2, 'DOWN': 2}
        kind = 'backward/recurrent' if stage[qc] <= stage[pc] else 'forward'
        unint[(pc + '->' + qc, kind)] += 1
        unint_list.append((pre, post, sign, kind))
    tot_int = sum(c['intended'] for c in per_cls.values())
    tot_ok = sum(c['present'] for c in per_cls.values())
    tot_pairs = len(pairs_by_role)
    res = dict(per_class={k: dict(v) for k, v in per_cls.items()},
               total_intended=tot_int, total_correct=tot_ok, total_pairs=tot_pairs,
               total_unintended=len(unint_list),
               precision=tot_ok / tot_pairs if tot_pairs else 0.0,
               recall=tot_ok / tot_int if tot_int else 0.0,
               unintended_by_class={'%s|%s' % k: v for k, v in unint.items()},
               missing=missing, wrong_sign=wrong, unintended=unint_list)
    return res


def print_report(res):
    print('\nIntended edge classes (pairs):')
    print('%-9s %9s %9s %10s %8s %7s' % ('class', 'intended', 'present', 'wrong_sign', 'missing', 'recall'))
    for c in S.EDGE_CLASSES:
        v = res['per_class'][c]
        print('%-9s %9d %9d %10d %8d %7.2f' % (c, v['intended'], v.get('present', 0), v.get('wrong_sign', 0),
                                               v.get('missing', 0), v.get('present', 0) / v['intended']))
    print('\nUnintended pairs by pre->post class:')
    for k, v in sorted(res['unintended_by_class'].items(), key=lambda kv: -kv[1]):
        print('  %-14s %s %d' % (k.split('|')[0], k.split('|')[1], v))
    print('\nTotals: intended %d, present with right sign %d, all pairs present %d, unintended %d'
          % (res['total_intended'], res['total_correct'], res['total_pairs'], res['total_unintended']))
    print('Precision %.3f  Recall %.3f' % (res['precision'], res['recall']))


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument('summary')
    p.add_argument('-json', default=None)
    p.add_argument('-Effective', action='store_true', help='tuned summary: ignore pairs tuned to zero')
    A = p.parse_args(argv)
    summ = json.load(open(A.summary))
    res = analyze(summ, A.Effective)
    print_report(res)
    if A.json:
        json.dump(res, open(A.json, 'w'), indent=1)
    return 0


if __name__ == '__main__':
    sys.exit(main())

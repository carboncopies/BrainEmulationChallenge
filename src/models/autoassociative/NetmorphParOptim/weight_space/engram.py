#!/usr/bin/env python3
"""Engram (assembly) design on a grown reservoir using the doc's assembly-sum criterion.

Criterion (doc §0.1/B1): for group G (|G| = PATTERNSIZE) and cue C subset of G (|C| = CUESIZE),
every non-cue member i in G\\C must receive  sum_{j in C} g_peak_sum[j -> i]  >=  TARGET nS
at weight 1.0 (TARGET = 27.44 nS = RETRIEVALPEAKCONDUCTANCEATMAXWEIGHT).
margin(G) = max over cues C of  min_{i in G\\C} sum_{j in C} A[j, i].

Greedy growth from every seed (maximizing the minimum in-group received conductance), a swap
local search, then the exact best-cue evaluation. Joint (disjoint) selection of K patterns is done
by exhaustive combination over the candidate pool, maximizing the minimum margin across patterns.
"""
import itertools
import numpy as np

TARGET_nS = 27.44
PATTERNSIZE = 8
CUESIZE = 4


def best_cue(A, G, cuesize=CUESIZE):
    """Return (margin, cue) maximizing min received conductance over non-cue members."""
    G = list(G)
    best = (-1.0, None)
    for C in itertools.combinations(G, cuesize):
        rest = [i for i in G if i not in C]
        recv = A[np.ix_(list(C), rest)].sum(axis=0)
        m = float(recv.min())
        if m > best[0]:
            best = (m, list(C))
    return best


def _group_objective(A, G):
    # minimum over members of conductance received from the other members
    idx = list(G)
    sub = A[np.ix_(idx, idx)]
    return float((sub.sum(axis=0) - np.diag(sub)).min()) if len(idx) > 1 else 0.0


def grow_group(A, seed, size=PATTERNSIZE, allowed=None):
    n = A.shape[0]
    allowed = set(range(n)) if allowed is None else set(allowed)
    G = [seed]
    while len(G) < size:
        cands = [i for i in allowed if i not in G]
        if not cands:
            return None
        # score = min over members of received-from-group, after adding i
        scores = [_group_objective(A, G + [i]) for i in cands]
        G.append(cands[int(np.argmax(scores))])
    return G


def improve_group(A, G, allowed=None, iters=50):
    """Swap local search on the exact best-cue margin."""
    n = A.shape[0]
    allowed = set(range(n)) if allowed is None else set(allowed)
    G = list(G)
    cur, _ = best_cue(A, G)
    for _ in range(iters):
        improved = False
        outside = [i for i in allowed if i not in G]
        for k in range(len(G)):
            for i in outside:
                H = G.copy()
                H[k] = i
                m, _ = best_cue(A, H)
                if m > cur + 1e-9:
                    G, cur, improved = H, m, True
                    break
            if improved:
                break
        if not improved:
            break
    return G, cur


def candidate_pool(A, allowed=None, size=PATTERNSIZE):
    """One improved candidate group per seed; returns list of (margin, cue, group) sorted desc."""
    n = A.shape[0]
    allowed = list(range(n)) if allowed is None else list(allowed)
    pool = {}
    for s in allowed:
        G = grow_group(A, s, size, allowed)
        if G is None:
            continue
        G, m = improve_group(A, G, allowed)
        key = tuple(sorted(G))
        if key not in pool:
            mm, cue = best_cue(A, list(key))
            pool[key] = (mm, cue, list(key))
    return sorted(pool.values(), key=lambda x: -x[0])


def select_joint(A, K, size=PATTERNSIZE, allowed=None, pool=None, topM=40):
    """Choose K disjoint groups maximizing the minimum margin. Exhaustive over the top-M pool,
    with a greedy-with-exclusion fallback (regrow after removing chosen cells) merged in."""
    n = A.shape[0]
    allowed = list(range(n)) if allowed is None else list(allowed)
    pool = candidate_pool(A, allowed, size) if pool is None else pool
    cands = pool[:topM]
    # Add greedy-exclusion candidates: regrow on the complement of the best group(s)
    chosen, remaining = [], set(allowed)
    for _ in range(K):
        sub = candidate_pool(A, sorted(remaining), size)
        if not sub:
            break
        chosen.append(sub[0])
        remaining -= set(sub[0][2])
        cands.extend(sub[:5])
    # exhaustive over disjoint K-combinations in cands
    best = None
    for combo in itertools.combinations(range(len(cands)), K):
        cells = [c for k in combo for c in cands[k][2]]
        if len(set(cells)) != len(cells):
            continue
        mm = min(cands[k][0] for k in combo)
        if best is None or mm > best[0]:
            best = (mm, [cands[k] for k in combo])
    return best  # (min margin, [(margin, cue, group), ...])


def design(A, K_list=(1, 2, 3), target=TARGET_nS):
    pool = candidate_pool(A)
    out = {'target_nS': target, 'patternsize': PATTERNSIZE, 'cuesize': CUESIZE,
           'n_candidate_groups': len(pool), 'K': {}}
    for K in K_list:
        sel = select_joint(A, K, pool=pool)
        if sel is None:
            out['K'][K] = {'feasible': False, 'reason': 'not enough cells'}
            continue
        pats = []
        for (m, cue, G) in sel[1]:
            pats.append({'group': [int(x) for x in G], 'cue': [int(x) for x in cue],
                         'margin_nS': round(m, 2), 'meets_target': bool(m >= target),
                         'fraction_of_target': round(m / target, 3)})
        out['K'][K] = {'feasible': all(p['meets_target'] for p in pats), 'min_margin_nS': round(sel[0], 2),
                       'patterns': pats}
    return out

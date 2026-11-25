"""Profiles (profiles/<name>.json) and the comparison of computed metrics with literature entries.

Profile fields
  name, description, species, tissue
  type_map   : {model type name -> profile type name}, e.g. {"excitatory": "pyramidal", "inhibitory": "interneuron"}; unmapped names pass through
  defaults   : {"tolerance_rel": 0.5, "sd_k": 2.0}
  comments   : {metric id or metric family -> text shown next to the check}
  literature : list of entries, each
      metric          metric id in profile type names (see rt/stats.py), e.g. "length.axon.interneuron"
      stat            "mean" | "median" | "max" (which model statistic is compared; default "mean")
      value / sd / range [lo, hi] (lo or hi may be null)  -- leave value and range null for a TODO entry
      unit, reference, source_tissue, evidence (READ / DERIVED / RECALLED / ...), verified (bool), derived_estimate (bool),
      comparable (bool, default true; false = shown as 'info', e.g. a whole-cell axon against a local patch), comment
Status: pass (inside range, or within sd_k*sd of value, or within tolerance_rel of value), flag (outside), unknown (no literature number),
info (not comparable like for like), n/a (the model has no such metric)."""
import json, os, re
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_profile(name_or_path):
    p = name_or_path if os.path.isfile(name_or_path) else os.path.join(HERE, 'profiles', name_or_path + '.json')
    prof = json.load(open(p)); prof['_path'] = os.path.abspath(p)
    prof.setdefault('type_map', {}); prof.setdefault('defaults', {}); prof.setdefault('literature', []); prof.setdefault('comments', {})
    return prof

def rename_types(metrics, type_map, model_types):
    """metric ids use model type names; rewrite them into profile type names."""
    tm = {t: type_map.get(t, t) for t in model_types}
    if len(set(tm.values())) < len(tm): raise ValueError('type_map merges several model types into one profile type: %s' % tm)
    out = {}
    for k, v in metrics.items():
        parts = k.split('.'); out['.'.join(tm.get(p, p) for p in parts)] = v
    return out, tm

def status_of(x, e, d):
    if e.get('comparable', True) is False: return 'info'
    rng, val, sd = e.get('range'), e.get('value'), e.get('sd')
    if rng is None and val is None: return 'unknown'
    if x is None: return 'n/a'
    if rng is not None:
        lo, hi = rng; return 'pass' if (lo is None or x >= lo) and (hi is None or x <= hi) else 'flag'
    if sd: return 'pass' if abs(x - val) <= d.get('sd_k', 2.0) * sd else 'flag'
    return 'pass' if val and abs(x / val - 1) <= d.get('tolerance_rel', 0.5) else 'flag'

def compare(metrics, prof):
    d = prof['defaults']; rows = []
    for e in prof['literature']:
        m = metrics.get(e['metric']); st = e.get('stat', 'mean'); x = m.get(st) if m else None
        rows.append(dict(e, model_value=x, model_mean=m.get('mean') if m else None, model_median=m.get('median') if m else None, model_n=m.get('n') if m else None,
                         status=status_of(x, e, d) if m or (e.get('range') is None and e.get('value') is None) else 'n/a'))
    return rows

def comment_for(metric, prof):
    c = prof.get('comments', {}); best = None
    for k, v in c.items():
        if metric == k or metric.startswith(k + '.'):
            if best is None or len(k) > len(best[0]): best = (k, v)
    return best[1] if best else ''

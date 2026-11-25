#!/usr/bin/env python3
"""Realism tester: compute Randal's realism checks for a grown model and compare them with a tissue profile.

usage: realism_tester.py --model <path-or-id> [--model ...] --profile ca3 --out report/ [--format auto|netmorph|nes] [--name LABEL ...]
                         [--region disc:cx,cy,cz,R,T | --region-from NETMORPH_DIR]
                         [--voxel 20] [--cell-types FILE|NETMORPH_DIR] [--no-one-axon-rule] [--volume-um3 V]
  --model  a NetMorph output folder, a NES saved model file, or an id resolved through roots.json (alias, NetMorph uuid or NES model name).
           With an alias that has both forms, --format picks one (auto = netmorph).
Outputs in --out: report.html (self-contained), results.json, summary.txt, grids/<name>/<grid>.npy + grids.json, radial.json.
Reads model files only (read-only); no NES API, no simulation."""
import argparse, json, os, sys, time, re, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from rt import io_netmorph, io_nes, stats, grids as GR, compare as CP, report as RP

def resolve(spec, fmt):
    if os.path.exists(spec): return os.path.abspath(spec)
    roots = json.load(open(os.path.join(HERE, 'roots.json')))
    al = roots.get('aliases', {}).get(spec)
    if al:
        f = 'netmorph' if fmt in ('auto', 'netmorph') and 'netmorph' in al else 'nes'
        spec = al[f]; fmt = f
    for r in (roots.get('netmorph_roots', []) if fmt in ('auto', 'netmorph') else []) + (roots.get('nes_model_roots', []) if fmt in ('auto', 'nes') else []):
        p = os.path.join(r, spec)
        if os.path.exists(p): return p
    raise SystemExit('model %r not found (not a path, alias or id under roots.json)' % spec)

def detect(path, fmt):
    if fmt == 'netmorph' or (fmt == 'auto' and io_netmorph.is_netmorph_dir(path)): return 'netmorph'
    if fmt == 'nes' or (fmt == 'auto' and io_nes.is_nes_model(path)): return 'nes'
    raise SystemExit('cannot detect the input format of %s (use --format)' % path)

def cell_types_from(spec, model_labels):
    if spec is None: return None
    if os.path.isdir(spec) or spec.endswith('.neurons'):
        f = spec if spec.endswith('.neurons') else [os.path.join(spec, x) for x in os.listdir(spec) if x.endswith('_net.txt.neurons')][0]
        lab = {}
        for l in open(f):
            if l[0] != '#' and l.strip(): p = l.split(','); lab[p[1]] = p[2]
        return [lab[x] for x in model_labels]
    v = json.load(open(spec)); return [v[x] for x in model_labels] if isinstance(v, dict) else list(v)

def notes_for(m, metrics, prof):
    n = []
    if m.meta.get('duplicated_neurite_geometry'):
        r = m.meta.get('relabel') or {}
        n.append('NES model file stores every neurite cylinder twice (dendrite and axon compartment lists are identical copies holding both dendrites and axons); '
                 'the tester used one copy and inferred axon/dendrite per neurite tree from synapse roles (%d trees; %d set to dendrite by the one-axon-per-cell rule; %d trees with both pre- and postsynaptic sites; unclassified length %.1f%%).'
                 % (r.get('n_trees', 0), r.get('trees_set_to_dendrite_by_rule', 0), r.get('trees_with_both_pre_and_post_sites', 0), 100 * r.get('unclassified_length_frac', 0)))
    if m.meta.get('input_format') == 'netmorph': n.append('NetMorph node files carry no radii: only length density is available (no volume fraction).')
    for k, v in metrics.items():
        if k.startswith('ball_index.') and v.get('mean') and v['mean'] > 2: n.append('%s = %.1f: the neurite is %.1fx denser near the centre than near the rim (axon/dendrite ball).' % (k, v['mean'], v['mean']))
    return n

def run_one(path, fmt, name, prof, args, outdir):
    t0 = time.time(); kind = detect(path, fmt)
    if kind == 'netmorph': m = io_netmorph.load(path)
    else: m = io_nes.load(path, one_axon_per_cell=not args.no_one_axon_rule)
    if args.region:
        sh, v = args.region.split(':', 1); cx, cy, cz, r, t = [float(x) for x in v.split(',')]; assert sh == 'disc', 'only disc regions are supported'
        m.region = dict(name='cli', shape='disc', center=[cx, cy, cz], radius=r, thickness=t, volume_um3=float(np.pi * r * r * t), source='--region')
    elif args.region_from:
        m.region = io_netmorph.read_region(args.region_from); m.region['source'] = '--region-from ' + m.region.get('source', '')
    ct = cell_types_from(args.cell_types, m.meta.get('cell_labels', []))
    if ct is not None: m.cell_type = list(ct); m.meta['cell_type_source'] = 'supplied: %s' % args.cell_types
    metrics, info = stats.compute(m, args.volume_um3)
    G, gmeta, prof_r = GR.build(m, voxel=args.voxel)
    for k, v in prof_r['ball_index'].items():
        if v is None: continue
        note = 'slab density r<R/3 over 2R/3<=r<R (R=%.0f um, %s)' % (prof_r['R_um'], prof_r['centre_source'])
        if v == float('inf'): v, note = 1e9, note + '; rim is empty, index infinite (shown as 1e9)'
        metrics['ball_index.%s' % k] = stats.single(v, note)
    pm, tmap = CP.rename_types(metrics, prof['type_map'], m.types)
    rows = CP.compare(pm, prof)
    def ren(k):   # rename type tokens in grid / radial keys
        return '.'.join(tmap.get(p, p) for p in k.split('.'))
    G = {ren(k): v for k, v in G.items()}; gmeta['units'] = {ren(k): v for k, v in gmeta['units'].items()}
    prof_r['series'] = {ren(k): v for k, v in prof_r['series'].items()}; prof_r['ball_index'] = {ren(k): (1e9 if v == float('inf') else v) for k, v in prof_r['ball_index'].items()}
    gd = os.path.join(outdir, 'grids', name); os.makedirs(gd, exist_ok=True)
    for k, g in G.items(): np.save(os.path.join(gd, k + '.npy'), g)
    json.dump(gmeta, open(os.path.join(gd, 'grids.json'), 'w'), indent=1)
    emb = {k: dict(RP.quantise(g), unit=gmeta['units'][k]) for k, g in G.items() if '_volfrac.' not in k and not (k.startswith('soma.') and not k.endswith('.all'))}
    comments = dict(prof.get('comments', {}))
    notes = notes_for(m, pm, prof)
    meta = dict(m.meta); meta['seconds'] = round(time.time() - t0, 1)
    print('%s: %s, %d cells, %d segments, %d contacts, %.0fs' % (name, kind, m.n_cells, len(m.seg_cell), len(m.syn_pre), time.time() - t0), flush=True)
    return dict(name=name, meta=meta, info=info, region=m.region, type_map=tmap, metrics=pm, comparisons=rows, comments=comments, notes=notes,
                defaults=dict(dict(tolerance_rel=0.5, sd_k=2.0), **prof['defaults']), grid=gmeta, grids=emb, radial=prof_r)

def summary_text(models, prof):
    out = ['Realism tester summary (profile %s)' % prof['name']]
    for M in models:
        out += ['', '== %s (%s) %s' % (M['name'], M['meta']['input_format'], M['meta']['path']), 'cells %s; volume %s um^3 (%s); contacts %d' % (M['info']['types'], M['info']['volume_um3'], M['info']['volume_source'], M['info']['n_contacts'])]
        for n in M['notes']: out.append('NOTE ' + n)
        out.append('%-46s %10s %10s  %-22s %-8s %s' % ('metric', 'mean', 'median', 'literature', 'status', 'evidence'))
        for r in M['comparisons']:
            litv = ('%s-%s' % tuple(r['range'])) if r.get('range') else (('%s+/-%s' % (r['value'], r['sd'])) if r.get('sd') else str(r.get('value')))
            f = lambda x: '-' if x is None else ('%.4g' % x)
            out.append('%-46s %10s %10s  %-22s %-8s %s%s' % (r['metric'], f(r['model_mean']), f(r['model_median']), litv[:22], r['status'], 'verified' if r.get('verified') else 'unverified', ', derived estimate' if r.get('derived_estimate') else ''))
    return '\n'.join(out) + '\n'

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--model', action='append', required=True); ap.add_argument('--name', action='append'); ap.add_argument('--profile', default='ca3')
    ap.add_argument('--out', required=True); ap.add_argument('--format', default='auto', choices=['auto', 'netmorph', 'nes']); ap.add_argument('--voxel', type=float, default=20.0)
    ap.add_argument('--cell-types'); ap.add_argument('--region', help='disc:cx,cy,cz,radius,thickness (um)'); ap.add_argument('--region-from', help='NetMorph output folder whose .nibr.clp region to use'); ap.add_argument('--no-one-axon-rule', action='store_true'); ap.add_argument('--volume-um3', type=float)
    args = ap.parse_args(argv)
    prof = CP.load_profile(args.profile); os.makedirs(args.out, exist_ok=True); models = []
    for i, spec in enumerate(args.model):
        path = resolve(spec, args.format); name = (args.name[i] if args.name and i < len(args.name) else re.sub(r'[^A-Za-z0-9_.-]', '_', spec if not os.path.exists(spec) else os.path.basename(os.path.normpath(spec))))
        models.append(run_one(path, args.format, name, prof, args, args.out))
    gen = time.strftime('%Y-%m-%d %H:%M')
    RP.write(os.path.join(args.out, 'report.html'), models, prof, gen)
    res = [{k: v for k, v in M.items() if k not in ('grids', 'radial')} for M in models]
    json.dump(dict(generated=gen, profile=prof['name'], profile_path=prof['_path'], models=res), open(os.path.join(args.out, 'results.json'), 'w'), indent=1, default=lambda o: None)
    json.dump({M['name']: M['radial'] for M in models}, open(os.path.join(args.out, 'radial.json'), 'w'), indent=1)
    open(os.path.join(args.out, 'summary.txt'), 'w').write(summary_text(models, prof))
    print('wrote', os.path.join(args.out, 'report.html'))

if __name__ == '__main__': main()

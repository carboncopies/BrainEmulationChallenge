#!/usr/bin/env python3
"""Step 0 audit (read-only): axon centre-collapse check on existing NES NetMorph output folders.
usage: python3 -I audit.py   -> writes results.json and results_table.md next to this script.
Inputs only read: /var/lib/BrainGenix/NES/Admonishing/NetmorphOutput/<uuid>/*  (neurons, rootnodes, continuationnodes, bifurcationnodes, growthcones, .nibr.clp)."""
import glob, os, re, json, collections, numpy as np
ROOT = '/var/lib/BrainGenix/NES/Admonishing/NetmorphOutput'
HERE = os.path.dirname(os.path.abspath(__file__))
def clpval(txt, key):
    m = re.search(r'^' + re.escape(key) + r'=([^;\n]*);', txt, re.M); return m.group(1) if m else None
# label by (seed, n_int, axon B_inf, dend B_inf)
LABEL = {(20240628,20,3.5,48):'pv_arbor V1', (20240628,20,5.0,48):'pv_arbor V2', (20240628,23,5.0,48):'pv_arbor V3',
         (20240628,26,5.0,48):'pv_arbor V4 (or dendrite_rerun 26/5)', (20240628,20,5.0,20):'pv_arbor V5', (20240628,26,5.0,20):'pv_arbor V6',
         (20240628,26,3.5,48):'S1 (dendrite_rerun grow_S1 / pv_arbor ref)'}
for s in (31415,27182,16180):
    LABEL[(s,26,3.5,48)]='seeds S1'; LABEL[(s,20,3.5,48)]='seeds V1'; LABEL[(s,23,5.0,48)]='seeds V3'
def audit(d):
    nt = {}
    for l in open(glob.glob(d+'/*.neurons')[0]):
        if l[0] != '#': p = l.split(','); nt[p[1]] = (p[2], np.array(p[4:7], float))
    pos = {}; par = {}; typ = {}; soma = {}; kind = {}
    for e in ('rootnodes','continuationnodes','bifurcationnodes','growthcones'):
        for l in open(glob.glob(d+'/*.'+e)[0]):
            if l[0] == '#': continue
            p = l.split(','); i = int(p[0]); pos[i] = np.array(p[3:6], float); typ[i] = p[2]; soma[i] = p[6]; kind[i] = e
            if e != 'rootnodes': par[i] = int(p[7])
    # attractor mix
    mix = collections.Counter(nt[soma[i]][0] for i in kind if kind[i]=='bifurcationnodes' and typ[i]=='dendrite')
    # per-cell axon node stats
    nodes = collections.defaultdict(list)
    for i in kind:
        if typ[i]=='axon' and kind[i]!='rootnodes': nodes[soma[i]].append(pos[i])
    out = {'attractor_mix': dict(mix)}
    for ct in ('interneuron','pyramidal'):
        bands = {'0-40':[], '40-80':[], '80-120':[]}; allr = []; nbeyond = 0; ntot = 0
        for s,v in nodes.items():
            if nt[s][0] != ct: continue
            a = np.array(v); sp = nt[s][1]; rs = np.hypot(*sp[:2]); rc = np.hypot(a[:,0], a[:,1]); rsoma = np.linalg.norm(a-sp, axis=1)
            nbeyond += int((rc>120).sum()); ntot += len(a)
            b = '0-40' if rs<40 else ('40-80' if rs<80 else '80-120')
            bands[b].append((np.median(rc), np.median(rsoma)))   # per-cell medians
        out[ct] = {'frac_nodes_r_gt_120': nbeyond/max(ntot,1), 'n_nodes': ntot,
                   'bands': {b: {'n_cells': len(v), 'median_dist_from_centre': float(np.mean([x[0] for x in v])) if v else None,
                                 'median_dist_from_own_soma': float(np.mean([x[1] for x in v])) if v else None} for b,v in bands.items()}}
    # path vs straight line for growth cones
    plen = {}
    def pl(i):
        chain = []; j = i
        while j not in plen and j in par and par[j] in pos: chain.append(j); j = par[j]
        if j not in plen: plen[j] = 0.0
        base = plen[j]
        for k in reversed(chain): base += float(np.linalg.norm(pos[k]-pos[par[k]])); plen[k] = base
        return plen[i]
    res = collections.defaultdict(list)
    for i in kind:
        if kind[i]=='growthcones' and typ[i]=='axon':
            res[nt[soma[i]][0]].append((pl(i), float(np.linalg.norm(pos[i]-nt[soma[i]][1]))))
    for ct,v in res.items():
        a = np.array(v); m = a[:,0]>100
        out[ct]['cones'] = len(a); out[ct]['path_len_median'] = float(np.median(a[:,0])); out[ct]['straight_mean'] = float(a[:,1].mean())
        out[ct]['straight_over_path'] = float(np.mean(a[m,1]/a[m,0])) if m.sum() else None
    return out
rows = []
for d in sorted(glob.glob(ROOT+'/*/')):
    c = glob.glob(d+'*_.nibr.clp')
    if not c or not glob.glob(d+'*.neurons') or not glob.glob(d+'*.growthcones'): continue
    t = open(c[0]).read()
    try:
        seed = int(clpval(t,'randomseed')); py = int(clpval(t,'In.pyramidal')); it = int(clpval(t,'In.interneuron')); rad = clpval(t,'In.shape.radius')
        ab = clpval(t,'all_interneuron_axons.B_inf'); db = clpval(t,'all_interneuron_dendrites.B_inf')
    except Exception: continue
    if py!=96 or rad!='120' or ab is None or db is None: continue
    key = (seed, round(float(ab),3) if float(ab) not in (20,23,26) else float(ab), float(db), it)
    key = (seed, int(float(ab)) if float(ab).is_integer() else float(ab), float(db), it)
    lab = LABEL.get((key[0], key[1], key[2], key[3]))
    if lab is None: continue
    print('auditing', os.path.basename(d.rstrip('/')), lab, flush=True)
    r = audit(d); r.update(folder=os.path.basename(d.rstrip('/')), label=lab, seed=seed, n_int=it, axB=key[1], dendB=key[2], ctime=os.path.getmtime(c[0])); rows.append(r)
json.dump(rows, open(HERE+'/results.json','w'), indent=1)

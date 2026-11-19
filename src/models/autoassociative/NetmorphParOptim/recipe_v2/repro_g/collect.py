"""Step 1: every same-(variant, n_int, seed) pair of finished runs across recipe_v2, with arbor lengths to full precision and run metadata. Read-only."""
import json,glob,re,os,time
W='/home/johnjose/cos/netmorph_work/recipe_v2'
rows=[]
for f in sorted(glob.glob(W+'/*/pv_results*.json')):
    folder=f.split('/')[-2]; fn=os.path.basename(f)
    if folder=='linefix_c' and fn!='pv_results.json': continue   # stage files are subsets of pv_results.json
    d=json.load(open(f))
    for key,v in d.items():
        m=re.match(r'^(S1|V1|V3)(n\d+)?(?:_s(\d+))?',key)
        if not m: continue   # V2,V4.. in pv_arbor handled below
        var=m.group(1); n=int(m.group(2)[1:]) if m.group(2) else v['n_int']; seed=int(m.group(3)) if m.group(3) else 20240628
        gd=os.path.join(W,folder,'grow_'+key); mf=glob.glob(gd+'/model_*'); res=gd+'/result.txt'
        wall=None
        if os.path.exists(res):
            mm=re.search(r'wall=(\d+)',open(res).read()); wall=int(mm.group(1)) if mm else None
        t=os.path.getmtime(res) if os.path.exists(res) else (os.path.getmtime(mf[0]) if mf else None)
        rows.append(dict(folder=folder,key=key,var=var,n_int=n,seed=seed,dir=v['dir'],ia=v['int_axon_len']['len_mean'],idn=v['int_dend_len']['len_mean'],pd=v['pyr_dend_len_mean'],pa=v['pyr_axon_len_mean'],finish=t,wall=wall,
            patched=folder in('linefix','linefix_b','linefix_c','capacity_d','inhib_e','inhib_f'),pyr_pyr=v['pyr_pyr']))
rows=[r for r in rows if not (r['folder']=='pv_arbor' and r['var'] not in('S1','V1','V3'))]
json.dump(rows,open('runs.json','w'),indent=1)
from collections import defaultdict
G=defaultdict(list)
for r in rows: G[(r['var'],r['n_int'],r['seed'])].append(r)
def fmt(t): return time.strftime('%m-%d %H:%M',time.localtime(t)) if t else '-'
for k,g in sorted(G.items()):
    if len(g)<2: continue
    g.sort(key=lambda r:r['finish'] or 0)
    base=g[0]; same=[]
    print('==',k,'runs',len(g))
    for r in g:
        eq=all(abs(r[x]-base[x])<1e-6*max(1,abs(base[x])) for x in('ia','idn','pd','pa'))
        print('  %-26s %-14s %s wall %-5s patched %-5s ia %.4f id %.4f pd %.4f pa %.4f %s'%(r['key'],r['folder'],fmt(r['finish']),r['wall'],r['patched'],r['ia'],r['idn'],r['pd'],r['pa'],'= first' if eq else 'DIFFERS (ia %+.2f%%)'%(100*(r['ia']/base['ia']-1))))

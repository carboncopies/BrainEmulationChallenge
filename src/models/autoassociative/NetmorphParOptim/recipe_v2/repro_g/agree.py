import sys,json,numpy as np
sys.path.insert(0,'.'); import measure
OUT='/home/johnjose/BrainGenix/wt/linefix-instance/out/Admonishing/NetmorphOutput/'
res=json.load(open('rep_results.json')); W='/home/johnjose/cos/netmorph_work/recipe_v2'
D={r:OUT+v['dir'] for r,v in res.items()}
D['A_linefix_b']=OUT+json.load(open(W+'/linefix_b/pv_results.json'))['V1n30_s31415_fix']['dir']
def pos(d):
    nt,p,par,typ,soma=measure.load(d); return np.array([p[i] for i in sorted(p)])
ref=sys.argv[1]; R=pos(D[ref])
for k in sys.argv[2:]:
    P=pos(D[k]); print('%s vs %s: %.4f of %d nodes identical (<1e-3 um)'%(ref,k,float((np.linalg.norm(R-P,axis=1)<1e-3).mean()),len(R)),flush=True)

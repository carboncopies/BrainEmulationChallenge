"""Cell-by-cell arbor comparison (matched by soma position) between repro_g runs; max abs difference of per-cell fibre length and node counts. usage: cellcmp.py REF REP..."""
import sys,json,numpy as np
sys.path.insert(0,'.'); import measure
OUT='/home/johnjose/BrainGenix/wt/linefix-instance/out/Admonishing/NetmorphOutput/'
res=json.load(open('rep_results.json'))
def per(rep):
    d=OUT+res[rep]['dir']; nt=measure.load(d)[0]; out,miss=measure.measure(d); r={}
    for ct in out:
        for t,rows in out[ct].items():
            for s,l,mx,p90,n in rows: r[(tuple(np.round(nt[s][1],3)),ct,t)]=(l,mx,n)
    return r
ref=sys.argv[1]; R=per(ref)
for rep in sys.argv[2:]:
    P=per(rep); ks=sorted(set(R)&set(P)); 
    dl=max(abs(R[k][0]-P[k][0]) for k in ks); dm=max(abs(R[k][1]-P[k][1]) for k in ks); dn=max(abs(R[k][2]-P[k][2]) for k in ks)
    print('%s vs %s: fibres compared %d of %d/%d, max |length diff| %.3e um, max |reach diff| %.3e um, max |node count diff| %d'%(rep,ref,len(ks),len(R),len(P),dl,dm,dn),flush=True)

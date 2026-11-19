import sys,json,glob,numpy as np,os,time
sys.path.insert(0,'.'); import measure
OUT='/home/johnjose/BrainGenix/wt/linefix-instance/out/Admonishing/NetmorphOutput/'
W='/home/johnjose/cos/netmorph_work/recipe_v2'
res=json.load(open('rep_results.json'))
D={r:OUT+v['dir'] for r,v in res.items()}
D['A_linefix_b']=OUT+json.load(open(W+'/linefix_b/pv_results.json'))['V1n30_s31415_fix']['dir']
D['B_linefix_c']=OUT+json.load(open(W+'/linefix_c/pv_results.json'))['V1n30_s31415_p0d0175_i0d0495']['dir']
def pos(d):
    nt,p,par,typ,soma=measure.load(d); ids=sorted(p); return np.array([p[i] for i in ids]),ids
P={}
for k,d in D.items():
    a,ids=pos(d); P[k]=a; n=len(ids)
names=list(P)
print('nodes',{k:len(v) for k,v in P.items()})
print('%-12s'%'', ' '.join('%11s'%n[:11] for n in names))
M={}
for a in names:
    row=[]
    for b in names:
        if len(P[a])!=len(P[b]): row.append('   n/a'); continue
        row.append('%11.4f'%float((np.linalg.norm(P[a]-P[b],axis=1)<1e-3).mean()))
    print('%-12s'%a[:12],' '.join(row),flush=True)

import sys, numpy as np, collections, json
sys.path.insert(0,'.'); from modelfile import *
P='/home/johnjose/BrainGenix/wt/linefix-instance/out/Admonishing/Models/v2-hdi-V1n20_s33333_p0d0175_i0d030000'
h, roff, nl = neurons(P, 116)
print(h, 'receptor off', roff)
r0=nl[0]['rec']; r1=nl[100]['rec']
print({n: (float(r0[n]), float(r1[n])) for n in BASE})
c2n = comp2neuron(nl); rec = np.memmap(P, dtype=RDT, mode='r', offset=roff, shape=(h['Rec'],))
pre = np.array([c2n.get(int(x), -1) for x in rec['Src']]); post = np.array([c2n.get(int(x), -1) for x in rec['Dst']])
print('unmapped src', int((pre<0).sum()), 'dst', int((post<0).sum()))
# aggregate pair GPeakSum per NT
agg = collections.defaultdict(float)
for a,b,nt,g in zip(pre,post,rec['NT'],rec['G']): agg[(int(a),int(b),int(nt))]+=float(g)
print('pairs per NT', collections.Counter(k[2] for k in agg))
# compare to growth dump
sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe'); import recipelib as L
D=L.Dump('/home/johnjose/cos/netmorph_work/recipe_v2/headline_i/grow_V1n20_s33333_p0d0175_i0d03/viz/sample_0000.json')
bad=0; n=0
for (a,b,nt),g in agg.items():
    if nt==0: n+=1; bad += abs(D.G[a,b]-g)>1e-3*max(1,g)
print('AMPA pairs', n, 'mismatch vs dump D.G', bad)
gb=0; ng=0
for (a,b,nt),g in agg.items():
    if nt==1: ng+=1; gb += abs(D.GA[a,b]-g)>1e-3*max(1,g)
print('GABA pairs', ng, 'mismatch vs dump D.GA', gb)

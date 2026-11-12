import sys,numpy as np
P='/home/johnjose/cos/netmorph_work/bec/src/models/autoassociative/NetmorphParOptim'
sys.path.insert(0,P+'/weight_space')
from reservoir import Reservoir,AMPA,GABA,NMDA
F='/home/johnjose/cos/netmorph_work/fable_loop/'
SIMS={127:(P+'/batchB/vviz4/sample_0000.json',20240628,0.1),133:(F+'it1/viz_a/sample_0000.json',20240628,0.5),
134:(F+'it1/viz_b/sample_0000.json',20240628,1.0),141:(F+'r2_seeds/viz_1001/sample_0000.json',1001,0.5),
145:(F+'r2_seeds/viz_1002/sample_0000.json',1002,0.5),146:(F+'r2_seeds/viz_1003/sample_0000.json',1003,0.5),
147:(F+'r2_it4/viz_d03/sample_0000.json',20240628,0.3),151:(F+'r2_it4/viz_d07/sample_0000.json',20240628,0.7)}
PATHS=['PP','PI','IP','II']
def load(s):
    r=Reservoir(SIMS[s][0]); p,i=r.pyr,r.int
    N={'PP':r.NR[AMPA][np.ix_(p,p)],'PI':r.NR[AMPA][np.ix_(p,i)],'IP':r.NR[GABA][np.ix_(i,p)],'II':r.NR[GABA][np.ix_(i,i)]}
    return r,N
def pairs(r,N,path):
    a,b={'PP':(r.pyr,r.pyr),'PI':(r.pyr,r.int),'IP':(r.int,r.pyr),'II':(r.int,r.int)}[path]
    d=np.linalg.norm(r.pos[a][:,None]-r.pos[b][None],axis=2); n=N[path]
    m=np.ones_like(d,bool)
    if path in('PP','II'): m=~np.eye(len(a),dtype=bool)
    ia,ib=np.where(m)
    return d[m],n[m].astype(float),a[ia],b[ib]

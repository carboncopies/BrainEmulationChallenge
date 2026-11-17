"""Threshold finished runs' interneuron pairs at D 0.02 (stored synapse distances); Pyr->Pyr at the grown D 0.0175 unchanged. usage: thr02.py TAG..."""
import sys,json,numpy as np
sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe_v2/linefix_c'); import pairs
FIX=pairs.FIX; pv=json.load(open('pv_results.json'))
def best8(v):
    v=sorted(v,reverse=True); return max(min(sum(v[4:8]),10.0)+sum(v[0:4]),min(sum(v[0:4]),10.0)+sum(v[4:8]))
out={}
for tag in sys.argv[1:]:
    t,xyz,pre,post,dist=pairs.load(FIX+pv[tag]['dir']); n=len(t); P=np.where(t)[0]; I=np.where(~t)[0]
    def M(a,b,th):
        m=np.isin(pre,a)&np.isin(post,b)&(dist<=th); X=np.zeros((n,n),int); np.add.at(X,(pre[m],post[m]),1); return X[np.ix_(a,b)]
    PP=M(P,P,0.0175); np.fill_diagonal(PP,0)
    r={}
    for th in (0.03,0.02):
        PI=M(P,I,th); IP=M(I,P,th); II=M(I,I,th)
        d8=int(sum(best8(PI[:,k]*0.98)>=13.84 for k in range(len(I))))
        r[th]=dict(A=round(float(IP.sum()/(IP.sum()+PP.sum())),3),IP_per_pair=round(float(IP.sum()/(IP>0).sum()),2),PI_per_pair=round(float(PI.sum()/(PI>0).sum()),2),IP=int(IP.sum()),PI=int(PI.sum()),drivable8=d8,IPprob=round(float((IP>0).mean()),3),PP=int(PP.sum()))
    out[tag]=r; print(tag,json.dumps(r))
json.dump(out,open('thr02_%s.json'%('_'.join(a.split('_')[0] for a in sys.argv[1:])),'w'),indent=1)

"""Read-only: 48-interneuron patched runs thresholded at the Stage 2 candidate (pyr 0.0175 / 0.021, int 0.05), for scaling S1/V3 to 30 interneurons."""
import json, numpy as np, sys
sys.path.insert(0,'.'); import pairs
W='/home/johnjose/cos/netmorph_work/recipe_v2'; fx=json.load(open(W+'/linefix/pv_results.json')); fb=json.load(open(W+'/linefix_b/pv_results.json'))
def best8(v):
    v=sorted(v,reverse=True); return max(min(sum(v[4:8]),10.0)+sum(v[0:4]),min(sum(v[0:4]),10.0)+sum(v[4:8]))
out={}
for k,src in [('S1_s16180_fix',fx),('V1_s16180_fix',fx),('V3_s16180_fix',fx),('V1_s31415_fix',fb),('V1_s27182_fix',fb),('S1_s31415_fix',fb),('V3_s31415_fix',fb)]:
    t,xyz,pre,post,dist=pairs.load(pairs.FIX+src[k]['dir']); n=len(t); P=np.where(t)[0]; I=np.where(~t)[0]
    def M(a,b,th):
        m=np.isin(pre,a)&np.isin(post,b)&(dist<=th); X=np.zeros((n,n),int); np.add.at(X,(pre[m],post[m]),1); return X[np.ix_(a,b)]
    r={}
    for th in(0.021,0.0175,0.015):
        S=M(P,P,th); c=S[S>0]; r['PP%g'%th]=(int(S.sum()),round(len(c)/9120,3),round(float(c.mean()),2))
    PI=M(P,I,0.05); IP=M(I,P,0.05)
    r['IP']=(int(IP.sum()),round(float((IP>0).mean()),3),round(float(IP.sum()/(IP>0).sum()),2)); r['PI']=(int(PI.sum()),round(float((PI>0).mean()),3),round(float(PI.sum()/(PI>0).sum()),2))
    r['drv8']=int(sum(best8(PI[:,j]*0.98)>=13.84 for j in range(len(I)))); out[k]=r; print(k,r)
json.dump(out,open('sweep_s2aux_results.json','w'),indent=1)

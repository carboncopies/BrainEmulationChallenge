"""Thresholding model: from patched B3 (V1 48 int, seed 16180, pyr D 0.05) stored synapse distances, Pyr->Pyr pair counts at lower D. Read-only."""
import sys,json,numpy as np
sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe_v2/linefix_c'); import pairs
FIX=pairs.FIX; s1=json.load(open('/home/johnjose/cos/netmorph_work/recipe_v2/linefix_c/pv_results_stage1.json'))
res={}
for k,d in s1.items():
    t,xyz,pre,post,dist=pairs.load(FIX+d['dir']); n=len(t); P=np.where(t)[0]
    m=np.isin(pre,P)&np.isin(post,P)
    out={}
    for th in (0.01,0.0175,0.021,0.03,0.035,0.04,0.05):
        mm=m&(dist<=th); X=np.zeros((n,n),int); np.add.at(X,(pre[mm],post[mm]),1); S=X[np.ix_(P,P)]; np.fill_diagonal(S,0)
        c=S[S>0]; out[th]=dict(syn=int(S.sum()),p=round(len(c)/9120,4),spc=round(float(c.mean()),2),ge5=int((S>=5).sum()),ge5_cells_tg4=int(sum(1 for j in range(96) if (S[:,j]>=5).sum()>=4)))
    res[k]=out; print(k)
    for th,v in out.items(): print('  ',th,v)
json.dump(res,open('thresh_results.json','w'),indent=1)

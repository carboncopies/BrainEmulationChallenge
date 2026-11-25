import numpy as np, rn, itertools, json, sys
d=rn.load_run('s77777_LH_r1_f1','rawB_'); A=d['A']; M=rn.member_matrices('s77777','LH',A,1.0); cl,meta=rn.events_cues(d,A)
sel=[i for i,e in enumerate(meta) if e['kind'] in ('full','p75','p50')]
S=np.array([rn.stored_bins(d,A,i) for i in sel]); 
print('stored median bins (full/p75/p50):',np.median(S,0))
res=[]
for gPI in (0.5,1.,2.,4.):
  for gIP in (0.,0.5,1.,2.,4.):
    R=rn.run_model(M,[cl[i] for i in sel],gPI=gPI,gIP=gIP)
    B=np.array([rn.pop_bins(R,j) for j in range(len(sel))]); loss=float(np.mean((np.log1p(np.median(B,0))-np.log1p(np.median(S,0)))**2))
    res.append((loss,gPI,gIP,np.median(B,0).astype(int).tolist())); print('gPI %.1f gIP %.1f loss %.3f'%(gPI,gIP,loss),np.median(B,0).astype(int).tolist(),flush=True)
res.sort(); json.dump(res,open('calib_grid.json','w')); print('BEST',res[0])

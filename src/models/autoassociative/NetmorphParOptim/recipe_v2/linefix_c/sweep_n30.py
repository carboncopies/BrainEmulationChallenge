"""Read-only: Stage 2 predictions for V1 with 30 interneurons, by thresholding the stored pre-post synapse distance
in the two patched V1n30 runs of ../linefix_b (D 1.5/0.1). -> sweep_n30_results.json"""
import json, numpy as np, sys
sys.path.insert(0,'.'); import pairs
W='/home/johnjose/cos/netmorph_work/recipe_v2'; fb=json.load(open(W+'/linefix_b/pv_results.json'))
def best8(v):
    v=sorted(v,reverse=True); return max(min(sum(v[4:8]),10.0)+sum(v[0:4]),min(sum(v[0:4]),10.0)+sum(v[4:8]))
PD=(1.5,0.05,0.03,0.025,0.0225,0.021,0.02,0.0175,0.015,0.0125,0.01,0.005); ID=(0.1,0.075,0.06,0.05,0.04,0.03)
out={}
for seed in(16180,31415):
    k='V1n30_s%d_fix'%seed; t,xyz,pre,post,dist=pairs.load(pairs.FIX+fb[k]['dir']); n=len(t); P=np.where(t)[0]; I=np.where(~t)[0]
    def M(a,b,th):
        m=np.isin(pre,a)&np.isin(post,b)&(dist<=th); X=np.zeros((n,n),int); np.add.at(X,(pre[m],post[m]),1); return X[np.ix_(a,b)]
    r={'n_pyr':len(P),'n_int':len(I),'PP':{},'int':{},'A':{}}
    for th in PD:
        S=M(P,P,th); c=S[S>0]; npair=len(P)*(len(P)-1)
        r['PP'][th]=dict(syn=int(S.sum()),p_conn=round(len(c)/npair,3),spc=round(float(c.mean()),2),zero_in=int((S.sum(0)==0).sum()),top5_in_share=round(float(np.sort(S.sum(0))[-5:].sum()/S.sum()),3))
    for th in ID:
        PI=M(P,I,th); IP=M(I,P,th); II=M(I,I,th)
        st=lambda S,npair:(int(S.sum()),round(float((S>0).sum()/npair),3),round(float(S.sum()/max(1,(S>0).sum())),2))
        r['int'][th]=dict(PI=st(PI,PI.size),IP=st(IP,IP.size),II=st(II,II.size-len(I)),drivable8=int(sum(best8(PI[:,j]*0.98)>=13.84 for j in range(len(I)))),drivable_simple=int((PI.sum(0)*0.98>=13.84).sum()),zero_in=int((PI.sum(0)==0).sum()),targets_per_int=round(float((IP>0).sum(1).mean()),1),viz_drivable8=fb[k]['drivable_8cell_capaware'] if th==0.1 else None)
        for tp in PD: r['A']['int%g_pp%g'%(th,tp)]=round(float(IP.sum()/(IP.sum()+r['PP'][tp]['syn'])),3)
    out[seed]=r; print('== V1n30',seed,'pyr',len(P),'int',len(I))
    for th,x in r['PP'].items(): print('  PP',th,x)
    for th,x in r['int'].items(): print('  int',th,x)
    print('  A',{a:b for a,b in r['A'].items() if a.split('_pp')[1] in('0.021','0.01','0.05','0.0175')})
json.dump(out,open('sweep_n30_results.json','w'),indent=1)

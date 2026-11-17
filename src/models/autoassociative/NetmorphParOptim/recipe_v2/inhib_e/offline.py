"""Read-only offline predictions for inhib_e: threshold stored synapse distances of existing patched 30-interneuron runs
(pyramidal D 0.0175) at interneuron D 0.04/0.03/0.02, and subsample interneurons to 24 and 20 (1000 random draws).
Subsampling is only a proxy for a regrown 20/24-interneuron network (a new cell count is a new realisation). -> offline_results.json"""
import json, numpy as np, sys
sys.path.insert(0,'../linefix_c'); import pairs
L='../linefix_c/'; pv=json.load(open(L+'pv_results_stage2.json')); pv.update(json.load(open(L+'pv_results_stage2b.json')))
RUNS={'V3n30_s16180':'V3n30_s16180_p0d0175_i0d04','V1n30_s16180':'V1n30_s16180_p0d0175_i0d0495','V3n30_s27182':'V3n30_s27182_p0d0175_i0d04','V1n30_s27182':'V1n30_s27182_p0d0175_i0d0495','V1n30_s31415':'V1n30_s31415_p0d0175_i0d0495'}
def best8(v):
    v=sorted(v,reverse=True); return max(min(sum(v[4:8]),10.0)+sum(v[0:4]),min(sum(v[0:4]),10.0)+sum(v[4:8]))
rng=np.random.default_rng(1); out={}
for name,tag in RUNS.items():
    t,xyz,pre,post,dist=pairs.load(pairs.FIX+pv[tag]['dir']); n=len(t); P=np.where(t)[0]; I=np.where(~t)[0]
    def M(a,b,th):
        m=np.isin(pre,a)&np.isin(post,b)&(dist<=th); X=np.zeros((n,n),int); np.add.at(X,(pre[m],post[m]),1); return X[np.ix_(a,b)]
    PP=M(P,P,0.0175).sum(); out[name]={'PP':int(PP)}; print('==',name,'PP',PP)
    for th in(0.04,0.03,0.02):
        PI=M(P,I,th); IP=M(I,P,th); II=M(I,I,th); drv=np.array([best8(PI[:,j]*0.98)>=13.84 for j in range(len(I))])
        for k in(30,24,20):
            rows=[]
            for _ in range(1 if k==30 else 1000):
                s=np.arange(30) if k==30 else rng.choice(30,k,replace=False)
                ip=IP[s]; pi=PI[:,s]; ii=II[np.ix_(s,s)]
                rows.append([ip.sum()/(ip.sum()+PP), ip.sum()/(ip>0).sum(), (ip>0).mean(), pi.sum()/(pi>0).sum(), (pi>0).mean(), ii.sum()/max(1,(ii>0).sum()), drv[s].sum(), ip.sum(), pi.sum(), ip.sum()/96, (ip.sum(0)==0).sum()])
            r=np.array(rows); m=r.mean(0); lo=np.percentile(r,10,0); hi=np.percentile(r,90,0)
            key='D%g_n%d'%(th,k); out[name][key]=dict(A=round(m[0],3),A_10_90=[round(lo[0],3),round(hi[0],3)],IP_spc=round(m[1],2),IP_p=round(m[2],3),PI_spc=round(m[3],2),PI_p=round(m[4],3),II_spc=round(m[5],2),drivable=round(m[6],1),drivable_10_90=[int(lo[6]),int(hi[6])],IP_syn=int(m[7]),PI_syn=int(m[8]),inh_per_pyr=round(m[9],1),pyr_no_inh=round(m[10],1))
            print(' ',key,out[name][key])
json.dump(out,open('offline_results.json','w'),indent=1)

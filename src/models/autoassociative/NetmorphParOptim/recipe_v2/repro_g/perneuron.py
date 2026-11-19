import sys,json,glob,numpy as np
sys.path.insert(0,'.'); import measure
W='/home/johnjose/cos/netmorph_work/recipe_v2'
BASES=('/var/lib/BrainGenix/NES/Admonishing/NetmorphOutput/','/home/johnjose/BrainGenix/wt/linefix-instance/out/Admonishing/NetmorphOutput/')
def path(folder,key):
    d=json.load(open(W+'/%s/pv_results.json'%folder))[key]['dir']
    for b in BASES:
        if glob.glob(b+d+'/*.neurons'): return b+d
def per(d):
    nt=measure.load(d)[0]; out,miss=measure.measure(d); r={}
    for ct in out:
        for t,rows in out[ct].items():
            for s,l,mx,p90,n in rows: r[(tuple(np.round(nt[s][1],3)),ct,t)]=l
    return r
pairs=[(('pv_arbor_seeds','V1_s27182'),('linefix_b','V1_s27182_fix')),(('linefix_b','V1n30_s31415_fix'),('linefix_c','V1n30_s31415_p0d0175_i0d0495')),
       (('linefix_c','V1n30_s27182_p0d0175_i0d0495'),('capacity_d','V1n30_s27182_p0d035_i0d0495')),(('capacity_d','V1n30_s16180_p0d035_i0d0495'),('capacity_d','V1n30_s16180_p0d05_i0d0495'))]
for a,b in pairs:
    A=per(path(*a)); B=per(path(*b)); ks=sorted(set(A)&set(B))
    for typ in ('pyramidal','interneuron'):
        for t in ('axon','dendrite'):
            kk=[k for k in ks if k[1]==typ and k[2]==t]
            if not kk: continue
            same=sum(abs(A[k]-B[k])<1e-6*max(1,A[k]) for k in kk); rel=np.array([abs(A[k]/B[k]-1) for k in kk])
            print('%-34s %-12s %-8s cells %3d identical %3d  median |rel diff| %.4f max %.3f'%(b[1][:34],typ,t,len(kk),same,np.median(rel),rel.max()))

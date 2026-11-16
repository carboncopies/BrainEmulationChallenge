"""Pair statistics for linefix_c runs from the .synapses files (same code as pairs.py). usage: stage1.py TAG..."""
import sys, json, numpy as np
sys.argv, tags = sys.argv[:1], sys.argv[1:]
import pairs
OUT='/home/johnjose/BrainGenix/wt/linefix-instance/out/Admonishing/NetmorphOutput/'
pv=json.load(open('pv_results.json')); res={}
for tag in tags:
    t,xyz,pre,post,dist=pairs.load(OUT+pv[tag]['dir']); n=len(t); P=np.where(t)[0]; I=np.where(~t)[0]; r={}
    for k,(a,b) in dict(PP=(P,P),PI=(P,I),IP=(I,P),II=(I,I)).items():
        m=np.isin(pre,a)&np.isin(post,b); r[k],S=pairs.stats(pre[m],post[m],a,b,n); r[k]['max_dist']=round(float(dist[m].max()),4)
        if k=='PP': r['pyr_zero_pyr_input']=int((S.sum(0)==0).sum()); r['top5_in_share']=round(float(np.sort(S.sum(0))[-5:].sum()/S.sum()),3)
        if k=='IP': r['targets_per_int']=round(float((S>0).sum(1).mean()),1)
    r['A']=round(r['IP']['syn']/(r['IP']['syn']+r['PP']['syn']),4); res[tag]=r
    print(tag,json.dumps(r),flush=True)
json.dump(res,open('stage1_results.json','w'),indent=1)

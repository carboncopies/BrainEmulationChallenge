"""Read-only pair statistics from NetMorph .synapses files (existing finished runs only).
For patched runs, thresholding the stored pre-post distance at D' reproduces what the patched test would accept at D_synmax = D'
(arbors do not depend on the synapse test). usage: pairs.py  -> pairs_results.json"""
import glob, json, numpy as np
FIX='/home/johnjose/BrainGenix/wt/linefix-instance/out/Admonishing/NetmorphOutput/'
BASE='/var/lib/BrainGenix/NES/Admonishing/NetmorphOutput/'
import os
W='/home/johnjose/cos/netmorph_work/recipe_v2'
fx=json.load(open(W+'/linefix/pv_results.json')); bs=json.load(open(W+'/pv_arbor_seeds/pv_results.json'))
RUNS={('fix',v):FIX+fx[v+'_s16180_fix']['dir'] for v in('S1','V1','V3')}
RUNS.update({('base',v):BASE+bs[v+'_s16180']['dir'] for v in('S1','V1','V3')})
def load(d):
    typ={};pos={}
    for l in open(glob.glob(d+'/*.neurons')[0]):
        if l[0]=='#': continue
        p=l.split(','); typ[p[1]]=p[2].strip(); pos[p[1]]=np.array(p[4:7],float)
    ids={k:i for i,k in enumerate(typ)}
    pre=[];post=[];dist=[]
    for l in open(glob.glob(d+'/*.synapses')[0]):
        if l[0]=='#': continue
        p=l.split(',')
        if p[1]=='NMDAR': continue
        pre.append(ids[p[10]]); post.append(ids[p[11]]); dist.append(((float(p[2])-float(p[5]))**2+(float(p[3])-float(p[6]))**2+(float(p[4])-float(p[7]))**2)**.5)
    t=np.array([typ[k]=='pyramidal' for k in typ]); xyz=np.array([pos[k] for k in typ])
    return t,xyz,np.array(pre),np.array(post),np.array(dist)
def stats(pre,post,selpre,selpost,n):
    M=np.zeros((n,n),int); np.add.at(M,(pre,post),1)
    S=M[np.ix_(selpre,selpost)]; same=(selpre is selpost) or (len(selpre)==len(selpost) and (selpre==selpost).all())
    npair=S.size-(len(selpre) if same else 0); c=S[S>0]
    return dict(syn=int(S.sum()),pairs_possible=int(npair),connected=int(len(c)),p_conn=round(len(c)/npair,4),syn_per_conn_mean=round(float(c.mean()),2) if len(c) else 0,
        syn_per_conn_median=float(np.median(c)) if len(c) else 0,syn_per_conn_p90=float(np.percentile(c,90)) if len(c) else 0,syn_per_all_pairs=round(float(S.sum()/npair),3),
        frac_conn_with_1=round(float((c==1).mean()),3) if len(c) else 0,out_per_cell_mean=round(float(S.sum(1).mean()),1),out_min=int(S.sum(1).min()),out_max=int(S.sum(1).max()),
        in_per_cell_mean=round(float(S.sum(0).mean()),1),in_min=int(S.sum(0).min()),in_max=int(S.sum(0).max()),autapses=int(np.trace(S)) if same else 0,
        reciprocal_frac=round(float(((S>0)&(S.T>0)).sum()/max(1,len(c))),3) if same else None),S
def main():
    res={}
    for (kind,v),d in RUNS.items():
        t,xyz,pre,post,dist=load(d); n=len(t); P=np.where(t)[0]; I=np.where(~t)[0]
        r={'dir':os.path.basename(d),'max_dist':{}}
        sel={'PP':(P,P),'PI':(P,I),'IP':(I,P),'II':(I,I)}
        for k,(a,b) in sel.items():
            m=np.isin(pre,a)&np.isin(post,b); r['max_dist'][k]=round(float(dist[m].max()),4)
            r[k],S=stats(pre[m],post[m],a,b,n)
            if k=='PP':
                D=np.linalg.norm(xyz[P][:,None]-xyz[P][None],axis=2); off=~np.eye(len(P),dtype=bool)
                r['PP_pconn_by_soma_dist']={'%d-%d'%(lo,hi):[int(((D>=lo)&(D<hi)&off).sum()),round(float((S>0)[(D>=lo)&(D<hi)&off].mean()),3),round(float(S[(D>=lo)&(D<hi)&off].mean()),2)] for lo,hi in((0,50),(50,100),(100,150),(150,250))}
                h,_=np.histogram(dist[m],bins=np.linspace(0,1.5,16)); r['PP_dist_hist_0.1bins']=h.tolist()
            if kind=='fix':
                ths=(1.5,1.0,0.7,0.5,0.4,0.3,0.2,0.15,0.1,0.05) if k=='PP' else (0.1,0.075,0.0667,0.05)
                r[k+'_by_D']={str(th):stats(pre[m&(dist<=th)],post[m&(dist<=th)],a,b,n)[0] for th in ths}
        res[kind+'_'+v]=r
        print(kind,v,{k:(r[k]['syn'],r[k]['connected'],r[k]['p_conn'],r[k]['syn_per_conn_mean'],r[k]['syn_per_all_pairs']) for k in sel},r['max_dist'],flush=True)
    json.dump(res,open('pairs_results.json','w'),indent=1)
if __name__=='__main__': main()

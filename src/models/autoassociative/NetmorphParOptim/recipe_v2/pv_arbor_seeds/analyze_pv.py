"""usage: analyze_pv.py S1_s111 V1_s111 ... Writes pv_results.json"""
import sys, os, json, glob, numpy as np
W='/home/johnjose/cos/netmorph_work'; HERE=W+'/recipe_v2/pv_arbor_seeds'
sys.path.insert(0, W+'/bec/src/models/autoassociative/NetmorphParOptim/weight_space'); sys.path.insert(0, W+'/bec/src/models/autoassociative/NetmorphParOptim'); sys.path.insert(0,W+'/extra'); sys.path.insert(0,HERE)
from reservoir import Reservoir, AMPA, GABA
import measure, pandas as pd, bio_check
OUT='/var/lib/BrainGenix/NES/Admonishing/NetmorphOutput'
CFG={'S1':(26,3.5,48),'V1':(20,3.5,48),'V3':(23,5,48)}
def nneur(d):
    g=glob.glob(d+'/*.neurons'); return sum(1 for l in open(g[0]) if l[0]!='#') if g else -1
def find_dir(tag):
    n,seed=tag.split('_s'); b,db,ni=CFG[n]; t0=os.path.getmtime('%s/grow_%s/model_%s'%(HERE,tag,tag)); c=[]
    for d in glob.glob(OUT+'/*'):
        for f in glob.glob(d+'/*.nibr.clp'):
            if os.path.getmtime(f)<t0-5: continue
            s=open(f).read()
            if 'randomseed=%s;'%seed in s and 'all_interneuron_axons.B_inf=%g;'%b in s and 'all_interneuron_dendrites.B_inf=%g;'%db in s and 'interneuron.min_basal=6' in s and nneur(d)==96+ni: c.append(d)
    assert len(c)==1,(n,c); return c[0]
def best8(G,P,k):
    v=sorted((float(G[p,k]) for p in P),reverse=True)
    return max(min(sum(v[4:8]),10.0)+sum(v[0:4]),min(sum(v[0:4]),10.0)+sum(v[4:8]))
res={}
for n in sys.argv[1:]:
    d=find_dir(n); vz='%s/grow_%s'%(HERE,n)+'/viz/sample_0000.json'
    R=Reservoir(vz); P,I=R.pyr,R.int; nP,nI=len(P),len(I)
    NA=R.NR[AMPA]; NG=R.NR[GABA]
    pp=int(NA[np.ix_(P,P)].sum()); pi=int(NA[np.ix_(P,I)].sum()); ip=int(NG[np.ix_(I,P)].sum()); ii=int(NG[np.ix_(I,I)].sum())
    IPm=NG[np.ix_(I,P)]; IIm=NG[np.ix_(I,I)]; PIm=NA[np.ix_(P,I)]
    ia=R.G[AMPA][np.ix_(P,I)].sum(axis=0)
    tg=(IPm>0).sum(axis=1)
    m=measure.summarize(d)
    df=pd.DataFrame([dict(days=25,pyramidal=96,interneuron=nI,minneuronseparation=10,**{'shape.radius':120,'shape.thickness':30,'dm.weight':0.9})])
    try: bio_check.assert_hard_limits(df); bio='pass'
    except Exception as e: bio='FAIL '+str(e)[:200]
    rep=[l.strip() for l in open(glob.glob(d+'/*_report')[0]) if 'all_interneuron' in l and 'B_inf' in l][:2]
    clp=open(glob.glob(d+'/*.nibr.clp')[0]).read(); dsyn=[l for l in clp.split('\n') if l.startswith('D_synmax')]
    res[n]=dict(dir=os.path.basename(d),n_pyr=nP,n_int=nI,bio_check=bio,D_synmax=dsyn,report=rep,
      int_dend_len=m['interneuron_dendrite'],int_axon_len=m['interneuron_axon'],pyr_dend_len_mean=m['pyramidal_dendrite']['len_mean'],pyr_axon_len_mean=m['pyramidal_axon']['len_mean'],
      pyr_pyr=pp,pyr_int=pi,int_pyr=ip,int_int=ii,
      pairs_pyr_int=int((PIm>0).sum()),pairs_int_pyr=int((IPm>0).sum()),pairs_int_int=int((IIm>0).sum()),
      syn_per_pair_int_pyr=round(ip/max(1,(IPm>0).sum()),2),syn_per_pair_pyr_int=round(pi/max(1,(PIm>0).sum()),2),syn_per_pair_int_int=round(ii/max(1,(IIm>0).sum()),2),
      pyr_targets_per_int_mean=round(float(tg.mean()),1),pyr_targets_per_int_median=float(np.median(tg)),pyr_targets_per_int_max=int(tg.max()),
      pyr_targets_frac_of_pyr=round(float(tg.mean())/nP,3),
      inhib_frac_ip_over_ip_pp=round(ip/(ip+pp),4),inhib_frac_all=round((ip+ii)/(ip+ii+pp+pi),4),
      drivable_simple=int((ia>=13.84).sum()),drivable_8cell_capaware=int(sum(best8(R.G[AMPA],P,k)>=13.84 for k in I)),
      zero_pyr_input=int((ia==0).sum()))
    print(n,json.dumps({k:v for k,v in res[n].items() if k not in('report','D_synmax')},default=float),flush=True)
old=json.load(open(HERE+'/pv_results.json')) if os.path.exists(HERE+'/pv_results.json') else {}
old.update(res); json.dump(old,open(HERE+'/pv_results.json','w'),indent=1,default=float)

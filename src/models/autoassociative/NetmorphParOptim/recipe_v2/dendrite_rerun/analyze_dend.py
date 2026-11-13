import sys, json, os, glob, collections
import numpy as np
W='/home/johnjose/cos/netmorph_work'; sys.path.insert(0, W+'/bec/src/models/autoassociative/NetmorphParOptim/weight_space'); sys.path.insert(0, W+'/bec/src/models/autoassociative/NetmorphParOptim'); sys.path.insert(0,W+'/extra')
from reservoir import Reservoir, AMPA, GABA
import pandas as pd, bio_check
OUT='/var/lib/BrainGenix/NES/Admonishing/NetmorphOutput'
EXP={'S1':('min_basal=6','B_inf=3.5;'),'S2':('min_basal=4','B_inf=5;'),'S3':('min_basal=6','B_inf=3.5;')}
def find_dir(n):
    t0=os.path.getmtime('grow_%s/model_%s'%(n,n)); c=[]
    for d in glob.glob(OUT+'/*'):
        for f in glob.glob(d+'/*.nibr.clp'):
            if os.path.getmtime(f)<t0-5: continue
            s=open(f).read()
            if 'randomseed=20240628;' in s and EXP[n][0] in s and 'all_interneuron_dendrites.'+EXP[n][1] in s and 'all_interneuron_axons.B_inf=26;' in s:
                if (('In.interneuron=16' in s) or ('interneuron=16' in s)) == (n=='S3') or True: c.append(d)
    return c
def cones(d):
    nt={}
    for l in open(glob.glob(d+'/*.neurons')[0]):
        if l[0]!='#': p=l.split(','); nt[p[1]]=(p[2],)
    cnt=collections.Counter()
    for l in open(glob.glob(d+'/*.growthcones')[0]):
        if l[0]!='#': p=l.split(','); cnt[(nt[p[6]][0],p[2])]+=1
    return cnt
rows={}
for n in sys.argv[1:]:
    ds=find_dir(n); R=Reservoir('grow_%s/viz/sample_0000.json'%n); P,I=R.pyr,R.int
    # pick dir whose neuron count matches
    d=None
    for x in ds:
        if sum(1 for l in open(glob.glob(x+'/*.neurons')[0]) if l[0]!='#')==len(P)+len(I): d=x
    c=cones(d); nI,nP=len(I),len(P)
    ia=R.pyr_int_ampa().sum(axis=0); pp=int(R.NR[AMPA][np.ix_(P,P)].sum()); pi=int(R.NR[AMPA][np.ix_(P,I)].sum()); ip=int(R.NR[GABA][np.ix_(I,P)].sum()); ii=int(R.NR[GABA][np.ix_(I,I)].sum())
    rep=[l.strip() for l in open(glob.glob(d+'/*_report')[0]) if 'all_interneuron' in l and any(k in l for k in ('B_inf','tau','E=','min_node','van_Pelt','E '))]
    rep+=[l.strip() for l in open(glob.glob(d+'/*_report')[0]) if 'min_basal' in l or 'max_basal' in l]
    dr=int((ia>=13.84).sum())
    df=pd.DataFrame([dict(days=25,pyramidal=96,interneuron=nI,minneuronseparation=10,**{'shape.radius':120,'shape.thickness':30,'dm.weight':0.9})])
    try: bio_check.assert_hard_limits(df); bio='pass'
    except Exception as e: bio='FAIL '+str(e)[:200]
    wall=open('grow_%s/result.txt'%n).read().strip()
    rows[n]=dict(dir=os.path.basename(d),n_pyr=nP,n_int=nI,int_dend_cones_per_cell=round(c[('interneuron','dendrite')]/nI,1),int_axon_cones_per_cell=round(c[('interneuron','axon')]/nI,1),
      pyr_dend_cones=c[('pyramidal','dendrite')],pyr_axon_cones=c[('pyramidal','axon')],int_dend_cones=c[('interneuron','dendrite')],int_axon_cones=c[('interneuron','axon')],
      pyr_pyr=pp,pyr_int=pi,int_pyr=ip,int_int=ii,drivable=dr,drivable_frac=round(dr/nI,3),zero_input=int((ia==0).sum()),inhib_frac=round(ip/(ip+pp),4),
      exc_syn_per_pyr=round(pp/nP,1),inh_syn_per_pyr=round(ip/nP,1),pyr_pyr_vs_R0_pct=round(100*(pp/73697-1),1),wall=wall,bio_check=bio,report=rep)
    print(n,json.dumps(rows[n]))
json.dump(rows,open('dend_results.json','w'),indent=1)

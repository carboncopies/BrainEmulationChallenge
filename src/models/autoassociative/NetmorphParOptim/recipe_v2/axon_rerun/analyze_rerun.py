import sys, json, os, glob, re, collections
import numpy as np
W='/home/johnjose/cos/netmorph_work'; sys.path.insert(0, W+'/bec/src/models/autoassociative/NetmorphParOptim/weight_space')
from reservoir import Reservoir, AMPA, GABA
OUT='/var/lib/BrainGenix/NES/Admonishing/NetmorphOutput'
def find_dir(name):
    key='randomseed=%s;' % ('20240629' if name=='R3' else '20240628')
    want_ax = {'R0':None,'R3':None,'R1':'B_inf=26;','R2':'B_inf=39;'}[name]
    t0=os.path.getmtime('grow_%s/model_%s'%(name,name))
    c=[]
    for d in glob.glob(OUT+'/*'):
        for f in glob.glob(d+'/*.nibr.clp'):
            if os.path.getmtime(f)<t0-5: continue
            s=open(f).read()
            if key in s and 'interneuron.min_basal=4' in s and ((want_ax in s) if want_ax else ('all_interneuron_axons.B_inf' not in s)): c.append(d)
    return c
def cones(d):
    nt={}
    for l in open(glob.glob(d+'/*.neurons')[0]):
        if l[0]!='#': p=l.split(','); nt[p[1]]=(p[2],np.array(p[4:7],float))
    res={}
    for ext,key in (('growthcones','cones'),('bifurcationnodes','bif')):
        cnt=collections.Counter(); pos=collections.defaultdict(list)
        for l in open(glob.glob(d+'/*.'+ext)[0]):
            if l[0]=='#': continue
            p=l.split(','); k=(nt[p[6]][0],p[2]); cnt[k]+=1
            if ext=='growthcones' and k==('interneuron','axon'): pos[p[6]].append([float(x) for x in p[3:6]]+[])
        res[key]=cnt; 
        if pos: res['pos']=(pos,nt)
    return res
def report(d):
    r=[l for l in open(glob.glob(d+'/*_report')[0]) if "all_interneuron_axons" in l and ("B_inf" in l or "van_Pelt" in l)]
    return [x.strip() for x in r][:6]
if __name__=='__main__':
    rows={}
    for n in sys.argv[1:]:
        ds=find_dir(n); print(n,'dirs',ds)
        d=ds[0]; c=cones(d); R=Reservoir('grow_%s/viz/sample_0000.json'%n); P,I=R.pyr,R.int
        ia=R.pyr_int_ampa().sum(axis=0); pp=int(R.NR[AMPA][np.ix_(P,P)].sum()); ip=int(R.NR[GABA][np.ix_(I,P)].sum())
        pos,nt=c['pos']
        # spatial: soma-relative; boundary check on absolute coords. region center approx from all somata
        allsoma=np.array([v[1] for v in nt.values()]); ctr=allsoma.mean(0); lo=allsoma.min(0); hi=allsoma.max(0)
        pts=np.array([q for v in pos.values() for q in v])
        rows[n]=dict(dir=os.path.basename(d), ncone_int_axon=c['cones'][('interneuron','axon')], per_cell=round(c['cones'][('interneuron','axon')]/len(I),1),
          bif_int_axon=c['bif'][('interneuron','axon')], bif_per_cell=round(c['bif'][('interneuron','axon')]/len(I),1),
          cones_int_dend=c['cones'][('interneuron','dendrite')], cones_pyr_axon=c['cones'][('pyramidal','axon')], cones_pyr_dend=c['cones'][('pyramidal','dendrite')],
          pyr_pyr=pp, pyr_int=int(R.NR[AMPA][np.ix_(P,I)].sum()), int_pyr=ip, int_int=int(R.NR[GABA][np.ix_(I,I)].sum()),
          drivable=int((ia>=13.84).sum()), inhib_frac=round(ip/(ip+pp),4), report=report(d),
          soma_min=lo.round(1).tolist(), soma_max=hi.round(1).tolist(), cone_min=pts.min(0).round(1).tolist(), cone_max=pts.max(0).round(1).tolist(),
          cone_pcts=[np.percentile(pts,q,axis=0).round(1).tolist() for q in (1,50,99)])
        np.save('cones_int_axon_%s.npy'%n, pts)
        print(n, json.dumps(rows[n]))
    json.dump(rows,open('rerun_results.json','w'),indent=1)

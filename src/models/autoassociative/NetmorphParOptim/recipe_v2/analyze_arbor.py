import sys, json, os, re
import numpy as np
W='/home/johnjose/cos/netmorph_work'; sys.path.insert(0, W+'/bec/src/models/autoassociative/NetmorphParOptim/weight_space')
from reservoir import Reservoir, AMPA, GABA
rows={}
for n in sys.argv[1:] or 'ABCD':
    p='grow_arbor_%s/viz/sample_0000.json'%n
    if not os.path.exists(p): continue
    r=Reservoir(p); P,I=r.pyr,r.int
    ia=r.pyr_int_ampa().sum(axis=0); ii_pyr_syn=int(r.NR[AMPA][np.ix_(P,I)].sum())
    gab_on_pyr=int(r.NR[GABA][np.ix_(I,P)].sum()); ampa_on_pyr=int(r.NR[AMPA][np.ix_(P,P)].sum())
    res=json.load(open('grow_%s/out-rawcounts.json'%n if os.path.exists('grow_%s/out-rawcounts.json'%n) else 'grow_%s/out-rawcounts.json'%n)) if False else None
    w=open('grow_arbor_%s/result.txt'%n).read()
    d=dict(config=w.strip(), n_pyr=len(P), n_int=len(I), pyr_pyr_syn=ampa_on_pyr, pyr_int_syn=ii_pyr_syn, int_pyr_syn=gab_on_pyr, int_int_syn=int(r.NR[GABA][np.ix_(I,I)].sum()),
      mean_pyr_syn_per_int=round(ii_pyr_syn/len(I),1), int_ge_13_84=int((ia>=13.84).sum()), frac_drivable=round(float((ia>=13.84).mean()),3), int_zero_input=int((ia==0).sum()),
      int_input_nS_median=round(float(np.median(ia)),1), int_input_nS_mean=round(float(ia.mean()),1),
      inhib_frac_onto_pyr=round(gab_on_pyr/(gab_on_pyr+ampa_on_pyr),3),
      gaba_per_pyr_mean_nS=round(float(r.int_pyr_gaba().sum(axis=0).mean()),1), int_int_gaba_mean_nS=round(float(r.int_int_gaba().sum(axis=0).mean()),1))
    rows[n]=d; print(n, json.dumps(d))
json.dump(rows,open('arbor_results.json','w'),indent=1)

import sys, json
import numpy as np
P='/home/johnjose/cos/netmorph_work/bec/src/models/autoassociative/NetmorphParOptim'
sys.path.insert(0, P+'/weight_space')
from reservoir import Reservoir, AMPA, GABA, NMDA
D='/home/johnjose/cos/netmorph_work/fable_loop/'
dumps={'sim133_ref':D+'it1/viz_a/sample_0000.json'}
for s in (1001,1002,1003): dumps['seed%d'%s]=D+'r2_seeds/viz_%d/sample_0000.json'%s
R={k:Reservoir(v) for k,v in dumps.items()}
def r1(x): return [round(float(v),1) for v in x]
for k,r in R.items():
    print('='*20,k)
    print('SUMMARY', json.dumps(r.summary()))
    p,i=r.pyr,r.int
    print('SYN pyrpyr AMPA',int(r.NR[AMPA][np.ix_(p,p)].sum()),'pyrpyr NMDA',int(r.NR[NMDA][np.ix_(p,p)].sum()),
          'pyrint AMPA',int(r.NR[AMPA][np.ix_(p,i)].sum()),'intpyr GABA',int(r.NR[GABA][np.ix_(i,p)].sum()),'intint GABA',int(r.NR[GABA][np.ix_(i,i)].sum()))
    ia=r.pyr_int_ampa().sum(axis=0)
    print('INT incoming AMPA from pyr sorted:',r1(np.sort(ia)))
    print(' mean %.3f median %.3f zeros %d >=7.84 %d >=13.84 %d'%(ia.mean(),np.median(ia),(ia==0).sum(),(ia>=7.84).sum(),(ia>=13.84).sum()))
    pg=r.int_pyr_gaba().sum(axis=0)
    print('PYR incoming GABA from int: mean %.3f median %.3f max %.3f zeros %d >=8 %d >=16 %d >=40 %d'%(pg.mean(),np.median(pg),pg.max(),(pg==0).sum(),(pg>=8).sum(),(pg>=16).sum(),(pg>=40).sum()))
    ig=r.int_int_gaba().sum(axis=0)
    print('INT incoming GABA from int: mean %.3f max %.3f zeros %d'%(ig.mean(),ig.max(),(ig==0).sum()))
    PI=r.pyr_int_ampa(); IP=r.int_pyr_gaba()
    print('PyrInt AMPA pairs %d mean %.3f max %.3f'%((PI>0).sum(),PI[PI>0].mean(),PI.max()))
    print('IntPyr GABA pairs %d mean %.3f max %.3f'%((IP>0).sum(),IP[IP>0].mean(),IP.max()))
    W=np.concatenate([r.W[t][r.W[t]>0] for t in (AMPA,GABA,NMDA)])
    print('as-built weights all types:',sorted(set(np.round(W,4).tolist())))
ref=R['sim133_ref']
for k,r in R.items():
    if k=='sim133_ref': continue
    if r.N!=ref.N: print(k,'N differs',r.N,ref.N); continue
    A=r.pyr_pyr_ampa(); B=ref.pyr_pyr_ampa()
    print('COMPARE',k,'pyrpyr AMPA identical to sim133:',np.array_equal(A,B),'pos identical:',np.allclose(r.pos,ref.pos,atol=0,rtol=0))
    if A.shape==B.shape: print('  corr pyrpyr AMPA: %.4f'%np.corrcoef(A.ravel(),B.ravel())[0,1])

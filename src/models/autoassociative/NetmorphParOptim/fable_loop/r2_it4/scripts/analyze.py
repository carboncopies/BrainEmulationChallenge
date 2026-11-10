import sys, json
import numpy as np
P='/home/johnjose/cos/netmorph_work/bec/src/models/autoassociative/NetmorphParOptim'
sys.path.insert(0, P+'/weight_space')
from reservoir import Reservoir, AMPA, GABA, NMDA
W='/home/johnjose/cos/netmorph_work/fable_loop/'
dumps={'sim133_ref':W+'it1/viz_a/sample_0000.json','d03':W+'r2_it4/viz_d03/sample_0000.json','d07':W+'r2_it4/viz_d07/sample_0000.json'}
R={k:Reservoir(v) for k,v in dumps.items()}
def r1(x): return [round(float(v),1) for v in x]
for k,r in R.items():
    print('='*20,k,'N',r.N)
    p,i=r.pyr,r.int
    print('SYN pyrpyr AMPA',int(r.NR[AMPA][np.ix_(p,p)].sum()),'pyrint AMPA',int(r.NR[AMPA][np.ix_(p,i)].sum()),
          'intpyr GABA',int(r.NR[GABA][np.ix_(i,p)].sum()),'intint GABA',int(r.NR[GABA][np.ix_(i,i)].sum()))
    ia=r.pyr_int_ampa().sum(axis=0)
    print('INT incoming AMPA from pyr sorted:',r1(np.sort(ia)))
    print(' mean %.3f zeros %d count>=7.84 %d count>=13.84 %d'%(ia.mean(),(ia==0).sum(),(ia>=7.84).sum(),(ia>=13.84).sum()))
    pg=r.int_pyr_gaba().sum(axis=0)
    print('PYR incoming GABA from int: mean %.3f median %.3f max %.3f count>=16 %d'%(pg.mean(),np.median(pg),pg.max(),(pg>=16).sum()))
ref=R['sim133_ref']
for k in ('d03','d07'):
    r=R[k]
    if r.N!=ref.N: print(k,'N differs',r.N,ref.N); continue
    A=r.pyr_pyr_ampa(); B=ref.pyr_pyr_ampa()
    print('COMPARE',k,'soma pos exactly identical:',bool(np.array_equal(r.pos,ref.pos)),'allclose:',bool(np.allclose(r.pos,ref.pos)),'max pos diff %.4f'%np.abs(r.pos-ref.pos).max(),
          '| pyrpyr AMPA identical:',bool(np.array_equal(A,B)),'corr %.4f'%np.corrcoef(A.ravel(),B.ravel())[0,1])

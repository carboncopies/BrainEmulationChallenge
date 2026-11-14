"""Patch a COPY of v2-arbor-S10000 (originals untouched). make(s, gx): Pyr->Int AMPA PeakConductance x s and Weight=1.0 (R3 weight; same as inhibition_timing P*),
all GABA (Int->Pyr and Int->Int) effective strength x gx relative to model default (W 0.2 x gx, cap W<=1 so gx<=5 via Weight, gx>5 via Weight=1.0 and PeakConductance x gx/5).
Rise/decay unchanged (0.5/10 ms). Name = v2-arbor-S1-optB_s{s}_g{gx}. delete(name) removes the copy."""
import sys, os, shutil, numpy as np
sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe_v2/inhibition_timing')
from patch_inh import D, SRC, locate, RDT
from recmap import pre_post
def masks(rec,path):
    pre,post=pre_post(rec,path); nt=np.array(rec['NT']); pyr=lambda x:x<96
    return dict(pi=(nt==0)&pyr(pre)&~pyr(post),gaba=(nt==1)),pre,post
def tag(x): return ('%g'%x).replace('.','p')
def name(s,gx,src=None): return 'v2-arbor-S1-optB%s_s%s_g%s'%('' if src is None else src, tag(s), tag(gx))
SEEDS={'629':'v2-arbor-S1-seed6290000','630':'v2-arbor-S1-seed6300000'}
def make(s,gx,src_model='v2-arbor-S10000',nm=None):
    nm=nm or name(s,gx); dst=D+nm; assert not os.path.exists(dst)
    shutil.copyfile(D+src_model,dst)
    cls,h,off=locate(dst); rec=np.memmap(dst,dtype=RDT,mode='r+',offset=off,shape=(h['Rec'],))
    M,pre,post=masks(rec,D+src_model); f32=lambda x:np.asarray(x,dtype='<f4')
    rec['G'][M['pi']]=f32(np.array(rec['G'][M['pi']],dtype=np.float64)*s); rec['W'][M['pi']]=f32(1.0)
    gw=min(gx,5.0); gG=gx/gw
    rec['W'][M['gaba']]=f32(np.array(rec['W'][M['gaba']],dtype=np.float64)*gw)
    if gG!=1.0: rec['G'][M['gaba']]=f32(np.array(rec['G'][M['gaba']],dtype=np.float64)*gG)
    rec.flush(); return nm
def delete(nm):
    assert nm.startswith('v2-arbor-S1-optB'); os.remove(D+nm)
if __name__=='__main__':
    sd=sys.argv[3] if len(sys.argv)>3 else None
    print(make(float(sys.argv[1]),float(sys.argv[2]),*( (SEEDS[sd],name(float(sys.argv[1]),float(sys.argv[2]),sd)) if sd else ())))

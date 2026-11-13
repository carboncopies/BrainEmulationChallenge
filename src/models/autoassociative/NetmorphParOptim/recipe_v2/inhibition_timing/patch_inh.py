"""Receptor-record patcher for a COPY of v2-arbor-S10000 (72-byte LIFCReceptorBase). Receptor -> (pre,post) via compartment->neuron map (recmap.py).
python patch_inh.py NEWNAME key=val ...   keys: pi_G (x PeakConductance of Pyr->Int AMPA), pi_W (set Weight of Pyr->Int AMPA), pi_rise, pi_decay (set),
  gaba_W (x Weight, all GABA), gaba_rise, gaba_decay (set, all GABA), ii_W (extra x Weight, Int->Int GABA only), ii_decay (set, Int->Int only), ii_G (x PeakConductance Int->Int)
  Original is only read. NEWNAME must start with v2-arbor-S1-inh."""
import sys, os, shutil, numpy as np
sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe_v2/inhibition_timing')
from recmap import *
D='/var/lib/BrainGenix/NES/Admonishing/Models/'; SRC=D+'v2-arbor-S10000'
def masks(rec):
    pre,post=pre_post(rec); nt=np.array(rec['NT']); pyr=lambda x:x<96
    return dict(pi=(nt==0)&pyr(pre)&~pyr(post), pp=(nt==0)&pyr(pre)&pyr(post), gaba=(nt==1), ii=(nt==1)&~pyr(pre)&~pyr(post), ip=(nt==1)&~pyr(pre)&pyr(post)), pre, post
def patch(new, spec, pair_edits=None):
    assert new.startswith('v2-arbor-S1-inh') and not os.path.exists(D+new)
    shutil.copyfile(SRC, D+new)
    cls,h,off=locate(D+new)
    rec=np.memmap(D+new,dtype=RDT,mode='r+',offset=off,shape=(h['Rec'],))
    M,pre,post=masks(rec); f32=lambda x:np.asarray(x,dtype='<f4')
    def mul(field,m,f): rec[field][m]=f32(np.array(rec[field][m],dtype=np.float64)*f)
    def put(field,m,v): rec[field][m]=f32(v)
    s=spec
    if 'pi_G' in s: mul('G',M['pi'],s['pi_G'])
    if 'pi_W' in s: put('W',M['pi'],s['pi_W'])
    if 'pi_rise' in s: put('Rise',M['pi'],s['pi_rise'])
    if 'pi_decay' in s: put('Decay',M['pi'],s['pi_decay'])
    if 'gaba_W' in s: mul('W',M['gaba'],s['gaba_W'])
    if 'gaba_rise' in s: put('Rise',M['gaba'],s['gaba_rise'])
    if 'gaba_decay' in s: put('Decay',M['gaba'],s['gaba_decay'])
    if 'ii_W' in s: mul('W',M['ii'],s['ii_W'])
    if 'ii_G' in s: mul('G',M['ii'],s['ii_G'])
    if 'ii_decay' in s: put('Decay',M['ii'],s['ii_decay'])
    for (a,b,nt),ed in (pair_edits or []):
        m=(pre==a)&(post==b)&(np.array(rec['NT'])==nt)
        assert m.any(),(a,b,nt)
        for k,v in ed.items(): put(k,m,v)
    rec.flush(); return new
if __name__=='__main__':
    spec={k:float(v) for k,v in (a.split('=') for a in sys.argv[2:])}
    patch(sys.argv[1],spec); print('made',sys.argv[1],spec)

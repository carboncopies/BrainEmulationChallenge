"""usage: patch_model.py FACTOR NEWNAME  -> copies v2-arbor-S10000 to NEWNAME in the models dir and scales Weight of GABA(NT==1) receptor records by FACTOR.
Original is only read. PeakConductance_nS is left unchanged (cap g_k<=g_peak_sum, Neuron.cpp:152-155)."""
import sys, shutil, numpy as np, os
sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe_v2/gaba_patch')
from gabafile import *
D='/var/lib/BrainGenix/NES/Admonishing/Models/'
f=float(sys.argv[1]); new=D+sys.argv[2]; src=D+'v2-arbor-S10000'
assert not os.path.exists(new) and sys.argv[2].startswith('v2-arbor-S1-gaba')
shutil.copyfile(src,new)
cls,h,off=locate(new)
rec=np.memmap(new,dtype=RDT,mode='r+',offset=off,shape=(h['Rec'],))
m=rec['NT']==1; rec['W'][m]=(rec['W'][m]*np.float32(f)).astype('<f4'); rec.flush()
r2=np.memmap(new,dtype=RDT,mode='r',offset=off,shape=(h['Rec'],))
print(new,'GABA',int(m.sum()),'W unique',np.unique(r2['W'][r2['NT']==1]),'AMPA W',np.unique(r2['W'][r2['NT']==0]),'NMDA W',np.unique(r2['W'][r2['NT']==2]))
print('size equal',os.path.getsize(src)==os.path.getsize(new))

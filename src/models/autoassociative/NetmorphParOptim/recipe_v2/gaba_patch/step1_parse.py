import sys, json, numpy as np
sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe_v2/gaba_patch')
from gabafile import *
p='/var/lib/BrainGenix/NES/Admonishing/Models/v2-arbor-S10000'
cls,h,off,rec = load(p)
print(cls,h,off)
sz=__import__('os').path.getsize(p); print('end of receptors',off+72*h['Rec'],'filesize',sz)
for nt,name in enumerate(['AMPA','GABA','NMDA']):
    r=rec[rec['NT']==nt]; print(name,len(r))
    for f in ['W','G','Erev','Rise','Decay','Delay','STDP']: print('  ',f,np.unique(np.round(r[f],4))[:6])
print('IDs sequential', np.all(rec['ID']==np.arange(len(rec))))

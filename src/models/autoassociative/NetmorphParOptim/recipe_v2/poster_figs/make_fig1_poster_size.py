import sys, json
sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe_v2/ripple_S1_R3')
from r3lib import load_pairs
import numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
SRC='/home/johnjose/cos/netmorph_work/recipe_v2/ripple_S1_R3/'
groups,_,_=load_pairs('R3_c0'); cols=['#1f77b4','#ff7f0e','#2ca02c','#d62728']
plt.rcParams.update({'font.size':24,'axes.labelsize':24,'xtick.labelsize':24,'ytick.labelsize':24,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none','font.family':'DejaVu Sans'})
e=json.load(open(SRC+'raw_s10_rip12_dt01.json')); vm=e['vm']; t=np.array(vm['times_ms']); sp={int(k):v for k,v in e['spikes'].items()}
fg,ax=plt.subplots(3,1,figsize=(11.25,8.5),sharex=True,gridspec_kw=dict(height_ratios=[2,1.2,1.2]))
y=0
for gi,(m,c) in enumerate(groups):
    for k in m:
        s=sp.get(k,[]); ax[0].plot(s,[y]*len(s),'|',color=cols[gi],ms=11,mew=2.5); y+=1
for i in vm['interneurons']:
    s=sp.get(i,[]); ax[0].plot(s,[y]*len(s),'|',color='k',ms=11,mew=2.5); y+=1
ax[0].set_yticks([]); ax[0].set_ylabel('cells')
ax[0].set_ylim(-1,y+4)
for gi,on in e['events']:
    for a in ax: a.axvline(on,color=cols[gi],lw=1.6,ls=':')
    ax[0].text(on+0.6,y+0.8,'cue %d'%(gi+1),color=cols[gi],fontsize=24,va='bottom')
for gi,(m,c) in enumerate(groups):
    nc=[x for x in m if x not in c]; ax[1].plot(t,vm['vm_mV'][str(nc[0])],color=cols[gi],lw=2.4)
ax[1].set_ylabel('pyr Vm\n(mV)'); ax[1].set_yticks([-60,0])
for n_,i in enumerate(vm['interneurons'][:8]): ax[2].plot(t,vm['vm_mV'][str(i)],lw=2,color=str(0.15+0.05*n_))
ax[2].set_ylabel('int Vm\n(mV)'); ax[2].set_yticks([-60,0]); ax[2].set_xlabel('ms after first cue')
ax[2].set_xlim(-3,60); ax[2].set_xticks([0,20,40,60])
fg.tight_layout(pad=0.4,h_pad=0.6); fg.savefig('fig1_ripple_poster_11.25x8.5in.png',dpi=300); fg.savefig('fig1_ripple_poster_11.25x8.5in.svg'); plt.close(fg)

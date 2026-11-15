import sys, json
sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe_v2/ripple_S1_R3')
from r3lib import load_pairs
import numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
SRC='/home/johnjose/cos/netmorph_work/recipe_v2/ripple_S1_R3/'
groups,_,_=load_pairs('R3_c0')
cols=['#1f77b4','#ff7f0e','#2ca02c','#d62728']
plt.rcParams.update({'font.size':14,'axes.spines.top':False,'axes.spines.right':False})
def ripple(name, out, xlim=None, title=''):
    e=json.load(open(SRC+name)); vm=e['vm']; t=np.array(vm['times_ms']); sp={int(k):v for k,v in e['spikes'].items()}
    fg,ax=plt.subplots(3,1,figsize=(13,10),sharex=True,gridspec_kw=dict(height_ratios=[2.2,1.3,1.3]))
    y=0
    for gi,(m,c) in enumerate(groups):
        for k in m:
            s=sp.get(k,[]); ax[0].plot(s,[y]*len(s),'|',color=cols[gi],ms=12,mew=2); y+=1
    for i in vm['interneurons']:
        s=sp.get(i,[]); ax[0].plot(s,[y]*len(s),'|',color='k',ms=12,mew=2); y+=1
    ax[0].set_yticks([]); ax[0].set_ylabel('neurons\n(colour = memory,\nblack = interneurons)')
    for gi,on in e['events']:
        for a in ax: a.axvline(on,color=cols[gi],lw=1.2,ls=':')
        ax[0].text(on,y+0.3,'cue %d'%(gi+1),color=cols[gi],fontsize=12,ha='left')
    for gi,(m,c) in enumerate(groups):
        nc=[x for x in m if x not in c]
        ax[1].plot(t,vm['vm_mV'][str(nc[0])],color=cols[gi],lw=1.6,label='memory %d, non-cue cell'%(gi+1))
    ax[1].set_ylabel('Vm, pyramidal\n(mV)'); ax[1].legend(fontsize=10,ncol=2,frameon=False,loc='upper right')
    for i in vm['interneurons'][:8]: ax[2].plot(t,vm['vm_mV'][str(i)],lw=1.2)
    ax[2].set_ylabel('Vm, interneurons\n(mV)'); ax[2].set_xlabel('ms after first cue')
    if xlim: ax[2].set_xlim(*xlim)
    ax[0].set_title(title,fontsize=14,loc='left')
    fg.tight_layout(); fg.savefig(out+'.png',dpi=300); fg.savefig(out+'.svg'); plt.close(fg)
ripple('raw_s10_rip12_dt01.json','fig1_ripple_4memories_12ms',title='Four memories cued 12 ms apart (4 of 8 engram cells cued each); Vm sampled at 0.1 ms')
def single(a,b,out):
    fg,ax=plt.subplots(1,2,figsize=(13,6),sharey=True)
    for a_,n,tt in zip(ax,(a,b),('With GABA (as grown)','GABA silenced, same network')):
        e=json.load(open(SRC+n)); sp={int(k):v for k,v in e['spikes'].items()}; y=0
        for gi,(m,c) in enumerate(groups):
            for k in m:
                s=sp.get(k,[]); a_.plot(s,[y]*len(s),'|',color=cols[gi],ms=10,mew=1.5); y+=1
        a_.set_title(tt); a_.set_xlabel('ms'); a_.set_yticks([])
    ax[0].set_ylabel('pyramidal cells in the four engrams'); fg.tight_layout(); fg.savefig(out+'.png',dpi=300); fg.savefig(out+'.svg'); plt.close(fg)
try: single('raw_s1_R3c0.json','raw_s2_R3c0_SG.json','fig2_single_recall_vs_silenced')
except Exception as ex: print('fig2 skipped:',ex)

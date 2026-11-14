"""Offline screen (numpy emulator fable_design_S1/net.py, NOT NES). Scales: s = Pyr->Int conductance x (R3 weight-1 value), gw = GABA Weight mult (<=5),
gG = GABA PeakConductance mult, bgw = Pyr->Pyr background weight, c = per-pair background cap nS. Prints per cond: single complete, spurious pyr spikes, last spike, int spikes."""
import sys, json, time
sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe_v2/fable_design_S1')
from design import *
def mk(groups,s,gx,bgw,c,SG=False):
    net=mknet(groups,gaba=1.0,T=16.5,Lnn=8,Lnc=8,bg=bgw,pc=c)
    net.GA_cap[:96,96:]*=s
    gw=min(gx,5.0); gG=gx/gw
    net.WG[:]=0.2*gw; net.GG_cap=net.GG_cap*gG
    if SG: net.gaba_scale=0.0
    return net
def one(groups,**kw):
    net=mk(groups,**kw); out={}
    # single, full cue for each memory; 3-cell cue
    ful=[];f3=0;spur=0
    for gi in range(4):
        sp=net.run(cues_for(groups,[(gi,0.0)]),T=120,dt=1.0)
        mem,cue=groups[gi]; nc=[m for m in mem if m not in cue]
        ful.append(sum(1 for m in nc if any(T0<=x<T0+10 for x in sp[m])))
        allm={m for mm,_ in groups for m in mm}
        spur+=sum(len(sp[i]) for i in range(96) if i not in allm)+sum(len(sp[m]) for g2,(mm,_) in enumerate(groups) if g2!=gi for m in mm)
        last=max([x for s_ in sp for x in s_],default=T0)-T0
        out.setdefault('last',[]).append(round(last,1)); out.setdefault('int',[]).append(sum(len(sp[i]) for i in range(96,144)))
        out.setdefault('pyr',[]).append(sum(len(sp[i]) for i in range(96)))
    for gi in range(4):
        for sub in (groups[gi][1][:3],groups[gi][1][1:]):
            sp=net.run([(T0+o,c) for c,o in zip(sub,CUE_OFFS)],T=60,dt=1.0)
            f3+=sum(1 for m in groups[gi][0] if m not in groups[gi][1] and sp[m])
    out.update(full=ful,false3=f3,spur=spur); return out
if __name__=='__main__':
    g=load_groups(); t=time.time()
    print(one(g,s=1.0,gx=1.0,bgw=0.2,c=0.15), time.time()-t)

"""Recipe R3 weight builder for S1 (v2-arbor-S10000) + emulator helpers. build() returns the AMPA weight matrix; export_pairs()
writes the (pre, post, conductance_nS, g_peak_sum_nS, role) list to program with BatchSetPrePostStrength. See ../FABLE_DESIGN_S1.md."""
import json, sys, os, numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from net import *
D=L.Dump('/home/johnjose/cos/netmorph_work/recipe_v2/dendrite_rerun/grow_S1/viz/sample_0000.json')
G=D.G
def build(groups,T=18.0,Lnn=10.0,Lnc=10.0,bg=0.0,bgB=None,inh=True,capcue=False,pc=None):
    """returns weight matrix WA (N x N) for AMPA. bgB: per-post normalised background budget nS (weight=min(bg, bgB/S_post))."""
    N=D.N; W=np.zeros((N,N)); nP=96
    S=G[:nP,:nP].sum(0)
    for j in range(nP):
        w=bg if bgB is None else min(bg, bgB/S[j]) if S[j]>0 else 0.0
        W[:nP,j]=w
    if pc is not None:
        Gp=G[:nP,:nP]; W[:nP,:nP]=np.minimum(W[:nP,:nP],pc/np.maximum(Gp,1e-9))
    for mem,cue in groups:
        nc=[m for m in mem if m not in cue]
        for a in mem:
            for b in mem:
                if a!=b and not (a in cue and b in cue and bg>0): W[a,b]=0.0   # cue->cue: 0 when pruned, background value otherwise
        for n in nc:
            for c in cue:
                assert G[c,n]>=T/4-1e-9; W[c,n]=(T/4)/G[c,n]
            s=sum(G[m,n] for m in nc if m!=n)
            sc=min(1.0,Lnn/s) if s>0 else 0.0
            for m in nc:
                if m!=n and G[m,n]>0: W[m,n]=sc
        for c in cue:
            s=sum(G[m,c] for m in nc); sc=min(1.0,Lnc/s) if s>0 else 0.0
            for m in nc:
                if G[m,c]>0: W[m,c]=sc
    W[:nP,nP:]=1.0 if inh else 0.0
    if capcue and inh:
        for mem,cue in groups:
            for k in range(nP,N):
                C=sum(G[c,k] for c in cue)
                if C>10:
                    for c in cue: W[c,k]=10.0/C
    return W
def mknet(groups,gaba=1.0,intC=100.0,intR=100.0,intref=2.0,**kw):
    net=Net(D); net.WA=build(groups,**kw); net.gaba_scale=gaba
    net.C[96:]=intC; net.gL[96:]=1000.0/intR; net.ref[96:]=intref
    return net
def single(net,groups,dt=1.0,T=120,label='',quiet=False):
    res=[]
    for gi in range(len(groups)):
        sp=net.run(cues_for(groups,[(gi,0.0)]),T=T,dt=dt)
        mem,cue=groups[gi]; nc=[m for m in mem if m not in cue]
        lat=[min([x-T0 for x in sp[m] if T0<=x<T0+10],default=None) for m in nc]
        nsp=sum(len(sp[m]) for m in mem); end=max(x for m in mem for x in sp[m])-T0
        byst=sum(len(sp[i]) for i in range(96) if i not in mem); ni=sum(len(sp[i]) for i in range(96,144)); nic=sum(1 for i in range(96,144) if sp[i])
        res.append(dict(fired=sum(l is not None for l in lat),nsp=nsp,end=round(end,1),byst=byst,ni=ni,nic=nic,last=round(max(x for s_ in sp for x in s_)-T0,1)))
    if not quiet: print(label,' | '.join('%d/4 nsp %d end %s byst %d int %d(%dc)'%(r['fired'],r['nsp'],r['end'],r['byst'],r['ni'],r['nic']) for r in res))
    return res
def three(net,groups,dt=1.0):
    fc=0
    for gi in range(len(groups)):
        for sub in (groups[gi][1][:3],groups[gi][1][1:]):
            sp=net.run([(T0+o,c) for c,o in zip(sub,CUE_OFFS)],T=60,dt=dt)
            fc+=sum(1 for m in groups[gi][0] if m not in groups[gi][1] and sp[m])
    return fc
def ripple(net,groups,order,s,dt=1.0,label=''):
    ev=[(g,i*s) for i,g in enumerate(order)]
    sp=net.run(cues_for(groups,ev),T=170,dt=dt); return summarize(sp,groups,ev,96,label)
def load(fn,idx=0):
    g=json.load(open(fn))[idx]['groups']; return [(sorted(x['members']),sorted(x['cue'])) for x in g]
def export_pairs(groups,fn,**kw):
    """write [[pre,post,conductance_nS,g_peak_sum_nS,role],...] for every Pyr->Pyr and Pyr->Int pair with g>0 (all must be programmed)."""
    W=build(groups,**kw); out=[]; nP=96
    cueof={c:i for i,(m,cu) in enumerate(groups) for c in cu}; memof={x:i for i,(m,cu) in enumerate(groups) for x in m}
    for a in range(nP):
        for b in range(D.N):
            g=float(G[a,b])
            if a==b or g<=0: continue
            w=float(W[a,b]); assert -1e-12<=w<=1+1e-9
            if b>=nP: role='pyr->int'
            elif a in memof and b in memof and memof[a]==memof[b]:
                role=('cue' if a in cueof else 'noncue')+'->'+('cue' if b in cueof else 'noncue')
            else: role='background'
            out.append([a,b,round(min(w,1.0)*g,6),round(g,6),role])
    json.dump(dict(groups=[dict(members=m,cue=c,noncue=[x for x in m if x not in c]) for m,c in groups],params={k:v for k,v in kw.items()},pairs=out),open(fn,'w'))
    return out
def load_groups(fn=None):
    import os
    fn=fn or os.path.join(os.path.dirname(os.path.abspath(__file__)),'groups_R3.json')
    return [(sorted(x['members']),sorted(x['cue'])) for x in json.load(open(fn))['groups']]
if __name__=='__main__':
    # emulator forecast for recipe R3 (T 16.5, loop cap 8, background cap 0.15 nS per connection) on S1
    g=load_groups()
    for gaba in (1.0,0.0):
        net=mknet(g,gaba=gaba,T=16.5,Lnn=8,Lnc=8,bg=0.2,pc=0.15)
        single(net,g,label='R3 c0.15 GABA x%g singles dt1:'%gaba)
        for name,order,s in (('s12',[0,1,2,3],12),('s16',[0,1,2,3],16),('s20',[0,1,2,3],20),('sh16',[2,0,3,1],16)):
            ripple(net,g,order,s,dt=1.0,label='R3 c0.15 GABA x%g %s dt1'%(gaba,name))

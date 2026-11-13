"""Offline numpy emulator of the NES LIFC network (abstracted receptors, AMPA+GABA, no NMDA, STDP off), written from the NES source
constants (NetmorphManagerThread.cpp, LIFCNeuron.cpp, Neuron.cpp, Receptor.cpp). NOT NES: no server is contacted.
Validated only against arbor A variant E1 (run this file). See ../FABLE_DESIGN_S1.md."""
import numpy as np, math, sys, json
sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe')
import recipelib as L
def norm(tr,td):
    tp=(tr*td)/(td-tr)*math.log(td/tr); return math.exp(-tp/td)-math.exp(-tp/tr)
NA=norm(0.5,3.0); NG=norm(0.5,10.0); NF=norm(2.5,30); NS=norm(30,300); NADP=norm(20,200); DELAY=1.0001
def ksum(t,ts,tr,td,nm):
    if len(ts)==0: return 0.0
    d=t-np.asarray(ts); d=d[d>=0]
    return float(((np.exp(-d/td)-np.exp(-d/tr))/nm).sum())
class Net:
    def __init__(s,dump):
        s.d=dump; s.N=dump.N; s.nP=len(dump.pyr)
        s.GA_cap=dump.G.copy(); s.GG_cap=dump.GA.copy()      # g_peak_sum
        s.WA=np.full((s.N,s.N),0.2); s.WG=np.full((s.N,s.N),0.2)
        s.is_int=np.array([i>=s.nP for i in range(s.N)])
        s.vth0=np.full(s.N,-50.0); s.ref=np.full(s.N,2.0); s.gL=np.full(s.N,10.0); s.C=np.full(s.N,100.0)
        s.gaba_scale=1.0
    def program(s,pairs):  # dict (a,b)->(g, cond, role)
        for (a,b),v in pairs.items(): s.WA[a,b]=v[1]/v[0]
    def run(s,cues,T=170.0,dt=1.0):
        N=s.N; V=np.full(N,-70.0); h=np.ones(N); floor=s.vth0.copy(); tl=np.full(N,-1e9); VR=np.full(N,-55.0); rd=np.ones(N,bool)
        sp=[[] for _ in range(N)]; forced={}
        for t,c in cues: forced.setdefault(c,[]).append(t)
        for c in forced: forced[c].sort()
        fi={c:0 for c in forced}
        EA=s.WA*s.GA_cap; EG=s.WG*s.GG_cap*s.gaba_scale
        n=int(round(T/dt)); tprev=0.0
        active=set()
        for i in range(1,n+1):
            t=i*dt
            KA=np.zeros(N); KG=np.zeros(N); gf=np.zeros(N); gs=np.zeros(N); ga=np.zeros(N)
            for j in active:
                ts=sp[j]
                if s.is_int[j]: KG[j]=ksum(t-DELAY,ts,0.5,10.0,NG)
                else: KA[j]=ksum(t-DELAY,ts,0.5,3.0,NA)
                gf[j]=min(3.0*ksum(t,ts,2.5,30,NF),5.0)
                if not s.is_int[j]:
                    gs[j]=min(1.0*ksum(t,ts,30,300,NS),2.0); ga[j]=min(0.3*ksum(t,ts,20,200,NADP),0.6)
            gA=np.minimum(s.GA_cap,EA*KA[:,None]).sum(0); gG=np.minimum(s.GG_cap,EG*KG[:,None]).sum(0)
            gt=s.gL+gf+gs+ga+gA+gG
            E=(s.gL*-70+(gf+gs)*-90+ga*-20+gG*-70)/gt
            Vp=V.copy(); V=E+(V-E)*np.exp(-dt/(s.C/gt))
            h+=dt*(1-h)/50.0; floor-=dt*(floor-s.vth0)/500.0
            vth=np.maximum(s.vth0+10*(1-h),floor)
            for j in range(N):
                if t>=tl[j]+s.ref[j]:
                    if not rd[j]: V[j]=VR[j]; rd[j]=True
                    fired=False
                    if j in forced and fi[j]<len(forced[j]) and forced[j][fi[j]]<=t:
                        tf=forced[j][fi[j]]; fi[j]+=1; fired=True
                    elif V[j]>=vth[j]:
                        tf=t
                        if V[j]>Vp[j]: tf=tprev+dt*(vth[j]-Vp[j])/(V[j]-Vp[j]); V[j]=vth[j]
                        fired=True
                    if fired:
                        VR[j]=min(V[j],s.vth0[j]); V[j]=30.0; rd[j]=False; tl[j]=tf; sp[j].append(tf); h[j]-=0.2; floor[j]+=1.0; active.add(j)
            tprev=t
        return sp
CUE_OFFS=[0.0,0.5,1.0,1.5]; T0=20.0
def cues_for(groups,events): return [(T0+on+o,c) for gi,on in events for c,o in zip(groups[gi][1],CUE_OFFS)]
def summarize(sp,groups,events,nP,label=''):
    out=[]
    evs=sorted(events,key=lambda e:e[1])
    allmem=set(m for g,_ in evs for m in groups[g][0])
    for k,(gi,on) in enumerate(evs):
        mem,cue=groups[gi]; nc=[m for m in mem if m not in cue]; t0=T0+on
        wend=T0+(evs[k+1][1] if k+1<len(evs) else 1e9)
        lat=[min([x-t0 for x in sp[m] if t0<=x<t0+10],default=None) for m in nc]
        ms=[x-t0 for m in mem for x in sp[m] if x>=t0 and x<wend+40]
        ms_all=[x-t0 for m in mem for x in sp[m] if x>=t0]
        ni=sum(1 for i in range(nP,len(sp)) for x in sp[i] if t0<=x<wend)
        out.append(dict(g=gi,fired=sum(l is not None for l in lat),lat=None if None in lat else round(max(lat),2),nsp=len(ms_all),end=round(max(ms_all),1) if ms_all else None,ints=ni))
    byst=sum(len(sp[i]) for i in range(nP) if i not in allmem)
    last=max([x for s_ in sp for x in s_],default=T0)-T0-evs[0][1]
    nint=sum(len(sp[i]) for i in range(nP,len(sp))); nintc=sum(1 for i in range(nP,len(sp)) if sp[i])
    print(label,'| '+' ; '.join('G%d %d/4 lat %s nsp %d end %s ints %d'%(o['g'],o['fired'],o['lat'],o['nsp'],o['end'],o['ints']) for o in out),'| bystander spikes',byst,'| int spikes %d (%d cells)'%(nint,nintc),'| last %.1f'%last)
    return out,byst,last
if __name__=='__main__':
    # validation against measured NES data: arbor A, variant E1 (see ripple_arborA/raw_E1.json)
    d=L.Dump('/home/johnjose/cos/netmorph_work/recipe_v2/grow_arbor_A/viz/sample_0000.json')
    gj=json.load(open('/home/johnjose/cos/netmorph_work/recipe_v2/ripple_arborA/design_K4.json'))
    groups=[(sorted(g['members']),sorted(g['cue'])) for g in gj['groups']]
    net=Net(d); net.program(L.build_pairs(d,groups,inh=True))
    for gi in range(4):
        sp=net.run(cues_for(groups,[(gi,0.0)]),T=90,dt=1.0); summarize(sp,groups,[(gi,0.0)],96,'arborA E1 single dt1 (NES measured: 11/40/40/53 spikes, ends 8.4/32.9/26.7/34.8)')
    ev=[(0,0),(1,12),(2,24),(3,36)]; sp=net.run(cues_for(groups,ev),T=170,dt=1.0); summarize(sp,groups,ev,96,'arborA E1 ripple 12 ms dt1 (NES measured: last 70.8, int spikes 1,1,4,11)')

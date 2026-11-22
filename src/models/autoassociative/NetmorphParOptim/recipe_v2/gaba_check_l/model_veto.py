import sys, json; sys.path.insert(0,'.')
from nesmodel import *
import numpy as np
out={}
# (a) IPSP from one GABA pair of conductance G (nS), at rest and with the target held depolarised by constant current (pA) to Vm0
rows=[]
for G in (0.16,0.7,1.6,4.0,40.0):
    for v0 in (-70,-65,-60,-55):
        # hold current so that Vm sits at v0 without GABA: I = gL*(v0-VREST) (pA with nS*mV)
        hold=GL*(v0-VREST)
        t,V,_,_,_=run([],[(5.0,G)],T=60,v0=v0,hold=hold)
        t0,V0,_,_,_=run([],[],T=60,v0=v0,hold=hold)
        d=V-V0; i=np.argmax(np.abs(d))
        rows.append(dict(G_nS=G,Vm0=v0,peak_dV_mV=round(float(d[i]),3),t_peak_after_spike_ms=round(float(t[i]-5.0),2)))
out['ipsp']=rows
# (b) veto: AMPA volley of A nS (4 cue spikes 0..1.5 ms) ; GABA G nS from interneuron spike at lead L ms before the first cue spike (negative L = after)
res=[]
for A in (16.5,20.0,25.0):
    for L in (10,5,3,2,1,0,-1,-2,-3,-4):
        need=None
        for G in np.concatenate([np.arange(0,5,0.25),np.arange(5,100,1.0)]):
            ev=[(o,A/4) for o in (0,0.5,1.0,1.5)]
            t,V,sp,_,_=run(ev,[(-L,G)] if G>0 else [],T=30,dt=0.02)
            if sp is None: need=float(G); break
        res.append(dict(A_nS=A,gaba_spike_lead_ms=L,G_to_veto_nS=need))
out['veto']=res
json.dump(out,open('model_veto.json','w'),indent=1)
for r in rows: print(r)
import collections
for A in (16.5,20.0,25.0):
    print('A',A,[(r['gaba_spike_lead_ms'],r['G_to_veto_nS']) for r in res if r['A_nS']==A])

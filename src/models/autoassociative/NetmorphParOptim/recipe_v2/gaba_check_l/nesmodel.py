"""Offline numerical copy of the NES LIFC update (LIFCNeuron.cpp update_membrane_potential_exponential_Euler_Cm + Receptor.cpp g_norm).
Not a simulation of the network: one target neuron, conductances given by hand. Constants from NetmorphManagerThread.cpp (LIFCNeuronPars, receptors).
Simplifications (stated): no fAHP/sAHP/ADP (only after a spike; we stop at the first spike), no adaptive threshold (it only acts after a spike), no refractory."""
import numpy as np
CM=100.0; RM=100.0; GL=1000.0/RM  # nS (Rm in MOhm -> 10 nS)
VREST=-70.0; VTH=-50.0; E_AMPA=0.0; E_GABA=-70.0
def kern(t, tr, td):
    t=np.asarray(t,float); tp=tr*td/(td-tr)*np.log(td/tr); nrm=np.exp(-tp/td)-np.exp(-tp/tr)
    return np.where(t>=0,(np.exp(-np.maximum(t,0)/td)-np.exp(-np.maximum(t,0)/tr))/nrm,0.0)
def run(ampa_events, gaba_events, T=60.0, dt=0.01, delay=1.0, v0=VREST, hold=None):
    """ampa_events/gaba_events: list of (spike_time_ms, peak_conductance_nS); conductance = peak*kernel(t-ts-delay) summed, clipped at nothing (clip is at pair g_peak_sum; here events are pairs).
    hold: constant extra current (pA) to hold Vm. returns t, V, first spike time (Vm>=VTH) or None, with peak conductances."""
    t=np.arange(0,T,dt); gE=np.zeros_like(t); gI=np.zeros_like(t)
    for ts,g in ampa_events: gE+=g*kern(t-ts-delay,0.5,3.0)
    for ts,g in gaba_events: gI+=g*kern(t-ts-delay,0.5,10.0)
    V=np.empty_like(t); v=v0; spike=None
    for i in range(len(t)):
        gt=GL+gE[i]+gI[i]; Et=(GL*VREST+gE[i]*E_AMPA+gI[i]*E_GABA+(hold or 0.0))/gt
        v=Et+(v-Et)*np.exp(-dt/(CM/gt)); V[i]=v
        if spike is None and v>=VTH: spike=t[i]; 
    return t,V,spike,gE,gI

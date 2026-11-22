#!/usr/bin/env python3
"""Reference case: hand-built LIFC mini-circuits (template: bec-tooling shift_register_lifc.py / full_adder_lifc.py), PATCHED instance only (API 8010).
Each circuit = target P (principal LIFC) + 4 AMPA driver neurons D1-4 + 1 interneuron I (GABA onto P). All circuits independent, one simulation, all started at T0.
Receptor constants as in the Netmorph build: AMPA E 0, rise 0.5, decay 3, onset delay 1 ms; GABA E -70, rise 0.5, decay 10, onset delay 1 ms. Neuron params: Netmorph principal defaults (Vrest -70, thr -50, reset -55, Rm 100, Cm 100).
kind: 'rest' (I only), 'dep10' (AMPA volley 10 nS peak total + I), 'thr16.5' (AMPA volley 16.5 nS = R3 threshold + I), 'thr20' (20 nS)
G = GABA pair conductance in nS (PeakConductance = G, Weight 1.0, so weight*peak = G); G=0 means no GABA receptor (control)."""
import sys, json, numpy as np
sys.path.insert(0,'/home/johnjose/BrainGenix/BrainEmulationChallenge/PythonClient')
import BrainGenix.NES as NES
PORT=8010; HERE='/home/johnjose/cos/netmorph_work/recipe_v2/gaba_check_l/'
T0=60.0; RUN=140.0
Gs=[0,0.66,1.65,3.3,7.0,14.0,40.0]
kinds={'rest':0.0,'dep10':10.0,'thr16.5':16.5,'thr20':20.0}
leads=[0.0,1.0,2.0]   # I spike this many ms BEFORE the first AMPA driver spike (0 = same time)
circ=[]
for k,A in kinds.items():
    for G in Gs:
        for L in (leads if (G>0 and A>0) else [0.0]):
            circ.append(dict(kind=k,A=A,G=G,lead=L))
print('circuits',len(circ),flush=True)
cfg=NES.Client.Configuration(); cfg.Mode=NES.Client.Modes.Remote; cfg.Host='localhost'; cfg.Port=PORT; cfg.UseHTTPS=False
cfg.AuthenticationMethod=NES.Client.Authentication.Password; cfg.Username='Admonishing'; cfg.Password='Instruction'
client=NES.Client.Client(cfg); assert client.IsReady()
sc=NES.Simulation.Configuration(); sc.Name='gabachk-ref'; sc.Seed=0; MySim=client.CreateSimulation(sc); sid=MySim.ID; assert sid>=0; print('sim',sid,flush=True)
def mkSphere(name,pos):
    c=NES.Shapes.Sphere.Configuration(); c.Name,c.Radius_um,c.Center_um=name,10.0,pos; return MySim.AddSphere(c)
def mkCyl(name,p1,p2):
    c=NES.Shapes.Cylinder.Configuration(); c.Name,c.Point1Position_um,c.Point2Position_um=name,p1,p2; c.Point1Radius_um,c.Point2Radius_um=2,1; return MySim.AddCylinder(c)
def mkBox(name,pos):
    bc=NES.Shapes.Box.Configuration(); bc.Name,bc.CenterPosition_um,bc.Dimensions_um,bc.Rotation_rad=name,pos,[0.1,0.1,0.1],[0,0,0]; return MySim.AddBox(bc)
def mkRec(name,src,dest,nt,g,w,delay,bid):
    c=NES.Models.Connections.LIFCReceptor.Configuration(); c.Name,c.SourceCompartment,c.DestinationCompartment,c.Neurotransmitter=name,src,dest,nt
    c.PeakConductance_nS,c.Weight,c.OnsetDelay_ms,c.ReceptorMorphology=g,w,delay,bid
    c.ReversalPotential_mV,c.PSPRise_ms,c.PSPDecay_ms=(0 if nt=='AMPA' else -70),0.5,(3.0 if nt=='AMPA' else 10.0)
    c.STDP_Method,c.STDP_Shift,c.voltage_gated='None',0.01,False; c.STDP_A_pos,c.STDP_A_neg,c.STDP_Tau_pos,c.STDP_Tau_neg=0,0,0,0
    return MySim.AddLIFCReceptor(c)
def mkComp(name,sid_):
    c=NES.Models.Compartments.LIFC.Configuration(); c.Name,c.Shape=name,sid_
    c.RestingPotential_mV,c.ResetPotential_mV,c.SpikeThreshold_mV=-70,-55,-50; c.MembraneResistance_MOhm,c.MembraneCapacitance_pF,c.AfterHyperpolarizationAmplitude_mV=100,100,-90
    return MySim.AddLIFCCompartment(c)
def mkNeur(name,sids,aids):
    c=NES.Models.Neurons.LIFC.Configuration(); c.Name,c.SomaIDs,c.DendriteIDs,c.AxonIDs=name,sids,[],aids
    c.RestingPotential_mV,c.ResetPotential_mV,c.SpikeThreshold_mV=-70,-55,-50; c.MembraneResistance_MOhm,c.MembraneCapacitance_pF=100,100; c.RefractoryPeriod_ms=2
    c.UpdateMethod,c.ResetMethod,c.SpikeDepolarization_mV='ExpEulerCm','ToVm',30
    c.AfterHyperpolarizationReversalPotential_mV=-90
    c.FastAfterHyperpolarizationRise_ms,c.FastAfterHyperpolarizationDecay_ms=2.5,30; c.FastAfterHyperpolarizationPeakConductance_nS,c.FastAfterHyperpolarizationMaxPeakConductance_nS=3.0,5.0; c.FastAfterHyperpolarizationHalfActConstant=1.5
    c.SlowAfterHyperpolarizationRise_ms,c.SlowAfterHyperpolarizationDecay_ms=30,300; c.SlowAfterHyperpolarizationPeakConductance_nS,c.SlowAfterHyperpolarizationMaxPeakConductance_nS=1.0,2.0; c.SlowAfterHyperpolarizationHalfActConstant,c.AfterHyperpolarizationSaturationModel=0.3,'clip'
    c.FatigueThreshold,c.FatigueRecoveryTime_ms=300,1000
    c.AdaptiveThresholdDiffPerSpike,c.AdaptiveTresholdRecoveryTime_ms=0.2,50; c.AdaptiveThresholdDiffPotential_mV,c.AdaptiveThresholdFloor_mV=10,-50
    c.AdaptiveThresholdFloorDeltaPerSpike_mV,c.AdaptiveThresholdFloorRecoveryTime_ms=1.0,500
    c.AfterDepolarizationRecoveryTime_ms,c.AfterDepolarizationDepletion=300,0.3; c.AfterDepolarizationSaturationMultiplier,c.AfterDepolarizationSaturationModel=2.0,'clip'
    c.AfterDepolarizationReversalPotential_mV,c.AfterDepolarizationRise_ms,c.AfterDepolarizationDecay_ms=-20,20,200; c.AfterDepolarizationPeakConductance_nS=0.0
    c.STDP_Method='None'
    return MySim.AddLIFCNeuron(c)
cues=[]; ids=[]
try:
    MySim.SetLIFCAbstractedFunctional(True); MySim.SetSTDP(False); MySim.SetLIFCPreciseSpikeTimes(_UsePreciseSpikeTimes=True)
    for ci,cdef in enumerate(circ):
        y=ci*100.0; pp=[0,y,0]; ip=[0,y+40,0]; dps=[[-60,y-30+15*j,0] for j in range(4)]
        sP=mkSphere('P%d'%ci,pp); sI=mkSphere('I%d'%ci,ip); sD=[mkSphere('D%d_%d'%(ci,j),dps[j]) for j in range(4)]
        cP=mkComp('cP%d'%ci,sP.ID); cI=mkComp('cI%d'%ci,sI.ID); cD=[mkComp('cD%d_%d'%(ci,j),sD[j].ID) for j in range(4)]
        aI=mkCyl('aI%d'%ci,ip,pp); aD=[mkCyl('aD%d_%d'%(ci,j),dps[j],pp) for j in range(4)]
        acI=mkComp('acI%d'%ci,aI.ID); acD=[mkComp('acD%d_%d'%(ci,j),aD[j].ID) for j in range(4)]
        nP=mkNeur('P%d'%ci,[cP.ID],[]); nI=mkNeur('I%d'%ci,[cI.ID],[acI.ID]); nD=[mkNeur('D%d_%d'%(ci,j),[cD[j].ID],[acD[j].ID]) for j in range(4)]
        box=mkBox('b%d'%ci,pp)
        if cdef['A']>0:
            for j in range(4): mkRec('rD%d_%d'%(ci,j),acD[j].ID,cP.ID,'AMPA',cdef['A']/4.0,1.0,1.0,box.ID)
        if cdef['G']>0: mkRec('rI%d'%ci,acI.ID,cP.ID,'GABA',cdef['G'],1.0,1.0,box.ID)
        cdef['P']=nP.ID; cdef['I']=nI.ID; cdef['D']=[n.ID for n in nD]
        tI=T0-cdef['lead']
        cues.append((tI,nI.ID))
        if cdef['A']>0: cues+= [(T0+0.5*j,nD[j].ID) for j in range(4)]
    r=MySim.SetSpecificAPTimes([(float(t),int(n)) for t,n in cues]); print('cues',r,flush=True)
    MySim.RecordAll(-1); MySim.RunAndWait(Runtime_ms=RUN,Dt_ms=0.1,timeout_s=1500.0)
    rec=MySim.GetRecording()['Recording']; sp=MySim.GetSpikeTimes()['SpikeTimes']
    t=np.array(rec['t_ms'],float); res=[]
    for cdef in circ:
        v=np.array(rec['neurons'][str(cdef['P'])]['Vm_mV'] if str(cdef['P']) in rec['neurons'] else rec['neurons'][cdef['P']]['Vm_mV'],float)
        spk=[float(x)-T0 for x in sp.get(str(cdef['P']),sp.get(cdef['P'],{'tSpike_ms':[]}))['tSpike_ms']] if (str(cdef['P']) in sp or cdef['P'] in sp) else []
        isp=[float(x)-T0 for x in sp[str(cdef['I'])]['tSpike_ms']] if str(cdef['I']) in sp else []
        base=float(v[(t>T0-20)&(t<T0-5)].mean()); w=(t>=T0-5)&(t<T0+60)
        res.append(dict(cdef=dict(kind=cdef['kind'],A=cdef['A'],G=cdef['G'],lead=cdef['lead']),baseline_mV=round(base,3),min_mV=round(float(v[w].min()),3),max_mV=round(float(v[w].max()),3),
            P_spikes=spk,I_spikes=isp,vm_trace=[round(float(x),3) for x in v[(t>=T0-2)&(t<T0+40)][::5]]))
    json.dump(dict(sim=sid,t0=T0,results=res),open(HERE+'unit_ref_result.json','w'),default=float)
    for r in res: print(r['cdef'],'base',r['baseline_mV'],'min',r['min_mV'],'max',r['max_mV'],'Pspk',[round(x,2) for x in r['P_spikes']][:3],'Ispk',[round(x,2) for x in r['I_spikes']][:2],flush=True)
finally:
    try: print('deleted',sid,MySim.DeleteResidentByID(),flush=True)
    except Exception as e: print('DELETE FAILED',sid,e,flush=True)

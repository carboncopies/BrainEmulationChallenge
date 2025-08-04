#!../../../venv/bin/python
# LIFtest.py
# Randal A. Koene, 20250724

'''
This script tests the LIFCNeuron NES class.
The intention is to achieve the same functional response as in the
components/IF_with_stdp.py script.
'''

scriptversion='0.1.0'

#import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
#from time import sleep
import argparse
import math
import json
import os

import vbpcommon as vbp
#from BrainGenix.BG_API import BG_API_Setup
#from NES_interfaces.KGTRecords import plot_recorded
import BrainGenix.NES as NES
import BrainGenix

Parser = argparse.ArgumentParser(description="LIFCNeuron test script")
Parser.add_argument("-Host", default="localhost", type=str, help="Host to connect to")
Parser.add_argument("-Port", default=8000, type=int, help="Port number to connect to")
Parser.add_argument("-UseHTTPS", default=False, type=bool, help="Enable or disable HTTPS")
Parser.add_argument("-ExpsDB", default="./ExpsDB.json", type=str, help="Path to experiments database JSON file")
Parser.add_argument("-STDP", default=False, type=bool, help="Enable STDP")
Parser.add_argument("-Seed", default=0, type=int, help="Set random seed")
Args = Parser.parse_args()

# Initialize data collection for entry in DB file
DBdata = vbp.InitExpDB(
    Args.ExpsDB,
    'LIFCtest',
    scriptversion,
    _initIN = {
    },
    _initOUT = {
    })

ClientCfg, ClientInstance = vbp.ClientFromArgs(DBdata, Args)

SimulationCfg, MySim = vbp.NewSimulation(DBdata, ClientInstance, 'LIFCtest', Seed=Args.Seed)
print('Simulation created')

MySim.SetLIFCAbstractedFunctional(_AbstractedFunctional=True) # needs to be called before building LIFC receptors
MySim.SetSTDP(_DoSTDP=Args.STDP)
print('Options specified')

PyrIn = {}
IntIn = {}
PyrOut = {}

def makeSphere(name, radius, center):
    SphereCfg = NES.Shapes.Sphere.Configuration()
    SphereCfg.Name = name
    SphereCfg.Radius_um = radius
    SphereCfg.Center_um = center
    return MySim.AddSphere(SphereCfg)

# Create spheres for 2 principal neurons and 1 interneuron
PyrIn['soma'] = makeSphere('PyrIn_Soma', 10, [0, -30, 0])
IntIn['soma'] = makeSphere('IntIn_Soma', 5, [0, 30, 0])
PyrOut['soma'] = makeSphere('PyrOut_Soma', 10, [100, 0, 0])
print('Made Spheres')

def makeCylinder(name, point1, point2, radius1, radius2):
    CylinderCfg = NES.Shapes.Cylinder.Configuration()
    CylinderCfg.Name = name
    CylinderCfg.Point1Position_um = point1
    CylinderCfg.Point2Position_um = point2
    CylinderCfg.Point1Radius_um = radius1
    CylinderCfg.Point2Radius_um = radius2
    return MySim.AddCylinder(CylinderCfg)

# Create cylinders for dendrite and axons
PyrOut['dendrite'] = makeCylinder('PyrOut_Dendrite', [50, 0, 0], [95, 0, 0], 2, 3)
PyrIn['axon'] = makeCylinder('PyrIn_Axon', [5, -30, 0], [50, 0, 0], 3, 2)
IntIn['axon'] = makeCylinder('IntIn_Axon', [2.5, 30, 0], [50, 0, 0], 3, 2)
print('Made Cylinders')

# NOTE: A number of parameters inherited from SCNeuron are automatically set in NES for LIFCNeuron.
def makeCompartment(name, Vrest, Vreset, Vth, R_m, C_m, E_AHP, shapeID):
    Cfg = NES.Models.Compartments.LIFC.Configuration()
    Cfg.Name = name
    Cfg.RestingPotential_mV = Vrest
    Cfg.ResetPotential_mV = Vreset
    Cfg.SpikeThreshold_mV = Vth
    Cfg.MembraneResistance_MOhm = R_m
    Cfg.MembraneCapacitance_pF = C_m
    Cfg.AfterHyperpolarizationAmplitude_mV = E_AHP
    Cfg.Shape = shapeID
    return MySim.AddLIFCCompartment(Cfg)

# Create compartments for somas, dendrites and axons
PyrIn['soma_comp'] = makeCompartment('PyrIn_Soma_LIFC', -70, -55, -50, 100, 100, -90, PyrIn['soma'].ID)
PyrIn['axon_comp'] = makeCompartment('PyrIn_Axon_LIFC', -70, -55, -50, 100, 100, -90, PyrIn['axon'].ID)
IntIn['soma_comp'] = makeCompartment('IntIn_Soma_LIFC', -70, -55, -50, 100, 100, -90, IntIn['soma'].ID)
IntIn['axon_comp'] = makeCompartment('IntIn_Axon_LIFC', -70, -55, -50, 100, 100, -90, IntIn['axon'].ID)
PyrOut['soma_comp'] = makeCompartment('PyrOut_Soma_LIFC', -70, -55, -50, 100, 100, -90, PyrOut['soma'].ID)
PyrOut['dendrite_comp'] = makeCompartment('PyrOut_Dendrite_LIFC', -70, -55, -50, 100, 100, -90, PyrOut['dendrite'].ID)
print('Made Compartments')

def makeNeuron(
    name, SomaIDs, DendriteIDs, AxonIDs,
    Vrest, Vreset, Vth, R_m, C_m,
    E_AHP,
    tau_rise_fAHP, tau_decay_fAHP, g_peak_fAHP, g_peak_fAHP_max, Kd_fAHP,
    tau_rise_sAHP, tau_decay_sAHP, g_peak_sAHP, g_peak_sAHP_max, Kd_sAHP,
    E_ADP, tau_rise_ADP, tau_decay_ADP, g_peak_ADP,
    ):
    Cfg = NES.Models.Neurons.LIFC.Configuration()
    Cfg.Name = name

    Cfg.SomaIDs = SomaIDs
    Cfg.DendriteIDs = DendriteIDs
    Cfg.AxonIDs = AxonIDs

    Cfg.RestingPotential_mV = Vrest
    Cfg.ResetPotential_mV = Vreset
    Cfg.SpikeThreshold_mV = Vth
    Cfg.MembraneResistance_MOhm = R_m
    Cfg.MembraneCapacitance_pF = C_m
    Cfg.RefractoryPeriod_ms = 2
    Cfg.SpikeDepolarization_mV = 30

    Cfg.UpdateMethod = 'ExpEulerCm'
    Cfg.ResetMethod = 'ToVm' # 'ToVm', 'Onset', 'After'

    Cfg.AfterHyperpolarizationReversalPotential_mV = E_AHP

    Cfg.FastAfterHyperpolarizationRise_ms = tau_rise_fAHP
    Cfg.FastAfterHyperpolarizationDecay_ms = tau_decay_fAHP
    Cfg.FastAfterHyperpolarizationPeakConductance_nS = g_peak_fAHP
    Cfg.FastAfterHyperpolarizationMaxPeakConductance_nS = g_peak_fAHP_max
    Cfg.FastAfterHyperpolarizationHalfActConstant = Kd_fAHP

    Cfg.SlowAfterHyperpolarizationRise_ms = tau_rise_sAHP
    Cfg.SlowAfterHyperpolarizationDecay_ms = tau_decay_sAHP
    Cfg.SlowAfterHyperpolarizationPeakConductance_nS = g_peak_sAHP
    Cfg.SlowAfterHyperpolarizationMaxPeakConductance_nS = g_peak_sAHP_max
    Cfg.SlowAfterHyperpolarizationHalfActConstant = Kd_sAHP

    Cfg.AfterHyperpolarizationSaturationModel = 'clip' # 'clip', 'sigmoidal'

    Cfg.FatigueThreshold = 300 # 0 means not applied
    Cfg.FatigueRecoveryTime_ms = 1000

    Cfg.AfterDepolarizationReversalPotential_mV = E_ADP
    Cfg.AfterDepolarizationRise_ms = tau_rise_ADP
    Cfg.AfterDepolarizationDecay_ms = tau_decay_ADP
    Cfg.AfterDepolarizationPeakConductance_nS = g_peak_ADP
    Cfg.AfterDepolarizationSaturationMultiplier = 2.0
    Cfg.AfterDepolarizationRecoveryTime_ms = 300
    Cfg.AfterDepolarizationDepletion = 0.3
    Cfg.AfterDepolarizationSaturationModel = 'clip' # 'clip', 'resource'

    Cfg.AdaptiveThresholdDiffPerSpike = 0.2
    Cfg.AdaptiveTresholdRecoveryTime_ms = 50
    Cfg.AdaptiveThresholdDiffPotential_mV = 10
    Cfg.AdaptiveThresholdFloor_mV = Vth # 0 means not applied
    Cfg.AdaptiveThresholdFloorDeltaPerSpike_mV = 1.0
    Cfg.AdaptiveThresholdFloorRecoveryTime_ms = 500

    return MySim.AddLIFCNeuron(Cfg)

# Create neurons
PyrIn['neuron'] = makeNeuron(
    'PyrIn_Neuron', [PyrIn['soma_comp'].ID], [], [PyrIn['axon_comp'].ID],
    -70, -55, -50, 100, 100,
    -90,
    2.5, 30, 3.0, 5.0, 1.5,
    30, 300, 1.0, 2.0, 0.3,
    -20, 20, 200, 0.3)
IntIn['neuron'] = makeNeuron(
    'IntIn_Neuron', [IntIn['soma_comp'].ID], [], [IntIn['axon_comp'].ID],
    -70, -55, -50, 100, 100,
    -90,
    2.5, 30, 3.0, 5.0, 1.5,
    30, 300, 0, 0, 0.3,
    -20, 20, 200, 0)
PyrOut['neuron'] = makeNeuron(
    'PyrOut_Neuron', [PyrOut['soma_comp'].ID], [PyrOut['dendrite_comp'].ID], [],
    -70, -55, -50, 100, 100,
    -90,
    2.5, 30, 3.0, 5.0, 1.5,
    30, 300, 1.0, 2.0, 0.3,
    -20, 20, 200, 0.3)
print('Made LIFC Neurons')

def makeBox(name, center, dimensions, rotation):
    BoxCfg = NES.Shapes.Box.Configuration()
    BoxCfg.Name = name
    BoxCfg.CenterPosition_um = center
    BoxCfg.Dimensions_um = dimensions
    BoxCfg.Rotation_rad = rotation
    return MySim.AddBox(BoxCfg)

def makePreSynReceptor(
    name, sourcecompID, destcompID, receptortype,
    E, tau_rise, tau_decay, g_peak, weight, onset_delay,
    STDP_type, A_pos, A_neg, tau_pos, tau_neg,
    voltage_gated,
    shapeID):
    Cfg = NES.Models.Connections.LIFCReceptor.Configuration()
    Cfg.Name = name
    Cfg.SourceCompartment = sourcecompID
    Cfg.DestinationCompartment = destcompID

    Cfg.Neurotransmitter = receptortype

    Cfg.ReversalPotential_mV = E
    Cfg.PSPRise_ms = tau_rise
    Cfg.PSPDecay_ms = tau_decay
    Cfg.PeakConductance_nS = g_peak
    Cfg.Weight = weight
    Cfg.OnsetDelay_ms = onset_delay

    Cfg.STDP_Method = STDP_type # 'Hebbian', 'Anti-Hebbian', 'None'
    Cfg.STDP_A_pos = A_pos
    Cfg.STDP_A_neg = A_neg
    Cfg.STDP_Tau_pos = tau_pos
    Cfg.STDP_Tau_neg = tau_neg

    Cfg.voltage_gated = voltage_gated

    Cfg.ReceptorMorphology = shapeID
    return MySim.AddLIFCReceptor(Cfg)

Synapses = {}
# Create receptors as determined in IF_with_stdp.py
Synapses['PyrInPyrOut'] = makeBox('PyrInPyrOut', [50, 0, 0], [0.1,0.1,0.1], [0,0,0])
Synapses['IntInPyrOut'] = makeBox('IntInPyrOut', [50, 0, 0], [0.1,0.1,0.1], [0,0,0])
print('Made Boxes')

g_peak_AMPA = int(0.83*60*0.0086/0.0086)*20e-3*21 #35 # was *21
g_peak_NMDA = int(0.17*60*0.0086/0.0086)*50e-3*21 #35 # was *21
g_peak_GABA = int(10*0.0086/0.0086)*80e-3*21
onset_delay = 1.0 + (100*1e-6)/1
Synapses['PyrInPyrOut_AMPA'] = makePreSynReceptor(
    'PyrInPyrOut_AMPA', PyrIn['axon_comp'].ID, PyrOut['dendrite_comp'].ID,
    'AMPA',
    0, 0.5, 3.0, g_peak_AMPA, 0.5, onset_delay,
    'Hebbian', 0.01, 0.01, 20.0, 20.0,
    False,
    Synapses['PyrInPyrOut'].ID)
Synapses['PyrInPyrOut_NMDA'] = makePreSynReceptor(
    'PyrInPyrOut_NMDA', PyrIn['axon_comp'].ID, PyrOut['dendrite_comp'].ID,
    'NMDA',
    0, 2.0, 100, g_peak_NMDA, 0.5, onset_delay,
    'None', 0, 0, 0, 0,
    True,
    Synapses['PyrInPyrOut'].ID)
Synapses['IntInPyrOut_GABA'] = makePreSynReceptor(
    'IntInPyrOut_GABA', IntIn['axon_comp'].ID, PyrOut['dendrite_comp'].ID,
    'GABA',
    -70, 0.5, 10, g_peak_GABA, 0.5, onset_delay,
    'None', 0, 0, 0, 0,
    False,
    Synapses['IntInPyrOut'].ID)
print('Made LIFC Receptors')

MySim.ModelSave('LIFtest')
print('Model saved')

# Set stimulation times
T = 4000
PyrIn_t_in = np.array([(t+1)*100 for t in range(int(0.75*T/100))])
IntIn_t_in = PyrIn_t_in+10 # was +3
timeneuronpairs_list = [(t, PyrIn['neuron'].ID) for t in PyrIn_t_in.tolist()]
timeneuronpairs_list += [(t, IntIn['neuron'].ID) for t in IntIn_t_in.tolist()]
MySim.SetSpecificAPTimes(timeneuronpairs_list)
print('Simulation stimulation specified')

# Run simulation and record membrane potential
MySim.RecordAll(-1)
MySim.RunAndWait(Runtime_ms=T, timeout_s=100.0)
print('Functional stimulation completed')

recording_dict = MySim.GetRecording()
print('Recorded data retrieved')

if not vbp.PlotAndStoreRecordedActivity(recording_dict, 'output', { 'figsize': (6,6), 'linewidth': 0.5, 'figext': 'pdf', }):
    vbp.ErrorToDB(DBdata, 'File error: Failed to store plots of recorded activity')
print('Data plot saved as PDF')

print('Done')

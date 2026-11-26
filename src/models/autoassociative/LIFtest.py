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
Parser.add_argument("-STDP", action="store_true", help="Enable STDP")
Parser.add_argument("-Seed", default=0, type=int, help="Set random seed")
Parser.add_argument("-Reload", action="store_true", help="Reload saved model")
Parser.add_argument("-Burst", action="store_true", help="Burst input")
Parser.add_argument("-Long", action="store_true", help="Long burst driver")
Parser.add_argument("-Autoassociative", action="store_true", help="Autoassociative network")
Parser.add_argument("-Patterns", default=1, type=int, help="Number of patterns")
# Autoassociative trial protocols:
#   default:       Encoding phase (full patterns, STDP as set by -STDP), followed by a
#                  retrieval phase (partial cues, STDP off unless -RetrievalSTDP).
#   -inspectSTDP:  Original protocol, alternating encoding and half-pattern cue batches
#                  throughout the run, useful for watching gradual STDP encoding.
Parser.add_argument("-inspectSTDP", action="store_true", help="Autoassociative: alternate encoding and half-pattern cue batches (original protocol)")
Parser.add_argument("-EncodeTrials", default=200, type=int, help="Autoassociative: number of full-pattern encoding presentations per pattern")
Parser.add_argument("-RetrievalTrials", default=20, type=int, help="Autoassociative: number of partial-cue retrieval trials per pattern")
Parser.add_argument("-CueMin", default=0.5, type=float, help="Autoassociative: minimum cue size as fraction of pattern")
Parser.add_argument("-CueMax", default=0.8, type=float, help="Autoassociative: maximum cue size as fraction of pattern")
Parser.add_argument("-EncodeInterval", default=70.0, type=float, help="Autoassociative: ms between encoding presentations")
Parser.add_argument("-RetrievalInterval", default=200.0, type=float, help="Autoassociative: ms between retrieval trials (also the response window)")
Parser.add_argument("-RetrievalSTDP", action="store_true", help="Autoassociative: keep STDP on during retrieval trials")
Parser.add_argument("-EncodeJitter", default=5.0, type=float, help="Autoassociative: max random delay (ms) of each neuron's spike in an encoding presentation (perfectly synchronous presentation only strengthens low-to-high neuron index connections)")
Parser.add_argument("-Dt", default=1.0, type=float, help="Simulation step size in ms")
Parser.add_argument("-T", type=float, help="Simulation time in ms")
Args = Parser.parse_args()

def saveModel(name:str):
    # ModelSave currently fails for this LIFC model on at least one NES build
    # (TaskStatus 3). Saving is only needed for -Reload, so failure is not fatal.
    try:
        MySim.ModelSave(name)
        print('Model saved')
    except Exception as e:
        print('WARNING: ModelSave failed, continuing without a saved model (-Reload will not work): '+str(e))

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
MySim.SetLIFCPreciseSpikeTimes(_UsePreciseSpikeTimes=(Args.Dt > 0.2))
MySim.SetSTDP(_DoSTDP=Args.STDP)
print('Options specified')

PyrIn = {}
IntIn = {}
PyrOut = {}

# For Autoassociative option
numpatterns = Args.Patterns
numneurons = 8*numpatterns
numinterneurons = 3

if Args.Reload:

    MySim.ModelLoad('LIFtest')
    print('Reloaded LIFC Receptors')

    class NeuronStub:
        def __init__(self, _ID):
            self.ID = _ID
    
    PyrIn['neuron'] = NeuronStub(0)
    IntIn['neuron'] = NeuronStub(1)
    PyrOut['neuron'] = NeuronStub(2)

else:

    def makeSphere(name, radius, center):
        SphereCfg = NES.Shapes.Sphere.Configuration()
        SphereCfg.Name = name
        SphereCfg.Radius_um = radius
        SphereCfg.Center_um = center
        return MySim.AddSphere(SphereCfg)

    def makeSphereConfig(name, radius, center):
        SphereCfg = NES.Shapes.Sphere.Configuration()
        SphereCfg.Name = name
        SphereCfg.Radius_um = radius
        SphereCfg.Center_um = center
        return SphereCfg

    def makeCylinder(name, point1, point2, radius1, radius2):
        CylinderCfg = NES.Shapes.Cylinder.Configuration()
        CylinderCfg.Name = name
        CylinderCfg.Point1Position_um = point1
        CylinderCfg.Point2Position_um = point2
        CylinderCfg.Point1Radius_um = radius1
        CylinderCfg.Point2Radius_um = radius2
        return MySim.AddCylinder(CylinderCfg)

    def makeBox(name, center, dimensions, rotation):
        BoxCfg = NES.Shapes.Box.Configuration()
        BoxCfg.Name = name
        BoxCfg.CenterPosition_um = center
        BoxCfg.Dimensions_um = dimensions
        BoxCfg.Rotation_rad = rotation
        return MySim.AddBox(BoxCfg)

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

    def makeCompartmentConfig(name, Vrest, Vreset, Vth, R_m, C_m, E_AHP, shapeID):
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
        Cfg.ResetMethod = 'After' # Both 'ToVm' and 'After' work well here # 'ToVm', 'Onset', 'After'

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
        Cfg.FatigueRecoveryTime_ms = 70 # 150 # 1000

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
        Cfg.STDP_Shift = -4.0

        Cfg.voltage_gated = voltage_gated

        Cfg.ReceptorMorphology = shapeID
        return MySim.AddLIFCReceptor(Cfg)

    def makeNetmorphPreSynReceptor(
        name, sourcecompID, destcompID, receptortype, E,
        tau_rise, tau_decay, g_rec_peak, quantity,
        hilloc_distance, velocity, syn_delay, voltage_gated,
        weight, STDP_type, A_pos, A_neg, tau_pos, tau_neg,
        shapeID):
        Cfg = NES.Models.Connections.NetmorphLIFCReceptor.Configuration()
        Cfg.Name = name
        Cfg.SourceCompartment = sourcecompID
        Cfg.DestinationCompartment = destcompID

        Cfg.Neurotransmitter = receptortype
        Cfg.ReversalPotential_mV = E
        Cfg.PSPRise_ms = tau_rise
        Cfg.PSPDecay_ms = tau_decay
        Cfg.ReceptorPeakConductance_nS = g_rec_peak
        Cfg.ReceptorQuantity = quantity

        Cfg.HillocDistance_um = hilloc_distance
        Cfg.Velocity_mps = velocity
        Cfg.SynapticDelay_ms = syn_delay
        Cfg.voltage_gated = voltage_gated

        Cfg.Weight = weight
        Cfg.STDP_Method = STDP_type # 'Hebbian', 'Anti-Hebbian', 'None'
        Cfg.STDP_A_pos = A_pos
        Cfg.STDP_A_neg = A_neg
        Cfg.STDP_Tau_pos = tau_pos
        Cfg.STDP_Tau_neg = tau_neg
        Cfg.STDP_Shift = -4.0

        Cfg.ReceptorMorphology = shapeID
        return MySim.AddNetmorphLIFCReceptor(Cfg)

    # Steps that typically happen in Netmorph to NES conversion
    #   These can happen in a number of ways.
    #   Morphology info: Should correspond to PSD area at Netmorph generated synapse
    PyrInPyrOut_Area_um2 = 60*0.0086
    IntInPyrOut_Area_um2 = 10*0.0086

    PyrInPyrOut_Hilloc_Distance_um = 100
    IntInPyrOut_Hilloc_Distance_um = 100

    #   Functional info: Proportions of receptor channels where they coreside at a synapse
    AMPAChannelsProportion = 0.83
    NMDAChannelsProportion = 0.17
    GABAChannelsProportion = 1.00

    g_rec_peak_AMPA = 20e-3 # nS
    g_rec_peak_NMDA = 50e-3 # nS
    g_rec_peak_GABA = 80e-3 # nS

    propagation_velocity = 1.0 # m/s
    PyrInPyrOut_syndelay = 1.0 # ms
    IntInPyrOut_syndelay = 1.0 # ms

    #   This conversion should precede calling AddNetmorphLIFCReceptor
    AMPAQuantityPerSynapse = int(AMPAChannelsProportion*PyrInPyrOut_Area_um2/0.0086)
    NMDAQuantityPerSynapse = int(NMDAChannelsProportion*PyrInPyrOut_Area_um2/0.0086)
    GABAQuantityPerSynapse = int(GABAChannelsProportion*IntInPyrOut_Area_um2/0.0086)

    if Args.Autoassociative:

        Neurons = {}
        Interneurons = {}
        for n in range(numneurons):
            Neurons[n] = {}
        for n in range(numinterneurons):
            Interneurons[n] = {}

        # Remember: Shapes are just 3D objects.
        #           They do not specify an associated cell.
        #           Compartments are linked to a shape, but they also
        #           do not specify an associated cell yet when created.
        # Make cell body spheres and compartments
        for n in range(numneurons):
            Neurons[n]['xyz'] = [0, n*60, 0]
            Neurons[n]['soma'] = makeSphere('%d_Soma' % n, 10, Neurons[n]['xyz'])
            Neurons[n]['soma_comp'] = makeCompartment('%d_Soma_LIFC' % n, -70, -55, -50, 100, 100, -90, Neurons[n]['soma'].ID)

        # configs = []
        # for n in range(numneurons):
        #     Neurons[n]['xyz'] = [0, n*60, 0]
        #     configs.append(makeSphereConfig('%d_Soma' % n, 10, Neurons[n]['xyz']))
        # response = MySim.AddSpheres(configs)
        # for n in range(numneurons):
        #     Neurons[n]['soma'] = response[n].ID
        # configs = []
        # for n in range(numneurons):
        #     configs.append(makeCompartmentConfig('%d_Soma_LIFC' % n, -70, -55, -50, 100, 100, -90, Neurons[n]['soma'].ID))
        # response = MySim.AddLIFCCompartments(configs)
        # for n in range(numneurons):
        #     Neurons[n]['soma_comp'] = response[n].ID
        print('Made cell body spheres and compartments')

        for n in range(numinterneurons):
            Interneurons[n]['xyz'] = [100, n*60, 0]
            Interneurons[n]['soma'] = makeSphere('%d_Soma' % n, 5, Interneurons[n]['xyz'])
            Interneurons[n]['soma_comp'] = makeCompartment('%d_Soma_LIFC' % n, -70, -55, -50, 100, 100, -90, Interneurons[n]['soma'].ID)
        print('Made interneuron body spheres and compartments')

        # Make apical dendrite cylinders and compartments
        for n in range(numneurons):
            Neurons[n]['dendrite'] = makeCylinder('%d_Dendrite' % n, [-50, Neurons[n]['xyz'][1], 0], [-5, Neurons[n]['xyz'][1], 0], 2, 3)
            Neurons[n]['dendrite_comp'] = makeCompartment('%d_Dendrite_LIFC' % n, -70, -55, -50, 100, 100, -90, Neurons[n]['dendrite'].ID)
        print('Made apical dendrite cylinders and compartments')

        # Make interneuron dendrite cylinders and compartments
        for n in range(numinterneurons):
            Interneurons[n]['dendrite'] = makeCylinder('%d_Dendrite' % n, [50, Interneurons[n]['xyz'][1], 0], [97.5, Interneurons[n]['xyz'][1], 0], 2, 3)
            Interneurons[n]['dendrite_comp'] = makeCompartment('%d_Dendrite_LIFC' % n, -70, -55, -50, 100, 100, -90, Interneurons[n]['dendrite'].ID)
        print('Made interneuron dendrite cylinders and compartments')

        # Make axon cylinders and compartments
        for n in range(numneurons):
            Neurons[n]['axon'] = []
            Neurons[n]['axon_comp'] = []
            for m in range(numneurons):
                if n != m:
                    cyl = makeCylinder('%d_%d_Axon' % (n, m), [5, Neurons[n]['xyz'][1], 0], [-50, Neurons[m]['xyz'][1], 0], 3, 2)
                    comp = makeCompartment('%d_%d_Axon_LIFC' % (n, m), -70, -55, -50, 100, 100, -90, cyl.ID)
                    Neurons[n]['axon'].append(cyl)
                    Neurons[n]['axon_comp'].append(comp)
                else: # Adding these so that we can reference by (n, m) neuron indices.
                    Neurons[n]['axon'].append(None)
                    Neurons[n]['axon_comp'].append(None)
        print('Made axon cylinders and compartments')

        # Make interneuron axon cylinders and compartments from interneurons to principal neurons
        for n in range(numinterneurons):
            Interneurons[n]['axon'] = []
            Interneurons[n]['axon_comp'] = []
            for m in range(numneurons):
                cyl = makeCylinder('%d_%d_Axon' % (n, m), [102.5, Interneurons[n]['xyz'][1], 0], [-50, Neurons[m]['xyz'][1], 0], 3, 2)
                comp = makeCompartment('%d_%d_Axon_LIFC' % (n, m), -70, -55, -50, 100, 100, -90, cyl.ID)
                Interneurons[n]['axon'].append(cyl)
                Interneurons[n]['axon_comp'].append(comp)
        print('Made interneuron axon cylinders and compartments to principal neurons')

        # Make internueron axon cylinders and compartments from interneurons to interneurons
        for n in range(numinterneurons):
            Interneurons[n]['axontoInt'] = []
            Interneurons[n]['axon_comptoInt'] = []
            for m in range(numinterneurons):
                if n != m:
                    cyl = makeCylinder('%d_%d_Axon' % (n, m), [102.5, Interneurons[n]['xyz'][1], 0], [50, Interneurons[m]['xyz'][1], 0], 3, 2)
                    comp = makeCompartment('%d_%d_Axon_LIFC' % (n, m), -70, -55, -50, 100, 100, -90, cyl.ID)
                    Interneurons[n]['axontoInt'].append(cyl)
                    Interneurons[n]['axon_comptoInt'].append(comp)
                else:
                    Interneurons[n]['axontoInt'].append(None)
                    Interneurons[n]['axon_comptoInt'].append(None)
        print('Made interneuron axon cylinders and compartments to interneurons')

        # Make interneuron axon cylinders and compartments from principal neurons to interneurons
        for n in range(numneurons):
            Neurons[n]['axontoInt'] = []
            Neurons[n]['axon_comptoInt'] = []
            for m in range(numinterneurons):
                cyl = makeCylinder('%d_%d_Axon' % (n, m), [5, Neurons[n]['xyz'][1], 0], [50, Interneurons[m]['xyz'][1], 0], 3, 2)
                comp = makeCompartment('%d_%d_Axon_LIFC' % (n, m), -70, -55, -50, 100, 100, -90, cyl.ID)
                Neurons[n]['axontoInt'].append(cyl)
                Neurons[n]['axon_comptoInt'].append(comp)
        print('Made axon cylinders and compartments to interneurons')

        # Remember: Here, compartments become associted with cells, but
        #           these are for 3D object association and do not yet
        #           specify functional connections.
        # Create neurons
        for n in range(numneurons):
            axons_compartments = []
            for axon_comp in Neurons[n]['axon_comp']:
                if axon_comp:
                    axons_compartments.append(axon_comp.ID)
            for axon_comp in Neurons[n]['axon_comptoInt']:
                if axon_comp:
                    axons_compartments.append(axon_comp.ID)
            Neurons[n]['neuron'] = makeNeuron(
                    '%d_Neuron' % n, [ Neurons[n]['soma_comp'].ID ], [ Neurons[n]['dendrite_comp'].ID ], axons_compartments,
                    -70, -55, -50, 100, 100,
                    -90,
                    2.5, 30, 3.0, 5.0, 1.5,
                    30, 300, 1.0, 2.0, 0.3,
                    -20, 20, 200, 0.3)
        print('Made LIFC Neurons')

        for n in range(numinterneurons):
            axons_compartments = []
            for axon_comp in Interneurons[n]['axon_comp']:
                if axon_comp:
                    axons_compartments.append(axon_comp.ID)
            for axon_comp in Interneurons[n]['axon_comptoInt']:
                if axon_comp:
                    axons_compartments.append(axon_comp.ID)
            Interneurons[n]['neuron'] = makeNeuron(
                    '%d_Neuron' % n, [ Interneurons[n]['soma_comp'].ID ], [ Interneurons[n]['dendrite_comp'].ID ], axons_compartments,
                    -70, -55, -50, 100, 100,
                    -90,
                    2.5, 30, 3.0, 5.0, 1.5,
                    30, 300, 0, 0, 0.3,
                    -20, 20, 200, 0)
        print('Made LIFC Interneurons')

        INITIALAMPAWEIGHT=0.1
        # The "SUPERSYNAPSES*" can be interpreted as having multiple synapses between pre- and post-synaptic pairs.
        SUPERSYNAPSES=7
        SUPERSYNAPSESONINT=8
        SUPERSYNAPSESFROMINT=20

        Synapses = {}
        for n in range(numneurons):
            Synapses[n] = {}

        # Remember: This is where actual functional connections are established.
        # Create boxes and receptors
        for source in range(numneurons):
            Synapses[source]['synapse'] = []
            Synapses[source]['AMPA'] = []
            Synapses[source]['NMDA'] = []
            for destination in range(numneurons):
                if source != destination:
                    syn = makeBox('%d_%d_Synapse' % (source, destination), [-50, Neurons[destination]['xyz'][1], 0], [0.1,0.1,0.1], [0,0,0])
                    source_comp_id = Neurons[source]['axon_comp'][destination].ID # requires full matrix
                    dest_comp_id = Neurons[destination]['dendrite_comp'].ID # requires full matrix
                    ampa = makeNetmorphPreSynReceptor(
                        '%d_%d_AMPA' % (source, destination), source_comp_id, dest_comp_id, 'AMPA', 0,
                        0.5, 3.0, g_rec_peak_AMPA, AMPAQuantityPerSynapse*SUPERSYNAPSES,
                        PyrInPyrOut_Hilloc_Distance_um, propagation_velocity, PyrInPyrOut_syndelay, False,
                        INITIALAMPAWEIGHT, 'Hebbian', 0.027, 0.02, 7.0, 7.0,
                        syn.ID)
                    
                    nmda = makeNetmorphPreSynReceptor(
                        '%d_%d_NMDA' % (source, destination), source_comp_id, dest_comp_id, 'NMDA', 0,
                        2.0, 100, g_rec_peak_NMDA, NMDAQuantityPerSynapse*SUPERSYNAPSES,
                        PyrInPyrOut_Hilloc_Distance_um, propagation_velocity, PyrInPyrOut_syndelay, True,
                        0.5, 'None', 0, 0, 0, 0,
                        syn.ID)
                    Synapses[source]['synapse'].append(syn)
                    Synapses[source]['AMPA'].append(ampa)
                    Synapses[source]['NMDA'].append(nmda)
                else: # Adding these so that we can reference by (n, m) neuron indices.
                    Synapses[source]['synapse'].append(None)
                    Synapses[source]['AMPA'].append(None)
                    Synapses[source]['NMDA'].append(None)

        print('Made boxes and LIFC Receptors')

        IntSynapses = {}
        for n in range(numinterneurons):
            IntSynapses[n] = {}

        # Interneurons are connected from every principal neuron and to every principal neuron
        for source in range(numinterneurons):
            IntSynapses[source]['synapse'] = []
            IntSynapses[source]['GABA'] = []
            for destination in range(numneurons):
                syn = makeBox('%d_%d_Synapse' % (source, destination), [-50, Neurons[destination]['xyz'][1], 0], [0.1,0.1,0.1], [0,0,0])
                source_comp_id = Interneurons[source]['axon_comp'][destination].ID # requires full matrix
                dest_comp_id = Neurons[destination]['dendrite_comp'].ID # requires full matrix
                gaba = makeNetmorphPreSynReceptor(
                    '%d_%d_GABA' % (source, destination), source_comp_id, dest_comp_id, 'GABA', -70,
                    0.5, 10.0, g_rec_peak_GABA, GABAQuantityPerSynapse*SUPERSYNAPSESFROMINT,
                    IntInPyrOut_Hilloc_Distance_um, propagation_velocity, IntInPyrOut_syndelay, False,
                    0.5, 'None', 0, 0, 0, 0,
                    syn.ID)
                IntSynapses[source]['synapse'].append(syn)
                IntSynapses[source]['GABA'].append(gaba)
        print('Made Interneuron synapse boxes and LIFC Receptors onto principal neurons')

        for source in range(numinterneurons):
            IntSynapses[source]['synapseonInt'] = []
            IntSynapses[source]['GABAonInt'] = []
            for destination in range(numinterneurons):
                if source != destination:
                    syn = makeBox('%d_%d_Synapse' % (source, destination), [50, Interneurons[destination]['xyz'][1], 0], [0.1,0.1,0.1], [0,0,0])
                    source_comp_id = Interneurons[source]['axon_comptoInt'][destination].ID # requires full matrix
                    dest_comp_id = Interneurons[destination]['dendrite_comp'].ID # requires full matrix
                    gaba = makeNetmorphPreSynReceptor(
                        '%d_%d_GABA' % (source, destination), source_comp_id, dest_comp_id, 'GABA', -70,
                        0.5, 10.0, g_rec_peak_GABA, GABAQuantityPerSynapse*SUPERSYNAPSESFROMINT,
                        IntInPyrOut_Hilloc_Distance_um, propagation_velocity, IntInPyrOut_syndelay, False,
                        0.5, 'None', 0, 0, 0, 0,
                        syn.ID)
                    IntSynapses[source]['synapseonInt'].append(syn)
                    IntSynapses[source]['GABAonInt'].append(gaba)
        print('Made Interneuron synapse boxes and LIFC Receptors onto interneurons')

        for source in range(numneurons):
            Synapses[source]['synapseonInt'] = []
            Synapses[source]['AMPAonInt'] = []
            for destination in range(numinterneurons):
                syn = makeBox('%d_%d_Synapse' % (source, destination), [50, Interneurons[destination]['xyz'][1], 0], [0.1,0.1,0.1], [0,0,0])
                source_comp_id = Neurons[source]['axon_comptoInt'][destination].ID # requires full matrix
                dest_comp_id = Interneurons[destination]['dendrite_comp'].ID # requires full matrix
                ampa = makeNetmorphPreSynReceptor(
                    '%d_%d_AMPA' % (source, destination), source_comp_id, dest_comp_id, 'AMPA', 0,
                    0.5, 3.0, g_rec_peak_AMPA, AMPAQuantityPerSynapse*SUPERSYNAPSESONINT,
                    PyrInPyrOut_Hilloc_Distance_um, propagation_velocity, PyrInPyrOut_syndelay, False,
                    1.0, 'None', 0, 0, 0, 0,
                    syn.ID)
            Synapses[source]['synapseonInt'].append(syn)
            Synapses[source]['AMPAonInt'].append(ampa)
        print('Made synapse boxes and LIFC Receptors from principal neurons onto interneurons')


        saveModel('LIFtest')

    else:

        # Create spheres for 2 principal neurons and 1 interneuron
        PyrIn['soma'] = makeSphere('PyrIn_Soma', 10, [0, -30, 0])
        IntIn['soma'] = makeSphere('IntIn_Soma', 5, [0, 30, 0])
        PyrOut['soma'] = makeSphere('PyrOut_Soma', 10, [100, 0, 0])
        print('Made Spheres')

        # Create cylinders for dendrite and axons
        PyrOut['dendrite'] = makeCylinder('PyrOut_Dendrite', [50, 0, 0], [95, 0, 0], 2, 3)
        PyrIn['axon'] = makeCylinder('PyrIn_Axon', [5, -30, 0], [50, 0, 0], 3, 2)
        IntIn['axon'] = makeCylinder('IntIn_Axon', [2.5, 30, 0], [50, 0, 0], 3, 2)
        print('Made Cylinders')

        # Create compartments for somas, dendrites and axons
        PyrIn['soma_comp'] = makeCompartment('PyrIn_Soma_LIFC', -70, -55, -50, 100, 100, -90, PyrIn['soma'].ID)
        PyrIn['axon_comp'] = makeCompartment('PyrIn_Axon_LIFC', -70, -55, -50, 100, 100, -90, PyrIn['axon'].ID)
        IntIn['soma_comp'] = makeCompartment('IntIn_Soma_LIFC', -70, -55, -50, 100, 100, -90, IntIn['soma'].ID)
        IntIn['axon_comp'] = makeCompartment('IntIn_Axon_LIFC', -70, -55, -50, 100, 100, -90, IntIn['axon'].ID)
        PyrOut['soma_comp'] = makeCompartment('PyrOut_Soma_LIFC', -70, -55, -50, 100, 100, -90, PyrOut['soma'].ID)
        PyrOut['dendrite_comp'] = makeCompartment('PyrOut_Dendrite_LIFC', -70, -55, -50, 100, 100, -90, PyrOut['dendrite'].ID)
        print('Made Compartments')

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

        Synapses = {}
        # Create receptors as determined in IF_with_stdp.py
        Synapses['PyrInPyrOut'] = makeBox('PyrInPyrOut', [50, 0, 0], [0.1,0.1,0.1], [0,0,0])
        Synapses['IntInPyrOut'] = makeBox('IntInPyrOut', [50, 0, 0], [0.1,0.1,0.1], [0,0,0])
        print('Made Boxes')

        # Morphology info: Number of synapses, e.g. typically generated in Netmorph
        NUMPyrInPyrOut = 32
        NUMIntInPyrOut = 21

        Synapses['PyrInPyrOut_AMPA'] = []
        Synapses['PyrInPyrOut_NMDA'] = []
        Synapses['IntInPyrOut_GABA'] = []

        use_Netmorphlike_data = True
        if use_Netmorphlike_data:
            for s in range(NUMPyrInPyrOut):
                Synapses['PyrInPyrOut_AMPA'].append(
                    makeNetmorphPreSynReceptor(
                        'PyrInPyrOut_AMPA_%2d' % s, PyrIn['axon_comp'].ID, PyrOut['dendrite_comp'].ID, 'AMPA', 0,
                        0.5, 3.0, g_rec_peak_AMPA, AMPAQuantityPerSynapse,
                        PyrInPyrOut_Hilloc_Distance_um, propagation_velocity, PyrInPyrOut_syndelay, False,
                        0.5, 'Hebbian', 0.027, 0.02, 7.0, 7.0,
                        Synapses['PyrInPyrOut'].ID)
                    )
                Synapses['PyrInPyrOut_NMDA'].append(
                    makeNetmorphPreSynReceptor(
                        'PyrInPyrOut_NMDA_%2d' % s, PyrIn['axon_comp'].ID, PyrOut['dendrite_comp'].ID, 'NMDA', 0,
                        2.0, 100, g_rec_peak_NMDA, NMDAQuantityPerSynapse,
                        PyrInPyrOut_Hilloc_Distance_um, propagation_velocity, PyrInPyrOut_syndelay, True,
                        0.5, 'None', 0, 0, 0, 0,
                        Synapses['PyrInPyrOut'].ID)
                    )

            for s in range(NUMIntInPyrOut):
                Synapses['IntInPyrOut_GABA'].append(
                    makeNetmorphPreSynReceptor(
                        'IntInPyrOut_GABA_%2d' % s, IntIn['axon_comp'].ID, PyrOut['dendrite_comp'].ID, 'GABA', -70,
                        0.5, 10, g_rec_peak_GABA, GABAQuantityPerSynapse,
                        IntInPyrOut_Hilloc_Distance_um, propagation_velocity, IntInPyrOut_syndelay, False,
                        0.5, 'None', 0, 0, 0, 0,
                        Synapses['IntInPyrOut'].ID)
                    )
        else:
            # Calculated in AddNetmorphLIFCReceptor
            g_peak_AMPA = AMPAQuantityPerSynapse*g_rec_peak_AMPA
            g_peak_NMDA = NMDAQuantityPerSynapse*g_rec_peak_NMDA
            g_peak_GABA = GABAQuantityPerSynapse*g_rec_peak_GABA
            onset_delay_AMPA = PyrInPyrOut_syndelay + (PyrInPyrOut_Hilloc_Distance_um*1e-6/propagation_velocity)
            onset_delay_NMDA = PyrInPyrOut_syndelay + (PyrInPyrOut_Hilloc_Distance_um*1e-6/propagation_velocity)
            onset_delay_GABA = IntInPyrOut_syndelay + (IntInPyrOut_Hilloc_Distance_um*1e-6/propagation_velocity)
            for s in range(NUMPyrInPyrOut):
                Synapses['PyrInPyrOut_AMPA'].append(
                    makePreSynReceptor(
                        'PyrInPyrOut_AMPA_%2d' % s, PyrIn['axon_comp'].ID, PyrOut['dendrite_comp'].ID,
                        'AMPA',
                        0, 0.5, 3.0, g_peak_AMPA, 0.5, onset_delay_AMPA,
                        'Hebbian', 0.027, 0.02, 7.0, 7.0,
                        False,
                        Synapses['PyrInPyrOut'].ID)
                    )
                Synapses['PyrInPyrOut_NMDA'].append(
                    makePreSynReceptor(
                        'PyrInPyrOut_NMDA_%2d' % s, PyrIn['axon_comp'].ID, PyrOut['dendrite_comp'].ID,
                        'NMDA',
                        0, 2.0, 100, g_peak_NMDA, 0.5, onset_delay_NMDA,
                        'None', 0, 0, 0, 0,
                        True,
                        Synapses['PyrInPyrOut'].ID)
                    )

            for s in range(NUMIntInPyrOut):
                Synapses['IntInPyrOut_GABA'].append(
                    makePreSynReceptor(
                        'IntInPyrOut_GABA_%2d' % s, IntIn['axon_comp'].ID, PyrOut['dendrite_comp'].ID,
                        'GABA',
                        -70, 0.5, 10, g_peak_GABA, 0.5, onset_delay_GABA,
                        'None', 0, 0, 0, 0,
                        False,
                        Synapses['IntInPyrOut'].ID)
                    )

        print('Made LIFC Receptors')

        saveModel('LIFtest')


if Args.Autoassociative:

    # Set stimulation times
    T = 80000
    if Args.T:
        T = int(Args.T)

    STIMINTERVAL = 70.0
    REPEATSPERBATCH = 4

    pattern_neurons = []
    for p in range(numpatterns):
        patt_n = [ 8*p + n for n in range(8) ]
        pattern_neurons.append(patt_n)
    print('Pattern neurons:')
    print(pattern_neurons)

    cue_neurons = []
    for p in range(numpatterns):
        cue_n = [ 8*p + n for n in range(4) ]
        cue_neurons.append(cue_n)
    print('Cue neurons:')
    print(cue_neurons)

    # Every stimulation event is recorded as a trial, so that encoding and retrieval
    # trials can be separated in analysis (see output/trials.csv).
    #   phase: 'encode' (full pattern) or 'retrieve' (partial cue)
    #   stim_offsets_ms: per stimulated neuron delay after t_ms (encoding jitter)
    trials = []
    def addTrial(phase:str, pattern:int, t_ms:float, stimulated:list, window_ms:float, offsets:list=None):
        stimulated = sorted(stimulated)
        trials.append({
            'trial': len(trials),
            'phase': phase,
            'pattern': pattern,
            't_ms': t_ms,
            'window_ms': window_ms,
            'stimulated': stimulated,
            'stim_offsets_ms': offsets if offsets else [ 0.0 for n in stimulated ],
            'cue_fraction': len(stimulated)/len(pattern_neurons[pattern]),
        })

    if Args.inspectSTDP:
        # Original protocol: batches of encoding presentations alternate with batches of
        # half-pattern cue presentations for the whole duration T.
        training_stim = [ i*STIMINTERVAL for i in range(numpatterns*REPEATSPERBATCH) ]
        batchduration = STIMINTERVAL*numpatterns*REPEATSPERBATCH
        batchinterval = batchduration + 100
        repeatinterval = 2*batchinterval
        repeats = int(T // repeatinterval)

        for r in range(repeats):
            for s in range(len(training_stim)):
                p = s % numpatterns
                addTrial('encode', p, training_stim[s]+repeatinterval*r, pattern_neurons[p], STIMINTERVAL)
            for s in range(len(training_stim)):
                p = s % numpatterns
                addTrial('retrieve', p, training_stim[s]+repeatinterval*r+batchinterval, cue_neurons[p], STIMINTERVAL)

        run_segments = [ (T, Args.STDP) ]

    else:
        # Default protocol: an encoding phase followed by a retrieval phase.
        #   Encoding: each pattern presented -EncodeTrials times (patterns interleaved).
        #   Retrieval: each pattern cued -RetrievalTrials times with cues of between
        #   -CueMin and -CueMax of the pattern's neurons, each cue a different subset.
        if Args.T:
            print('Note: -T is ignored by the default Autoassociative protocol, T is derived from the number of trials.')
        if not Args.STDP:
            print('WARNING: -STDP not set, so the encoding phase will not change weights (no-learning control).')
        if numpatterns > 1:
            # With jittered encoding, within-pattern weights saturate in both directions, and the
            # resulting stronger attractors can ignite spontaneously, so that STDP then links
            # the patterns. The -inspectSTDP protocol does not do this, because its synchronous
            # presentations only strengthen low-to-high neuron index connections.
            print('WARNING: With -Patterns > 1 the default protocol currently develops cross-pattern weights (see -inspectSTDP).')

        rng = np.random.RandomState(Args.Seed)
        PHASEGAP = 500.0 # ms of quiet between encoding and retrieval phases

        t = 0.0
        for r in range(Args.EncodeTrials):
            for p in range(numpatterns):
                offsets = [ round(float(rng.uniform(0.0, Args.EncodeJitter)), 2) for n in pattern_neurons[p] ]
                addTrial('encode', p, t, pattern_neurons[p], Args.EncodeInterval, offsets)
                t += Args.EncodeInterval
        t_encode_end = t + PHASEGAP

        # Distinct cue subsets per pattern, cycling through cue sizes so that the
        # range from CueMin to CueMax is evenly represented.
        def cueSubsets(pattern:list, num:int)->list:
            psize = len(pattern)
            minsize = max(1, int(math.ceil(Args.CueMin*psize - 1e-9)))
            maxsize = min(psize, int(math.floor(Args.CueMax*psize + 1e-9)))
            if minsize > maxsize:
                raise ValueError('No cue size between -CueMin %.2f and -CueMax %.2f of a %d neuron pattern.' % (Args.CueMin, Args.CueMax, psize))
            sizes = list(range(minsize, maxsize+1))
            available = { s: math.comb(psize, s) for s in sizes }
            used = set()
            subsets = []
            i = 0
            while len(subsets) < num:
                if not any(available.values()):
                    print('Note: Only %d distinct cues exist, repeating cues.' % len(used))
                    used.clear()
                    available = { s: math.comb(psize, s) for s in sizes }
                s = sizes[i % len(sizes)]
                i += 1
                if available[s] == 0:
                    continue
                while True:
                    cue = tuple(sorted(rng.choice(pattern, size=s, replace=False).tolist()))
                    if cue not in used:
                        break
                used.add(cue)
                available[s] -= 1
                subsets.append(list(cue))
            rng.shuffle(subsets)
            return subsets

        cues = [ cueSubsets(pattern_neurons[p], Args.RetrievalTrials) for p in range(numpatterns) ]
        retrieval_order = [ (p, k) for p in range(numpatterns) for k in range(Args.RetrievalTrials) ]
        rng.shuffle(retrieval_order)

        t = t_encode_end
        for p, k in retrieval_order:
            addTrial('retrieve', p, t, cues[p][k], Args.RetrievalInterval)
            t += Args.RetrievalInterval
        T = int(math.ceil(t))

        run_segments = [ (t_encode_end, Args.STDP), (T - t_encode_end, Args.STDP and Args.RetrievalSTDP) ]

    num_encode = sum(1 for tr in trials if tr['phase']=='encode')
    num_retrieve = len(trials) - num_encode
    print('Trials: %d encoding, %d retrieval, T = %d ms' % (num_encode, num_retrieve, T))

    timeneuronpairs_list = sorted([ (tr['t_ms']+dt, n) for tr in trials for n, dt in zip(tr['stimulated'], tr['stim_offsets_ms']) ])

    MySim.SetSpecificAPTimes(timeneuronpairs_list)
    print('Simulation stimulation specified')

else:

    # Set stimulation times
    T = 8000
    if Args.T:
        T = int(Args.T)

    tau_sim_rec_inhibition = 3
    regular_spacing_ms = 100

    compact_driver_spikes = 10
    compact_spacing_ms = 5
    long_driver_spikes = 200
    non_compact_spacing_ms = 10

    if Args.Burst:
        if Args.Long:
            PyrIn_t_in = np.array([(t+1)*non_compact_spacing_ms for t in range(long_driver_spikes)])
        else:
            PyrIn_t_in = np.array([(t+1)*compact_spacing_ms for t in range(compact_driver_spikes)])
    else:
        PyrIn_t_in = np.array([(t+1)*regular_spacing_ms for t in range(int(0.75*T/regular_spacing_ms))])
    IntIn_t_in = PyrIn_t_in+tau_sim_rec_inhibition

    timeneuronpairs_list = [(t, PyrIn['neuron'].ID) for t in PyrIn_t_in.tolist()]
    timeneuronpairs_list += [(t, IntIn['neuron'].ID) for t in IntIn_t_in.tolist()]
    MySim.SetSpecificAPTimes(timeneuronpairs_list)
    print('Simulation stimulation specified')

    run_segments = [ (T, Args.STDP) ]

connections_before_dict = MySim.GetConnectome()
if not vbp.PlotAndStoreConnections(connections_before_dict, 'output', 'before', { 'figsize': (6,6), 'linewidth': 0.5, 'figext': 'pdf', }):
    vbp.ErrorToDB(DBdata, 'File error: Failed to store plots of connectivity')
if not vbp.PlotAndStoreConnections(connections_before_dict, 'output', 'before_conductance', { 'figsize': (6,6), 'linewidth': 0.5, 'figext': 'pdf', }, usematrix='conductance'):
    vbp.ErrorToDB(DBdata, 'File error: Failed to store plots of connectivity conductance')

# Run simulation and record membrane potential
MySim.RecordAll(-1)
for segment_ms, segment_STDP in run_segments:
    MySim.SetSTDP(_DoSTDP=segment_STDP)
    print('Running %.1f ms with STDP %s' % (segment_ms, 'on' if segment_STDP else 'off'))
    MySim.RunAndWait(Runtime_ms=segment_ms, Dt_ms=Args.Dt, timeout_s=100.0)
print('Functional stimulation completed')

recording_dict = MySim.GetRecording()
print('Recorded data retrieved')
spikes_dict = MySim.GetSpikeTimes()
print('Spike times retrieved')

if Args.Autoassociative:
    # Score every trial from the spikes in its response window [t_ms, t_ms+window_ms):
    #   recalled:   pattern neurons that were not stimulated but spiked
    #   recall:     fraction of non-stimulated pattern neurons that spiked
    #   intruders:  principal neurons outside the pattern that spiked
    import csv
    spiketimes = { int(k): v.get('tSpike_ms', []) for k, v in spikes_dict.get('SpikeTimes', {}).items() }
    def spikedIn(n:int, t0:float, t1:float)->bool:
        return any(t0 <= ts < t1 for ts in spiketimes.get(n, []))

    for tr in trials:
        t0, t1 = tr['t_ms'], tr['t_ms']+tr['window_ms']
        pattern = pattern_neurons[tr['pattern']]
        targets = [ n for n in pattern if n not in tr['stimulated'] ]
        tr['recalled'] = [ n for n in targets if spikedIn(n, t0, t1) ]
        tr['intruders'] = [ n for n in range(numneurons) if n not in pattern and spikedIn(n, t0, t1) ]
        tr['interneurons_spiking'] = sum(1 for i in range(numinterneurons) if spikedIn(numneurons+i, t0, t1))
        tr['recall'] = len(tr['recalled'])/len(targets) if targets else 1.0
        tr['complete'] = (len(tr['recalled']) == len(targets)) and not tr['intruders']

    os.makedirs('output', exist_ok=True)
    with open('output/trials.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['trial', 'phase', 'pattern', 't_ms', 'window_ms', 'cue_fraction', 'stimulated', 'recalled', 'intruders', 'interneurons_spiking', 'recall', 'complete'])
        for tr in trials:
            writer.writerow([
                tr['trial'], tr['phase'], tr['pattern'], tr['t_ms'], tr['window_ms'], '%.3f' % tr['cue_fraction'],
                ' '.join(map(str, tr['stimulated'])), ' '.join(map(str, tr['recalled'])), ' '.join(map(str, tr['intruders'])),
                tr['interneurons_spiking'], '%.3f' % tr['recall'], int(tr['complete']),
            ])
    with open('output/trials.json', 'w') as f:
        json.dump({
            'protocol': 'inspectSTDP' if Args.inspectSTDP else 'encode_then_retrieve',
            'T_ms': T,
            'STDP_segments': [ {'duration_ms': d, 'STDP': s} for d, s in run_segments ],
            'pattern_neurons': pattern_neurons,
            'interneuron_ids': [ numneurons+i for i in range(numinterneurons) ],
            'trials': trials,
        }, f, indent=1)
    print('Trial records saved to output/trials.csv and output/trials.json')

    retrieval = [ tr for tr in trials if tr['phase']=='retrieve' ]
    if retrieval:
        print('Retrieval summary (%d trials):' % len(retrieval))
        for frac in sorted(set(round(tr['cue_fraction'], 3) for tr in retrieval)):
            sub = [ tr for tr in retrieval if round(tr['cue_fraction'], 3) == frac ]
            print('  cue %5.1f%%: %3d trials, mean recall %.2f, complete %d/%d, with intruders %d' % (
                100*frac, len(sub), np.mean([tr['recall'] for tr in sub]),
                sum(tr['complete'] for tr in sub), len(sub), sum(1 for tr in sub if tr['intruders'])))

#with open('output/raw.json', 'w') as f:
#    json.dump(recording_dict, f)
#with open('output/spikes.json', 'w') as f:
#    json.dump(spikes_dict, f)

if not vbp.PlotAndStoreRecordedActivity(recording_dict, 'output', { 'figsize': (6,6), 'linewidth': 0.5, 'figext': 'pdf', }, spikes_dict):
    vbp.ErrorToDB(DBdata, 'File error: Failed to store plots of recorded activity')
print('Data plot saved as PDF')

connections_after_dict = MySim.GetConnectome()
if not vbp.PlotAndStoreConnections(connections_after_dict, 'output', 'after', { 'figsize': (6,6), 'linewidth': 0.5, 'figext': 'pdf', }):
    vbp.ErrorToDB(DBdata, 'File error: Failed to store plots of connectivity')
if not vbp.PlotAndStoreConnections(connections_after_dict, 'output', 'after_conductance', { 'figsize': (6,6), 'linewidth': 0.5, 'figext': 'pdf', }, usematrix='conductance'):
    vbp.ErrorToDB(DBdata, 'File error: Failed to store plots of connectivity conductance')

print('Done')

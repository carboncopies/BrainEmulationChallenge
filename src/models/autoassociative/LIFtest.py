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

numneurons = 8 # for Autoassociative option

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
        for n in range(numneurons):
            Neurons[n] = {}

        # Remember: Shapes are just 3D objects.
        #           They do not specify an associated cell.
        #           Compartments are linked to a shape, but they also
        #           do not specify an associated cell yet when created.
        # Make cell body spheres and compartments
        for n in range(numneurons):
            Neurons[n]['xyz'] = [0, n*60, 0]
            Neurons[n]['soma'] = makeSphere('%d_Soma' % n, 10, Neurons[n]['xyz'])
            Neurons[n]['soma_comp'] = makeCompartment('%d_Soma_LIFC' % n, -70, -55, -50, 100, 100, -90, Neurons[n]['soma'].ID)
        print('Made cell body spheres and compartments')

        # Make apical dendrite cylinders and compartments
        for n in range(numneurons):
            Neurons[n]['dendrite'] = makeCylinder('%d_Dendrite' % n, [-50, Neurons[n]['xyz'][1], 0], [-5, Neurons[n]['xyz'][1], 0], 2, 3)
            Neurons[n]['dendrite_comp'] = makeCompartment('%d_Dendrite_LIFC' % n, -70, -55, -50, 100, 100, -90, Neurons[n]['dendrite'].ID)
        print('Made apical dendrite cylinders and compartments')

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

        # Remember: Here, compartments become associted with cells, but
        #           these are for 3D object association and do not yet
        #           specify functional connections.
        # Create neurons
        for n in range(numneurons):
            axons_compartments = []
            for axon_comp in Neurons[n]['axon_comp']:
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

        SUPERSYNAPSES=4

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
                        0.5, 'Hebbian', 0.027, 0.02, 7.0, 7.0,
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

        MySim.ModelSave('LIFtest')
        print('Model saved')

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

        MySim.ModelSave('LIFtest')
        print('Model saved')


if Args.Autoassociative:

    response = MySim.GetAbstractConnectome(Sparse=True)
    print(response)

    # Set stimulation times
    T = 80000

    training_pattern = [ 1 for n in range(numneurons) ]
    testing_pattern = [ 1 for n in range(numneurons // 2) ] + [ 0 for n in range(numneurons // 2) ]
    print('Training pattern:')
    print(training_pattern)
    print('Testing pattern:')
    print(testing_pattern)

    training_stim = [ i*70.0 for i in range(8) ]
    repeats = T // 1600

    timeneuronpairs_list = []
    for n in range(numneurons):
        if training_pattern[n]==1:
            for r in range(repeats):
                t_list = [ (t+1600*r, n) for t in training_stim ] # Neurons[n]['neuron'].ID
                timeneuronpairs_list += t_list

    for n in range(numneurons):
        if testing_pattern[n]==1:
            for r in range(repeats):
                t_list = [ (t+1600*r+800, n) for t in training_stim ] # Neurons[n]['neuron'].ID
                timeneuronpairs_list += t_list

    MySim.SetSpecificAPTimes(timeneuronpairs_list)
    print('Simulation stimulation specified')

else:

    # Set stimulation times
    T = 8000

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

#!../../../venv/bin/python
# full_adder_lifc.py
# Randal A. Koene, 20250724

'''
This script implements a full adder circuit using LIFCNeuron NES class.
The intention is to achieve the same functional response as in the
full_adder_bs.py script, but using LIFC neurons instead of ball-and-stick.

Full adder circuit:

                   +-----------------------------------------------------------------+
                   |                                                                 |
                   +------------------------------------------+----+                 |
                   |                                          |    |                 |
    Cin (-60,30)---+    +----------------------+            +------+> I_C0 (30,30)---+--> Sum (60,30)
                        |                      |            | |                      
    P_inA (-60,0)-------+--+> I_A0 (-30,0)-----+> P_B0 (0,0)+ | +---> P_C0 (30,0)----+
                        |  |                   |            | | |                    | 
    P_inB (-60,-30)--+-----+-------------------+            +-+-|---> P_C1 (30,-30)--+--> Cout (60,-30)
                     |  |                                       |                      
                     |  +---------------------------------------+                  
                     |                                          |   
                     +------------------------------------------+  
'''

scriptversion='0.2.0'

#import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
#from time import sleep
import argparse
import math
import json
import os

import vbpcommon as vbp
# from BrainGenix.BG_API import BG_API_Setup
#from NES_interfaces.KGTRecords import plot_recorded
import BrainGenix.NES as NES
import BrainGenix

Parser = argparse.ArgumentParser(description="Full Adder LIFC test script")
Parser.add_argument("-Host", default="localhost", type=str, help="Host to connect to")
Parser.add_argument("-Port", default=8000, type=int, help="Port number to connect to")
Parser.add_argument("-UseHTTPS", default=False, type=bool, help="Enable or disable HTTPS")
Parser.add_argument("-ExpsDB", default="./ExpsDB.json", type=str, help="Path to experiments database JSON file")
Parser.add_argument("-STDP", action="store_true", help="Enable STDP")
Parser.add_argument("-Seed", default=0, type=int, help="Set random seed")
Parser.add_argument("-Reload", actions="store_true", help="Reload saved model")
Parser.add_argument("-Burst", action="store_true", help="Burst input")
Parser.add_argument("-Long", action="store_true", help="Long burst driver")
Args = Parser.parse_args()

# Initialize data collection for entry in DB file
DBdata = vbp.InitExpDB(
    Args.ExpsDB,
    'FullAdderLIFCtest',
    scriptversion,
    _initIN = {
    },
    _initOUT = {
    })

ClientCfg, ClientInstance = vbp.ClientFromArgs(DBdata, Args)

SimulationCfg, MySim = vbp.NewSimulation(DBdata, ClientInstance, 'FullAdderLIFCtest', Seed=Args.Seed)
print('Simulation created')

MySim.SetLIFCAbstractedFunctional(_AbstractedFunctional=True) # needs to be called before building LIFC receptors
MySim.SetSTDP(_DoSTDP=Args.STDP)
print('Options specified')

# Define neuron positions for full adder circuit
Cin_pos   = [-60, 30, 0]
P_inA_pos = [-60,  0, 0]
P_inB_pos = [-60,-30, 0]

I_A0_pos =  [-30,  0, 0]

P_B0_pos =  [0, 0, 0]

I_C0_pos =  [30, 30, 0]
P_C0_pos =  [30, 90, 0]
P_C1_pos =  [30,  0, 0]

Sum_pos =   [60, 30, 0]
Cout_pos =  [60,-30, 0]

# Define neuron types and parameters
principal_soma_radius_um = 10.0
interneuron_soma_radius_um = 5.0

neuron_positions = {
    'Cin': Cin_pos,
    'P_inA': P_inA_pos,
    'P_inB': P_inB_pos,
    'I_A0': I_A0_pos,
    'P_B0': P_B0_pos,
    'I_C0': I_C0_pos,
    'P_C0': P_C0_pos,
    'P_C1': P_C1_pos,
    'Sum': Sum_pos,
    'Cout': Cout_pos,
}

neuron_radii = {
    'Cin': principal_soma_radius_um,
    'P_inA': principal_soma_radius_um,
    'P_inB': principal_soma_radius_um,
    'I_A0': interneuron_soma_radius_um,
    'P_B0': principal_soma_radius_um,
    'I_C0': interneuron_soma_radius_um,
    'P_C0': principal_soma_radius_um,
    'P_C1': principal_soma_radius_um,
    'Sum': principal_soma_radius_um,
    'Cout': principal_soma_radius_um,
}

if Args.Reload:

    MySim.ModelLoad('FullAdderLIFCtest')
    print('Reloaded LIFC Receptors')

    class NeuronStub:
        def __init__(self, _ID):
            self.ID = _ID
    
    # Create stub neurons for reloaded model
    neurons = {}
    for i, name in enumerate(neuron_positions.keys()):
        neurons[name] = NeuronStub(i)

else:

    def makeSphere(name, radius, center):
        SphereCfg = NES.Shapes.Sphere.Configuration()
        SphereCfg.Name = name
        SphereCfg.Radius_um = radius
        SphereCfg.Center_um = center
        return MySim.AddSphere(SphereCfg)

    # Create spheres for all neurons
    somas = {}
    for name, pos in neuron_positions.items():
        somas[name] = makeSphere(f'{name}_Soma', neuron_radii[name], pos)
    print('Made Spheres')

    def makeCylinder(name, point1, point2, radius1, radius2):
        CylinderCfg = NES.Shapes.Cylinder.Configuration()
        CylinderCfg.Name = name
        CylinderCfg.Point1Position_um = point1
        CylinderCfg.Point2Position_um = point2
        CylinderCfg.Point1Radius_um = radius1
        CylinderCfg.Point2Radius_um = radius2
        return MySim.AddCylinder(CylinderCfg)

    # Create cylinders for axons - define all connections
    axons = {}
    
    # Define axon connections based on full adder circuit
    axon_connections = {
        'Cin_IC0': (Cin_pos, I_C0_pos),
        'Cin_PC1': (Cin_pos, P_C1_pos),
        'Cin_Sum': (Cin_pos, Sum_pos),
        
        'PinA_IA0': (P_inA_pos, I_A0_pos),
        'PinA_PB0': (P_inA_pos, P_B0_pos),
        'PinA_PC0': (P_inA_pos, P_C0_pos),
        
        'PinB_IA0': (P_inB_pos, I_A0_pos),
        'PinB_PB0': (P_inB_pos, P_B0_pos),
        'PinB_PC0': (P_inB_pos, P_C0_pos),
        
        'IA0_PB0': (I_A0_pos, P_B0_pos),
        
        'PB0_IC0': (P_B0_pos, I_C0_pos),
        'PB0_PC1': (P_B0_pos, P_C1_pos),
        'PB0_Sum': (P_B0_pos, Sum_pos),
        
        'IC0_Sum': (I_C0_pos, Sum_pos),
        
        'PC0_Cout': (P_C0_pos, Cout_pos),
        'PC1_Cout': (P_C1_pos, Cout_pos),
        
        # Output axons (dummy connections for output neurons)
        'Sum_out': (Sum_pos, [Sum_pos[0] + 30, Sum_pos[1], Sum_pos[2]]),
        'Cout_out': (Cout_pos, [Cout_pos[0] + 30, Cout_pos[1], Cout_pos[2]]),
    }
    
    for name, (start_pos, end_pos) in axon_connections.items():
        # Find the neuron names for start and end positions
        start_neuron = None
        end_neuron = None
        for neuron_name, pos in neuron_positions.items():
            if pos == start_pos:
                start_neuron = neuron_name
            if pos == end_pos:
                end_neuron = neuron_name
        
        # Debug output
        if start_neuron is None:
            print(f"Warning: Could not find start neuron for {name} with position {start_pos}")
        if end_neuron is None and not name.endswith('_out'):
            print(f"Warning: Could not find end neuron for {name} with position {end_pos}")
        
        # Handle special cases for output axons that don't have target neurons
        if end_neuron is None:
            if name == 'Sum_out':
                end_neuron = 'Sum'
                end_radius = neuron_radii['Sum']
            elif name == 'Cout_out':
                end_neuron = 'Cout'
                end_radius = neuron_radii['Cout']
            else:
                # For other cases, use a default radius
                end_neuron = 'Sum'  # fallback
                end_radius = 10.0
        else:
            end_radius = neuron_radii[end_neuron]
        
        # Calculate start and end points relative to soma positions
        start_point = [start_pos[0] + neuron_radii[start_neuron], start_pos[1], start_pos[2]]
        end_point = [end_pos[0] - end_radius, end_pos[1], end_pos[2]]
        
        axons[name] = makeCylinder(f'{name}_Axon', start_point, end_point, 3, 2)
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

    # Create compartments for somas and axons
    soma_compartments = {}
    axon_compartments = {}
    
    for name in neuron_positions.keys():
        soma_compartments[name] = makeCompartment(f'{name}_Soma_LIFC', -70, -55, -50, 100, 100, -90, somas[name].ID)
    
    for name in axons.keys():
        axon_compartments[name] = makeCompartment(f'{name}_Axon_LIFC', -70, -55, -50, 100, 100, -90, axons[name].ID)
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

    # Create neurons with appropriate axon connections
    neurons = {}
    
    # Input neurons
    neurons['Cin'] = makeNeuron(
        'Cin_Neuron', [soma_compartments['Cin'].ID], [], [axon_compartments['Cin_IC0'].ID, axon_compartments['Cin_PC1'].ID, axon_compartments['Cin_Sum'].ID],
        -70, -55, -50, 100, 100,
        -90,
        2.5, 30, 3.0, 5.0, 1.5,
        30, 300, 1.0, 2.0, 0.3,
        -20, 20, 200, 0.3)
    
    neurons['P_inA'] = makeNeuron(
        'P_inA_Neuron', [soma_compartments['P_inA'].ID], [], [axon_compartments['PinA_IA0'].ID, axon_compartments['PinA_PB0'].ID, axon_compartments['PinA_PC0'].ID],
        -70, -55, -50, 100, 100,
        -90,
        2.5, 30, 3.0, 5.0, 1.5,
        30, 300, 1.0, 2.0, 0.3,
        -20, 20, 200, 0.3)
    
    neurons['P_inB'] = makeNeuron(
        'P_inB_Neuron', [soma_compartments['P_inB'].ID], [], [axon_compartments['PinB_IA0'].ID, axon_compartments['PinB_PB0'].ID, axon_compartments['PinB_PC0'].ID],
        -70, -55, -50, 100, 100,
        -90,
        2.5, 30, 3.0, 5.0, 1.5,
        30, 300, 1.0, 2.0, 0.3,
        -20, 20, 200, 0.3)
    
    # Layer A interneuron
    neurons['I_A0'] = makeNeuron(
        'I_A0_Neuron', [soma_compartments['I_A0'].ID], [], [axon_compartments['IA0_PB0'].ID],
        -70, -55, -50, 100, 100,
        -90,
        2.5, 30, 3.0, 5.0, 1.5,
        30, 300, 0, 0, 0.3,
        -20, 20, 200, 0)
    
    # Layer B principal neuron
    neurons['P_B0'] = makeNeuron(
        'P_B0_Neuron', [soma_compartments['P_B0'].ID], [], [axon_compartments['PB0_IC0'].ID, axon_compartments['PB0_PC1'].ID, axon_compartments['PB0_Sum'].ID],
        -70, -55, -50, 100, 100,
        -90,
        2.5, 30, 3.0, 5.0, 1.5,
        30, 300, 1.0, 2.0, 0.3,
        -20, 20, 200, 0.3)
    
    # Layer C neurons
    neurons['I_C0'] = makeNeuron(
        'I_C0_Neuron', [soma_compartments['I_C0'].ID], [], [axon_compartments['IC0_Sum'].ID],
        -70, -55, -50, 100, 100,
        -90,
        2.5, 30, 3.0, 5.0, 1.5,
        30, 300, 0, 0, 0.3,
        -20, 20, 200, 0)
    
    neurons['P_C0'] = makeNeuron(
        'P_C0_Neuron', [soma_compartments['P_C0'].ID], [], [axon_compartments['PC0_Cout'].ID],
        -70, -55, -50, 100, 100,
        -90,
        2.5, 30, 3.0, 5.0, 1.5,
        30, 300, 1.0, 2.0, 0.3,
        -20, 20, 200, 0.3)
    
    neurons['P_C1'] = makeNeuron(
        'P_C1_Neuron', [soma_compartments['P_C1'].ID], [], [axon_compartments['PC1_Cout'].ID],
        -70, -55, -50, 100, 100,
        -90,
        2.5, 30, 3.0, 5.0, 1.5,
        30, 300, 1.0, 2.0, 0.3,
        -20, 20, 200, 0.3)
    
    # Output neurons
    neurons['Sum'] = makeNeuron(
        'Sum_Neuron', [soma_compartments['Sum'].ID], [], [axon_compartments['Sum_out'].ID],
        -70, -55, -50, 100, 100,
        -90,
        2.5, 30, 3.0, 5.0, 1.5,
        30, 300, 1.0, 2.0, 0.3,
        -20, 20, 200, 0.3)
    
    neurons['Cout'] = makeNeuron(
        'Cout_Neuron', [soma_compartments['Cout'].ID], [], [axon_compartments['Cout_out'].ID],
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

    # Create synapses for all connections
    Synapses = {}
    
    # Define connection patterns based on full adder circuit
    connection_patterns = {
        'Cin_IC0': (neurons['Cin'], neurons['I_C0'], 'AMPA', 0, 0.5, 3.0, 20, 1.0, 1.0, 'None', 0, 0, 0, 0, False),
        'Cin_PC1': (neurons['Cin'], neurons['P_C1'], 'AMPA', 0, 0.5, 3.0, 20, 1.0, 1.0, 'None', 0, 0, 0, 0, False),
        'Cin_Sum': (neurons['Cin'], neurons['Sum'], 'AMPA', 0, 0.5, 3.0, 20, 1.0, 1.0, 'None', 0, 0, 0, 0, False),
        
        'PinA_IA0': (neurons['P_inA'], neurons['I_A0'], 'AMPA', 0, 0.5, 3.0, 20, 0.5, 1.0, 'None', 0, 0, 0, 0, False),
        'PinA_PB0': (neurons['P_inA'], neurons['P_B0'], 'AMPA', 0, 0.5, 3.0, 20, 0.9, 1.0, 'None', 0, 0, 0, 0, False),
        'PinA_PC0': (neurons['P_inA'], neurons['P_C0'], 'AMPA', 0, 0.5, 3.0, 20, 1.0, 1.0, 'None', 0, 0, 0, 0, False),
        
        'PinB_IA0': (neurons['P_inB'], neurons['I_A0'], 'AMPA', 0, 0.5, 3.0, 20, 0.5, 1.0, 'None', 0, 0, 0, 0, False),
        'PinB_PB0': (neurons['P_inB'], neurons['P_B0'], 'AMPA', 0, 0.5, 3.0, 20, 0.9, 1.0, 'None', 0, 0, 0, 0, False),
        'PinB_PC0': (neurons['P_inB'], neurons['P_C0'], 'AMPA', 0, 0.5, 3.0, 20, 1.0, 1.0, 'None', 0, 0, 0, 0, False),
        
        'IA0_PB0': (neurons['I_A0'], neurons['P_B0'], 'GABA', -70, 0.5, 10, 40, 2.0, 1.0, 'None', 0, 0, 0, 0, False),
        
        'PB0_IC0': (neurons['P_B0'], neurons['I_C0'], 'AMPA', 0, 0.5, 3.0, 20, 1.0, 1.0, 'None', 0, 0, 0, 0, False),
        'PB0_PC1': (neurons['P_B0'], neurons['P_C1'], 'AMPA', 0, 0.5, 3.0, 20, 1.0, 1.0, 'None', 0, 0, 0, 0, False),
        'PB0_Sum': (neurons['P_B0'], neurons['Sum'], 'AMPA', 0, 0.5, 3.0, 20, 1.0, 1.0, 'None', 0, 0, 0, 0, False),
        
        'IC0_Sum': (neurons['I_C0'], neurons['Sum'], 'GABA', -70, 0.5, 10, 40, 1.0, 1.0, 'None', 0, 0, 0, 0, False),
        
        'PC0_Cout': (neurons['P_C0'], neurons['Cout'], 'AMPA', 0, 0.5, 3.0, 20, 1.0, 1.0, 'None', 0, 0, 0, 0, False),
        'PC1_Cout': (neurons['P_C1'], neurons['Cout'], 'AMPA', 0, 0.5, 3.0, 20, 1.0, 1.0, 'None', 0, 0, 0, 0, False),
    }
    
    # Create synapse boxes and receptors
    for connection_name, (from_neuron, to_neuron, neurotransmitter, E, tau_rise, tau_decay, g_peak, weight, onset_delay, STDP_type, A_pos, A_neg, tau_pos, tau_neg, voltage_gated) in connection_patterns.items():
        # Create synapse box at the target neuron position
        # Create a mapping from connection names to target neuron names
        connection_to_target = {
            'Cin_IC0': 'I_C0',
            'Cin_PC1': 'P_C1', 
            'Cin_Sum': 'Sum',
            'PinA_IA0': 'I_A0',
            'PinA_PB0': 'P_B0',
            'PinA_PC0': 'P_C0',
            'PinB_IA0': 'I_A0',
            'PinB_PB0': 'P_B0',
            'PinB_PC0': 'P_C0',
            'IA0_PB0': 'P_B0',
            'PB0_IC0': 'I_C0',
            'PB0_PC1': 'P_C1',
            'PB0_Sum': 'Sum',
            'IC0_Sum': 'Sum',
            'PC0_Cout': 'Cout',
            'PC1_Cout': 'Cout',
        }
        
        target_neuron_name = connection_to_target.get(connection_name)
        if target_neuron_name is None:
            print(f"Warning: No target mapping found for connection {connection_name}")
            continue
        
        synapse_pos = neuron_positions[target_neuron_name]
        Synapses[connection_name] = makeBox(connection_name, synapse_pos, [0.1,0.1,0.1], [0,0,0])
        
        # Create receptor
        source_comp = axon_compartments[connection_name].ID
        dest_comp = soma_compartments[target_neuron_name].ID
        
        makePreSynReceptor(
            f'{connection_name}_Receptor', source_comp, dest_comp, neurotransmitter,
            E, tau_rise, tau_decay, g_peak, weight, onset_delay,
            STDP_type, A_pos, A_neg, tau_pos, tau_neg,
            voltage_gated,
            Synapses[connection_name].ID
        )

    MySim.ModelSave('FullAdderLIFCtest')
    print('Model saved')

    print('Made LIFC Receptors')


# Set stimulation times for XOR test (same as in ball-and-stick version)
T = 800

# XOR test stimulation pattern
t_soma_fire_ms = [
    (100.0, neurons['P_inA'].ID),  # Test P_inA only
    (200.0, neurons['P_inB'].ID),  # Test P_inB only  
    (300.0, neurons['P_inA'].ID),  # Test both P_inA and P_inB
    (300.0, neurons['P_inB'].ID),
]

timeneuronpairs_list = [(t, neuron_id) for t, neuron_id in t_soma_fire_ms]
MySim.SetSpecificAPTimes(timeneuronpairs_list)
print('Simulation stimulation specified')

# Run simulation and record membrane potential
MySim.RecordAll(-1)
MySim.RunAndWait(Runtime_ms=T, timeout_s=100.0)
print('Functional stimulation completed')

recording_dict = MySim.GetRecording()
print('Recorded data retrieved')

savefolder = '/home/skim/output/output'+str(datetime.now()).replace(":", "_")

if not vbp.PlotAndStoreRecordedActivity(recording_dict, savefolder, { 'figsize': (6,6), 'linewidth': 0.5, 'figext': 'pdf', }):
    vbp.ErrorToDB(DBdata, 'File error: Failed to store plots of recorded activity')
print('Data plot saved as PDF')

print('Done')


# 5.3 Retrieve recordings and plot
print("\n=== RECORDING ANALYSIS ===")

def find_cell_with_id(id:int) -> str:
    """Enhanced cell lookup with debug output"""
    for n in cells.keys():
        if cells[n].ID == id:
            print(f"Found match - ID: {id}, Name: {n}")
            return n
    print(f"Warning: No matching neuron found for ID: {id}")
    return ''

recording_dict = bg_api.BGNES_get_recording()
print("\nRaw recording keys:", list(recording_dict.keys()))

if isinstance(recording_dict, dict):
    if "StatusCode" in recording_dict:
        print(f"API Status Code: {recording_dict['StatusCode']}")
        
    if "Recording" in recording_dict and recording_dict["Recording"] is not None:
        recording = recording_dict["Recording"]
        print("\n=== RECORDING DETAILS ===")
        print("Available data categories:", list(recording.keys()))
        
        if 'neurons' in recording:
            print("\nNeurons with recorded data:")
            recorded_neuron_ids = list(recording['neurons'].keys())
            print("Raw neuron IDs in recording:", recorded_neuron_ids)
            
            # Create mapping of all expected neurons
            print("\nExpected neurons in model:")
            for name, cell in cells.items():
                print(f"Name: {name}, ID: {cell.ID}")
            
            # Check for recorded neurons not in our model
            print("\nNeuron ID analysis:")
            missing_ids = []
            for neuron_idstr in recorded_neuron_ids:
                neuron_id = int(neuron_idstr)
                name = find_cell_with_id(neuron_id)
                if not name:
                    missing_ids.append(neuron_idstr)
            
            if missing_ids:
                print(f"\nWarning: Recording contains data for unknown neuron IDs: {missing_ids}")
            
            # Prepare for plotting
            sorted_neuron_names = []
            for neuron_idstr in recorded_neuron_ids:
                neuron_id = int(neuron_idstr)
                neuron_name = find_cell_with_id(neuron_id)
                if neuron_name:
                    sorted_neuron_names.append(neuron_name)
                else:
                    sorted_neuron_names.append(f"Unknown_{neuron_idstr}")
            
            print("\nFinal neuron mapping for plotting:")
            for i, name in enumerate(sorted_neuron_names):
                print(f"Plot position {i}: {name}")
            
            # Generate plot
            print(f"\nGenerating plot in {savefolder}")
            plot_recorded(
                savefolder=savefolder,
                data=recording,
                figspecs=figspecs,
                cell_titles=sorted_neuron_names
            )
        else:
            print("Error: No neuron data in recording")
    else:
        print("Error: Recording data is missing or empty")
else:
    print("Error: Invalid recording format received")

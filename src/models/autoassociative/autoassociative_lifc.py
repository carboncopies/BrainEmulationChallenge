#!/usr/bin/env python3
# autoassociative_lifc.py
# 8-neuron fully-connected recurrent LIFC autoassociative memory (Hopfield-style).
#
# Extracted from LIFtest.py's -Autoassociative branch (Randal A. Koene) as a
# dedicated, parameterized circuit for Optuna tuning -- same pattern as
# shift_register_lifc.py. The synaptic weight and AMPA STDP parameters that are
# hardcoded inline in LIFtest.py are exposed here as CLI args; ALL defaults equal
# the original hardcoded constants, so running this with default args reproduces
# LIFtest.py's behavior exactly (see SESSION_STATUS.md, "default-identical").
#
# Recall requires plasticity: pass -STDP (LIFtest.py's default is STDP OFF, which
# produces no recall -- see SESSION_STATUS.md). The optimizer always passes -STDP.
#
# On completion it prints one machine-parseable line consumed by the optimizer:
#   SCORE clean_recall=<0..1> full_recall_cycles=<int> clean_recall_cycles=<int> leak=<int>
# clean_recall is the objective (see phase1_diagnostic.score_recall).

import argparse
from datetime import datetime

import vbpcommon as vbp                       # sets sys.path for NES_interfaces
import BrainGenix.NES as NES
from NES_interfaces.KGTRecords import extract_t_Vm
from phase1_diagnostic import score_recall

scriptversion = '0.1.0'

Parser = argparse.ArgumentParser(description="Autoassociative LIFC memory (tunable)")
Parser.add_argument("-Host", default="localhost", type=str, help="Host to connect to")
Parser.add_argument("-Port", default=8000, type=int, help="Port number to connect to")
Parser.add_argument("-UseHTTPS", default=False, type=bool, help="Enable or disable HTTPS")
Parser.add_argument("-ExpsDB", default="./ExpsDB.json", type=str, help="Path to experiments DB JSON")
Parser.add_argument("-Seed", default=0, type=int, help="Random seed")
Parser.add_argument("-STDP", action="store_true", help="Enable STDP (required for recall)")
# --- tunable circuit parameters (defaults = original LIFtest.py hardcoded values) ---
Parser.add_argument("-Weight", default=0.5, type=float, help="Receptor weight, AMPA & NMDA (orig 0.5)")
Parser.add_argument("-STDP_A_pos", default=0.027, type=float, help="AMPA Hebbian potentiation rate (orig 0.027)")
Parser.add_argument("-STDP_A_neg", default=0.02, type=float, help="AMPA Hebbian depression rate (orig 0.02)")
Parser.add_argument("-STDP_Tau_pos", default=7.0, type=float, help="AMPA STDP potentiation tau ms (orig 7.0)")
Parser.add_argument("-STDP_Tau_neg", default=7.0, type=float, help="AMPA STDP depression tau ms (orig 7.0)")
Parser.add_argument("-SuperSynapses", default=4, type=int, help="Receptor-quantity multiplier (orig 4)")
Parser.add_argument("-Save", action="store_true", help="Also save Vm pickle + PDF plot to /tmp/vbp_*")
Args = Parser.parse_args()

DBdata = vbp.InitExpDB(Args.ExpsDB, 'AutoassocLIFC', scriptversion, _initIN={}, _initOUT={})
ClientCfg, ClientInstance = vbp.ClientFromArgs(DBdata, Args)
SimulationCfg, MySim = vbp.NewSimulation(DBdata, ClientInstance, 'AutoassocLIFC', Seed=Args.Seed)

MySim.SetLIFCAbstractedFunctional(_AbstractedFunctional=True)  # before building LIFC receptors
MySim.SetSTDP(_DoSTDP=Args.STDP)

numneurons = 8


def makeSphere(name, radius, center):
    c = NES.Shapes.Sphere.Configuration()
    c.Name, c.Radius_um, c.Center_um = name, radius, center
    return MySim.AddSphere(c)


def makeCylinder(name, point1, point2, radius1, radius2):
    c = NES.Shapes.Cylinder.Configuration()
    c.Name = name
    c.Point1Position_um, c.Point2Position_um = point1, point2
    c.Point1Radius_um, c.Point2Radius_um = radius1, radius2
    return MySim.AddCylinder(c)


def makeBox(name, center, dimensions, rotation):
    c = NES.Shapes.Box.Configuration()
    c.Name, c.CenterPosition_um, c.Dimensions_um, c.Rotation_rad = name, center, dimensions, rotation
    return MySim.AddBox(c)


def makeCompartment(name, Vrest, Vreset, Vth, R_m, C_m, E_AHP, shapeID):
    c = NES.Models.Compartments.LIFC.Configuration()
    c.Name = name
    c.RestingPotential_mV, c.ResetPotential_mV, c.SpikeThreshold_mV = Vrest, Vreset, Vth
    c.MembraneResistance_MOhm, c.MembraneCapacitance_pF = R_m, C_m
    c.AfterHyperpolarizationAmplitude_mV, c.Shape = E_AHP, shapeID
    return MySim.AddLIFCCompartment(c)


def makeNeuron(name, SomaIDs, DendriteIDs, AxonIDs):
    # All neuron biophysics identical to LIFtest.py's makeNeuron autoassociative
    # calls (fixed; not tuned here).
    c = NES.Models.Neurons.LIFC.Configuration()
    c.Name = name
    c.SomaIDs, c.DendriteIDs, c.AxonIDs = SomaIDs, DendriteIDs, AxonIDs
    c.RestingPotential_mV, c.ResetPotential_mV, c.SpikeThreshold_mV = -70, -55, -50
    c.MembraneResistance_MOhm, c.MembraneCapacitance_pF = 100, 100
    c.RefractoryPeriod_ms, c.SpikeDepolarization_mV = 2, 30
    c.UpdateMethod, c.ResetMethod = 'ExpEulerCm', 'ToVm'
    c.AfterHyperpolarizationReversalPotential_mV = -90
    c.FastAfterHyperpolarizationRise_ms, c.FastAfterHyperpolarizationDecay_ms = 2.5, 30
    c.FastAfterHyperpolarizationPeakConductance_nS, c.FastAfterHyperpolarizationMaxPeakConductance_nS = 3.0, 5.0
    c.FastAfterHyperpolarizationHalfActConstant = 1.5
    c.SlowAfterHyperpolarizationRise_ms, c.SlowAfterHyperpolarizationDecay_ms = 30, 300
    c.SlowAfterHyperpolarizationPeakConductance_nS, c.SlowAfterHyperpolarizationMaxPeakConductance_nS = 1.0, 2.0
    c.SlowAfterHyperpolarizationHalfActConstant = 0.3
    c.AfterHyperpolarizationSaturationModel = 'clip'
    c.FatigueThreshold, c.FatigueRecoveryTime_ms = 300, 1000
    c.AfterDepolarizationReversalPotential_mV, c.AfterDepolarizationRise_ms = -20, 20
    c.AfterDepolarizationDecay_ms, c.AfterDepolarizationPeakConductance_nS = 200, 0.3
    c.AfterDepolarizationSaturationMultiplier, c.AfterDepolarizationRecoveryTime_ms = 2.0, 300
    c.AfterDepolarizationDepletion, c.AfterDepolarizationSaturationModel = 0.3, 'clip'
    c.AdaptiveThresholdDiffPerSpike, c.AdaptiveTresholdRecoveryTime_ms = 0.2, 50
    c.AdaptiveThresholdDiffPotential_mV, c.AdaptiveThresholdFloor_mV = 10, -50
    c.AdaptiveThresholdFloorDeltaPerSpike_mV, c.AdaptiveThresholdFloorRecoveryTime_ms = 1.0, 500
    return MySim.AddLIFCNeuron(c)


def makeNetmorphPreSynReceptor(name, sourcecompID, destcompID, receptortype, E,
                               tau_rise, tau_decay, g_rec_peak, quantity,
                               hilloc_distance, velocity, syn_delay, voltage_gated,
                               weight, STDP_type, A_pos, A_neg, tau_pos, tau_neg, shapeID):
    c = NES.Models.Connections.NetmorphLIFCReceptor.Configuration()
    c.Name = name
    c.SourceCompartment, c.DestinationCompartment = sourcecompID, destcompID
    c.Neurotransmitter, c.ReversalPotential_mV = receptortype, E
    c.PSPRise_ms, c.PSPDecay_ms = tau_rise, tau_decay
    c.ReceptorPeakConductance_nS, c.ReceptorQuantity = g_rec_peak, quantity
    c.HillocDistance_um, c.Velocity_mps, c.SynapticDelay_ms = hilloc_distance, velocity, syn_delay
    c.voltage_gated, c.Weight = voltage_gated, weight
    c.STDP_Method = STDP_type
    c.STDP_A_pos, c.STDP_A_neg, c.STDP_Tau_pos, c.STDP_Tau_neg = A_pos, A_neg, tau_pos, tau_neg
    c.STDP_Shift, c.ReceptorMorphology = -4.0, shapeID
    return MySim.AddNetmorphLIFCReceptor(c)


# Netmorph-to-NES conversion constants (unchanged from LIFtest.py)
PyrInPyrOut_Area_um2 = 60 * 0.0086
PyrInPyrOut_Hilloc_Distance_um = 100
AMPAChannelsProportion = 0.83
NMDAChannelsProportion = 0.17
g_rec_peak_AMPA = 20e-3  # nS
g_rec_peak_NMDA = 50e-3  # nS
propagation_velocity = 1.0  # m/s
PyrInPyrOut_syndelay = 1.0  # ms
AMPAQuantityPerSynapse = int(AMPAChannelsProportion * PyrInPyrOut_Area_um2 / 0.0086)
NMDAQuantityPerSynapse = int(NMDAChannelsProportion * PyrInPyrOut_Area_um2 / 0.0086)

# --- Build the 8-neuron fully-connected recurrent network ---
Neurons = {n: {} for n in range(numneurons)}

for n in range(numneurons):
    Neurons[n]['xyz'] = [0, n * 60, 0]
    Neurons[n]['soma'] = makeSphere('%d_Soma' % n, 10, Neurons[n]['xyz'])
    Neurons[n]['soma_comp'] = makeCompartment('%d_Soma_LIFC' % n, -70, -55, -50, 100, 100, -90, Neurons[n]['soma'].ID)

for n in range(numneurons):
    Neurons[n]['dendrite'] = makeCylinder('%d_Dendrite' % n, [-50, Neurons[n]['xyz'][1], 0], [-5, Neurons[n]['xyz'][1], 0], 2, 3)
    Neurons[n]['dendrite_comp'] = makeCompartment('%d_Dendrite_LIFC' % n, -70, -55, -50, 100, 100, -90, Neurons[n]['dendrite'].ID)

for n in range(numneurons):
    Neurons[n]['axon'] = []
    Neurons[n]['axon_comp'] = []
    for m in range(numneurons):
        if n != m:
            cyl = makeCylinder('%d_%d_Axon' % (n, m), [5, Neurons[n]['xyz'][1], 0], [-50, Neurons[m]['xyz'][1], 0], 3, 2)
            comp = makeCompartment('%d_%d_Axon_LIFC' % (n, m), -70, -55, -50, 100, 100, -90, cyl.ID)
            Neurons[n]['axon'].append(cyl)
            Neurons[n]['axon_comp'].append(comp)
        else:
            Neurons[n]['axon'].append(None)
            Neurons[n]['axon_comp'].append(None)

for n in range(numneurons):
    axons_compartments = [ac.ID for ac in Neurons[n]['axon_comp'] if ac]
    Neurons[n]['neuron'] = makeNeuron('%d_Neuron' % n, [Neurons[n]['soma_comp'].ID], [Neurons[n]['dendrite_comp'].ID], axons_compartments)
print('Made LIFC Neurons')

for source in range(numneurons):
    for destination in range(numneurons):
        if source != destination:
            syn = makeBox('%d_%d_Synapse' % (source, destination), [-50, Neurons[destination]['xyz'][1], 0], [0.1, 0.1, 0.1], [0, 0, 0])
            source_comp_id = Neurons[source]['axon_comp'][destination].ID
            dest_comp_id = Neurons[destination]['dendrite_comp'].ID
            makeNetmorphPreSynReceptor(
                '%d_%d_AMPA' % (source, destination), source_comp_id, dest_comp_id, 'AMPA', 0,
                0.5, 3.0, g_rec_peak_AMPA, AMPAQuantityPerSynapse * Args.SuperSynapses,
                PyrInPyrOut_Hilloc_Distance_um, propagation_velocity, PyrInPyrOut_syndelay, False,
                Args.Weight, 'Hebbian', Args.STDP_A_pos, Args.STDP_A_neg, Args.STDP_Tau_pos, Args.STDP_Tau_neg,
                syn.ID)
            makeNetmorphPreSynReceptor(
                '%d_%d_NMDA' % (source, destination), source_comp_id, dest_comp_id, 'NMDA', 0,
                2.0, 100, g_rec_peak_NMDA, NMDAQuantityPerSynapse * Args.SuperSynapses,
                PyrInPyrOut_Hilloc_Distance_um, propagation_velocity, PyrInPyrOut_syndelay, True,
                Args.Weight, 'None', 0, 0, 0, 0,
                syn.ID)
print('Made LIFC Receptors')

# --- Stimulation protocol (identical to LIFtest.py -Autoassociative) ---
T = 80000
training_pattern = [1 for _ in range(numneurons)]
testing_pattern = [1 for _ in range(numneurons // 2)] + [0 for _ in range(numneurons // 2)]
training_stim = [i * 70.0 for i in range(8)]
repeats = T // 1600

timeneuronpairs_list = []
for n in range(numneurons):
    if training_pattern[n] == 1:
        for r in range(repeats):
            timeneuronpairs_list += [(t + 1600 * r, n) for t in training_stim]
for n in range(numneurons):
    if testing_pattern[n] == 1:
        for r in range(repeats):
            timeneuronpairs_list += [(t + 1600 * r + 800, n) for t in training_stim]
MySim.SetSpecificAPTimes(timeneuronpairs_list)
print('Simulation stimulation specified')

MySim.RecordAll(-1)
MySim.RunAndWait(Runtime_ms=T, timeout_s=100.0)
print('Functional stimulation completed')

recording_dict = MySim.GetRecording()
t_ms, Vm_cells = extract_t_Vm(data=recording_dict["Recording"])
if not t_ms:
    print('SCORE clean_recall=0.0 full_recall_cycles=0 clean_recall_cycles=0 leak=-1')
    raise SystemExit('Error: no recording returned')

s = score_recall(t_ms, Vm_cells)
print(f"SCORE clean_recall={s['clean_recall_fraction']:.4f} "
      f"full_recall_cycles={s['full_recall_cycles']} "
      f"clean_recall_cycles={s['clean_recall_cycles']} "
      f"leak={s['leak_spikes']}")

if Args.Save:
    savefolder = '/tmp/vbp_' + str(datetime.now()).replace(":", "_")
    if not vbp.PlotAndStoreRecordedActivity(recording_dict, savefolder, {'figsize': (6, 6), 'linewidth': 0.5, 'figext': 'pdf'}):
        vbp.ErrorToDB(DBdata, 'File error: Failed to store plots of recorded activity')
    print('Saved to ' + savefolder)
print('Done')

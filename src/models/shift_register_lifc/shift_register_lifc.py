#!/Users/apple/fun_project/BrainEmulationChallenge/venv/bin/python
# shift_register_lifc.py
# 8-bit SIPO Shift Register (v12.1 - Single-Pulse Clock Sync)
# Architecture: High-Tau Integration (Tau=500ms) for Priming + Single-Pulse Sync-CLK.
# This prevents the daisy-chain runaway seen in burst-clock models.

import numpy as np
from datetime import datetime
import argparse
import os

import vbpcommon as vbp
from NES_interfaces.KGTRecords import plot_recorded
import BrainGenix.NES as NES

scriptversion = '12.1.0'

Parser = argparse.ArgumentParser(description="8-bit SIPO Shift Register v12.1")
Parser.add_argument("-Host", default="pve.braingenix.org", type=str, help="Host to connect to")
Parser.add_argument("-Port", default=8000, type=int, help="Port number to connect to")
Parser.add_argument("-UseHTTPS", default=False, type=bool, help="Enable or disable HTTPS")
Parser.add_argument("-ExpsDB", default="./ExpsDB.json", type=str, help="Path to experiments database JSON file")
Parser.add_argument("-Seed", default=0, type=int, help="Set random seed")
Args = Parser.parse_args()

# Initialize
DBdata = vbp.InitExpDB(Args.ExpsDB, 'ShiftRegLIFC', scriptversion, _initIN={}, _initOUT={})
ClientCfg, ClientInstance = vbp.ClientFromArgs(DBdata, Args)
SimulationCfg, MySim = vbp.NewSimulation(DBdata, ClientInstance, 'ShiftRegLIFC', Seed=Args.Seed)

MySim.SetLIFCAbstractedFunctional(True)
MySim.SetSTDP(False)

# Layout
stages = 8
CLK_p, Din_p = [-120, 100, 0], [-120, 0, 0]
n_pos = {'CLK': CLK_p, 'Din': Din_p}
for i in range(stages):
    n_pos[f'P{i}'], n_pos[f'Q{i}'] = [i*100, 0, 0], [i*100, -50, 0]

# Helpers
def mkSphere(name, rad, pos):
    c = NES.Shapes.Sphere.Configuration(); c.Name, c.Radius_um, c.Center_um = name, rad, pos
    return MySim.AddSphere(c)

def mkCyl(name, p1, p2, r1, r2):
    c = NES.Shapes.Cylinder.Configuration(); c.Name, c.Point1Position_um, c.Point2Position_um = name, p1, p2
    c.Point1Radius_um, c.Point2Radius_um = r1, r2
    return MySim.AddCylinder(c)

def mkBox(name, pos):
    bc = NES.Shapes.Box.Configuration(); bc.Name, bc.CenterPosition_um, bc.Dimensions_um, bc.Rotation_rad = name, pos, [0.1, 0.1, 0.1], [0, 0, 0]
    return MySim.AddBox(bc)

def mkRec(name, src, dest, type, g, w, d, bid):
    c = NES.Models.Connections.LIFCReceptor.Configuration()
    c.Name, c.SourceCompartment, c.DestinationCompartment, c.Neurotransmitter = name, src, dest, type
    c.PeakConductance_nS, c.Weight, c.OnsetDelay_ms, c.ReceptorMorphology = g, w, d, bid
    c.ReversalPotential_mV, c.PSPRise_ms, c.PSPDecay_ms = (0 if type == 'AMPA' else -70), 0.5, (3.0 if type == 'AMPA' else 13.0)
    c.STDP_Method, c.STDP_Shift, c.voltage_gated = "None", 0.01, False
    c.STDP_A_pos, c.STDP_A_neg, c.STDP_Tau_pos, c.STDP_Tau_neg = 0, 0, 0, 0
    return MySim.AddLIFCReceptor(c)

somas = {n: mkSphere(f'{n}_S', 10.0, p) for n, p in n_pos.items()}

ax_conns = {'Din_P0': (Din_p, n_pos['P0'])}
for i in range(stages):
    ax_conns[f'CLK_P{i}'] = (CLK_p, n_pos[f'P{i}'])
    ax_conns[f'P{i}_Q{i}'] = (n_pos[f'P{i}'], n_pos[f'Q{i}'])
    ax_conns[f'Q{i}_o'] = (n_pos[f'Q{i}'], [n_pos[f'Q{i}'][0]+20, -50, 0])
    if i < stages-1: ax_conns[f'P{i}_P{i+1}'] = (n_pos[f'P{i}'], n_pos[f'P{i+1}'])

axons = {n: mkCyl(f'{n}_A', st, en, 2, 1) for n, (st, en) in ax_conns.items()}

# Master-Slave with Rm=5000 (Tau=500ms)
def mkComp(name, sid, Rm=100, Cm=100):
    c = NES.Models.Compartments.LIFC.Configuration(); c.Name, c.Shape = name, sid
    c.RestingPotential_mV, c.ResetPotential_mV, c.SpikeThreshold_mV = -70, -70, -50
    c.MembraneResistance_MOhm, c.MembraneCapacitance_pF, c.AfterHyperpolarizationAmplitude_mV = Rm, Cm, -90
    return MySim.AddLIFCCompartment(c)

s_comps = {}
for n in n_pos:
    Rm, Cm = (5000, 100) if 'P' in n else (100, 100)
    s_comps[n] = mkComp(f'{n}_S_L', somas[n].ID, Rm, Cm)
a_comps = {n: mkComp(f'{n}_A_L', axons[n].ID) for n in axons}

def mkNeur(name, sids, aids, type):
    c = NES.Models.Neurons.LIFC.Configuration()
    c.Name, c.SomaIDs, c.DendriteIDs, c.AxonIDs = name, sids, [], aids
    c.RestingPotential_mV, c.ResetPotential_mV, c.SpikeThreshold_mV = -70, -70, -50
    c.MembraneResistance_MOhm, c.MembraneCapacitance_pF = 100, 100
    c.RefractoryPeriod_ms = 400 if type == 'Master' else 2
    c.UpdateMethod, c.ResetMethod, c.SpikeDepolarization_mV = 'ExpEulerCm', 'ToVm', 30
    # Defaults
    c.AfterHyperpolarizationReversalPotential_mV = -90
    c.FastAfterHyperpolarizationRise_ms, c.FastAfterHyperpolarizationDecay_ms = 2.5, 30
    c.FastAfterHyperpolarizationPeakConductance_nS, c.FastAfterHyperpolarizationMaxPeakConductance_nS = 3.0, 5.0
    c.FastAfterHyperpolarizationHalfActConstant = 1.5
    c.SlowAfterHyperpolarizationRise_ms, c.SlowAfterHyperpolarizationDecay_ms = 30, 300
    c.SlowAfterHyperpolarizationPeakConductance_nS, c.SlowAfterHyperpolarizationMaxPeakConductance_nS = 1.0, 2.0
    c.SlowAfterHyperpolarizationHalfActConstant, c.AfterHyperpolarizationSaturationModel = 0.3, 'clip'
    c.FatigueThreshold, c.FatigueRecoveryTime_ms = 300, 3000
    c.AdaptiveThresholdDiffPerSpike, c.AdaptiveTresholdRecoveryTime_ms = 0.2, 50
    c.AdaptiveThresholdDiffPotential_mV, c.AdaptiveThresholdFloor_mV = 10, -50
    c.AdaptiveThresholdFloorDeltaPerSpike_mV, c.AdaptiveThresholdFloorRecoveryTime_ms = 1.0, 500
    c.AfterDepolarizationRecoveryTime_ms, c.AfterDepolarizationDepletion = 300, 0.3
    c.AfterDepolarizationSaturationMultiplier, c.AfterDepolarizationSaturationModel = 2.0, 'clip'
    c.AfterDepolarizationReversalPotential_mV, c.AfterDepolarizationRise_ms, c.AfterDepolarizationDecay_ms = -20, 10, 50
    c.AfterDepolarizationPeakConductance_nS = 0.4 if type == 'Slave' else 0.0
    c.STDP_Method = "None"
    return MySim.AddLIFCNeuron(c)

neurons = {
    'CLK': mkNeur('CLK', [s_comps['CLK'].ID], [a_comps[f'CLK_P{i}'].ID for i in range(stages)], 'Driver'),
    'Din': mkNeur('Din', [s_comps['Din'].ID], [a_comps['Din_P0'].ID], 'Driver')
}
for i in range(stages):
    la_ids = [a_comps[f'P{i}_Q{i}'].ID]
    if i < stages-1: la_ids.append(a_comps[f'P{i}_P{i+1}'].ID)
    neurons[f'P{i}'] = mkNeur(f'P{i}', [s_comps[f'P{i}'].ID], la_ids, 'Master')
    neurons[f'Q{i}'] = mkNeur(f'Q{i}', [s_comps[f'Q{i}'].ID], [a_comps[f'Q{i}_o'].ID], 'Slave')

syn_b = {c: mkBox(f'S_{c}', n_pos['CLK']) for c in ax_conns}

# Weights: CLK=14, Prime=14. Sum=28 > 20. CLK Alone=14 < 20.
for i in range(stages):
    mkRec(f'R_CP{i}', a_comps[f'CLK_P{i}'].ID, s_comps[f'P{i}'].ID, 'AMPA', 200, 14, 0, syn_b[f'CLK_P{i}'].ID)
    mkRec(f'R_PQ{i}', a_comps[f'P{i}_Q{i}'].ID, s_comps[f'Q{i}'].ID, 'AMPA', 200, 40, 2, syn_b[f'P{i}_Q{i}'].ID)
    if i == 0: mkRec('R_DP0', a_comps['Din_P0'].ID, s_comps['P0'].ID, 'AMPA', 200, 14, 0, syn_b['Din_P0'].ID)
    if i < stages-1: mkRec(f'R_PP{i}', a_comps[f'P{i}_P{i+1}'].ID, s_comps[f'P{i+1}'].ID, 'AMPA', 200, 14, 495, syn_b[f'P{i}_P{i+1}'].ID)

# Pattern: 1, 1, 0, 0, 1, 1, 0, 1
# Bit=1: Burst (10 spikes, 5ms). CLK: Single Pulse.
pattern = [1, 1, 0, 0, 1, 1, 0, 1] 
t_fire = []
for i, bit in enumerate(pattern):
    t_clk = 200 + i * 500
    t_fire.append((t_clk, neurons['CLK'].ID))
    if bit:
        for b_idx in range(10): t_fire.append((t_clk + b_idx*5, neurons['Din'].ID))

MySim.SetSpecificAPTimes(t_fire)
MySim.RecordAll(-1); MySim.RunAndWait(Runtime_ms=4500, timeout_s=300.0)
rec = MySim.GetRecording()

# Verify
bits = []
for i in range(stages-1, -1, -1):
    vm = rec['Recording']['neurons'][str(neurons[f'Q{i}'].ID)]['Vm_mV']
    has_spiked = any(v > -20 for v in vm[-500:]) 
    bits.append(1 if has_spiked else 0)
print(f"Observed final pattern [Q7-Q0]: {bits}")
if bits == [1, 1, 0, 0, 1, 1, 0, 1]: print("VERIFICATION: [ PASS ]")
else: print("VERIFICATION: [ FAIL ]")

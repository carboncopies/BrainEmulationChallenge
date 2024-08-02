#!/usr/bin/env python3
# xor_scnm_groundtruth_connectome.py
# Randal A. Koene, 20240731

# This script is STEP 2 in the creation of realistic
# ground-truth virtual tissue containing an intended
# cognitive function.
#
# The BrainGenix API is used to load a simulation model with
# previously generated connection reservoirs.
#
# The available connections are analyzed with the aim to tune
# and prune them to the desired functional connectome.

scriptversion='0.0.1'

import numpy as np
from datetime import datetime
from time import sleep
import json
import base64

import vbpcommon
from BrainGenix.BG_API import NES

import argparse
# Handle Arguments for Host, Port, etc
Parser = argparse.ArgumentParser(description="BrainGenix-API Simple Python Test Script")
Parser.add_argument("-Host", default="localhost", type=str, help="Host to connect to")
Parser.add_argument("-Port", default=8000, type=int, help="Port number to connect to")
Parser.add_argument("-UseHTTPS", default=False, type=bool, help="Enable or disable HTTPS")
Parser.add_argument("-modelname", default="xor_scnm", type=str, help="Name of neuronal circuit model to save")
Parser.add_argument("-DoOBJ", default=False, type=bool, help="Netmorph should produce OBJ output")
Parser.add_argument("-DoBlend", default=False, type=bool, help="Netmorph should produce Blender output")
Parser.add_argument("-BlendExec", default="/home/rkoene/blender-4.1.1-linux-x64/blender", type=str, help="Path to Blender executable")
Parser.add_argument("-BevelDepth", default=0.1, type=float, help="Blender neurite bevel depth")
Args = Parser.parse_args()

if Args.DoBlend:
    Args.DoOBJ = True

# Create Client Configuration For Local Simulation
print(" -- Creating Client Configuration For Local Simulation")
ClientCfg = NES.Client.Configuration()
ClientCfg.Mode = NES.Client.Modes.Remote
ClientCfg.Host = Args.Host
ClientCfg.Port = Args.Port
ClientCfg.UseHTTPS = Args.UseHTTPS
ClientCfg.AuthenticationMethod = NES.Client.Authentication.Password
ClientCfg.Username = "Admonishing"
ClientCfg.Password = "Instruction"

# Create Client Instance
print(" -- Creating Client Instance")
ClientInstance = NES.Client.Client(ClientCfg)

assert(ClientInstance.IsReady())


# Create A New Simulation
print(" -- Creating Simulation")
SimulationCfg = NES.Simulation.Configuration()
SimulationCfg.Name = "From Netmorph"
SimulationCfg.Seed = 0
MySim = ClientInstance.CreateSimulation(SimulationCfg)

# Load previously generated model

MySim.ModelLoad(Args.modelname)

print("Loaded neuronal circuit model "+Args.modelname)

response = MySim.GetAbstractConnectome(Sparse=True)

# Neuron-to-neuron connections:
PrePostNumReceptors = response['PrePostNumReceptors']
# Regions and the neurons in them:
Regions = response['Regions']

def RegionByNeuronID(NeuronID:int)->str:
    for reg in list(Regions.keys()):
        if NeuronID in Regions[reg]:
            return reg
    return 'unknown'

PreRegions = {}
for preidx, postidx, reccnt in PrePostNumReceptors:
    prereg = RegionByNeuronID(preidx)
    postreg = RegionByNeuronID(postidx)
    if prereg not in PreRegions:
        PreRegions[prereg] = {}
    if postreg not in PreRegions[prereg]:
        PreRegions[prereg][postreg] = 1
    else:
        PreRegions[prereg][postreg] += 1

print("Region-to-region connections in resevoirs:")
print(PreRegions)

# Make neuron to region map (assuming only one region per neuron):
Neuron2RegionMap = {}
for reg in Regions:
    for n in Regions[reg]:
        Neuron2RegionMap[n] = reg

# Active connections in reservoir:
Neuron2Neuron = PrePostNumReceptors.copy()
for i in range(len(Neuron2Neuron)):
    Neuron2Neuron[i][2] = 1

def ActiveInputsTo(NeuronID:int)->list:
    res = []
    for pre, post, active in Neuron2Neuron:
        if active>0 and post==NueronID:
            res.append(pre)
    return res

def ConnectionsFrom(SourceRegion:str, NeuronID:int)->list:
    res = []
    activeinputs = ActiveInputsTo(NeuronID)
    for pre in activeinputs:
        if Neuron2RegionMap[pre]==SourceRegion:
            res.append(pre)
    return res

# Neurons that appear in PyrOut:
for n in Regions['PyrOut']:
    frompyrmid = ConnectionsFrom('PyrMid', n)
    print('%d: %s' % (n, str(frompyrmid)))

print(Neuron2Neuron)

print(" -- Done.")

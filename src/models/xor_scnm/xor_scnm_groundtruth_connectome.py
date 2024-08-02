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
import copy

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

def SetAll(TheList:list, Value:int):
    for i in range(len(TheList)):
        TheList[i][2] = Value

def SetOneByPost(TheList:list, PostID:int, Value:int):
    for i in range(len(TheList)):
        if TheList[i][1]==PostID:
            TheList[i][2] = Value

def SetOneByPre(TheList:list, PreID:int, Value:int):
    for i in range(len(TheList)):
        if TheList[i][0]==PreID:
            TheList[i][2] = Value

def PostIs(TheList:list, PostID:int)->int:
    for i in range(len(TheList)):
        if TheList[i][1]==PostID:
            return TheList[i][2]
    return 0

def PreIs(TheList:list, PreID:int)->int:
    for i in range(len(TheList)):
        if TheList[i][0]==PreID:
            return TheList[i][2]
    return 0

# Active connections in reservoir:
Neuron2Neuron = copy.deepcopy(PrePostNumReceptors)
SetAll(Neuron2Neuron, 1)

def ActiveInputsTo(NeuronID:int)->list:
    res = []
    for pre, post, active in Neuron2Neuron:
        if active>0 and post==NeuronID:
            res.append(pre)
    return res

def ActiveOutputsFrom(NeuronID:int)->list:
    res = []
    for pre, post, active in Neuron2Neuron:
        if active>0 and pre==NeuronID:
            res.append(post)
    return res

def ConnectionsFrom(SourceRegion:str, NeuronID:int)->list:
    res = []
    activeinputs = ActiveInputsTo(NeuronID)
    for pre in activeinputs:
        if Neuron2RegionMap[pre]==SourceRegion:
            res.append(pre)
    return res

def EliminateByPost(NeuronID:int):
    SetOneByPost(Neuron2Neuron, NeuronID, 0)

def EliminateByPre(NeuronID:int):
    SetOneByPre(Neuron2Neuron, NeuronID, 0)

# Eliminate Neurons that appear in PyrOut with fewer than 2 connections from PyrMid:
for n in Regions['PyrOut']:
    frompyrmid = ConnectionsFrom('PyrMid', n)
    if len(frompyrmid)<2:
        EliminateByPost(n)
    else:
        print('%d: %s' % (n, str(frompyrmid)))

def PreRecurse(TrackerFlags:list, NeuronID:int):
    SetOneByPost(TrackerFlags, NeuronID, 1)
    inp = ActiveInputsTo(NeuronID)
    for i in inp:
        if PostIs(TrackerFlags, i)==0:
            PreRecurse(TrackerFlags, i)

def PostRecurse(TrackerFlags:list, NeuronID:int):
    SetOneByPre(TrackerFlags, NeuronID, 1)
    out = ActiveOutputsFrom(NeuronID)
    for o in out:
        if PreIs(TrackerFlags, o)==0:
            PostRecurse(TrackerFlags, o)

N2NFromOutput = copy.deepcopy(Neuron2Neuron)
SetAll(N2NFromOutput, 0)
# Set flags for all neurons reachable from active PyrOut neurons:
for n in Regions['PyrOut']:
    if PostIs(Neuron2Neuron, n)>0:
        PreRecurse(N2NFromOutput, n)
N2NFromInput = copy.deepcopy(Neuron2Neuron)
SetAll(N2NFromInput, 0)
# Set flags for all neurons reachable from active PyrIn neurons:
for n in Regions['PyrIn']:
    if PreIs(Neuron2Neuron, n)>0:
        PostRecurse(N2NFromInput, n)
# Keep only those that are reachable in both directions:
for idx in range(len(Neuron2Neuron)):
    if N2NFromOutput[idx][2]==0 or N2NFromInput[idx][2]==0:
        Neuron2Neuron[idx][2]=0

def NumActive()->int:
    num = 0;
    for pre, post, active in Neuron2Neuron:
        if active>0:
            num += 1
    return num

print("There are %d usable connections on input-to-output paths (out of %d)." % (NumActive(), len(Neuron2Neuron)))

def HasInputFromRegion(NeuronID:int, Reg:str)->bool:
    inp = ActiveInputsTo(NeuronID)
    for i in inp:
        if Neuron2RegionMap[i]==Reg:
            return True
    return False

def SubsetByInput(Neurons:list, Reg:str)->list:
    res = []
    for n in Neurons:
        if HasInputFromRegion(n, Reg):
            res.append(n)
    return res

def Intersection(NeuronsA:list, NeuronsB:list)->list:
    res = []
    for n in NeuronsA:
        if n in NeuronsB:
            res.append(n)
    return res

# Eliminate connections with PyrMid neurons that do not have input from both PyrIn and Int:
pyrmid = Regions['PyrMid']
pyrmid_from_pyrin = SubsetByInput(pyrmid, 'PyrIn')
pyrmid_from_int = SubsetByInput(pyrmid, 'Int')
pyrmid_from_pyrin_and_int = Intersection(pyrmid_from_pyrin, pyrmid_from_int)
print("List of neurons in PyrMid with inputs from both PyrIn and Int: %s" % str(pyrmid_from_pyrin_and_int))
for n in pyrmid:
    if n not in pyrmid_from_pyrin_and_int:
        EliminateByPost(n)
        EliminateByPre(n)
print("Usable connections remaining after eliminating connections through other PyrMid neurons: %d" % NumActive())

# Eliminate connections with PyrMid neurons that do not have inputs that can creata A and not B:
pyrmid_from_pyrin_and_not_int = []
for n in pyrmid_from_pyrin_and_int:
    frompyrin = ConnectionsFrom('PyrIn', n)
    fromint = ConnectionsFrom('Int', n)
    fromint_frompyrin = []
    for pre in fromint:
        fromint_frompyrin += ConnectionsFrom('PyrIn', pre)
    for pre in fromint_frompyrin:
        if pre not in frompyrin:
            pyrmid_from_pyrin_and_not_int.append(n)
            break
print("List of neurons in PyrMid creating PyrIn and not-Int connections: %s" % str(pyrmid_from_pyrin_and_not_int))
for n in pyrmid:
    if n not in pyrmid_from_pyrin_and_not_int:
        EliminateByPost(n)
        EliminateByPre(n)
print("Usable connections remaining after eliminating connections through other PyrMid neurons: %d" % NumActive())

# Let's take a look at what we still have:
for n in pyrmid_from_pyrin_and_not_int:
    print('PyrMid %d: From PyrIn %s' % (n, ConnectionsFrom('PyrIn', n)))

def FindIntAndInDifferent(PyrMidID:int, NotPyrInID:int)->tuple:
    midint = ConnectionsFrom('Int', PyrMidID)
    for mi in midint:
        intinp = ConnectionsFrom('PyrIn', mi)
        for ii in intinp:
            if ii != NotPyrInID:
                return mi, ii

# For the first side of the XOR connectome:
XORInput = []
PrePostPairs = []
pyrmid0 = pyrmid_from_pyrin_and_not_int[0]
pyrin0 = ConnectionsFrom('PyrIn', pyrmid0)[0]
pyrint1, pyrin1 = FindIntAndInDifferent(pyrmid0, pyrin0)
PrePostPairs.append( (pyrin0, pyrmid0) )
XORInput.append('InA')
PrePostPairs.append( (pyrint1, pyrmid0) )
XORInput.append('...')
PrePostPairs.append( (pyrin1, pyrint1) )
XORInput.append('InB')

# For the second side of the XOR connectome:
pyrmid1 = pyrmid_from_pyrin_and_not_int[1]
midin = ConnectionsFrom('PyrIn', pyrmid1)
for mi in midin:
    if mi != pyrin0:
        pyrin1 = mi
pyrint0, pyrin0 = FindIntAndInDifferent(pyrmid1, pyrin1)
PrePostPairs.append( (pyrin1, pyrmid1) )
XORInput.append('InB')
PrePostPairs.append( (pyrint0, pyrmid1) )
XORInput.append('...')
PrePostPairs.append( (pyrin0, pyrint0) )
XORInput.append('InA')

# Find the PyrOut that receives from both PyrMid neurons:
PyrOutGroup = []
pyrout = Regions['PyrOut']
for n in pyrout:
    frommid = ConnectionsFrom('PyrMid', n)
    if pyrmid0 in frommid and pyrmid1 in frommid:
        PyrOutGroup.append(n)
PrePostPairs.append( (pyrmid0, PyrOutGroup[0]) )
XORInput.append('Out')
PrePostPairs.append( (pyrmid1, PyrOutGroup[0]) )
XORInput.append('Out')

print("Connectome pre-post pairs for both branches of the XOR:")
for i in range(len(PrePostPairs)):
    pre, post = PrePostPairs[i]
    print('  %s: %s %d -> %s %d' % (XORInput[i], Neuron2RegionMap[pre],pre,Neuron2RegionMap[post],post))

# Set connections as per the intentions expressed in PrePostPairs:
PreSynList = []
PostSynList = []
ConductanceList = []
for pre, post, active in Neuron2Neuron:
    if (pre, post) in PrePostPairs:
        # Set this to a specific strength:
        PreSynList.append(pre)
        PostSynList.append(post)
        if Neuron2RegionMap[pre]=="Int":
            ConductanceList.append(-40.0) # AMPA 40.0, GABA -40.0
        else:
            ConductanceList.append(40.0) # AMPA 40.0, GABA -40.0
    else:
        # Set this to zero:
        PreSynList.append(pre)
        PostSynList.append(post)
        ConductanceList.append(0.0)
MySim.BatchSetPrePostStrength(PreSynList, PostSynList, ConductanceList)

print("Updated model connectome accordingly.")

# Let's test the update:
response = MySim.GetAbstractConnectome(Sparse=True, NonZero=True)

print(response)

print(" -- Done.")

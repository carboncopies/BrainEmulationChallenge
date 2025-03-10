#!/usr/bin/env python3
# xor_scnm_groundtruth_direct.py
# Randal A. Koene, 20240708

# This version attempts to run the Netmorph model directly as an embedded
# processin the NES backend and to build the corresponding NES model from there.

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
Parser.add_argument("-modelfile", type=str, help="File to read model instructions from")
Parser.add_argument("-modelname", default="xor_scnm", type=str, help="Name of neuronal circuit model to save")
Parser.add_argument("-DoOBJ", default=False, type=bool, help="Netmorph should produce OBJ output")
Parser.add_argument("-DoBlend", default=False, type=bool, help="Netmorph should produce Blender output")
Parser.add_argument("-BlendExec", default="/home/rkoene/blender-4.1.1-linux-x64/blender", type=str, help="Path to Blender executable")
Parser.add_argument("-BevelDepth", default=0.1, type=float, help="Blender neurite bevel depth")
Args = Parser.parse_args()

if Args.DoBlend:
    Args.DoOBJ = True

modelcontent = 'kjhskdjfhkjhs'

if Args.modelfile:
    with open(Args.modelfile, 'r') as f:
        modelcontent = f.read()

NETMORPH_OBJ = '''
outattr_make_full_OBJ=true;
outattr_OBJ_bevdepth_axon=%.1f;
outattr_OBJ_bevdepth_dendrite=%.1f;
'''

NETMORPH_BLEND = '''
outattr_make_full_blend=true;
blender_exec_path=%s;
'''

if Args.DoOBJ:
    modelcontent += NETMORPH_OBJ % (Args.BevelDepth, Args.BevelDepth)
if Args.DoBlend:
    modelcontent += NETMORPH_BLEND % Args.BlendExec

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

MySim.Netmorph_RunAndWait(modelcontent)

MySim.ModelSave(Args.modelname)

print(" -- Neuronal Circuit Model saved as "+Args.modelname)

if Args.DoBlend:
    print(" -- Getting Gzipped Blender file to netmorph-net.blend.gz")
    FileBytes = MySim.Netmorph_GetFile('net.obj.blend.gz')
    with open('netmorph-net.blend.gz', 'wb') as f:
        f.write(base64.decodebytes(FileBytes))

print(" -- Done.")

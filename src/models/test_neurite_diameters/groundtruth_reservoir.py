#!/usr/bin/env python3
# xor_scnm_groundtruth_reservoir.py
# Randal A. Koene, 20240731

# This script is STEP 1 in the creation of realistic
# ground-truth virtual tissue containing an intended
# cognitive function.
#
# The BrainGenix API is used to direct NES to run embedded
# Netmorph on Netmorph script to grow a reservoir of
# connections between pyramidal cell and interneuron
# regions.
#
# For example, call this with the nesvbp-xor-res-sep-targets
# script: ./xor_scnm_groundtruth_reservoir.py -modelfile nesvbp-xor-res-sep-targets
#
# The ModelSave API function is called to ensure that the resulting
# NES Simulation model is stored in a rapid binary format on the server.

scriptversion='0.0.1'

import numpy as np
from datetime import datetime
from time import sleep
import json
import base64

import vbpcommon
from BrainGenix.BG_API import NES

DEFAULT_MODELNAME='test_neurite_diameters'

import argparse
# Handle Arguments for Host, Port, etc
Parser = argparse.ArgumentParser(description="BrainGenix-API Simple Python Test Script")
Parser.add_argument("-Host", default="localhost", type=str, help="Host to connect to")
Parser.add_argument("-Port", default=8000, type=int, help="Port number to connect to")
Parser.add_argument("-UseHTTPS", default=False, type=bool, help="Enable or disable HTTPS")
Parser.add_argument("-modelfile", type=str, help="File to read model instructions from")
Parser.add_argument("-modelname", default=DEFAULT_MODELNAME, type=str, help="Name of neuronal circuit model to save")
Parser.add_argument("-growdays", type=int, help="Number of days Netmorph growth")
Parser.add_argument("-DoOBJ", default=False, type=bool, help="Netmorph should produce OBJ output")
Parser.add_argument("-DoBlend", default=False, type=bool, help="Netmorph should produce Blender output")
Parser.add_argument("-BlendExec", default="/home/rkoene/blender-4.1.1-linux-x64/blender", type=str, help="Path to Blender executable")
Parser.add_argument("-BevelDepth", default=0.1, type=float, help="Blender neurite bevel depth")

Parser.add_argument("-PullNetmorphLogs", default=False, type=bool, help="Pull Netmorph Buffered Logs")
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

GROWDAYS = '''
days=%d;
'''

if Args.DoOBJ:
    modelcontent += NETMORPH_OBJ % (Args.BevelDepth, Args.BevelDepth)
if Args.DoBlend:
    modelcontent += NETMORPH_BLEND % Args.BlendExec
if Args.growdays:
    modelcontent += GROWDAYS % Args.growdays

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

if Args.PullNetmorphLogs:
    MySim.Netmorph_SetLogBuffers('progress')

MySim.Netmorph_RunAndWait(modelcontent)

MySim.ModelSave(Args.modelname)

print(" -- Neuronal Circuit Model saved as "+Args.modelname)

FileBytes = MySim.Netmorph_GetFile('report')
NetmorphReport = base64.decodebytes(FileBytes).decode()
diam_data_start = NetmorphReport.find('Soma and Neurite Root diameters:')
if diam_data_start>=0:
    diam_data_end = NetmorphReport.find('---', diam_data_start)
    print(NetmorphReport[diam_data_start:diam_data_end])

if Args.PullNetmorphLogs:
    print('\nBuffered Netmorph Progress Log:')
    NetmorphLogData = MySim.Netmorph_GetLogBuffers()
    print(NetmorphLogData['LogBuffers']['progress'])

if Args.DoBlend:
    print(" -- Getting Gzipped Blender file to netmorph-net.blend.gz")
    FileBytes = MySim.Netmorph_GetFile('net.obj.blend.gz')
    with open('netmorph-net.blend.gz', 'wb') as f:
        f.write(base64.decodebytes(FileBytes))

print(" -- Done.")

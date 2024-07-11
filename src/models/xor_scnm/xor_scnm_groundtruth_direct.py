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
Args = Parser.parse_args()

modelcontent = 'kjhskdjfhkjhs'

if Args.modelfile:
    with open(Args.modelfile, 'r') as f:
        modelcontent = f.read()

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

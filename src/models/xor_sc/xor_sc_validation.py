#!/usr/bin/env python3
# xor_sc_validation.py
# Randal A. Koene, 20240429

'''
Validation of XOR SC emulation with ground-truth.

'''

scriptversion='0.0.1'

from datetime import datetime
from time import sleep
import argparse
import json

import vbpcommon
#import common.glb as glb
import os

import BrainGenix.NES as NES
import BrainGenix.EVM as EVM
import BrainGenix

savefolder = 'output/'+str(datetime.now()).replace(":", "_")+'-acquisition'

# 1. Init NES connection

# Handle Arguments for Host, Port, etc
Parser = argparse.ArgumentParser(
    description="BrainGenix-API Simple Python Validation Test Script"
)
Parser.add_argument(
    "-Host", default="localhost", type=str, help="Host to connect to"
)
Parser.add_argument(
    "-Port", default=8000, type=int, help="Port number to connect to"
)
Parser.add_argument(
    "-UseHTTPS", default=False, type=bool, help="Enable or disable HTTPS"
)
Args = Parser.parse_args()

# Start Tests
print("----------------------------")
print("Starting BG-EVM Validation Test")

# Create Client Configuration For Local Simulation
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

assert ClientInstance.IsReady()

with open('./.SimulationHandle', 'r') as f:
    KTGSaveNAme = f.read()

with open('./.EmulationHandle', 'r') as f:
    EMUSaveName = f.read()

Result = EVM.Validation.SCValidation(ClientInstance, KTGSaveNAme, EMUSaveName)
print(Result)


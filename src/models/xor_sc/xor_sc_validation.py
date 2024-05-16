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

KGTSaveNameFile = './.SimulationHandle'
EMUSaveNameFile = './.EmulationHandle'
DataSaveFile = './.TestData'
#savefolder = 'output/'+str(datetime.now()).replace(":", "_")+'-acquisition'

# 0: Setup Output Report
SaveFolder = 'ValidationReports/'+str(datetime.now()).replace(":", "_")+'-acquisition'

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

with open(KGTSaveNameFile, 'r') as f:
    KGTSaveName = f.read()
with open(EMUSaveNameFile, 'r') as f:
    EMUSaveName = f.read()
with open(DataSaveFile, 'r') as f:
    TestDataJSON = json.load(f)

EditJSON = EVM.Validation.SCValidation(ClientInstance, KGTSaveName, EMUSaveName, TestDataJSON)

print(" -- Generating Report Information")
os.makedirs(SaveFolder + "/JSON")

print(" -- Creating Markdown Report")

EditListMarkdown = ""
GraphEditListJSON = EditJSON["GraphEdits"]
for i in range(len(GraphEditListJSON)):
    Edit = GraphEditListJSON[i]
    EditListMarkdown += f"""
##### Edit {i}  
- Cost: {Edit["Cost"]}  
- Data: {Edit["Data"]}  
- Operation: {Edit["Op"]}  

"""

Report:str = f"""
# WBE Standardized Challenge - Submission Report



## Report Summary

### Structural Metrics

#### Edit Distance
 - Score: {EditJSON["Scores"]["GraphEditDistanceScore"]}
 - RawCost: {EditJSON["Scores"]["GraphEditRawCost"]}
 - NumElements: {EditJSON["Scores"]["NumElements"]}

 
### Functional Metrics

Coming soon!



## Detailed Information

### Structural Metrics

#### Edit Distance
See `JSON/EditDistance.json` for detailed information. 
{EditListMarkdown}



## Legend

### Graph Edit Operations
The enumerated ops (top is 0):  
- vertex_insertion = 0,  
- vertex_deletion = 1,  
- vertex_substitution = 2,  
- edge_insertion = 3,  
- edge_deletion = 4,  
- edge_substitution = 5,  


"""
with open(f"{SaveFolder}/Report.md", "w") as f:
    f.write(Report)

print(" -- Saving Edit Distance JSON Info")
with open(f"{SaveFolder}/JSON/EditDistance.json", "w") as f:
    f.write(json.dumps(EditJSON))


#!/usr/bin/env python3
# xor_sc_emulation.py
# Randal A. Koene, 20240326

'''
The XOR SimpleCompartmental example uses branching axons in a representation of a
meaningful logic circuit to produce expected functional output.

This file implements a validation procedure for the resulting emulation.

VBP process step 03: emulation validation
WBE topic-level III: evolving similarity / performance metrics
'''

scriptversion='0.0.1'

import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from time import sleep
import argparse
import math
import json

import vbpcommon
import os
from BrainGenix.BG_API import BG_API_Setup
from NES_interfaces.KGTRecords import plot_recorded

import BrainGenix.NES as NES
import BrainGenix
from BrainGenix.Tools.StackStitcher import StackStitcher, CaImagingStackStitcher

Parser = argparse.ArgumentParser(description="vbp script")
Parser.add_argument("-RenderVisualization", action='store_true', help="Enable or disable visualization")
Parser.add_argument("-RenderEM", action='store_true', help="Enable or disable em stack rendering")
Parser.add_argument("-RenderCA", action='store_true', help="Enable or disable Calcium imaging rendering")
Parser.add_argument('-Electrodes', action='store_true', help="Place electrodes")
Parser.add_argument("-Local", action='store_true', help="Render remotely or on localhost")
Parser.add_argument("-Remote", action='store_true', help="Run on remote NES server")
Args = Parser.parse_args()

#default:
api_is_local=True
if Args.Remote:
    api_is_local=False
if Args.Local:
    api_is_local=True

TotalElectrodes:int = 0;
TotalCARenders:int = 0;
TotalEMRenders:int = 0;

runtime_ms=500.0
savefolder = 'output/'+str(datetime.now()).replace(":", "_")+'-validation'
figspecs = {
    'figsize': (6,6),
    'linewidth': 0.5,
    'figext': 'pdf',
}

# 1. Init NES connection

bg_api = BG_API_Setup(user='Admonishing', passwd='Instruction')
if api_is_local:
    bg_api.set_local()
if not bg_api.BGNES_QuickStart(scriptversion, versionmustmatch=False, verbose=False):
    print('BG NES Interface access failed.')
    exit(1)

# 2. Load ground-truth network

# 2.1 Request Loading
sys_name=None
with open(".EmulationHandle", "r") as f:
    sys_name = f.read()
print(f"Loading emulation with handle '{sys_name}'")

loadingtaskID = bg_api.BGNES_load(timestampedname=sys_name)

print('Started Loading Task (%s) for Saved Simulation %s' % (str(loadingtaskID), str(sys_name)))

# 2.2 Await Loading and set Simulation ID

while True:
    sleep(0.005)
    response_list = bg_api.BGNES_get_manager_task_status(taskID=loadingtaskID)
    if not isinstance(response_list, list):
        print('Bad response format. Expected list of NESRequest responses.')
        exit(1)
    task_status_response = response_list[0]
    if task_status_response['StatusCode'] != 0:
        print('Checking task status failed, status code: '+str(task_status_response['StatusCode']))
        exit(1)
    if "TaskStatus" not in task_status_response:
        print('No TaskStatus received.')
        exit(1)
    task_status = task_status_response['TaskStatus']
    if task_status > 1:
        print('Loading Task failed.')
        exit(1)
    if task_status == 0:
        break

print('Loading task completed successfully.')
if "SimulationID" not in task_status_response:
    print('Missing SimulationID.')
    exit(1)
SimulationID = task_status_response["SimulationID"]
bg_api.Simulation.Sim.ID = SimulationID

print('New ID of loaded Simulation: '+str(SimulationID))

# ----------------------------------------------------

print('\nRunning functional data acquisition for %.1f milliseconds...\n' % runtime_ms)

# 5.1 Set record-all and record instruments

t_max_ms=-1 # record forever
bg_api.BGNES_simulation_recordall(t_max_ms)
if not bg_api.BGNES_set_record_instruments(t_max_ms):
    exit(1)

# 5.2 Run for specified simulation time
if not bg_api.BGNES_simulation_runfor_and_await_outcome(runtime_ms):
    exit(1)

# if not calcium_specs['generate_during_sim']:
#     glb.bg_api.BGNES_calcium_imaging_record_aposteriori()

# 5.3 Retrieve recordings and plot

recording_dict = bg_api.BGNES_get_recording()
success, instrument_data = bg_api.BGNES_get_instrument_recordings()
if not success:
    exit(1)

if isinstance(recording_dict, dict):
    if "StatusCode" in recording_dict:
        if recording_dict["StatusCode"] != 0:
            print('Retrieving recording failed: StatusCode = '+str(recording_dict["StatusCode"]))
        else:
            if "Recording" not in recording_dict:
                print('Missing "Recording" key.')
            else:
                if recording_dict["Recording"] is None:
                    print('Recording is empty.')
                else:
                    print('Keys in record: '+str(list(recording_dict["Recording"].keys())))

                    plot_recorded(
                        savefolder=savefolder,
                        data=recording_dict["Recording"],
                        figspecs=figspecs,)


#!/usr/bin/env python3
# bs_vbp00_groundtruth_xi_sampleprep.py
# Randal A. Koene, 20240208

'''
The ball-and-stick example is intended to provide the simplest in-silico case with the smallest
number of variables to address while still demonstrating the full process and dependencies
chain for whole brain emulation.

This file implements double-blind experimental data acquisition from a fully known
ground-truth system.

VBP process step 01: double-blind data acquisition
WBE topic-level X: data acquisition (in-silico)
'''

scriptversion='0.0.1'

import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from time import sleep
import argparse
import math

import vbpcommon
import common.glb as glb
import os
from NES_interfaces.BG_API import BG_API_Setup
from NES_interfaces.KGTRecords import plot_recorded

import BrainGenix.NES as NES
import BrainGenix
from BrainGenix.Tools.StackStitcher.StackStitcher import StitchManySlices

def PointsInCircum(r,n=100):
    return [(math.cos(2*math.pi/n*x)*r,math.sin(2*math.pi/n*x)*r) for x in range(0,n+1)]



Parser = argparse.ArgumentParser(description="vbp script")
Parser.add_argument("-RenderVisualization", default=False, type=bool, help="Enable or disable visualization")
Parser.add_argument("-RenderEM", default=False, type=bool, help="Enable or disable em stack rendering")
Args = Parser.parse_args()




api_is_local=True
runtime_ms=500.0
savefolder = './Renders/vbp_'+datetime.now().strftime("%F_%X")
figspecs = {
    'figsize': (6,6),
    'linewidth': 0.5,
    'figext': 'pdf',
}

# 1. Init NES connection

BG_API_Setup(user='Admonishing', passwd='Instruction')
if api_is_local:
    glb.bg_api.set_local()
if not glb.bg_api.BGNES_QuickStart(scriptversion, versionmustmatch=False, verbose=False):
    print('BG NES Interface access failed.')
    exit(1)

# 2. Load ground-truth network

# 2.1 Request Loading
sys_name=None
with open(".SimulationHandle", "r") as f:
    sys_name = f.read()
print(f"Loading simulation with handle '{sys_name}'")

loadingtaskID = glb.bg_api.BGNES_load(timestampedname=sys_name)

print('Started Loading Task (%s) for Saved Simulation %s' % (str(loadingtaskID), str(sys_name)))

# 2.2 Await Loading and set Simulation ID

while True:
    sleep(0.005)
    response_list = glb.bg_api.BGNES_get_manager_task_status(taskID=loadingtaskID)
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
glb.bg_api.Simulation.Sim.ID = SimulationID

print('New ID of loaded Simulation: '+str(SimulationID))

# 2.3 Show model

# (add call here)

# 3. Initialize functional data acquisition

ACQSETUPTEXT1='''
Simulated functional data acquisition:
Two types of simulated functional recording methods are
set up, an electrode and a calcium imaging microscope.
Calcium imaging is slower and may reflect a summation
of signals (Wei et al., 2019).

Model activity is elicited by spontaneous activity.

Simulated functional recording involves the application
of simulated physics to generate data derived from a
combination of model neuronal activity and simulated
confounding factors.
'''

print(ACQSETUPTEXT1)

# 3.1 Initialize spontaneous activity

# Spontaneous activity can be turned on or off, a list of neurons can be
# provided by ID, an empty list means "all" neurons.
neuron_ids = [] # all
spont_spike_interval_ms_mean = 280
spont_spike_interval_ms_stdev = 140 # 0 means no spontaneous activity

success = glb.bg_api.BGNES_set_spontaneous_activity(
    spont_spike_interval_ms_mean=spont_spike_interval_ms_mean,
    spont_spike_interval_ms_stdev=spont_spike_interval_ms_stdev,
    neuron_ids=neuron_ids)

if not success:
    print('Failed to set up spontaneous activity.')
    exit(1)

print('Spontaneous activity at each neuron successfully activated.')

# 3.2 Initialize recording electrodes

# 3.3 Initialize calcium imaging

# ----------------------------------------------------

print('\nRunning experiment for %.1f milliseconds...\n' % runtime_ms)

# 5.1 Set record-all

t_max_ms=-1 # record forever
glb.bg_api.BGNES_simulation_recordall(t_max_ms)

# 5.2 Run for specified simulation time

if not glb.bg_api.BGNES_simulation_runfor_and_await_outcome(runtime_ms):
    exit(1)

# 5.3 Retrieve recordings and plot

recording_dict = glb.bg_api.BGNES_get_recording()
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

# ----------------------------------------------------


# ----------------------------------------------------
# Now, we render the visualized data optionally
# ----------------------------------------------------
if (Args.RenderVisualization):
    print("rendering visualization of neural network\n")
    VisualizerJob = BrainGenix.NES.Visualizer.Configuration()
    VisualizerJob.ImageWidth_px = 2048
    VisualizerJob.ImageHeight_px = 2048


    # Render In Circle Around Sim
    Radius = 20
    Steps = 10
    ZHeight = 0

    for Point in PointsInCircum(Radius, Steps):

        VisualizerJob.CameraFOVList_deg.append(110)
        VisualizerJob.CameraPositionList_um.append([Point[0], Point[1], ZHeight])
        VisualizerJob.CameraLookAtPositionList_um.append([0, 0, ZHeight])

    Visualizer = glb.bg_api.Simulation.Sim.SetupVisualizer()
    Visualizer.GenerateVisualization(VisualizerJob)


    Visualizer.SaveImages("Renders/Visualizations", 2)

# ----------------------------------------------------
# And, we optionally render the EM Stack, and reconstruct it.
# ----------------------------------------------------
if (Args.RenderEM):
    print("\nRendering EM image stack to disk\n")


    EMConfig = NES.VSDA.EM.Configuration()
    EMConfig.PixelResolution_nm = 0.05
    EMConfig.ImageWidth_px = 1024
    EMConfig.ImageHeight_px = 1024
    EMConfig.SliceThickness_nm = 100
    EMConfig.ScanRegionOverlap_percent = 10
    EMConfig.MicroscopeFOV_deg = 50
    EMConfig.NumPixelsPerVoxel_px = 1
    VSDAEMInstance = glb.bg_api.Simulation.Sim.AddVSDAEM(EMConfig)

    VSDAEMInstance.DefineScanRegion([-10,-10,-10], [10,10,10])
    VSDAEMInstance.QueueRenderOperation()
    VSDAEMInstance.WaitForRender()
    VSDAEMInstance.SaveImageStack("Renders/EM/Raw")


    print(" -- Reconstructing Image Stack")
    StitchManySlices("Renders/EM/Raw", "Renders/EM/Stitched", borderSizePx=3, nWorkers=os.cpu_count(), makeGIF=True)


# ----------------------------------------------------

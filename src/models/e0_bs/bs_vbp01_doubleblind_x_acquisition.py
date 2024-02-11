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
import math

import vbpcommon
import common.glb as glb
from NES_interfaces.BG_API import BG_API_Setup
from NES_interfaces.KGTRecords import plot_recorded

import BrainGenix.NES as NES
import BrainGenix

def PointsInCircum(r,n=100):
    return [(math.cos(2*math.pi/n*x)*r,math.sin(2*math.pi/n*x)*r) for x in range(0,n+1)]


api_is_local=True
runtime_ms=500.0
savefolder = '/tmp/vbp_'+datetime.now().strftime("%F_%X")
figspecs = {
    'figsize': (6,6),
    'linewidth': 0.5,
    'figext': 'pdf',
}
extra_pars = {
    'num_nodes': 2,
    'distribution': 'aligned',
    'calcium_fov': 12.0,
    'calcium_y': -5.0,
    'load_kgt': 'kgt.json',
    'save_data': 'data.pkl.gz',
    'save_kgt': 'kgt.json',
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

sys_name='2024-02-08_18:15:53-e0_bs'
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

# 3.2.1 Find the geometric center of the system based on soma center locations

success, geocenter = glb.bg_api.BGNES_get_geometric_center()
if not success:
    print('Failed to find geometric center of simulation.')
    exit(1)

print('Geometric center of simulation: '+str(geocenter))

# 3.2.2 Set up electrode parameters

num_sites = 1
sites_ratio = 0.1
noise_level = 0
end_position = np.array(geocenter) + np.array([0, 0, 5.0])

rec_sites_on_electrode = [ [0, 0, 0], ] # Only one site at the tip.
for rec_site in range(1, num_sites):
    electrode_ratio = rec_site * sites_ratio
    rec_sites_on_electrode.append( [0, 0, electrode_ratio] )

electrode_specs = {
    'id': 'electrode_0',
    'tip_position': geo_center_xyz_um,
    'end_position': end_position.tolist(),
    'sites': rec_sites_on_electrode,
    'noise_level': noise_level,
}
set_of_electrode_specs = [ electode_specs, ] # A single electrode.

list_of_electrode_IDs = glb.bg_api.BGNES_attach_recording_electrodes(set_of_electrode_specs)

print('Attached %s recording electrodes.' % str(len(list_of_electrode_IDs)))

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

exit(0)

VisualizerJob = BrainGenix.NES.Visualizer.Configuration()
VisualizerJob.ImageWidth_px = 2048
VisualizerJob.ImageHeight_px = 2048



# Render In Circle Around Sim
Radius = 30
Steps = 50
ZHeight = 50

for Point in PointsInCircum(Radius, Steps):

    VisualizerJob.CameraFOVList_deg.append(110)
    VisualizerJob.CameraPositionList_um.append([Point[0], Point[1], ZHeight])
    VisualizerJob.CameraLookAtPositionList_um.append([0, 0, ZHeight])

Visualizer = glb.bg_api.Simulation.Sim.SetupVisualizer()
Visualizer.GenerateVisualization(VisualizerJob)


Visualizer.SaveImages("Visualizations", 2)


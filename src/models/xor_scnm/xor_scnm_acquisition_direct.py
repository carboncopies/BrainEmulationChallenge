#!/usr/bin/env python3
# xor_bs_acquisition.py
# Randal A. Koene, 20240618

'''
This version makes a new simulation but uses neuronal circiut model data
previously saved after generating it with Netmorph.

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
import json

import vbpcommon
#import common.glb as glb
import os
from BrainGenix.BG_API import BG_API_Setup
from NES_interfaces.KGTRecords import plot_recorded

import BrainGenix.NES as NES
import BrainGenix
from BrainGenix.Tools.StackStitcher import StackStitcher, CaImagingStackStitcher
from BrainGenix.Tools.NeuroglancerConverter import NeuroglancerConverter

def PointsInCircum(r, n=100):
    return [(math.cos(2*math.pi/n*x)*r,math.sin(2*math.pi/n*x)*r) for x in range(0,n+1)]



Parser = argparse.ArgumentParser(description="vbp script")
Parser.add_argument("-modelname", default="xor_scnm-tuned", type=str, help="Name of neuronal circuit model prevoiusly saved")
Parser.add_argument("-RenderVisualization", action='store_true', help="Enable or disable visualization")
Parser.add_argument("-RenderEM", action='store_true', help="Enable or disable em stack rendering")
Parser.add_argument("-Neuroglancer", action='store_true', help="Generate the neuroglancer verison of the dataset for EM images")
Parser.add_argument("-RenderCA", action='store_true', help="Enable or disable Calcium imaging rendering")
Parser.add_argument('-Electrodes', action='store_true', help="Place electrodes")
Parser.add_argument("-Host", default="localhost", type=str, help="Host to connect to")
Parser.add_argument("-Port", default=8000, type=int, help="Port number to connect to")
Parser.add_argument("-Resolution_um", default=0.05, type=float, help="Resolution in microns of each voxel")
Parser.add_argument("-SubdivideSize", default=5, type=int, help="Amount to subdivide region in, 1 is full size, 2 is half size, etc.")
Parser.add_argument("-UseHTTPS", default=False, type=bool, help="Enable or disable HTTPS")
Parser.add_argument("-NoDownloadEM", action="store_true", help="Disable downloading of EM Images")
Args = Parser.parse_args()

# 1. Instantiate new simulation

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

# 2. Load previously saved neuronal circuit model

MySim.ModelLoad(Args.modelname)

print("Loaded neuronal circuit model "+Args.modelname)

with open(Args.modelname+'-IOIDs.json', 'r') as f:
    XORInOutIdentifiers = json.load(f)
print('Loaded XOR I/O neuron identifiers.')

# 2.3 Prepare model for data acquisition

TotalElectrodes:int = 0;
TotalCARenders:int = 0;
TotalEMRenders:int = 0;

runtime_ms=500.0
savefolder = 'output/'+str(datetime.now()).replace(":", "_")+'-acquisition'
figspecs = {
    'figsize': (6,6),
    'linewidth': 0.5,
    'figext': 'pdf',
}

# 3. Initialize functional data acquisition

# ACQSETUPTEXT1='''
# Simulated functional data acquisition:
# Two types of simulated functional recording methods are
# set up, an electrode and a calcium imaging microscope.
# Calcium imaging is slower and may reflect a summation
# of signals (Wei et al., 2019).

# Model activity is elicited by spontaneous activity.

# Simulated functional recording involves the application
# of simulated physics to generate data derived from a
# combination of model neuronal activity and simulated
# confounding factors.
# '''

# print(ACQSETUPTEXT1)

t_soma_fire_ms = []
def SpikeInputNeuronsAt(InputID:str, t_ms:float):
    for n in XORInOutIdentifiers[InputID]:
        t_soma_fire_ms.append( (t_ms, n) )

t_test_ms = {
    'XOR_10': 100.0,
    'XOR_01': 200.0,
    'XOR_11': 300.0,
}
# The 0 0 case is not explicitly tested.
# Add 1 0 XOR test case.
SpikeInputNeuronsAt('InA', t_test_ms['XOR_10'])
# Add 0 1 XOR test case.
SpikeInputNeuronsAt('InB', t_test_ms['XOR_01'])
# Add 1 1 XOR test case.
SpikeInputNeuronsAt('InA', t_test_ms['XOR_11'])
SpikeInputNeuronsAt('InB', t_test_ms['XOR_11'])

print('Directed somatic firing: '+str(t_soma_fire_ms))

MySim.SetSpecificAPTimes(TimeNeuronPairs=t_soma_fire_ms)

# 3.1 Initialize spontaneous activity

# use_spontaneous_activity=False
# if use_spontaneous_activity:

#     # Spontaneous activity can be turned on or off, a list of neurons can be
#     # provided by ID, an empty list means "all" neurons.
#     neuron_ids = [] # all
#     spont_spike_interval_ms_mean = 280
#     spont_spike_interval_ms_stdev = 140 # 0 means no spontaneous activity

#     success = bg_api.BGNES_set_spontaneous_activity(
#         spont_spike_interval_ms_mean=spont_spike_interval_ms_mean,
#         spont_spike_interval_ms_stdev=spont_spike_interval_ms_stdev,
#         neuron_ids=neuron_ids)

#     if not success:
#         print('Failed to set up spontaneous activity.')
#         exit(1)

#     print('Spontaneous activity at each neuron successfully activated.')


# 3.2 Initialize recording electrodes

# ---- WILL PROBABLY BREAK ABOUT HERE

# if (Args.Electrodes or Args.RenderEM):

#     # NOTE: Copied these soma locations from the ground-truth script to
#     #       put electrodes fairly close to neurons for simplicity right now.
#     # somacenters = {
#     #     'P_in0_pos': np.array([-45,-45, 0]),
#     #     'P_in1_pos': np.array([-45, 45, 0]),
#     #     'I_A0_pos': np.array([-15,-15, 0]),
#     #     'I_A1_pos': np.array([-15, 15, 0]),
#     #     'P_B0_pos': np.array([ 15,-45, 0]),
#     #     'P_B1_pos': np.array([ 15, 45, 0]),
#     #     'P_out_pos': np.array([ 45,  0, 0]),
#     # }

#     # 3.2.1 Find the geometric center of the system based on soma center locations

#     success, geocenter = bg_api.BGNES_get_geometric_center()
#     if not success:
#         print('Failed to find geometric center of simulation.')
#         exit(1)

#     print('Geometric center of simulation: '+str(geocenter))

#     # 3.2.2 Set up electrode parameters

#     num_sites = 1
#     sites_ratio = 0.01
#     noise_level = 0

#     set_of_electrode_specs = []

#     # Note that shank spacing on a 4-shank Neuropixels electrode is 250 um.
#     # See https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8244810/

#     tip_positions = {
#         'A': np.array([0, 0, 0]),
#         'B': np.array([-200, -200, 0]),
#         'C': np.array([200, 200, 0]),
#     }

#     for soma_name in tip_positions:

#         tip_position = tip_positions[soma_name]
#         end_position = tip_position + np.array([0, 0, 2000.0]) # electrodes are typically a few mm to (sometimes a few cm) in length

#         rec_sites_on_electrode = [ [0, 0, 0], ] # Only one site at the tip.
#         for rec_site in range(1, num_sites):
#             electrode_ratio = rec_site * sites_ratio
#             rec_sites_on_electrode.append( [0, 0, electrode_ratio] )

#         electrode_specs = {
#             'name': 'electrode_'+soma_name,
#             'tip_position': tip_position.tolist(),
#             'end_position': end_position.tolist(),
#             'sites': rec_sites_on_electrode,
#             'noise_level': noise_level,
#         }
#         set_of_electrode_specs.append( electrode_specs )

#     success, list_of_electrode_IDs = bg_api.BGNES_attach_recording_electrodes(set_of_electrode_specs)

#     print('Attached %s recording electrodes.' % str(len(list_of_electrode_IDs)))
#     print('IDs are: '+str(list_of_electrode_IDs))

# 3.3 Initialize calcium imaging

# calcium_fov = 12.0
# calcium_y = -5.0
# calcium_specs = {
#     'name': 'calcium_0',
# }

# CAConfig = NES.VSDA.Calcium.Configuration()
# CAConfig.BrightnessAmplification = 3.0
# CAConfig.AttenuationPerUm = 0.01
# CAConfig.VoxelResolution_nm = 0.05 # This is actually um!!!!!!!!!!!
# CAConfig.ImageWidth_px = 1024
# CAConfig.ImageHeight_px = 1024
# CAConfig.NumVoxelsPerSlice = 16
# CAConfig.ScanRegionOverlap_percent = 0
# CAConfig.FlourescingNeuronIDs = []
# CAConfig.NumPixelsPerVoxel_px = 1
# CAConfig.CalciumIndicator = 'jGCaMP8'
# CAConfig.IndicatorRiseTime_ms = 2.0
# CAConfig.IndicatorDecayTime_ms = 40.0
# CAConfig.IndicatorInterval_ms = 20.0 # Max. spike rate trackable 50 Hz.
# CAConfig.ImagingInterval_ms = 10.0   # Interval at which CCD snapshots are made of the microscope image.
# VSDACAInstance = bg_api.Simulation.Sim.AddVSDACa(CAConfig)


# BottomLeftPos_um = [-60,-60, -6]
# TopRightPos_um = [60,60,6]
# SampleRotation_rad = [0,0,0]

# VSDACAInstance.DefineScanRegion(BottomLeftPos_um, TopRightPos_um, SampleRotation_rad)



# glb.bg_api.BGNES_calcium_imaging_attach(calcium_specs)

# glb.bg_api.BGNES_calcium_imaging_show_voxels()

# ----------------------------------------------------

print('\nRunning functional data acquisition for %.1f milliseconds...\n' % runtime_ms)

# 5.1 Set record-all and record instruments

t_max_ms=-1 # record forever
MySim.RecordAll(_MaxRecordTime_ms=t_max_ms)

#MySim.SetRecordInstruments(_MaxRecordTime_ms=t_max_ms)

# 5.2 Run for specified simulation time
MySim.RunAndWait(Runtime_ms=runtime_ms, timeout_s=100.0)

# 5.3 Retrieve recordings and plot

# 5.3.1 Carry out post-run Calcium Imaging

if (Args.RenderCA):
    VSDACAInstance.QueueRenderOperation()
    VSDACAInstance.WaitForRender()
    os.makedirs(f"{savefolder}/ChallengeOutput/CARegions/0/Data")
    VSDACAInstance.SaveImageStack(f"{savefolder}/ChallengeOutput/CARegions/0/Data", 10)

    TotalCARenders += 1

    CaJSON:dict = {
        "SheetThickness_um": CAConfig.NumVoxelsPerSlice * CAConfig.VoxelResolution_nm,
        "ScanRegionBottomLeft_um": BottomLeftPos_um,
        "ScanRegionTopRight_um": TopRightPos_um,
        "SampleRotation_rad": SampleRotation_rad,
        "IndicatorName": CAConfig.CalciumIndicator,
        "ImageTimestep_ms": CAConfig.ImagingInterval_ms
    }
    with open(f"{savefolder}/ChallengeOutput/CARegions/0/Params.json", 'w') as F:
        F.write(json.dumps(CaJSON))

    os.makedirs(f"{savefolder}/CARegions/0")
    ### Buggy: CaImagingStackStitcher.StitchManySlices(f"{savefolder}/ChallengeOutput/CARegions/0/Data", f"{savefolder}/CARegions/0", borderSizePx=0, nWorkers=os.cpu_count(), makeGIF=True)

# 5.3.2 Collect God-mode recording of neural activity

recording_dict = MySim.GetRecording()

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

# 5.3.3 Collect activity-dendendent recordings

#instrument_data = MySim.GetInstrumentRecordings()

                   # *** TODO: Here you can add God's eye neuron-Ca signal plotting.
def write_electrode_output(
    folder:str,
    electrode_number:int,
    data:dict):
    os.makedirs(folder, exist_ok=True)
    with open(folder+'/'+str(electrode_number)+'.json','w') as f:
        json.dump(data, f)

# if 't_ms' not in instrument_data:
#     print('Missing t_ms record in instruments data.')
# else:
#     t_ms = instrument_data['t_ms']

#     if 'Electrodes' not in instrument_data:
#         print('No Electrode recording data in instrument data.')
#     else:
#         electrode_data = instrument_data['Electrodes']
#         print('Creating graphs for electrodes: '+str(electrode_data.keys()))
#         electrode_file_number = 0
#         for electrode_name in electrode_data.keys():
#             specific_electrode_data = electrode_data[electrode_name]
#             E_mV = specific_electrode_data['E_mV']
#             if len(E_mV)<1:
#                 print('Zero E_mV records found at electrode %s.' % electrode_name)
#             else:

#                 # Plot electrode data
#                 fig = plt.figure(figsize=figspecs['figsize'])
#                 gs = fig.add_gridspec(len(E_mV),1, hspace=0)
#                 axs = gs.subplots(sharex=True, sharey=True)
#                 axs.set_xlabel("Time (ms)")
#                 axs.set_ylabel("Electrode Voltage (mV)")
#                 fig.suptitle('Electrode %s' % electrode_name)
#                 for site in range(len(E_mV)):
#                     if len(E_mV)==1:
#                         axs.plot(t_ms, E_mV[site], linewidth=figspecs['linewidth'])
#                     else:
#                         axs[site].plot(t_ms, E_mV[site], linewidth=figspecs['linewidth'])
#                 plt.draw()
#                 print(savefolder+f'/{str(electrode_name)}.{figspecs["figext"]}')
#                 plt.savefig(savefolder+f'/{str(electrode_name)}.{figspecs["figext"]}', dpi=300)

#                 # Produce electrode data output in standardized format (see ChallengeFormat)
#                 outputdata = {
#                     'Name': str(electrode_name),
#                     'TipPosition': set_of_electrode_specs[electrode_file_number]['tip_position'],
#                     'EndPosition': set_of_electrode_specs[electrode_file_number]['end_position'],
#                     'Sites': set_of_electrode_specs[electrode_file_number]['sites'],
#                     'TimeStamp_ms': t_ms,
#                     'ElectricField_mV': E_mV,
#                 }
#                 write_electrode_output(
#                     folder=savefolder+'/ChallengeOutput/Electrodes',
#                     electrode_number=electrode_file_number,
#                     data=outputdata,
#                     )

#                 electrode_file_number += 1
#                 TotalElectrodes = electrode_file_number


#     if 'Calcium' not in instrument_data:
#         print('No Calcium Concentration neuron data in instrument data')
#     else:
#         # Returns "Ca_t_ms" data and data for each neuron ID (e.g. "0") with a list of calcium concentrations
#         # at each "Ca_t_ms" time point.
#         caimaging_data = instrument_data['Calcium']
#         # Get the time points
#         if "Ca_t_ms" in caimaging_data:
#             Ca_t_ms = caimaging_data["Ca_t_ms"]
#             # Find the neuron IDs for which data is included
#             neuron_ids = []
#             for n in range(100):
#                 if str(n) in caimaging_data:
#                     neuron_ids.append(str(n))
#             for neuron_id in neuron_ids:
#                 neuron_Ca_data = caimaging_data[neuron_id]
#                 if len(neuron_Ca_data) < 1:
#                     print('No Calcium concentration data for neuron '+neuron_id)
#                 else:
#                     fig = plt.figure(figsize=figspecs['figsize'])
#                     gs = fig.add_gridspec(len(E_mV),1, hspace=0)
#                     axs = gs.subplots(sharex=True, sharey=True)
#                     axs.set_xlabel("Time (ms)")
#                     axs.set_ylabel("Calcium Concentrations")
#                     fig.suptitle('Neuron %s' % neuron_id)
#                     axs.plot(Ca_t_ms, neuron_Ca_data, linewidth=figspecs['linewidth'])
#                     plt.draw()
#                     print(savefolder+f'/Ca_{str(neuron_id)}.{figspecs["figext"]}')
#                     plt.savefig(savefolder+f'/Ca_{str(neuron_id)}.{figspecs["figext"]}', dpi=300)


# ----------------------------------------------------


# ----------------------------------------------------
# Now, we render the visualized model optionally
# ----------------------------------------------------
if (Args.RenderVisualization):
    print("rendering visualization of neural network\n")
    VisualizerJob = BrainGenix.NES.Visualizer.Configuration()
    VisualizerJob.ImageWidth_px = 8192
    VisualizerJob.ImageHeight_px = 4096


    ## ONLY SHOW NEURON 0, DISABLE OTHERS (EXCEPT FOR THEIR SOMA) ##
    # VisualizerJob.Optional_VisibleNeuronIDs = [1] 


    # Render In Circle Around Sim
    Radius = 500
    Steps = 10
    ZHeight = -550

    for Point in PointsInCircum(Radius, Steps):

        VisualizerJob.CameraFOVList_deg.append(110)
        VisualizerJob.CameraPositionList_um.append([Point[0], Point[1], ZHeight])
        VisualizerJob.CameraLookAtPositionList_um.append([0, 0, -1000])

    Visualizer = MySim.SetupVisualizer()
    Visualizer.GenerateVisualization(VisualizerJob)


    Visualizer.SaveImages(f"{savefolder}/Visualizations/0", 2)

# ----------------------------------------------------
# And, we optionally render the EM Stack, and reconstruct it.
# ----------------------------------------------------
if (Args.RenderEM):
    print("\nRendering EM image stack to disk\n")

    # A receptor is located at [-5.06273255 -0.20173953 -0.02163604] -- zooming in on that for some tweaking
    EMConfig = NES.VSDA.EM.Configuration()
    EMConfig.PixelResolution_nm = Args.Resolution_um # is actually um!!!!!
#    EMConfig.PixelResolution_nm = 0.1 # is actually um!!!!!
#    EMConfig.PixelResolution_nm = 0.3 # is actually um!!!!!
    EMConfig.ImageWidth_px = 512
    EMConfig.ImageHeight_px = 512
    EMConfig.SliceThickness_nm = 0.2 # actually um!
    EMConfig.ScanRegionOverlap_percent = 0
    EMConfig.MicroscopeFOV_deg = 50 # This is currently not used.
    EMConfig.NumPixelsPerVoxel_px = 1
    EMConfig.ImageNoiseIntensity = 130
    EMConfig.BorderThickness_um = 0.0275
    EMConfig.GuassianBlurSigma = 1.25
    EMConfig.BorderThickness_um = 0.3
    EMConfig.PostBlurNoisePasses = 1
    EMConfig.PreBlurNoisePasses = 0
    EMConfig.TearingEnabled = False
    EMConfig.EnableGaussianBlur = False
    EMConfig.EnableInterferencePattern = False
    VSDAEMInstance = MySim.AddVSDAEM(EMConfig)


    # Get bounding box for rendering
    BottomLeft_um, TopRight_um = MySim.GetBoundingBox()

    SubdivideSize = Args.SubdivideSize

    BottomLeft_um = [BottomLeft_um[0]/SubdivideSize, BottomLeft_um[1]/SubdivideSize, BottomLeft_um[2]/SubdivideSize]
    TopRight_um = [TopRight_um[0]/SubdivideSize, TopRight_um[1]/SubdivideSize, TopRight_um[2]/SubdivideSize]

    # BottomLeft_um = [-75,-75,-20]
    # TopRight_um = [75,75,20]
    Rotation_rad = [0,0,0]
    VSDAEMInstance.DefineScanRegion(BottomLeft_um, TopRight_um, Rotation_rad)
    VSDAEMInstance.QueueRenderOperation()
    VSDAEMInstance.WaitForRender()
    os.makedirs(f"{savefolder}/ChallengeOutput/EMRegions/0/Data")

    if (not Args.NoDownloadEM):
        NumImagesX, NumImagesY, NumSlices = VSDAEMInstance.SaveImageStack(f"{savefolder}/ChallengeOutput/EMRegions/0/Data", 20)


        # Generate EM JSON Info
        EMInfoJSON:dict = {
            'ScanRegionBottomLeft_um': BottomLeft_um,
            'ScanRegionTopRight_um': TopRight_um,
            'SampleRotation_rad': Rotation_rad,
            'Overlap_percent': EMConfig.ScanRegionOverlap_percent,
            'SliceThickness_um': EMConfig.SliceThickness_nm, # We are modeling FIBSEM, this is the same as ZResolution_um.
            'XResolution_um': EMConfig.PixelResolution_nm,
            'YResolution_um': EMConfig.PixelResolution_nm,
            'ZResolution_um': EMConfig.SliceThickness_nm,
            'NumImagesX': NumImagesX,
            'NumImagesY': NumImagesY,
            'NumSlices': NumSlices
        }
        with open(f"{savefolder}/ChallengeOutput/EMRegions/0/Params.json", 'w') as F:
            F.write(json.dumps(EMInfoJSON))

        print(" -- Reconstructing Image Stack")
        os.makedirs(f"{savefolder}/EMRegions/0")
        #StackStitcher.StitchManySlices(f"{savefolder}/ChallengeOutput/EMRegions/0/Data", f"{savefolder}/EMRegions/0", borderSizePx=3, nWorkers=os.cpu_count(), makeGIF=False)

    # if (Args.Neuroglancer):
        # NeuroglancerConverter(VSDAEMInstance, f"{savefolder}/NeuroglancerDataset")

    if (Args.Neuroglancer):
        VSDAEMInstance.PrepareNeuroglancerDataset()
        VSDAEMInstance.WaitForConversion()
        print(f"Dataset Handle: {VSDAEMInstance.GetDatasetHandle()}")
        print(f"URL: {VSDAEMInstance.GetNeuroglancerDatasetURL()}")


    TotalEMRenders += 1


# ----------------------------------------------------


# Now, we generate the Index file
# OutputData:dict = {
#     "TotalElectrodes": TotalElectrodes,
#     "TotalEMRegions": TotalEMRenders,
#     "TotalCARegions": TotalCARenders
# }
# with open(f"{savefolder}/ChallengeOutput/Index.json", 'w') as F:
#     F.write(json.dumps(OutputData))

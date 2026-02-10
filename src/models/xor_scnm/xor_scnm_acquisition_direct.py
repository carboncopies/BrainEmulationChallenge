#!../../../venv/bin/python
# xor_bs_acquisition.py
# Randal A. Koene, 20240618

'''
This version makes a new simulation but uses neuronal circiut model data
previously saved after generating it with Netmorph.

VBP process step 01: double-blind data acquisition
WBE topic-level X: data acquisition (in-silico)
'''

scriptversion='0.1.0'

#import matplotlib.pyplot as plt
#import numpy as np
from datetime import datetime
#from time import sleep
import argparse
import math
import json
import os

import vbpcommon as vbp
#from BrainGenix.BG_API import BG_API_Setup
#from NES_interfaces.KGTRecords import plot_recorded
import BrainGenix.NES as NES
import BrainGenix
from BrainGenix.Tools.StackStitcher import StackStitcher, CaImagingStackStitcher
#from BrainGenix.Tools.NeuroglancerConverter import NeuroglancerConverter

def PointsInCircum(r, n=100):
    return [(math.cos(2*math.pi/n*x)*r,math.sin(2*math.pi/n*x)*r) for x in range(0,n+1)]


# Handle Arguments for Host, Port, etc
Parser = argparse.ArgumentParser(description="vbp script")
Parser.add_argument("-modelname", default="xor_scnm-tuned", type=str, help="Name of neuronal circuit model prevoiusly saved")
Parser.add_argument("-simID", default=None, type=int, help="Re-process an active simulation by ID (finds corresponding modelname)")
Parser.add_argument("-RenderVisualization", action='store_true', help="Enable or disable visualization")
Parser.add_argument("-RenderEM", action='store_true', help="Enable or disable em stack rendering")
Parser.add_argument("-Segmentation", action='store_true', help="Generate EM segmentation images (e.g. for Neuroglancer)")
Parser.add_argument("-Neuroglancer", action='store_true', help="Generate the Neuroglancer verison of the dataset for EM images")
Parser.add_argument("-NeuroglancerURLBase", default=None, type=str, help="Force a different URL base for the generated Neuroglancer URL")
Parser.add_argument("-Meshes", action='store_true', help="Generate Mesh data for Neuroglancer")
Parser.add_argument("-RenderCA", action='store_true', help="Enable or disable Calcium imaging rendering")
Parser.add_argument('-Electrodes', action='store_true', help="Place electrodes")
Parser.add_argument("-Host", default="localhost", type=str, help="Host to connect to")
Parser.add_argument("-Port", default=8000, type=int, help="Port number to connect to")
Parser.add_argument("-Resolution_um", default=0.05, type=float, help="Resolution in microns of each voxel")
Parser.add_argument("-SubdivideSize", default=5, type=int, help="Amount to subdivide region in, 1 is full size, 2 is half size, etc.")
Parser.add_argument("-UseHTTPS", default=False, type=bool, help="Enable or disable HTTPS")
Parser.add_argument("-DownloadEM", action="store_true", help="Enable downloading of EM Images")
Parser.add_argument("-ExpsDB", default="./ExpsDB.json", type=str, help="Path to experiments database JSON file")
Args = Parser.parse_args()

if Args.simID:
    # Re-attach to existing Simulation and find corresponding modelname in SimsDatabase.json
    # Notes:
    # - This is not the same as loading a saved simulation from a file containing all
    #   requests that were made (as with Client.LoadSimulation()).
    # - This is not the same as loading a saved model from a binary format file with all
    #   the simulation data (as with Simulation.ModelLoad()).
    # - This is an attempt to continue working with a Simulation that is already in the
    #   memory of the running NES server. It is the fastest restart possible, but it is
    #   no longer available if the NES server was restarted.
    foundID=False
    try:
        with open('./SimsDatabase.json', 'r') as f:
            SimsDatabase = json.load(f)
        modelnames = list(SimsDatabase.keys())
        for modelname in modelnames:
            if str(Args.simID) in SimsDatabase[modelname]:
                foundID=True
                Args.modelname=modelname
                break
    except Exception as e:
        print('Unable to open SimsDatabase.json file: '+str(e))
    if not foundID:
        print('Sorry... Simulation with ID %s not found in SimsDatabase.json.' % str(Args.simID))
        exit(1)


# Initialize data collection for entry in DB file
DBdata = vbp.InitExpDB(
    Args.ExpsDB,
    'acquisition',
    scriptversion,
    _initIN = {
        'modelname': Args.modelname,
        'simID': str(Args.simID),
        'resolution_um':  Args.Resolution_um,
        'subdivide': Args.SubdivideSize,
    },
    _initOUT = {
    })

### ========================================= ###
### Retrieve Model                            ###
### ========================================= ###

# Find I/O IDs corresponding with the modelname
DBconnectome = vbp.GetMostRecentDBEntryOUT(DBdata, 'connectome', False, Args.modelname, exit_on_error=True)
if 'IOIDs' not in DBconnectome:
    vbp.ErrorExit(DBdata, 'Experiments database error: Missing IOIDs in most recent entry for modelname '+str(Args.modelname))
XORInOutIdentifiers = DBconnectome['IOIDs']
print('Loaded XOR I/O neuron identifiers.')


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
try:
    ClientInstance = NES.Client.Client(ClientCfg)
    if not ClientInstance.IsReady():
        vbp.ErrorExit(DBdata, 'NES.Client error: not ready')
except Exception as e:
    vbp.ErrorExit(DBdata, 'NES.Client error: '+str(e))


if not Args.simID:
    # Create A New Simulation
    print(" -- Creating Simulation")
    SimulationCfg = NES.Simulation.Configuration()
    SimulationCfg.Name = "Netmorph-"+Args.modelname
    SimulationCfg.Seed = 0
    try:
        MySim = ClientInstance.CreateSimulation(SimulationCfg)
    except:
        vbp.ErrorExit(DBdata, 'NES error: Failed to create simulation')
else:
    # Reconnect to Simulation in NES memory
    print(" -- Re-processing active (in-memory) Simulation")
    SimulationCfg = NES.Simulation.Configuration()
    SimulationCfg.Name = "Netmorph-"+Args.modelname
    SimulationCfg.Seed = 0
    try:
        MySim = ClientInstance.CreateSimulation(SimulationCfg, _Create=False)
        MySim.ID = int(Args.simID)
    except:
        vbp.ErrorExit(DBdata, 'NES error: Failed to reconnect to simulation '+str(Args.simID))


# Prepare front-end output folder
savefolder = 'output/'+datetime.now().strftime('%Y%m%d%H%M%S.%f')+'-acquisition'
vbp.AddOutputToDB(DBdata, 'output_folder', savefolder)

TotalEMRenders:int = 0


if not Args.simID:
    # Load previously saved neuronal circuit model
    try:
        MySim.ModelLoad(Args.modelname)
        print("Loaded neuronal circuit model "+Args.modelname)
        print('')
    except:
        vbp.ErrorExit(DBdata, 'NES error: model load failed')


### ========================================= ###
### Dynamic Data Acquisition                  ###
### ========================================= ###

if not Args.simID:
    # Prepare model for data acquisition
    TotalElectrodes:int = 0
    TotalCARenders:int = 0

    runtime_ms=500.0
    figspecs = {
        'figsize': (6,6),
        'linewidth': 0.5,
        'figext': 'pdf',
    }
    print('\nRunning functional data acquisition for %.1f milliseconds...\n' % runtime_ms)

    # Initialize functional data acquisition

    # Two types of simulated functional recording methods are
    # set up, an electrode and a calcium imaging microscope.
    # Calcium imaging is slower and may reflect a summation
    # of signals (Wei et al., 2019).
    #
    # Model activity is elicited by spontaneous activity.
    #
    # Simulated functional recording involves the application
    # of simulated physics to generate data derived from a
    # combination of model neuronal activity and simulated
    # confounding factors.

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

    try:
        MySim.SetSpecificAPTimes(TimeNeuronPairs=t_soma_fire_ms)
    except:
        vbp.ErrorExit(DBdata, 'NES error: Failed to set specific spike times')

    # Initialize spontaneous activity
    #
    # use_spontaneous_activity=False
    # if use_spontaneous_activity:
    #
    #     # Spontaneous activity can be turned on or off, a list of neurons can be
    #     # provided by ID, an empty list means "all" neurons.
    #     neuron_ids = [] # all
    #     spont_spike_interval_ms_mean = 280
    #     spont_spike_interval_ms_stdev = 140 # 0 means no spontaneous activity
    #
    #     success = bg_api.BGNES_set_spontaneous_activity(
    #         spont_spike_interval_ms_mean=spont_spike_interval_ms_mean,
    #         spont_spike_interval_ms_stdev=spont_spike_interval_ms_stdev,
    #         neuron_ids=neuron_ids)
    #
    #     if not success:
    #         print('Failed to set up spontaneous activity.')
    #         exit(1)
    #
    #     print('Spontaneous activity at each neuron successfully activated.')


    # Initialize recording electrodes
    #
    # if (Args.Electrodes or Args.RenderEM):
    #
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
    #
    #     # Find the geometric center of the system based on soma center locations
    #
    #     success, geocenter = bg_api.BGNES_get_geometric_center()
    #     if not success:
    #         print('Failed to find geometric center of simulation.')
    #         exit(1)
    #
    #     print('Geometric center of simulation: '+str(geocenter))
    #
    #     # Set up electrode parameters
    #
    #     num_sites = 1
    #     sites_ratio = 0.01
    #     noise_level = 0
    #
    #     set_of_electrode_specs = []
    #
    #     # Note that shank spacing on a 4-shank Neuropixels electrode is 250 um.
    #     # See https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8244810/
    #
    #     tip_positions = {
    #         'A': np.array([0, 0, 0]),
    #         'B': np.array([-200, -200, 0]),
    #         'C': np.array([200, 200, 0]),
    #     }
    #
    #     for soma_name in tip_positions:
    #
    #         tip_position = tip_positions[soma_name]
    #         end_position = tip_position + np.array([0, 0, 2000.0]) # electrodes are typically a few mm to (sometimes a few cm) in length
    #
    #         rec_sites_on_electrode = [ [0, 0, 0], ] # Only one site at the tip.
    #         for rec_site in range(1, num_sites):
    #             electrode_ratio = rec_site * sites_ratio
    #             rec_sites_on_electrode.append( [0, 0, electrode_ratio] )
    #
    #         electrode_specs = {
    #             'name': 'electrode_'+soma_name,
    #             'tip_position': tip_position.tolist(),
    #             'end_position': end_position.tolist(),
    #             'sites': rec_sites_on_electrode,
    #             'noise_level': noise_level,
    #         }
    #         set_of_electrode_specs.append( electrode_specs )
    #
    #     success, list_of_electrode_IDs = bg_api.BGNES_attach_recording_electrodes(set_of_electrode_specs)
    #
    #     print('Attached %s recording electrodes.' % str(len(list_of_electrode_IDs)))
    #     print('IDs are: '+str(list_of_electrode_IDs))

    # Initialize calcium imaging
    #
    # calcium_fov = 12.0
    # calcium_y = -5.0
    # calcium_specs = {
    #     'name': 'calcium_0',
    # }
    #
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
    #
    # BottomLeftPos_um = [-60,-60, -6]
    # TopRightPos_um = [60,60,6]
    # SampleRotation_rad = [0,0,0]
    #
    # VSDACAInstance.DefineScanRegion(BottomLeftPos_um, TopRightPos_um, SampleRotation_rad)
    #
    #
    #
    # glb.bg_api.BGNES_calcium_imaging_attach(calcium_specs)
    #
    # glb.bg_api.BGNES_calcium_imaging_show_voxels()
    #
    # ----------------------------------------------------


    # Set record-all and record instruments
    t_max_ms=-1 # record for the entire runtime
    vbp.AddInputToDB(DBdata, 'Ephys', {
        'runtime_ms': runtime_ms,
        'dyn_figspecs': figspecs,
        't_soma_fire_ms': t_soma_fire_ms,
        't_record_max_ms': t_max_ms,
    })

    try:
        MySim.RecordAll(_MaxRecordTime_ms=t_max_ms)
    except:
        vbp.ErrorToDB(DBdata, 'NES error: Failed to set RecordAll')

    #MySim.SetRecordInstruments(_MaxRecordTime_ms=t_max_ms)


    # Run for specified simulation time
    try:
        MySim.RunAndWait(Runtime_ms=runtime_ms, timeout_s=100.0)
    except:
        vbp.ErrorToDB(DBdata, 'NES error: RunAndWait dynamic simulation failed')

    # Retrieve recordings and plot

    # Carry out post-run Calcium Imaging

    if (Args.RenderCA):
        try:
            VSDACAInstance.QueueRenderOperation()
            VSDACAInstance.WaitForRender()

            CAimagesfolder = f"{savefolder}/ChallengeOutput/CARegions/0/Data"
            CAparamsfile = f"{savefolder}/ChallengeOutput/CARegions/0/Params.json"
            vbp.AddOutputToDB(DBdata, 'CAimagesfolder', CAimagesfolder)
            vbp.AddOutputToDB(DBdata, 'CAparamsfile', CAparamsfile)
        except:
            vbp.ErrorToDB(DBdata, 'NES error: Failed to render CA images')

        try:
            os.makedirs(CAimagesfolder)
            VSDACAInstance.SaveImageStack(CAimagesfolder, 10)
        except:
            vbp.ErrorToDB(DBdata, 'NES error: Failed to retrieve CA images to '+str(CAimagesfolder))

        TotalCARenders += 1

        CaJSON:dict = {
            "SheetThickness_um": CAConfig.NumVoxelsPerSlice * CAConfig.VoxelResolution_nm,
            "ScanRegionBottomLeft_um": BottomLeftPos_um,
            "ScanRegionTopRight_um": TopRightPos_um,
            "SampleRotation_rad": SampleRotation_rad,
            "IndicatorName": CAConfig.CalciumIndicator,
            "ImageTimestep_ms": CAConfig.ImagingInterval_ms
        }
        vbp.AddInputToDB(DBdata, 'Calcium', CaJSON)
        try:
            with open(CAparamsfile, 'w') as F:
                F.write(json.dumps(CaJSON))
        except:
            vbp.ErrorToDB(DBdata, 'File error: Failed to write CA parameters to '+str(CAparamsfile))

        # NOTE: Stitching is BUGGY, temporarily deactivated.
        #stitchedCA_folder = f"{savefolder}/CARegions/0"
        #vbp.AddOutputToDB(DBdata, 'CAstitchedfolder', stitchedCA_folder)
        #os.makedirs(stitchedCA_folder)
        #CaImagingStackStitcher.StitchManySlices(CAimagesfolder, stitchedCA_folder, borderSizePx=0, nWorkers=os.cpu_count(), makeGIF=True)

    # Collect God-mode recording of neural activity
    try:
        recording_dict = MySim.GetRecording()

        if not vbp.PlotAndStoreRecordedActivity(recording_dict, savefolder, figspecs):
            vbp.ErrorToDB(DBdata, 'File error: Failed to store plots of recorded activity')
    except:
        vbp.ErrorToDB(DBdata, 'NES error: Failed to retrieve recorded activity')

    # Collect activity-dendendent recordings

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

### ========================================= ###
### Structure Data Acquisition                ###
### ========================================= ###

if (Args.RenderVisualization):
    # Abstract visualization of model
    # NOTE: If the model was created with NES-Netmorph, and alternative to
    #       this visualization is to use the Blender output option of Netmorph,
    #       as demonstrated in the xor_scnm_groundtruth_reservoir.py script.
    print("Rendering visualization of neural network\n")
    VisualizerJob = BrainGenix.NES.Visualizer.Configuration()
    VisualizerJob.ImageWidth_px = 8192
    VisualizerJob.ImageHeight_px = 4096

    # Option to only show neuron 0, disable neurite visualization for others
    # (somas still shown).
    #VisualizerJob.Optional_VisibleNeuronIDs = [1] 

    # Render In Circle Around Sim
    Radius = 500
    Steps = 10
    ZHeight = -550

    for Point in PointsInCircum(Radius, Steps):

        VisualizerJob.CameraFOVList_deg.append(110)
        VisualizerJob.CameraPositionList_um.append([Point[0], Point[1], ZHeight])
        VisualizerJob.CameraLookAtPositionList_um.append([0, 0, -1000])

    vbp.AddInputToDB(DBdata, 'Visualization', {
        'Vis_Image_px': [ VisualizerJob.ImageWidth_px, VisualizerJob.ImageHeight_px ],
        'Vis_FOVList_deg': VisualizerJob.CameraFOVList_deg,
        'Vis_PositionList_um': VisualizerJob.CameraPositionList_um,
        'Vis_LookAtPositionList_um': VisualizerJob.CameraLookAtPositionList_um,
    })

    Visualizer = MySim.SetupVisualizer()
    try:
        Visualizer.GenerateVisualization(VisualizerJob)
    except:
        vbp.ErrorToDB(DBdata, 'NES error: Failed to generate visualization')

    visualizations_folder = f"{savefolder}/Visualizations/0"
    vbp.AddOutputToDB(DBdata, 'Vis_folder', visualizations_folder)
    try:
        Visualizer.SaveImages(visualizations_folder, 2)
    except:
        vbp.ErrorToDB(DBdata, 'NES error: Failed to retrieve visualization images to '+str(visualizations_folder))


if (Args.RenderEM):
    # EM images rendering
    print("\nRendering and storing EM images\n")

    # Configure EM rendering
    EMConfig = NES.VSDA.EM.Configuration()
    EMConfig.PixelResolution_nm = Args.Resolution_um # is actually um!!!!!
    EMConfig.ImageWidth_px = 512
    EMConfig.ImageHeight_px = 512
    EMConfig.SliceThickness_nm = 0.2 # actually um!
    EMConfig.ScanRegionOverlap_percent = 0
    EMConfig.MicroscopeFOV_deg = 50 # This is currently not used.
    EMConfig.NumPixelsPerVoxel_px = 1
    EMConfig.ImageNoiseIntensity = 130
    EMConfig.GuassianBlurSigma = 1.25
    EMConfig.BorderThickness_um = 0.3
    EMConfig.PostBlurNoisePasses = 1
    EMConfig.PreBlurNoisePasses = 0
    EMConfig.TearingEnabled = False
    EMConfig.RenderBorders = True
    EMConfig.GeneratePerlinNoise = True
#    EMConfig.GenerateImageNoise = False
#    EMConfig.EnableGaussianBlur = False
#    EMConfig.EnableInterferencePattern = False

    EMConfig.GenerateSegmentation = Args.Segmentation
    EMConfig.GenerateMeshes = Args.Meshes


    EMerror = False
    try:
        VSDAEMInstance = MySim.AddVSDAEM(EMConfig)
    except:
        vbp.ErrorToDB(DBdata, 'NES error: Failed to configure EM instance')
        EMerror = True

    if not EMerror:
        # Get bounding box for rendering
        try:
            BottomLeft_um, TopRight_um = MySim.GetBoundingBox()
            vbp.AddOutputToDB(DBdata, 'BoundingBox', {
                'BottomLeft_um': BottomLeft_um,
                'TopRight_um': TopRight_um,
            })
        except:
            vbp.ErrorToDB(DBdata, 'NES error: Failed to retrieve bounding box')
            EMerror = True

    if not EMerror:
        SubdivideSize = Args.SubdivideSize

        BottomLeft_um = [BottomLeft_um[0]/SubdivideSize, BottomLeft_um[1]/SubdivideSize, BottomLeft_um[2]/SubdivideSize]
        TopRight_um = [TopRight_um[0]/SubdivideSize, TopRight_um[1]/SubdivideSize, TopRight_um[2]/SubdivideSize]

        Rotation_rad = [0,0,0]

        vbp.AddInputToDB(DBdata, 'EM', {
            'EM_BoundingBox': {
                'BottomLeft_um': BottomLeft_um,
                'TopRight_um': TopRight_um,
            },
            'EM_Rotation_rad': Rotation_rad,
            'EM_Resolution_um': Args.Resolution_um,
            'EM_Image_px': [ EMConfig.ImageWidth_px, EMConfig.ImageHeight_px ],
            'EM_Thickness_um': EMConfig.SliceThickness_nm,
            'EM_Overlap_pct': EMConfig.ScanRegionOverlap_percent,
            'EM_FOV_deg': EMConfig.MicroscopeFOV_deg,
            'EM_px_per_voxel': EMConfig.NumPixelsPerVoxel_px,
            'EM_Border_um': EMConfig.BorderThickness_um,
            'EM_Border': EMConfig.RenderBorders,
            'EM_Artifacts': {
                'Noise': EMConfig.GenerateImageNoise,
                'NoiseIntensity': EMConfig.ImageNoiseIntensity,
                'GaussianBlur': EMConfig.EnableGaussianBlur,
                'GuassianBlurSigma': EMConfig.GuassianBlurSigma,
                'PreBlurNoisePasses': EMConfig.PreBlurNoisePasses,
                'PostBlurNoisePasses': EMConfig.PostBlurNoisePasses,
                'Tearing': EMConfig.TearingEnabled,
                'PerlinNoise': EMConfig.GeneratePerlinNoise,
                'InterferencePattern': EMConfig.EnableInterferencePattern,
            },
            'EM_Segmentation': EMConfig.GenerateSegmentation,
            'EM_Meshes': EMConfig.GenerateMeshes,
        })

        # Run EM rendering
        try:
            VSDAEMInstance.DefineScanRegion(BottomLeft_um, TopRight_um, Rotation_rad)
            VSDAEMInstance.QueueRenderOperation()
            VSDAEMInstance.WaitForRender()
        except:
            vbp.ErrorToDB(DBdata, 'NES error: Failed to render EM images')
            EMerror = True


        if Args.DownloadEM and not EMerror:
            # Retrieve EM data to front-end
            EMoutput_folder = f"{savefolder}/ChallengeOutput/EMRegions/0/Data"
            EMparams_file = f"{savefolder}/ChallengeOutput/EMRegions/0/Params.json"
            vbp.AddOutputToDB(DBdata, 'EMoutputfolder', EMoutput_folder)
            vbp.AddOutputToDB(DBdata, 'EMparamsfile', EMparams_file)

            try:
                os.makedirs(EMoutput_folder)
                NumImagesX, NumImagesY, NumSlices = VSDAEMInstance.SaveImageStack(EMoutput_folder, 20)
            except Exception as e:
                vbp.ErrorToDB(DBdata, 'File error: Failed to retrieve EM images: '+str(e))
                EMerror = True

            if not EMerror:
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
                try:
                    with open(EMparams_file, 'w') as F:
                        F.write(json.dumps(EMInfoJSON))
                except:
                    vbp.ErrorToDB(DBdata, 'File error: Failed to save EM parameters file '+str(EMparams_file))
                    EMerror = True

                # NOTE: Stitching is BUGGY, temporarily deactivated.
                # if not EMerror:
                #     print(" -- Reconstructing Image Stack")
                #     EMstitched_folder = f"{savefolder}/EMRegions/0"
                #     vbp.AddOutputToDB(DBdata, 'EMstitchedfolder', EMstitched_folder)
                #     os.makedirs(EMstitched_folder)
                #     StackStitcher.StitchManySlices(EMoutput_folder, EMstitched_folder, borderSizePx=3, nWorkers=os.cpu_count(), makeGIF=False)

        DatasetHandle = None
        NeuroglancerURL = None
        if Args.Neuroglancer and not EMerror:
            try:
                VSDAEMInstance.PrepareNeuroglancerDataset()
                VSDAEMInstance.WaitForConversion()
                DatasetHandle = VSDAEMInstance.GetDatasetHandle()
                print(f"Dataset Handle: {DatasetHandle}")
                NeuroglancerURL = VSDAEMInstance.GetNeuroglancerDatasetURL(_ForceURLBase=Args.NeuroglancerURLBase)
                print(f"URL: {NeuroglancerURL}")
                vbp.AddOutputToDB(DBdata, 'NeuroglancerDataHandle', DatasetHandle)
                vbp.AddOutputToDB(DBdata, 'NeuroglancerURL', NeuroglancerURL)
            except:
                vbp.ErrorToDB(DBdata, 'NES error: Failed to generate Neuroglancer data set')

        TotalEMRenders += 1

# ----------------------------------------------------

# Update experiments database file with results
vbp.UpdateExpsDB(DBdata)

# Update the local Simulations Database
SimsDatabase = {}
try:
    with open('./SimsDatabase.json', 'r') as f:
        SimsDatabase = json.load(f)
except:
    pass
simIDstr = str(MySim.ID)
if Args.modelname not in SimsDatabase:
    SimsDatabase[Args.modelname] = {}
if simIDstr not in SimsDatabase[Args.modelname]:
    SimsDatabase[Args.modelname][simIDstr] = {}
if Args.Neuroglancer and DatasetHandle and NeuroglancerURL:
    if "Neuroglancer" not in SimsDatabase[Args.modelname][simIDstr]:
        SimsDatabase[Args.modelname][simIDstr]["Neuroglancer"] = {}
    SimsDatabase[Args.modelname][simIDstr]["Neuroglancer"][DatasetHandle] = NeuroglancerURL
try:
    with open('./SimsDatabase.json', 'w') as f:
        json.dump(SimsDatabase, f)
except Exception as e:
    print('Failed to update the SimDatabase: '+str(e))

print(" -- Done.")


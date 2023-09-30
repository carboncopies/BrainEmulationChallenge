#!/usr/bin/env python3
# bs_vbp01_doubleblind_x_acquisition.py
# Randal A. Koene, 20230914

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

from sys import argv

USENES='-p' not in argv

import vbpcommon
from bs_vbp00_groundtruth_xi_sampleprep import init_groundtruth

if USENES:
    from NES_interfaces.BG_API import BGNES_QuickStart
    from NES_interfaces.System import System
    from NES_interfaces.KGTRecords import plot_electrodes
    from NES_interfaces.Spatial import vec3add
else:
    from prototyping.System import System
    from prototyping.KGTRecords import plot_recorded, plot_electrodes
    from prototyping.Spatial import vec3add

def quickstart(user:str, passwd:str):
    if USENES:
        if not BGNES_QuickStart(user, passwd, scriptversion, versionmustmatch=False, verbose=False):
            print('BG NES Interface access failed.')
            exit(1)

# -- Initialize Functional Data Acquisition: ---------------------------------

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

def init_spontaneous_activity(bs_acq_system:System):
    spont_spike_interval_ms_mean = 280
    spont_spike_interval_ms_stdev = 140
    spont_spike_interval_pair = (spont_spike_interval_ms_mean, spont_spike_interval_ms_stdev)
    spont_spike_settings = [
        (spont_spike_interval_pair, '0'), # Setting for neuron 0.
        (spont_spike_interval_pair, '1'), # Setting for neuron 1.
    ]
    print('Setting up spontaneous activity at each neuron.')

    bs_acq_system.set_spontaneous_activity(spont_spike_settings)

def init_recording_electrode(bs_acq_system:System, num_sites:int, sites_ratio:float, noise_level:float):
    geo_center_xyz_um = bs_acq_system.get_geo_center()
    sites = [ (0, 0, 0), ] # Only one site at the tip.
    for s in range(1,num_sites):
        r = s*sites_ratio
        sites.append((0, 0, r))
    electode_specs = {
        'id': 'electrode_0',
        'tip_position': geo_center_xyz_um,
        'end_position': vec3add(geo_center_xyz_um, (0, 0, 5.0)),
        'sites': sites,
        'noise_level': noise_level
    }
    set_of_electrode_specs = [ electode_specs, ] # A single electrode.

    bs_acq_system.attach_recording_electrodes(set_of_electrode_specs)

def init_calcium_imaging(bs_acq_system:System):
    calcium_specs = {
        'id': 'calcium_0',
        'fluorescing_neurons': [ '0', '1', ], # All neurons show up in calcium imaging.
        'calcium_indicator': 'jGCaMP8', # Fast sensitive GCaMP (Zhang et al., 2023).
        'indicator_rise_ms': 2.0,
        'indicator_interval_ms': 20.0, # Max. spike rate trackable 50 Hz.
        #'microscope_lensfront_position_um': (0.0, 20.0, 0.0),
        #'microscope_rear_position_um': (0.0, 40.0, 0.0),
        'voxelspace_side_px': 30,
    }

    bs_acq_system.attach_calcium_imaging(calcium_specs)

def init_functional_data_acquisition(bs_acq_system:System, num_sites:int, sites_ratio:float, noise_level:float):
    print(ACQSETUPTEXT1)

    init_spontaneous_activity(bs_acq_system)

    init_recording_electrode(bs_acq_system, num_sites, sites_ratio, noise_level)

    init_calcium_imaging(bs_acq_system)

# -- Run Experiment: ---------------------------------------------------------

RUNTEXT1='''
Running functional data acquisition for %.1f milliseconds...
'''

def run_functional_data_acquisition(bs_acq_system:System, runtime_ms:float):
    print(RUNTEXT1 % runtime_ms)

    bs_acq_system.set_record_all() # Turning this on for comparison with electrodes.
    bs_acq_system.set_record_instruments()

    bs_acq_system.run_for(runtime_ms)

    #data = {}
    #data['electrode'] = bs_acq_system.component_by_id('electrode_0', 'get_record')
    #data['calcium'] = bs_acq_system.component_by_id('calcium_0', 'get_record')

    godseye = bs_acq_system.get_recording()
    data = bs_acq_system.get_instrument_recordings()    

    plot_recorded(godseye)
    plot_electrodes(data)

    #print(str(data))

RUNTEXT2='''
Running structural data acquisition...
'''

def run_structural_data_acquisition(bs_acq_system:System):
    print(RUNTEXT2)

    em_specs = {
        'scope': 'full',
        'sample_width_um': 6.0,
        'sample_height_um': 6.0,
        'resolution_nm': (4.0, 4.0, 30.0),
    }

    data = bs_acq_system.get_em_stack(em_specs)

    #plot_recorded(data)

# -- Entry point: ------------------------------------------------------------

HELP='''
Usage: bs_vbp01_doubleblind_x_acquisition.py [-h] [-v] [-t ms] [-p] [-s num] [-S ratio] [-n level]

       -h         Show this usage information.
       -v         Be verbose, show all diagrams.
       -t         Run for ms milliseconds.
       -p         Run prototype code (default is NES interface).
       -s         Number of sites per electrode.
       -S         Ratio separation of each site on an electrode.
       -n         Noise level.

       VBP process step 01: This script specifies double-blind data acquisition.
       WBE topic-level X: data acquisition (in-silico).

       The acquisition experiment carried out here collects data by simulating
       the use of brain data collection methods. The resulting data is intended
       for use in system identification and emulation.

'''

def parse_command_line()->tuple:
    show_all = False
    runtime_ms = 500.0
    num_sites = 1
    sites_ratio = 0.1
    noise_level = 0

    cmdline = argv.copy()
    scriptpath = cmdline.pop(0)
    while len(cmdline) > 0:
        arg = cmdline.pop(0)
        if arg == '-h':
            print(HELP)
            exit(0)
        elif arg== '-v':
            show_all = True
        elif arg== '-t':
            runtime_ms = float(cmdline.pop(0))
        elif arg== '-s':
            num_sites = int(cmdline.pop(0))
        elif arg== '-S':
            sites_ratio = float(cmdline.pop(0))
        elif arg== '-n':
            noise_level = float(cmdline.pop(0))
        # Note that -p is tested at the top of the script.

    if show_all:
        if USENES:
            print('Using NES Interface code.')
        else:
            print('Using prototype code.')

    return (show_all, runtime_ms, num_sites, sites_ratio, noise_level)

if __name__ == '__main__':

    show_all, runtime_ms, num_sites, sites_ratio, noise_level = parse_command_line()

    quickstart('Admonishing','Instruction')

    bs_acq_system = init_groundtruth(show_all=show_all)

    init_functional_data_acquisition(bs_acq_system, num_sites, sites_ratio, noise_level)

    run_functional_data_acquisition(bs_acq_system, runtime_ms)

    run_structural_data_acquisition(bs_acq_system)

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

USENES=True

import vbpcommon
from bs_vbp00_groundtruth_xi_sampleprep import init_groundtruth

if USENES:
    from NES_interfaces.BG_API import BGNES_QuickStart
else:
    pass

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
        (spont_spike_interval_pair, 0), # Setting for neuron 0.
        (spont_spike_interval_pair, 1), # Setting for neuron 1.
    ]
    print('Setting up spontaneous activity at each neuron.')

    bs_acq_system.set_spontaneous_activity(spont_spike_settings)

def init_recording_electrode(bs_acq_system:System):
    electode_specs = {
        'id': 'electrode_0',
        'tip_position': bs_acq_system.get_geo_center(),
        'sites': [ (0, 0, 0), ], # Only one site at the tip.
    }
    set_of_electrode_specs = [ electode_specs, ] # A single electrode.

    bs_acq_system.attach_recording_electrodes(set_of_electrode_specs)

def init_calcium_imaging(bs_acq_system:System):
    calcium_specs = {
        'id': 'calcium_0',
        'fluorescing_neurons': [ 0, 1, ], # All neurons show up in calcium imaging.
        'calcium_indicator': 'jGCaMP8', # Fast sensitive GCaMP (Zhang et al., 2023).
        'indicator_rise_ms': 2.0,
        'indicator_interval_ms': 20.0, # Max. spike rate trackable 50 Hz.
        'microscope_lensfront_position_um': (0.0, 20.0, 0.0),
        'microscope_rear_position_um': (0.0, 40.0, 0.0),
    }

    bs_acq_system.attach_calcium_imaging(calcium_specs)

def init_functional_data_acquisition(bs_acq_system:System):
    print(ACQSETUPTEXT1)

    init_spontaneous_activity(bs_acq_system)

    init_recording_electrode(bs_acq_system)

    init_calcium_imaging(bs_acq_system)

# -- Run Experiment: ---------------------------------------------------------

RUNTEXT1='''
Running functional data acquisition for %.1f milliseconds...
'''

def run_functional_data_acquisition(bs_acq_system:System, runtime_ms:float):
    print(RUNTEXT1 % runtime_ms)

    bs_acq_system.run_for(runtime_ms)

    data = {}
    data['electrode'] = bs_acq_system.component_by_id('electrode_0', 'get_record')
    data['calcium'] = bs_acq_system.component_by_id('calcium_0', 'get_record')

    plot_recorded(data)

RUNTEXT2='''
Running structural data acquisition...
'''

def run_structural_data_acquisition(bs_acq_system:System):
    print(RUNTEXT2 % runtime_ms)

    em_specs = {
        'scope': 'full',
        'sample_width_um': 6.0,
        'sample_height_um': 6.0,
        'resolution_nm': (4.0, 4.0, 30.0),
    }

    data = bs_acq_system.get_em_stack(em_specs)

    plot_recorded(data)

# -- Entry point: ------------------------------------------------------------

HELP='''
Usage: bs_vbp01_doubleblind_x_acquisition.py [-h] [-v] [-t ms]

       -h         Show this usage information.
       -v         Be verbose, show all diagrams.
       -t         Run for ms milliseconds.

       VBP process step 01: This script specifies double-blind data acquisition.
       WBE topic-level X: data acquisition (in-silico).

       The acquisition experiment carried out here collects data by simulating
       the use of brain data collection methods. The resulting data is intended
       for use in system identification and emulation.

'''

def parse_command_line()->tuple:
    from sys import argv

    show_all = False
    runtime_ms = 500.0

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

    return (show_all, runtime_ms)

if __name__ == '__main__':

    quickstart('Admonishing','Instruction')

    show_all, runtime_ms = parse_command_line()

    bs_acq_system = init_groundtruth(show_all=show_all)

    init_functional_data_acquisition(bs_acq_system)

    run_functional_data_acquisition(bs_acq_system, runtime_ms)

    run_structural_data_acquisition(bs_acq_system)

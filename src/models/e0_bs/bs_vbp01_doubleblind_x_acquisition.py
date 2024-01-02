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

import matplotlib.pyplot as plt
import numpy as np
from sys import argv

USENES='-p' not in argv

import vbpcommon
from bs_vbp00_groundtruth_xi_sampleprep import init_groundtruth

from common.Common_Parameters import Common_Parameters, common_commandline_parsing, make_savefolder, COMMON_HELP
if USENES:
    from NES_interfaces.BG_API import BGNES_QuickStart
    from NES_interfaces.System import System
    from NES_interfaces.KGTRecords import plot_electrodes
    from NES_interfaces.Spatial import vec3add, VecBox
    from NES_interfaces.Data import save_acq_data
else:
    from prototyping.System import System
    from prototyping.KGTRecords import plot_recorded, plot_electrodes, plot_calcium_signals, plot_calcium
    from prototyping.Spatial import vec3add, VecBox
    from prototyping.Data import save_acq_data

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

LOADTEXT1='''
1. Loading system from file %s.
'''

def load_groundtruth(pars:Common_Parameters)->System:

    file = pars.fullpath(pars.extra['load_kgt'])
    print(LOADTEXT1 % file)

    kgt_system = System('e0_bs')

    kgt_system.load(file=file)

    if pars.show['regions']: kgt_system.show(show=pars.show)

    return kgt_system

def init_spontaneous_activity(bs_acq_system:System):
    spont_spike_interval_ms_mean = 280
    spont_spike_interval_ms_stdev = 140
    spont_spike_interval_pair = (spont_spike_interval_ms_mean, spont_spike_interval_ms_stdev)
    neuron_ids = bs_acq_system.get_all_neuron_IDs()
    spont_spike_settings = [ (spont_spike_interval_pair, neuron_id) for neuron_id in neuron_ids ]
    print('Setting up spontaneous activity at each neuron.')

    bs_acq_system.set_spontaneous_activity(spont_spike_settings)

def init_recording_electrode(bs_acq_system:System, pars:Common_Parameters):
    geo_center_xyz_um = bs_acq_system.get_geo_center()
    sites = [ (0, 0, 0), ] # Only one site at the tip.
    for s in range(1,pars.extra['num_sites']):
        r = s*pars.extra['sites_ratio']
        sites.append((0, 0, r))
    electode_specs = {
        'id': 'electrode_0',
        'tip_position': geo_center_xyz_um,
        'end_position': vec3add(geo_center_xyz_um, (0, 0, 5.0)),
        'sites': sites,
        'noise_level': pars.extra['noise_level']
    }
    set_of_electrode_specs = [ electode_specs, ] # A single electrode.

    bs_acq_system.attach_recording_electrodes(set_of_electrode_specs)

def init_calcium_imaging(bs_acq_system:System, pars:Common_Parameters):
    calcium_specs = {
        'id': 'calcium_0',
        'fluorescing_neurons': bs_acq_system.get_all_neuron_IDs(), # All neurons show up in calcium imaging.
        'calcium_indicator': 'jGCaMP8', # Fast sensitive GCaMP (Zhang et al., 2023).
        'indicator_rise_ms': 2.0,
        'indicator_decay_ms': 40.0,
        'indicator_interval_ms': 20.0, # Max. spike rate trackable 50 Hz.
        #'microscope_lensfront_position_um': (0.0, 20.0, 0.0),
        #'microscope_rear_position_um': (0.0, 40.0, 0.0),
        'voxelspace_side_px': 30,
        'imaged_subvolume': VecBox(
                center=np.array([0, pars.extra['calcium_y'], 0]),
                half=np.array([pars.extra['calcium_fov']/2.0, pars.extra['calcium_fov']/2.0, 2.0]),
                dx=np.array([1.0, 0.0, 0.0]),
                dy=np.array([0.0, 1.0, 0.0]),
                dz=np.array([0.0, 0.0, 1.0]), # Positive dz indicates most visible top surface.
            ),
        'generate_during_sim': False,
    }

    bs_acq_system.attach_calcium_imaging(calcium_specs, pars=pars)

    if pars.show['voxels']: bs_acq_system.calcium_imaging.show_voxels(
        savefolder=pars.savefolder,
        voxelfile='Ca-voxels.'+pars.figspecs()['figext'],
        figspecs=pars.figspecs())

def init_functional_data_acquisition(bs_acq_system:System, pars:Common_Parameters):
    print(ACQSETUPTEXT1)

    init_spontaneous_activity(bs_acq_system)

    init_recording_electrode(bs_acq_system, pars=pars)

    init_calcium_imaging(bs_acq_system, pars=pars)

# -- Run Experiment: ---------------------------------------------------------

RUNTEXT1='''
Running functional data acquisition for %.1f milliseconds...
'''

def run_functional_data_acquisition(bs_acq_system:System, pars:Common_Parameters)->tuple:
    print(RUNTEXT1 % pars.runtime_ms)

    bs_acq_system.set_record_all() # Turning this on for comparison with electrodes.
    bs_acq_system.set_record_instruments()

    bs_acq_system.run_for(pars.runtime_ms)

    if not bs_acq_system.calcium_imaging.specs['generate_during_sim']:
        bs_acq_system.calcium_imaging.record_aposteriori()

    godseye = bs_acq_system.get_recording()
    data = bs_acq_system.get_instrument_recordings()    

    casignals = {
        't_Ca_samples': [],
        'Ca_samples': [],
    }
    for neuron in bs_acq_system.calcium_imaging.neuron_refs:
        casignals['t_Ca_samples'] = neuron.t_Ca_samples
        casignals['Ca_samples'].append(neuron.Ca_samples)

    plot_calcium_signals(savefolder=pars.savefolder, data=casignals, figspecs=pars.figspecs())
    plot_recorded(savefolder=pars.savefolder, data=godseye, figspecs=pars.figspecs())
    plot_electrodes(savefolder=pars.savefolder, data=data, figspecs=pars.figspecs())
    plot_calcium(data, gifpath=pars.savefolder+'/vbp01.gif', show_all=False)

    #print(str(data))

    return data, casignals, godseye

RUNTEXT2='''
Running structural data acquisition...
'''

def run_structural_data_acquisition(bs_acq_system:System)->dict:
    print(RUNTEXT2)

    em_specs = {
        'scope': 'full',
        'sample_width_um': 6.0,
        'sample_height_um': 6.0,
        'resolution_nm': (4.0, 4.0, 30.0),
    }

    data = bs_acq_system.get_em_stack(em_specs)

    #plot_recorded(data)

    return data

# -- Entry point: ------------------------------------------------------------

HELP='''
Usage: bs_vbp01_doubleblind_x_acquisition.py [-h] [-v] [-V output] [-t ms]
       [-R seed] [-d dir] [-l width] [-f size] [-x ext] [-p] [-N neurons]
       [-D method] [-s sites] [-S ratio] [-n level] [-C um] [-c ycenter]
       [-L file] [-A file] [-K file]
%s
       -N         Number of neurons in ground truth system.
       -D         Distribution method: aligned, unirand.
       -s         Number of sites per electrode.
       -S         Ratio separation of each site on an electrode.
       -n         Noise level.
       -C         Calcium imaging FOV diameter in micrometers.
       -c         Calcium imaging y-axis center position.
       -L         Load known ground-truth system (KTG) ('' means generate,
                  default: kgt.json).
       -A         Save acquired data (default: data.pkl.gz).
       -K         Save known ground-truth system (KTG) as file (default:
                  kgt.json).

       VBP process step 01: This script specifies double-blind data acquisition.
       WBE topic-level X: data acquisition (in-silico).

       The acquisition experiment carried out here collects data by simulating
       the use of brain data collection methods. The resulting data is intended
       for use in system identification and emulation.

''' % COMMON_HELP

def parse_command_line()->tuple:
    extra_pars = {
        'num_nodes': 2,
        'distribution': 'aligned',
        'num_sites': 1,
        'sites_ratio': 0.1,
        'noise_level': 0,
        'calcium_fov': 12.0,
        'calcium_y': -5.0,
        'load_kgt': 'kgt.json',
        'save_data': 'data.pkl.gz',
        'save_kgt': 'kgt.json',
    }

    cmdline = argv.copy()
    pars = Common_Parameters(cmdline.pop(0))
    while len(cmdline) > 0:
        arg = common_commandline_parsing(cmdline, pars, HELP)
        if arg is not None:
            if arg== '-s':
                extra_pars['num_sites'] = int(cmdline.pop(0))
            elif arg== '-S':
                extra_pars['sites_ratio'] = float(cmdline.pop(0))
            elif arg== '-n':
                extra_pars['noise_level'] = float(cmdline.pop(0))
            elif arg== '-N':
                extra_pars['num_nodes'] = int(cmdline.pop(0))
            elif arg== '-C':
                extra_pars['calcium_fov'] = float(cmdline.pop(0))
            elif arg== '-c':
                extra_pars['calcium_y'] = float(cmdline.pop(0))
            elif arg== '-D':
                extra_pars['distribution'] = str(cmdline.pop(0))
            elif arg== '-L':
                extra_pars['load_kgt'] = str(cmdline.pop(0))
            elif arg== '-A':
                extra_pars['save_data'] = str(cmdline.pop(0))
            elif arg== '-K':
                extra_pars['save_kgt'] = str(cmdline.pop(0))
            else:
                print('Unknown command line parameter: '+str(arg))
                exit(0)
        # Note that -p is tested at the top of the script.

    if pars.show['text']:
        if USENES:
            print('Using NES Interface code.')
        else:
            print('Using prototype code.')

    pars.extra = extra_pars
    return pars

if __name__ == '__main__':

    pars = parse_command_line()
    make_savefolder(pars)

    quickstart('Admonishing','Instruction')

    if pars.extra['load_kgt']=='':
        bs_acq_system = init_groundtruth(pars=pars)
    else:
        bs_acq_system = load_groundtruth(pars=pars)

    init_functional_data_acquisition(bs_acq_system, pars=pars)

    functional_data, casignals, godseye = run_functional_data_acquisition(bs_acq_system, pars=pars)

    structural_data = run_structural_data_acquisition(bs_acq_system)

    data = {
        'functional': functional_data,
        'structural': structural_data,
    }
    file = pars.fullpath(pars.extra['save_data'])

    print('Saving acquired data to %s.' % file)
    save_acq_data(data=data, file=file)

    print('Generating figure plots...')
    plt.show()
    print('Done')

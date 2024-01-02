#!/usr/bin/env python3
# bs_vbp02_translation_iv_system_identification.py
# Randal A. Koene, 20231007

'''
The ball-and-stick example is intended to provide the simplest in-silico case with the smallest
number of variables to address while still demonstrating the full process and dependencies
chain for whole brain emulation.

This file implements system identification using the data acquired from the known
ground-truth system.

VBP process step 02: system identification
WBE topic-level IV: system identification of model architecture & translation of data
to model parameters
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
    from NES_interfaces.Data import load_acq_data
else:
    from prototyping.System import System
    from prototyping.KGTRecords import plot_recorded, plot_electrodes, plot_calcium_signals, plot_calcium
    from prototyping.Spatial import vec3add, VecBox
    from prototyping.Data import load_acq_data

def quickstart(user:str, passwd:str):
    if USENES:
        if not BGNES_QuickStart(user, passwd, scriptversion, versionmustmatch=False, verbose=False):
            print('BG NES Interface access failed.')
            exit(1)

# -- System Identification: --------------------------------------------------

LOADACQTEXT1='''
1. Loading acquired data from file %s.
'''

def system_identification(pars:Common_Parameters):

    file = pars.fullpath(pars.extra['load_data'])
    print(LOADACQTEXT1 % file)

    data = load_acq_data(file=file)


# -- Load System: ------------------------------------------------------------

LOADEMUTEXT1='''
1. Skipping system identification, loading system from %s.
'''

def load_system(pars:Common_Parameters):

    file = pars.fullpath(pars.extra['load_kgt'])
    print(LOADEMUTEXT1 % file)

    bs_system = System('e0_bs')

    bs_system.load(file=file)

    if pars.show['regions']: bs_system.show(show=pars.show)

    file = pars.fullpath(pars.extra['save_emu'])
    print('Saving emulation system to %s' % file)

    bs_system.save(file=file)

# -- Entry point: ------------------------------------------------------------

HELP='''
Usage: bs_vbp02_translation_iv_system_identification.py [-h] [-v] [-V output] [-t ms]
       [-R seed] [-d dir] [-l width] [-f size] [-x ext] [-p] [-s] [-L file] [-K file]
       [-E file]
%s
       -s         Skip system identification, simply duplicate KGT.
       -L         Load acquired data from file (default: data.pkl.gz).
       -K         Load system from file (default: kgt.json).
       -E         Save emulated system to file (default: emu.json).

       VBP process step 01: This script specifies double-blind data acquisition.
       WBE topic-level X: data acquisition (in-silico).

''' % COMMON_HELP

def parse_command_line()->tuple:
    extra_pars = {
        'identify': True,
        'load_data': 'data.pkl.gz',
        'load_kgt': 'kgt.json',
        'save_emu': 'emu.json',
    }

    cmdline = argv.copy()
    pars = Common_Parameters(cmdline.pop(0))
    while len(cmdline) > 0:
        arg = common_commandline_parsing(cmdline, pars, HELP)
        if arg is not None:
            if arg== '-s':
                extra_pars['identify'] = False
            elif arg== '-L':
                extra_pars['load_data'] = str(cmdline.pop(0))
            elif arg== '-K':
                extra_pars['load_kgt'] = str(cmdline.pop(0))
            elif arg== '-E':
                extra_pars['save_emu'] = str(cmdline.pop(0))
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

    if pars.extra['identify']:
        system_identification(pars=pars)
    else:
        load_system(pars=pars)

    print('Generating figure plots...')
    plt.show()
    print('Done')

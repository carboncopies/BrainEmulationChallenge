#!/usr/bin/env python3
# bs_vbp03_emulation_iii_validation.py
# Randal A. Koene, 20231007

'''
The ball-and-stick example is intended to provide the simplest in-silico case with the smallest
number of variables to address while still demonstrating the full process and dependencies
chain for whole brain emulation.

This file implements a validation procedure for the resulting emulation.

VBP process step 03: emulation validation
WBE topic-level III: evolving similarity / performance metrics
'''

scriptversion='0.0.1'

import matplotlib.pyplot as plt
import numpy as np
from sys import argv

USENES='-p' not in argv

import vbpcommon
from bs_vbp00_groundtruth_xi_sampleprep import init_groundtruth

if USENES:
    from NES_interfaces.BG_API import BGNES_QuickStart
    from NES_interfaces.System import System, Common_Parameters, common_commandline_parsing, COMMON_HELP, make_savefolder
    from NES_interfaces.KGTRecords import plot_electrodes
    from NES_interfaces.Spatial import vec3add, VecBox
else:
    from prototyping.System import System, Common_Parameters, common_commandline_parsing, COMMON_HELP, make_savefolder
    from prototyping.KGTRecords import plot_recorded, plot_electrodes, plot_calcium_signals, plot_calcium
    from prototyping.Spatial import vec3add, VecBox

def quickstart(user:str, passwd:str):
    if USENES:
        if not BGNES_QuickStart(user, passwd, scriptversion, versionmustmatch=False, verbose=False):
            print('BG NES Interface access failed.')
            exit(1)

# -- Load Emulation: ---------------------------------------------------------

LOADEMUTEXT1='''
1. Loading emulation from %s.
'''

def load_emulation(pars:Common_Parameters)->System:

    file = pars.fullpath(pars.extra['load_emu'])
    print(LOADEMUTEXT1 % file)

    bs_emulation = System('e0_bs')

    bs_emulation.load(file=file)

    if pars.show['regions']: bs_emulation.show(show=pars.show)

    return bs_emulation

# -- Load Ground Truth: ------------------------------------------------------

LOADKGTTEXT1='''
2. Loading ground truth from %s.
'''

def load_ground_truth(pars:Common_Parameters)->System:

    file = pars.fullpath(pars.extra['load_kgt'])
    print(LOADKGTTEXT1 % file)

    bs_kgt = System('e0_bs')

    bs_kgt.load(file=file)

    if pars.show['regions']: bs_kgt.show(show=pars.show)

    return bs_kgt

# -- Validate Success Criteria: ----------------------------------------------

def validate_success_criteria(bs_emulation:System, bs_kgt:System):

    print('Success criterion: ')

# -- Entry point: ------------------------------------------------------------

HELP='''
Usage: bs_vbp03_emulation_iii_validation.py [-h] [-v] [-V output] [-t ms]
       [-R seed] [-d dir] [-l width] [-f size] [-x ext] [-p] [-E file]
       [-K file]
%s
       -E         Load emulation system from file (default: emu.json).
       -K         Load ground truth system from file (default: kgt.json).

       VBP process step 03: This script specifies a validation procedure for
       the resulting emulation.
       WBE topic-level III: emulation validation.

''' % COMMON_HELP

def parse_command_line()->tuple:
    extra_pars = {
        'load_emu': 'emu.json',
        'load_kgt': 'kgt.json',
    }

    cmdline = argv.copy()
    pars = Common_Parameters(cmdline.pop(0))
    while len(cmdline) > 0:
        arg = common_commandline_parsing(cmdline, pars, HELP)
        if arg is not None:
            if arg== '-E':
                extra_pars['load_emu'] = str(cmdline.pop(0))
            if arg== '-K':
                extra_pars['load_kgt'] = str(cmdline.pop(0))
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

    bs_emulation = load_emulation(pars=pars)
    bs_kgt = load_ground_truth(pars=pars)

    validate_success_criteria(bs_emulation, bs_kgt)

    print('Generating figure plots...')
    plt.show()
    print('Done')

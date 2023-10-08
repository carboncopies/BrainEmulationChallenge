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

if __name__ == '__main__':

    pars = parse_command_line()
    make_savefolder(pars)

    quickstart('Admonishing','Instruction')

    bs_acq_system = init_groundtruth(pars=pars)

    #init_functional_data_acquisition(bs_acq_system, pars=pars)

    #run_functional_data_acquisition(bs_acq_system, pars=pars)

    #run_structural_data_acquisition(bs_acq_system)

    print('Generating figure plots...')
    plt.show()
    print('Done')

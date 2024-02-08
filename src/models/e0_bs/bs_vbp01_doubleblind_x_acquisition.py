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

import vbpcommon
import common.glb as glb
from NES_interfaces.BG_API import BG_API_Setup

api_is_local=True
savefolder = '/tmp/vbp_'+datetime.now().strftime("%F_%X")
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


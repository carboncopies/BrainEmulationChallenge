#!/usr/bin/env python3
# xor_sc_emulation.py
# Randal A. Koene, 20240326

'''
The XOR SimpleCompartmental example uses branching axons in a representation of a
meaningful logic circuit to produce expected functional output.

This file implements a validation procedure for the resulting emulation.

VBP process step 03: emulation validation
WBE topic-level III: evolving similarity / performance metrics
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
import os
from BrainGenix import Credentials, SimClient

from NES_interfaces.Metrics_N1 import Metrics_N1

import BrainGenix.NES as NES
import BrainGenix

from connectomes import get_connectomes

Parser = argparse.ArgumentParser(description="vbp validation script")
Parser.add_argument("-Local", action='store_true', help="Render remotely or on localhost")
Parser.add_argument("-Remote", action='store_true', help="Run on remote NES server")
Args = Parser.parse_args()

runtime_ms=500.0
savefolder = 'output/'+str(datetime.now()).replace(":", "_")+'-validation'
figspecs = {
    'figsize': (6,6),
    'linewidth': 0.5,
    'figext': 'pdf',
}

groundtruth, emulation = get_connectomes(Args, user='Admonishing', passwd='Instruction')

# -- Run structure comparison with Metrics N1

print('')
metric_n1 = Metrics_N1(emulation, groundtruth)
metric_n1.validate()

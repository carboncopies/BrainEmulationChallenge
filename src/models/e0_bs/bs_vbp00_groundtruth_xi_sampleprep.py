#!/usr/bin/env python3
# bs_vbp00_groundtruth_xi_sampleprep.py
# Randal A. Koene, 20230621

'''
The ball-and-stick example is intended to provide the simplest in-silico case with the smallest
number of variables to address while still demonstrating the full process and dependencies
chain for whole brain emulation.

This file implements an in-silico fully known ground-truth system.

VBP process step 00: groundtruth
WBE topic-level XI: sample preparation / preservation (in-silico)
'''

# TODO: *** Do some rewriting such that all of the functional
#           setup through NES is nicely separated from the
#           morphology and other things that are handled only in Python.
#           Then, have the prototyping version work the same way, except
#           that the functional part is also in Python. Ideally, the
#           non-functional parts can use shared code across both versions.
# TODO: *** Ensure that the NES and prototype update functions are
#           indeed identical, i.e. the default parameters are also the same.

scriptversion='0.0.1'

from sys import argv

USENES='-p' not in argv

import vbpcommon
if USENES:
    from NES_interfaces.BG_API import BGNES_QuickStart
    from NES_interfaces.System import System
    from NES_interfaces.Geometry import Box
    from NES_interfaces.BS_Aligned_NC import BS_Aligned_NC
    from NES_interfaces.Region import BrainRegion
    from NES_interfaces.KGTRecords import plot_recorded
else:
    from prototyping.System import System
    from prototyping.Geometry import Box
    from prototyping.BS_Aligned_NC import BS_Aligned_NC
    from prototyping.Region import BrainRegion
    from prototyping.KGTRecords import plot_recorded

def quickstart(user:str, passwd:str):
    if USENES:
        if not BGNES_QuickStart(user, passwd, scriptversion, versionmustmatch=False, verbose=False):
            print('BG NES Interface access failed.')
            exit(1)

# -- Initialize Known Ground-Truth System: -----------------------------------

INITTEXT1='''
1. Defining a 2-neuron system:
   a. Scale: The number of principal nodes.
   b. Functional: The type of network arrangment
      (aligned ball-and-stick).
   c. Physical: A specific volume (a box region).
   Defaults are applied to other parameters.
'''

def init_groundtruth(show_all=False)->System:

    bs_system = System('e0_bs')

    print(INITTEXT1)

    NUM_NODES=2
    bs_net = bs_system.add_circuit( BS_Aligned_NC(id='BS NC', num_cells=NUM_NODES) )
    bs_region = bs_system.add_region( BrainRegion(
        id='BS',
        shape=Box( dims_um=(20.0, 20.0, 20.0) ),
        content=bs_net) )

    if show_all: bs_region.show()

    # 2. Initialize the connection between the 2 neurons:
    bs_net.Encode(
        pattern_set=[ ( '0', '1' ), ], # From cell 0 to cell 1.
        encoding_method='instant',
        synapse_weight_method='binary'
        )

    if show_all: bs_region.show()

    return bs_system

# -- Initialize Experiment: --------------------------------------------------

STIMTEXT1='''
Dynamic activity:
The imagined nature of the 2-neuron ball-and-stick circuit
provides no differentiation of dendritic input sources to
the neurons. Activity is elicited exclusively by generating
potential at or near a soma to the point where a cell fires
and action potential.

God's eye direct access to every aspect of the in-silico
ground-truth system includes the ability to specifically
cause a somatic action potential at any time.
'''

def init_experiment(bs_kgt_system:System):
    print(STIMTEXT1)
    t_soma_fire_ms = [
        (100.0, '0'),
        (200.0, '0'),
        (300.0, '0'),
        (400.0, '0'),
    ]
    print('Directed somatic firing: '+str(t_soma_fire_ms))

    bs_kgt_system.attach_direct_stim(t_soma_fire_ms)

# -- Run Experiment: ---------------------------------------------------------

RUNTEXT1='''
Running experiment for %.1f milliseconds...
'''

def run_experiment(bs_kgt_system:System, runtime_ms:float):
    print(RUNTEXT1 % runtime_ms)
    bs_kgt_system.set_record_all()

    bs_kgt_system.run_for(runtime_ms)

    data = bs_kgt_system.get_recording()

    plot_recorded(data)

# -- Entry point: ------------------------------------------------------------

HELP='''
Usage: bs_vbp00_groundtruth_xi_sampleprep.py [-h] [-v] [-t ms] [-p]

       -h         Show this usage information.
       -v         Be verbose, show all diagrams.
       -t         Run for ms milliseconds.
       -p         Run prototype code (default is NES interface).

       VBP process step 00: This script specifies a known ground-truth system.
       WBE topic-level XI: sample preparation / preservation (in-silico).

       The test run of the model that is carried out here obtains data in
       God's Eye mode. This data should not be used to test system
       identification and emulation.

'''

def parse_command_line()->tuple:
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
        # Note that -p is tested at the top of the script.

    if show_all:
        if USENES:
            print('Using NES Interface code.')
        else:
            print('Using prototype code.')

    return (show_all, runtime_ms)

if __name__ == '__main__':

    show_all, runtime_ms = parse_command_line()

    quickstart('Admonishing','Instruction')

    bs_kgt_system = init_groundtruth(show_all=show_all)

    init_experiment(bs_kgt_system)

    run_experiment(bs_kgt_system, runtime_ms)

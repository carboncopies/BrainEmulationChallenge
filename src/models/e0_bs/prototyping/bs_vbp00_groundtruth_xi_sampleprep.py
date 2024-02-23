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
import common.glb as glb
from common.Common_Parameters import Common_Parameters, common_commandline_parsing, make_savefolder, COMMON_HELP
if USENES:
    from NES_interfaces.BG_API import BG_API_Setup
    from NES_interfaces.System import System
    from NES_interfaces.Geometry import Box
    from NES_interfaces.BS_Aligned_NC import BS_Aligned_NC, BS_Uniform_Random_NC
    from NES_interfaces.Region import BrainRegion
    from NES_interfaces.KGTRecords import plot_recorded
else:
    from prototyping.System import System
    from prototyping.Geometry import Box
    from prototyping.BS_Aligned_NC import BS_Aligned_NC, BS_Uniform_Random_NC
    from prototyping.Region import BrainRegion
    from prototyping.KGTRecords import plot_recorded

def quickstart(user:str, passwd:str, api_is_local:bool):
    if USENES:
        BG_API_Setup(user=user, passwd=passwd)
        if api_is_local:
            glb.bg_api.set_local()
        if not glb.bg_api.BGNES_QuickStart(scriptversion, versionmustmatch=False, verbose=False):
            print('BG NES Interface access failed.')
            exit(1)
        return glb.bg_api
    else:
        return None

# -- Initialize Known Ground-Truth System: -----------------------------------

INITTEXT1='''
1. Defining a %s-neuron system:
   a. Scale: The number of principal nodes.
   b. Functional: The type of network arrangment
      (aligned ball-and-stick).
   c. Physical: A specific volume (a box region).
   Defaults are applied to other parameters.
'''

def init_groundtruth(pars:Common_Parameters)->System:

    bs_system = System('e0_bs')

    print(INITTEXT1 % str(pars.extra['num_nodes']))

    if pars.extra['distribution'] == 'unirand':
        bs_net = bs_system.add_circuit( BS_Uniform_Random_NC(id='BS NC', num_cells=pars.extra['num_nodes']) )
    else:
        bs_net = bs_system.add_circuit( BS_Aligned_NC(id='BS NC', num_cells=pars.extra['num_nodes']) )
    bs_region = bs_system.add_region( BrainRegion(
        id='BS',
        shape=Box( dims_um=(20.0, 20.0, 20.0) ),
        content=bs_net) )

    if pars.show['regions']: bs_region.show(show=pars.show)

    # 2. Initialize the connection between the 2 neurons:
    bs_net.Encode(
        pattern_set=[ ( '0', '1' ), ], # From cell 0 to cell 1.
        encoding_method='instant',
        synapse_weight_method='binary'
        )

    #if pars.show['regions']: bs_region.show()
    if pars.show['regions']: bs_system.show(show=pars.show)

    file = pars.fullpath(pars.extra['save_kgt'])
    print('Saving known ground-truth (KGT) system to %s.' % file)
    bs_system.save(file)

    return bs_system

# -- Initialize Experiment: --------------------------------------------------

STIMTEXT1='''
Dynamic activity:
The imagined nature of the 2-neuron ball-and-stick circuit
provides no differentiation of dendritic input sources to
the neurons. Activity is elicited exclusively by generating
potential at or near a soma to the point where a cell fires
and action potential is propagated.

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

def run_experiment(bs_kgt_system:System, pars:Common_Parameters):
    print(RUNTEXT1 % pars.runtime_ms)
    bs_kgt_system.set_record_all()

    bs_kgt_system.run_for(pars.runtime_ms)

    data = bs_kgt_system.get_recording()

    plot_recorded(savefolder=pars.savefolder, data=data, figspecs=pars.figspecs())

# -- Entry point: ------------------------------------------------------------

HELP='''
Usage: bs_vbp00_groundtruth_xi_sampleprep.py [-h] [-v] [-V output] [-t ms]
       [-R seed] [-d dir] [-l width] [-f size] [-x ext] [-p] [-a]
       [-N neurons] [-D method] [-K file]
%s
       -N         Number of neurons in ground truth system.
       -D         Distribution method: aligned, unirand.
       -K         Save known ground-truth system (KTG) as file (default:
                  kgt.json).

       VBP process step 00: This script specifies a known ground-truth system.
       WBE topic-level XI: sample preparation / preservation (in-silico).

       The test run of the model that is carried out here obtains data in
       God's Eye mode. This data should not be used to test system
       identification and emulation.

''' % COMMON_HELP

def parse_command_line()->tuple:
    extra_pars = {
        'num_nodes': 2,
        'distribution': 'aligned',
        'save_kgt': 'kgt.json',
    }

    cmdline = argv.copy()
    pars = Common_Parameters(cmdline.pop(0))
    while len(cmdline) > 0:
        arg = common_commandline_parsing(cmdline, pars, HELP)
        if arg is not None:
            if arg== '-N':
                extra_pars['num_nodes'] = int(cmdline.pop(0))
            elif arg== '-D':
                extra_pars['distribution'] = str(cmdline.pop(0))
            elif arg== '-K':
                extra_pars['save_kgt'] = str(cmdline.pop(0))
            pass
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

    quickstart(
        user='Admonishing',
        passwd='Instruction',
        api_is_local=pars.api_is_local)

    bs_kgt_system = init_groundtruth(pars=pars)

    init_experiment(bs_kgt_system)

    run_experiment(bs_kgt_system, pars=pars)

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
if USENES:
    pass
else:
    pass

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

    bs_kgt_system = init_groundtruth(show_all=show_all)

    init_experiment(bs_kgt_system)

    run_experiment(bs_kgt_system, runtime_ms)

#!/usr/bin/env python3
# Metrics_N1.py
# Randal A. Koene, 20231102

'''
Methods with which to apply validation metrics for the
success criterion:
N-1 Reconstruction of neuronal circuits through system identification
and tuning of properties is sufficiently accurate.
'''

from .System import System

class Metrics_N1:
    def __init__(self, emulation:System, kgt:System):
        self.emulation = emulation
        self.kgt = kgt

    def validate_accurate_system_identification(self):
        print('Validating accurate system identification...')
        # TODO: Given that this is first of all intended to be used
        #       in the standardized WBE challenge, where the KGT
        #       is (at least initially) in-silico, it is possible to
        #       explicitly compare relevant aspects of circuit
        #       architecture identification, e.g. number of neurons,
        #       connectivity matrix (with possible transposes),
        #       types of neurons, their morphology, synapses, ion
        #       channels.

    def validate_accurate_tuning(self):
        print('Validating accurate tuning...')

    def validate(self):
        self.validate_accurate_system_identification()
        self.validate_accurate_tuning()

if __name__ == '__main__':

    print('Test demonstration of N-1 metric.')

    kgt = None
    emulation = kgt

    metrics = Metrics_N1(emulation, kgt)
    metrics.validate()

    print('Done')

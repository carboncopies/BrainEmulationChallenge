#!/usr/bin/env python3
# Metrics_N3.py
# Randal A. Koene, 20231102

'''
Methods with which to apply validation metrics for the
success criterion:
N-3 Spatio-temporal patterns, brain rhythms, synchronization are
sufficiently similar when stimulated.
'''

from .System import System

class Metrics_N3:
    def __init__(self, emulation:System, kgt:System):
        self.emulation = emulation
        self.kgt = kgt

    def validate(self):
        pass

if __name__ == '__main__':

    print('Test demonstration of N-3 metric.')

    kgt = None
    emulation = kgt

    metrics = Metrics_N3(emulation, kgt)
    metrics.validate()

    print('Done')

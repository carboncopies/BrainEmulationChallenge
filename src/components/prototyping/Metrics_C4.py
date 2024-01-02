#!/usr/bin/env python3
# Metrics_C4.py
# Randal A. Koene, 20231102

'''
Methods with which to apply validation metrics for the
success criterion:
C-4 Dynamic evolution through plasticity.
'''

from .System import System

class Metrics_C4:
    def __init__(self, emulation:System, kgt:System):
        self.emulation = emulation
        self.kgt = kgt

    def validate(self):
        pass

if __name__ == '__main__':

    print('Test demonstration of C-4 metric.')

    kgt = None
    emulation = kgt

    metrics = Metrics_C4(emulation, kgt)
    metrics.validate()

    print('Done')

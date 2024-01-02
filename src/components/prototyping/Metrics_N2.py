#!/usr/bin/env python3
# Metrics_N2.py
# Randal A. Koene, 20231102

'''
Methods with which to apply validation metrics for the
success criterion:
N-2 MIMO neural traces match within a specified envelope.
'''

from .System import System

class Metrics_N2:
    def __init__(self, emulation:System, kgt:System):
        self.emulation = emulation
        self.kgt = kgt

    def validate(self):
        pass

if __name__ == '__main__':

    print('Test demonstration of N-2 metric.')

    kgt = None
    emulation = kgt

    metrics = Metrics_N2(emulation, kgt)
    metrics.validate()

    print('Done')

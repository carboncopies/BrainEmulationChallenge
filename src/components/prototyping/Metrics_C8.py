#!/usr/bin/env python3
# Metrics_C8.py
# Randal A. Koene, 20231102

'''
Methods with which to apply validation metrics for the
success criterion:
C-8 A specified set of memories, possibly encoded specifically for
the test, is retrieved sufficiently well.
'''

from .System import System

class Metrics_C8:
    def __init__(self, emulation:System, kgt:System):
        self.emulation = emulation
        self.kgt = kgt

    def validate(self):
        pass

if __name__ == '__main__':

    print('Test demonstration of C-8 metric.')

    kgt = None
    emulation = kgt

    metrics = Metrics_C8(emulation, kgt)
    metrics.validate()

    print('Done')

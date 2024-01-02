#!/usr/bin/env python3
# Metrics_P3.py
# Randal A. Koene, 20231102

'''
Methods with which to apply validation metrics for the
success criterion:
P-3 Observable behavior and responses are sufficiently similar.
'''

from .System import System

class Metrics_P3:
    def __init__(self, emulation:System, kgt:System):
        self.emulation = emulation
        self.kgt = kgt

    def validate(self):
        pass

if __name__ == '__main__':

    print('Test demonstration of P-3 metric.')

    kgt = None
    emulation = kgt

    metrics = Metrics_P3(emulation, kgt)
    metrics.validate()

    print('Done')

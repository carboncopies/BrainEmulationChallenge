#!/usr/bin/env python3
# Metrics_C11.py
# Randal A. Koene, 20231102

'''
Methods with which to apply validation metrics for the
success criterion:
C-11 Objectively verifiable memories are retrieved with a sufficiently
similar set of correct and incorrect answers.
'''

from .System import System

class Metrics_C11:
    def __init__(self, emulation:System, kgt:System):
        self.emulation = emulation
        self.kgt = kgt

    def validate(self):
        pass

if __name__ == '__main__':

    print('Test demonstration of C-11 metric.')

    kgt = None
    emulation = kgt

    metrics = Metrics_C11(emulation, kgt)
    metrics.validate()

    print('Done')

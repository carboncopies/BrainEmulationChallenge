# SignalFunctions.py
# Randal A. Koene, 20230930

'''
Mathematical signal functions.
'''

import numpy as np

def dblexp(amp:float, tau_rise:float, tau_decay:float, tdiff:float)->float:
    if tdiff<0: return 0
    return amp*( -np.exp(-tdiff/tau_rise) + np.exp(-tdiff/tau_decay) )

def delayed_pulse(amp:float, tau_delay:float, tau_pulse:float, tdiff:float)->float:
    if tdiff<tau_delay: return 0
    if tdiff<(tau_delay+tau_pulse): return amp
    return 0

def convolve_1d(signal:np.array, kernel:np.array)->list:
    kernel = kernel[::-1]
    # Could normalize a bit by dividing kernel by len(kernel)...
    return [
        np.dot(
            signal[max(0,i):min(i+len(kernel),len(signal))],
            kernel[max(-i,0):len(signal)-i*(len(signal)-len(kernel)<i)],
        )
        for i in range(1-len(kernel),len(signal))
    ]

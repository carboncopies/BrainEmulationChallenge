#!/usr/bin/env python3
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
    revkernel = kernel[::-1]
    # Could normalize a bit by dividing kernel by len(kernel)...
    kernelsize = len(revkernel)                                          # E.g. 100
    signalsize = len(signal)                                             # E.g. 1000
    return [
        np.dot(
            signal[max(0,i):min(i+kernelsize,signalsize)],               # E.g. at i=-50, [0:50]
            revkernel[max(-i,0):signalsize-i*(signalsize-kernelsize<i)], # E.g. at i=-50, [50:100]
        )
        # E.g. if kernel is size 100 and signal is size 1000 then the convolved
        #      signal has 1099 elements.
        for i in range(1-kernelsize,signalsize)                          # E.g. -99:1000
    ]

if __name__ == '__main__':
    import matplotlib.pyplot as plt

    show_dblexp = input('Show double exponential? ')
    if show_dblexp == 'y':

        amp = 1.0
        tau_rise = 3 # ms
        tau_decay = 30 # ms

        v = []
        t = []
        for i in range(0, 1000):
            t_i = 0.1*i # ms
            t.append(t_i)
            v.append(dblexp(amp, tau_rise, tau_decay, t_i))

        print('Max amplitude: '+str(max( [abs(max(v)), abs(min(v))] )) )
        plt.plot(t, v)
        plt.show()

    show_delayed_pulse_kernel = input('Show delayed pulse kernel? ')
    if show_delayed_pulse_kernel == 'y':

        amp = 1.0
        tau_rise = 3 # ms
        tau_decay = 30 # ms

        v = []
        t = []
        for i in range(0, 1000):
            t_i = 0.1*i # ms
            t.append(t_i)
            v.append(delayed_pulse(amp, tau_rise, tau_decay, t_i))

        print('Max amplitude: '+str(max( [abs(max(v)), abs(min(v))] )) )
        plt.plot(t, v)
        plt.show()

    show_pulse_convolved = input('Show impulse convolved with delayed square pulse kernel? ')
    if show_pulse_convolved == 'y':

        signal = np.zeros(1000)
        signal[4] = 1.0

        amp = 1.0
        tau_rise = 3 # ms
        tau_decay = 30 # ms

        v = []
        t = []
        for i in range(0, 1000):
            t_i = 0.1*i # ms
            t.append(t_i)
            v.append(delayed_pulse(amp, tau_rise, tau_decay, t_i))

        convolved = convolve_1d(signal, v)
        t = [ 0.1*t_i for t_i in range(len(convolved))]

        print('Max amplitude: '+str(max( [abs(max(convolved)), abs(min(convolved))] )) )
        plt.plot(t, convolved)
        plt.show()

    print('Demo of main application')
    # PRESETS
    fifosize = 100
    kernelsize = 80
    neuron_Vahp_mV = -20
    brightness_amplification = 5.0
    tau_rise = 3 # ms
    tau_decay = 30 # ms
    dt_ms = 1.0
    fluorescence_grabidx = -10

    # PREPARE KERNEL
    # show convolved
    amp = 1.0

    use_square_pulse = input('Use square pulse kernel (otherwise, double exponential)? ')

    v = []
    t = []
    sum_v = 0
    for i in range(0, kernelsize):
        t_i = dt_ms*i # ms
        t.append(t_i)
        if use_square_pulse == 'y':
            k_val = delayed_pulse(amp, tau_rise, tau_decay, t_i)
        else:
            k_val = dblexp(amp, tau_rise, tau_decay, t_i)
        v.append(k_val)
        sum_v += k_val
    v_np = (1/sum_v)*np.array(v)
    plt.plot(t, v_np)
    plt.title('Kernel, scaled to normalize convolution')
    plt.show()

    # EXAMPLE SIGNAL
    AP = np.array([-60, -60, -60, -46, -50, 0, -25, -50, -80, -77, -74, -71, -69, -67, -65, -64, -63, -62, -61, -60, ])
    Vdiff = AP - (-60.0)
    signal = np.zeros(1000)
    signal[len(signal)-len(Vdiff):len(signal)] = Vdiff
    # show signal
    t = [ dt_ms*t_i for t_i in range(len(Vdiff))]
    plt.plot(t, Vdiff)
    plt.title('Action potential difference from Vrest')
    plt.show()
    t = [ dt_ms*t_i for t_i in range(len(signal))]
    plt.plot(t, signal)
    plt.title('Signal as difference from Vrest')
    plt.show()

    # COLLECTED MEMBRANE FIFO
    # show fifo content
    fifo = signal[-fifosize:]  # This is in the order fifo[0] (head) is oldest fifo[-1] (tail) is newest.
    # TEST: Let's not reverse this and do a reversal of kernel (which if reversed back in convolve_1d)... casignal = -1.0*fifo[::-1]
    casignal = -1.0*fifo  # TESTING
    v_np = v_np[::-1]     # TESTING
    t = [ dt_ms*t_i for t_i in range(len(casignal))]
    plt.plot(t, casignal)
    plt.title('FIFO buffered diff potential, flipped and negated')
    plt.show()
    casignal[casignal < 0.0] = 0
    casignal = (1/abs(neuron_Vahp_mV)) * casignal
    plt.plot(t, casignal)
    plt.title('flipped and negated FIFO buffered diff potential, clipped at 0, normalized')
    plt.show()

    # CALCULATE NEURON FLUORESCENCE AND AMPLIFY TO VISIBLE COLOR LEVELS
    fluorescence = (255.0*brightness_amplification*np.array(convolve_1d(casignal, v_np))).astype(int)
    t = [ dt_ms*t_i for t_i in range(len(fluorescence))]
    # *** Because we have the newest at FIFO[0] now and we undo the reversal of the kernel,
    #     the fluorescence at onset is at fluorescence[-1], then we follow it back to fluorescence[0] over time.
    plt.plot(t, fluorescence)
    plt.title('Fluorescence: FIFO convolved with kernel, brightness amplified, pixel color')
    plt.show()

    # show value taken
    # Now, let's put the action potential in the middle of the signal, and let's roll the FIFO along the
    # signal and calculate fluorescence as we go.
    signal = np.zeros(1000)
    signal[500:500+len(Vdiff)] = Vdiff
    t = [ dt_ms*t_i for t_i in range(len(signal))]
    plt.plot(t, signal)
    plt.title('AP in middle of Vdiff signal')
    plt.show()

    # Rolling the FIFO over the signal:
    fifosize = len(fifo)
    fluorescence = []
    for t_ms in range(len(signal)-fifosize):
        fifo = signal[t_ms:t_ms+fifosize]
        casignal = -1.0*fifo
        casignal[casignal < 0.0] = 0
        casignal = (1/abs(neuron_Vahp_mV)) * casignal
        fluorescence_t = convolve_1d(casignal, v_np)
        fluorescence.append(255.0*brightness_amplification*fluorescence_t[fluorescence_grabidx])
    T = [ dt_ms*t_i for t_i in range(len(fluorescence))]
    plt.plot(T, fluorescence)
    plt.title('Fluorescence over time, as the signal evolves')
    plt.show()
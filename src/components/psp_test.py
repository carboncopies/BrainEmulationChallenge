import numpy as np
import matplotlib.pyplot as plt

# Simulation parameters
dt = 0.1  # ms
T = 200   # total time in ms
time = np.arange(0, T, dt)

# Neuron parameters
V_rest = -70.0  # mV
V_th = -54.0    # mV (not used here)
tau_m = 20.0    # ms
R_m = 10.0      # MΩ

# Synapse parameters
tau_s = 5.0     # ms for exponential and alpha
w = 1.0         # synaptic weight (arbitrary units)
E_rev = 0.0     # mV, excitatory reversal potential for conductance-based

# Presynaptic spike time
spike_time = 50.0  # ms

# Initialize variables
V_exp = np.full_like(time, V_rest)
V_alpha = np.full_like(time, V_rest)
V_cond = np.full_like(time, V_rest)

I_syn_exp = np.zeros_like(time)
I_syn_alpha = np.zeros_like(time)
g_syn_cond = np.zeros_like(time)

# Generate synaptic currents
for i, t in enumerate(time):
    if np.isclose(t, spike_time):
        I_syn_exp[i:] += w * np.exp(-(time[i:] - t) / tau_s)
        I_syn_alpha[i:] += w * ((time[i:] - t)/tau_s) * np.exp(1 - (time[i:] - t) / tau_s)
        g_syn_cond[i:] += w * np.exp(-(time[i:] - t) / tau_s)

# Simulate membrane voltage
for i in range(1, len(time)):
    dV_exp = (-(V_exp[i-1] - V_rest) + R_m * I_syn_exp[i]) * dt / tau_m
    dV_alpha = (-(V_alpha[i-1] - V_rest) + R_m * I_syn_alpha[i]) * dt / tau_m
    I_cond = g_syn_cond[i] * (E_rev - V_cond[i-1])
    dV_cond = (-(V_cond[i-1] - V_rest) + R_m * I_cond) * dt / tau_m

    V_exp[i] = V_exp[i-1] + dV_exp
    V_alpha[i] = V_alpha[i-1] + dV_alpha
    V_cond[i] = V_cond[i-1] + dV_cond

# Plot results
plt.figure(figsize=(10, 6))
plt.plot(time, V_exp, label='Exponential PSP (current-based)', lw=2)
plt.plot(time, V_alpha, label='Alpha function PSP (current-based)', lw=2)
plt.plot(time, V_cond, label='Conductance-based PSP', lw=2)
plt.axvline(spike_time, color='gray', linestyle='--', label='Spike time')
plt.title('Post-synaptic potential (PSP) shapes')
plt.xlabel('Time (ms)')
plt.ylabel('Membrane potential (mV)')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

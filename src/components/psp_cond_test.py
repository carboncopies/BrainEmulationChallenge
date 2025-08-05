import numpy as np
import matplotlib.pyplot as plt

# Simulation parameters
dt = 0.1  # ms
T = 200   # ms
time = np.arange(0, T, dt)

# Neuron parameters
V_rest = -70.0  # mV
tau_m = 20.0    # ms
R_m = 100.0      # MΩ

# Synaptic parameters
w = 1.0         # synaptic strength (scaling factor)
E_rev = 0.0     # reversal potential for excitatory synapse (mV)
tau_rise = 1.0  # ms
tau_decay = 5.0 # ms

# Presynaptic spike time
spike_time = 50.0  # ms

# Initialize membrane potential and conductance
V_cond = np.full_like(time, V_rest)
g_syn_cond = np.zeros_like(time)

# Compute double-exponential conductance trace
for i, t in enumerate(time):
    if t >= spike_time:
        t_rel = t - spike_time
        g_syn_cond[i] = w * (np.exp(-t_rel / tau_decay) - np.exp(-t_rel / tau_rise))

# Normalize peak to 1 for fair comparison
g_syn_cond /= np.max(g_syn_cond)

# Simulate membrane potential using conductance-based synapse
for i in range(1, len(time)):
    I_cond = g_syn_cond[i] * (E_rev - V_cond[i-1])  # driving current
    dV = (-(V_cond[i-1] - V_rest) + R_m * I_cond) * dt / tau_m
    V_cond[i] = V_cond[i-1] + dV

# Plot the conductance and resulting PSP
fig, ax = plt.subplots(2, 1, figsize=(10, 6), sharex=True)

ax[0].plot(time, g_syn_cond, label='Double-exponential conductance', color='teal')
ax[0].set_ylabel('Conductance (normalized)')
ax[0].legend()
ax[0].grid(True)

ax[1].plot(time, V_cond, label='Membrane potential (conductance-based)', color='navy')
ax[1].axvline(spike_time, color='gray', linestyle='--', label='Spike time')
ax[1].set_xlabel('Time (ms)')
ax[1].set_ylabel('Membrane potential (mV)')
ax[1].legend()
ax[1].grid(True)

plt.suptitle('Conductance-Based PSP with Double-Exponential Kernel')
plt.tight_layout()
plt.show()

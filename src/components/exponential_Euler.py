import numpy as np
import matplotlib.pyplot as plt

# Simulation parameters
dt = 1.0  # ms
T = 200  # total time in ms
time = np.arange(0, T, dt)
n_steps = len(time)

# Neuron parameters
C_m = 200.0  # pF
g_L = 10.0  # nS
E_L = -70.0  # mV
V_th = -50.0  # mV
V_reset = -65.0  # mV

# Synapse parameters
E_AMPA = 0.0   # mV
E_GABA = -80.0 # mV
tau_rise_AMPA, tau_decay_AMPA = 0.5, 2.0  # ms
tau_rise_GABA, tau_decay_GABA = 1.0, 10.0  # ms
g_peak_AMPA = 1.0  # nS
g_peak_GABA = 1.5  # nS
weight_AMPA = 0.5
weight_GABA = 0.5

# AHP parameters (modeled as conductance)
E_AHP = -90.0  # mV
tau_rise_AHP, tau_decay_AHP = 2.0, 20.0  # ms
g_peak_AHP = 2.0  # nS

# Initialize variables
V = np.zeros(n_steps)
V[0] = E_L
g_AMPA = np.zeros(n_steps)
g_GABA = np.zeros(n_steps)
g_AHP = np.zeros(n_steps)
spikes = []

# Precompute normalization constants for double-exponential kernels
def k_norm(tau_rise, tau_decay):
    t_peak = (tau_rise * tau_decay) / (tau_decay - tau_rise) * np.log(tau_decay / tau_rise)
    return 1.0 / (np.exp(-t_peak / tau_decay) - np.exp(-t_peak / tau_rise))

k_AMPA = k_norm(tau_rise_AMPA, tau_decay_AMPA)
k_GABA = k_norm(tau_rise_GABA, tau_decay_GABA)
k_AHP = k_norm(tau_rise_AHP, tau_decay_AHP)

# Example input spikes
input_spike_times = [20, 50, 80, 110, 150]

for t_idx in range(1, n_steps):
    t = time[t_idx]

    # Add synaptic conductance for input spikes
    if any(np.isclose(t, s, atol=0.1) for s in input_spike_times):
        g_AMPA[t_idx] += weight_AMPA * g_peak_AMPA * k_AMPA
        g_GABA[t_idx] += weight_GABA * g_peak_GABA * k_GABA

    # Add AHP conductance after spikes
    if (t_idx - 1) in spikes:
        g_AHP[t_idx] += g_peak_AHP * k_AHP

    # Update synaptic conductances (double exponential)
    g_AMPA[t_idx] += g_AMPA[t_idx-1] * np.exp(-dt / tau_decay_AMPA) - g_AMPA[t_idx-1] * np.exp(-dt / tau_rise_AMPA)
    g_GABA[t_idx] += g_GABA[t_idx-1] * np.exp(-dt / tau_decay_GABA) - g_GABA[t_idx-1] * np.exp(-dt / tau_rise_GABA)
    g_AHP[t_idx] += g_AHP[t_idx-1] * np.exp(-dt / tau_decay_AHP) - g_AHP[t_idx-1] * np.exp(-dt / tau_rise_AHP)

    # Total conductance and reversal potential
    g_total = g_L + g_AMPA[t_idx] + g_GABA[t_idx] + g_AHP[t_idx]
    E_total = (g_L * E_L + g_AMPA[t_idx] * E_AMPA +
               g_GABA[t_idx] * E_GABA + g_AHP[t_idx] * E_AHP) / g_total

    tau_eff = C_m / g_total
    V[t_idx] = E_total + (V[t_idx-1] - E_total) * np.exp(-dt / tau_eff)

    # Spike threshold
    if V[t_idx] >= V_th:
        V[t_idx] = V_reset
        spikes.append(t_idx)

# Plotting
plt.figure(figsize=(10, 6))
plt.subplot(2,1,1)
plt.plot(time, V, label='Membrane potential (V_m)')
plt.ylabel('V_m (mV)')
plt.title('IF Neuron with Exponential Euler Integration')
plt.axhline(V_th, color='gray', linestyle='--', label='Threshold')
plt.legend()

plt.subplot(2,1,2)
plt.plot(time, g_AMPA, label='g_AMPA')
plt.plot(time, g_GABA, label='g_GABA')
plt.plot(time, g_AHP, label='g_AHP')
plt.ylabel('Conductance (nS)')
plt.xlabel('Time (ms)')
plt.legend()

plt.tight_layout()
plt.show()

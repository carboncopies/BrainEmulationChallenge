import numpy as np
import matplotlib.pyplot as plt

# Simulation parameters
dt = 0.1  # ms
T = 500  # total simulation time in ms
time = np.arange(0, T, dt)
n_steps = len(time)

# Neuron parameters
V_rest = -70  # mV
V_th = -50    # spike threshold mV
V_reset = -65  # mV after spike
tau_m = 20     # ms
R_m = 100  # MΩ
refractory_period = 2  # ms was 5
refractory_steps = int(refractory_period / dt)

# Reversal potentials (mV)
E_AMPA = 0
E_NMDA = 0
E_GABA = -70
E_AHP = -90
E_ADP = -20

# Synaptic conductance parameters
def double_exp_kernel(t, tau_rise, tau_decay):
    return (np.exp(-t / tau_decay) - np.exp(-t / tau_rise)) * (t >= 0)

def single_exp_kernel(t, tau):
    return np.exp(-t / tau) * (t >= 0)

# Time constants (ms)
tau_rise_AMPA, tau_decay_AMPA = 0.5, 3
tau_rise_NMDA, tau_decay_NMDA = 2, 100
tau_rise_GABA, tau_decay_GABA = 0.5, 10
tau_AHP = 150 # was 200
tau_ADP = 120 # was 100

# Synaptic event times (ms)
syn_times_AMPA = [100, 200, 300, 400]
syn_times_NMDA = [100, 200, 300, 400]
syn_times_GABA = [150, 250, 350]

# Spike-triggered conductance increments
delta_g_AMPA = 0.5
delta_g_NMDA = 0.2
delta_g_GABA = 0.3
delta_g_AHP = 1.0
delta_g_ADP = 0.3

# Initialize variables
V = np.zeros(n_steps)
V[0] = V_rest
spike_train = np.zeros(n_steps, dtype=bool)
last_spike_idx = -np.inf

# Conductance arrays
g_AMPA = np.zeros(n_steps)
g_NMDA = np.zeros(n_steps)
g_GABA = np.zeros(n_steps)
g_AHP = np.zeros(n_steps)
g_ADP = np.zeros(n_steps)

# Generate synaptic conductance traces
kernel_len = int(300 / dt)
t_kernel = np.arange(0, kernel_len) * dt

def add_kernel_to_trace(trace, spike_times, kernel, delta_g):
    for t_spike in spike_times:
        idx = int(t_spike / dt)
        end_idx = min(idx + kernel_len, n_steps)
        kernel_len_adjusted = end_idx - idx
        trace[idx:end_idx] += delta_g * kernel[:kernel_len_adjusted]

add_kernel_to_trace(g_AMPA, syn_times_AMPA, double_exp_kernel(t_kernel, tau_rise_AMPA, tau_decay_AMPA), delta_g_AMPA)
add_kernel_to_trace(g_NMDA, syn_times_NMDA, double_exp_kernel(t_kernel, tau_rise_NMDA, tau_decay_NMDA), delta_g_NMDA)
add_kernel_to_trace(g_GABA, syn_times_GABA, double_exp_kernel(t_kernel, tau_rise_GABA, tau_decay_GABA), delta_g_GABA)

# Simulate
for i in range(1, n_steps):
    if i - last_spike_idx < refractory_steps:
        V[i] = V_reset
        continue

    I_syn = (
        g_AMPA[i] * (V[i-1] - E_AMPA) +
        g_NMDA[i] * (V[i-1] - E_NMDA) +
        g_GABA[i] * (V[i-1] - E_GABA) +
        g_AHP[i] * (V[i-1] - E_AHP) +
        g_ADP[i] * (V[i-1] - E_ADP)
    )
    dV = (-(V[i-1] - V_rest) + R_m * (-I_syn)) * dt / tau_m
    V[i] = V[i-1] + dV

    if V[i] >= V_th:
        V[i] = V_reset
        spike_train[i] = True
        last_spike_idx = i
        g_AHP[i:min(i+kernel_len, n_steps)] += delta_g_AHP * single_exp_kernel(t_kernel, tau_AHP)[:n_steps-i]
        g_ADP[i:min(i+kernel_len, n_steps)] += delta_g_ADP * single_exp_kernel(t_kernel, tau_ADP)[:n_steps-i]

# Plotting
fig, axs = plt.subplots(2, 1, figsize=(12, 7), sharex=True)

axs[0].plot(time, V, label="Membrane Voltage (mV)")
axs[0].scatter(time[spike_train], V[spike_train], color='red', label='Spikes', zorder=5)
axs[0].axhline(V_th, color='gray', linestyle='--', label='Threshold')
axs[0].set_ylabel("Voltage (mV)")
axs[0].legend()
axs[0].grid(True)

axs[1].plot(time, g_AMPA, label="AMPA", alpha=0.8)
axs[1].plot(time, g_NMDA, label="NMDA", alpha=0.8)
axs[1].plot(time, g_GABA, label="GABA", alpha=0.8)
axs[1].plot(time, g_AHP, label="AHP", linestyle='--', alpha=0.8)
axs[1].plot(time, g_ADP, label="ADP", linestyle='--', alpha=0.8)
axs[1].set_ylabel("Conductance (nS)")
axs[1].set_xlabel("Time (ms)")
axs[1].legend()
axs[1].grid(True)

plt.suptitle("IF Neuron: Membrane Response and Synaptic Inputs")
plt.tight_layout()
plt.show()

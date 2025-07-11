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
refractory_period = 2  # ms
refractory_steps = int(refractory_period / dt)

# Reversal potentials (mV)
E_AMPA = 0
E_NMDA = 0
E_GABA = -70
E_AHP = -90
E_ADP = -20

# Synaptic parameters
tau_rise_AMPA, tau_decay_AMPA = 0.5, 3
tau_rise_NMDA, tau_decay_NMDA = 2, 100
tau_rise_GABA, tau_decay_GABA = 0.5, 10

tau_rise_AHP, tau_decay_AHP = 5, 150 # was 10, 150
tau_rise_ADP, tau_decay_ADP = 20, 200

# Synaptic event times (ms)
syn_times_AMPA = [100, 200, 300, 400]
syn_times_NMDA = [100, 200, 300, 400]
syn_times_GABA = [150, 250, 350]

# Number of receptors on excitatory synapse
num_AMPA = 50
num_NMDA = 10

# Number of receptors on inhibitory synapse
num_GABA = 10

# per-receptor peak conductance
g_rec_peak_AMPA = 20e-3 # 20 pS
g_rec_peak_NMDA = 50e-3/2 # 50 pS adjusted for open-probability
g_rec_peak_GABA = 30e-3 # 30 pS

# Conductance peak values and weights
g_peak_AMPA = num_AMPA * g_rec_peak_AMPA
g_peak_NMDA = num_NMDA * g_rec_peak_NMDA
g_peak_GABA = 0.8
print('AMPA peak conductance (nS): '+str(g_peak_AMPA))
print('NMDA peak conductance (nS): '+str(g_peak_NMDA))
print('GABA peak conductance (nS): '+str(g_peak_GABA))

weight_AMPA = 0.5
weight_NMDA = 0.5
weight_GABA = 0.5

g_peak_AHP = 1.0  # nS
g_peak_ADP = 0.3  # nS

# Initialize variables
V = np.zeros(n_steps)
V[0] = V_rest
spike_train = np.zeros(n_steps, dtype=bool)
last_spike_idx = -np.inf

g_AMPA = np.zeros(n_steps)
g_NMDA = np.zeros(n_steps)
g_GABA = np.zeros(n_steps)
g_AHP = np.zeros(n_steps)
g_ADP = np.zeros(n_steps)

# Kernel generation
kernel_len = int(300 / dt)
t_kernel = np.arange(0, kernel_len) * dt

def compute_normalization(tau_rise, tau_decay):
    if tau_rise == tau_decay:
        raise ValueError("tau_rise must be different from tau_decay for normalization.")
    t_peak = (tau_rise * tau_decay) / (tau_decay - tau_rise) * np.log(tau_decay / tau_rise)
    norm = np.exp(-t_peak / tau_decay) - np.exp(-t_peak / tau_rise)
    return norm

def g_norm(t, spike_times, tau_rise, tau_decay, norm):
    """Compute total synaptic conductance at time t from all spikes."""
    gnorm = 0
    for ts in spike_times:
        spike_dt = t - ts
        if spike_dt >= 0:
            gnorm += (np.exp(-spike_dt / tau_decay) - np.exp(-spike_dt / tau_rise)) / norm
    return gnorm

# Pre-calculate normalizations
norm_AMPA = compute_normalization(tau_rise_AMPA, tau_decay_AMPA)
norm_NMDA = compute_normalization(tau_rise_NMDA, tau_decay_NMDA)
norm_GABA = compute_normalization(tau_rise_GABA, tau_decay_GABA)
print('norm_AMPA: '+str(norm_AMPA))
print('norm_NMDA: '+str(norm_NMDA))
print('norm_GABA: '+str(norm_GABA))

norm_AHP = compute_normalization(tau_rise_AHP, tau_decay_AHP)
norm_ADP = compute_normalization(tau_rise_ADP, tau_decay_ADP)
print('norm_AHP: '+str(norm_AHP))
print('norm_ADP: '+str(norm_ADP))


# Simulation loop
t = 0
t_postspikes = []
t_last_spike = -1000
for i in range(1, n_steps):

    g_AMPA[i] = weight_AMPA * g_peak_AMPA * g_norm(t, syn_times_AMPA, tau_rise_AMPA, tau_decay_AMPA, norm_AMPA)
    g_NMDA[i] = weight_NMDA * g_peak_NMDA * g_norm(t, syn_times_NMDA, tau_rise_NMDA, tau_decay_NMDA, norm_NMDA)
    g_GABA[i] = weight_GABA * g_peak_GABA * g_norm(t, syn_times_GABA, tau_rise_GABA, tau_decay_GABA, norm_GABA)

    g_AHP[i] = g_peak_AHP * g_norm(t, t_postspikes, tau_rise_AHP, tau_decay_AHP, norm_AHP)
    g_ADP[i] = g_peak_ADP * g_norm(t, t_postspikes, tau_rise_ADP, tau_decay_ADP, norm_ADP)

    if t < (t_last_spike+refractory_period):
        V[i] = V_reset
        t += dt
        continue

    I = (
        g_AMPA[i] * (V[i-1] - E_AMPA) +
        g_NMDA[i] * (V[i-1] - E_NMDA) +
        g_GABA[i] * (V[i-1] - E_GABA) +
        g_AHP[i] * (V[i-1] - E_AHP) +
        g_ADP[i] * (V[i-1] - E_ADP)
    )

    dV = (-(V[i-1] - V_rest) + R_m * (-I)) * dt / tau_m
    V[i] = V[i-1] + dV

    if V[i] >= V_th:
        V[i] = V_reset
        spike_train[i] = True
        last_spike_idx = i
        t_last_spike = t
        t_postspikes.append(t_last_spike)

    t += dt

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

plt.suptitle("IF Neuron: Membrane Response with Normalized Synaptic Kernels")
plt.tight_layout()
plt.show()

import numpy as np
import matplotlib.pyplot as plt

# Time vector
t = np.linspace(0, 100, 1000)  # ms

# Receptor parameters
receptors = {
    'AMPA': {'tau_rise': 0.5, 'tau_decay': 2.0, 'g_peak': 0.5},    # in nS
    'NMDA': {'tau_rise': 2.0, 'tau_decay': 100.0, 'g_peak': 0.8},
    'GABA': {'tau_rise': 0.5, 'tau_decay': 10.0, 'g_peak': 0.6}
}
E_syn = {'AMPA': 0.0, 'NMDA': 0.0, 'GABA': -70.0}  # reversal potentials (mV)
V_m = -65.0  # membrane potential (mV)
weight = 0.5  # all weights set to 0.5

def compute_normalization(tau_rise, tau_decay):
    t_peak = (tau_rise * tau_decay) / (tau_decay - tau_rise) * np.log(tau_decay / tau_rise)
    norm = np.exp(-t_peak / tau_decay) - np.exp(-t_peak / tau_rise)
    return norm

def normalized_kernel(t, tau_rise, tau_decay, norm):
    kernel = (np.exp(-t / tau_decay) - np.exp(-t / tau_rise)) / norm
    kernel[t < 0] = 0  # Heaviside step
    return kernel

# Initialize plots
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

# Plot normalized conductance kernels and resulting synaptic currents
for name, params in receptors.items():
    tau_rise = params['tau_rise']
    tau_decay = params['tau_decay']
    g_peak = params['g_peak']
    norm = compute_normalization(tau_rise, tau_decay)
    kernel = normalized_kernel(t, tau_rise, tau_decay, norm)
    g = weight * g_peak * kernel
    I_syn = g * (V_m - E_syn[name])  # Ohm's law: I = g * (V - E)

    ax1.plot(t, kernel, label=f'{name}')
    ax2.plot(t, I_syn, label=f'{name}')

# Labels and legends
ax1.set_title('Normalized Synaptic Conductance Kernels')
ax1.set_ylabel('Normalized g(t)')
ax1.legend()
ax1.grid(True)

ax2.set_title('Synaptic Currents with g_peak and weight = 0.5')
ax2.set_xlabel('Time (ms)')
ax2.set_ylabel('I_syn (nA)')
ax2.legend()
ax2.grid(True)

plt.tight_layout()
plt.show()

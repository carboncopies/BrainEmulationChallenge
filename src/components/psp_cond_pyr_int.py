import numpy as np
import matplotlib.pyplot as plt

def double_exp_kernel(t, tau_rise, tau_decay):
    """
    Return normalized double exponential kernel: (exp(-t/tau_decay) - exp(-t/tau_rise))
    Normalized to peak at 1.0.
    """
    g = np.exp(-t / tau_decay) - np.exp(-t / tau_rise)
    g[t < 0] = 0  # Ensure causality
    peak = np.max(g)
    if peak > 0:
        g /= peak
    return g

# Time vector in ms
t = np.linspace(0, 300, 1000)

# Define kernels and their time constants
receptors = {
    "AMPA":     (0.4, 4),
    "NMDA-fast": (3, 80),
    "NMDA-slow": (7, 200),
    "GABA_A":   (0.5, 10),
}

# Plot each kernel
plt.figure(figsize=(10, 6))
for name, (tau_rise, tau_decay) in receptors.items():
    g = double_exp_kernel(t, tau_rise, tau_decay)
    plt.plot(t, g, label=f"{name} (τr={tau_rise} ms, τd={tau_decay} ms)")

plt.title("Normalized Synaptic Conductance Kernels (Double Exponential)")
plt.xlabel("Time (ms)")
plt.ylabel("Normalized Conductance")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

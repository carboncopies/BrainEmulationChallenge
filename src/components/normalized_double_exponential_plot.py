import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # registers the 3D projection

def compute_normalization(tau_rise, tau_decay):
    if np.any(tau_rise == tau_decay):
        raise ValueError("tau_rise must be different from tau_decay for normalization.")
    t_peak = (tau_rise * tau_decay) / (tau_decay - tau_rise) * np.log(tau_decay / tau_rise)
    norm = np.exp(-t_peak / tau_decay) - np.exp(-t_peak / tau_rise)
    return norm

# 1) define your parameter ranges
spike_dts   = np.linspace(0.1, 5.0, 25)   # e.g. 0.1–5 ms
tau_rises   = np.linspace(0.5, 5.0, 25)   # e.g. 0.5–5 ms
tau_decays  = np.linspace(1.0, 10.0, 25)  # e.g. 1–10 ms

# 2) build a 3D grid of all combinations
SD, TR, TD = np.meshgrid(spike_dts, tau_rises, tau_decays, indexing='ij')

# 3) flatten for vectorized computation
sd = SD.ravel()
tr = TR.ravel()
td = TD.ravel()

# 4) compute normalized output for each triplet
norm = compute_normalization(tr, td)
g_norm = np.exp(-sd/td) - np.exp(-sd/tr)
out = g_norm / norm

# 5) mask out any invalid points (e.g. tau_rise == tau_decay)
valid = tr != td
sd = sd[valid]
tr = tr[valid]
td = td[valid]
out = out[valid]

# 6) plot
fig = plt.figure(figsize=(8,6))
ax = fig.add_subplot(111, projection='3d')

sc = ax.scatter(tr, td, sd,
                c=out,
                cmap='viridis',
                marker='o',
                s=20,
                alpha=0.8)

fig.colorbar(sc, ax=ax, label='normalized PSP amplitude')
ax.set_xlabel('tau_rise (ms)')
ax.set_ylabel('tau_decay (ms)')
ax.set_zlabel('spike_dt (ms)')
ax.set_title('Output landscape vs. spike_dt, tau_rise & tau_decay')

plt.tight_layout()
plt.show()

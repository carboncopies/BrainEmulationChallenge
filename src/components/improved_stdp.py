import numpy as np
import matplotlib.pyplot as plt

# Time difference range (ms)
dt = np.linspace(-50, 50, 1000)

# Continuous symmetric STDP window (original)
def stdp_symmetric(dt, A=0.01, tau=20):
    return A * dt / tau * np.exp(-np.abs(dt) / tau)

# Shifted and steeper version of the symmetric STDP
def stdp_shifted(dt, A=0.02, tau=10, shift=-2):
    dt_shifted = dt - shift
    return A * dt_shifted / tau * np.exp(-np.abs(dt_shifted) / tau)

# Shifted and steeper version of the symmetric STDP
def stdp_shifted_two_part(dt, Apos=0.027, Aneg=0.02, taupos=7, tauneg=7, shift=-4):
    out = np.zeros(dt.shape)
    dt_shifted = dt - shift
    for i in range(len(dt_shifted)):
        dt_i = dt_shifted[i]
        if dt_i >= 0:
            dtdivtaupos = dt_i / taupos
            out[i] = Apos * dtdivtaupos * np.exp(-dtdivtaupos)
        else:
            dtdivtauneg = dt_i / tauneg
            out[i] = Aneg * dtdivtauneg * np.exp(dtdivtauneg)
    return out


# Compute values
#dw_original = stdp_symmetric(dt)
#dw_shifted = stdp_shifted(dt)
#dw_shifted2 = stdp_shifted(dt, A=0.027, tau=7, shift = -4)
dw_twopart = stdp_shifted_two_part(dt)

# Plot
plt.figure(figsize=(10, 6))
#plt.plot(dt, dw_original, label='Continuous Symmetric STDP', linestyle='--')
#plt.plot(dt, dw_shifted, label='A=0.02, tau=10 ms, shift=-2 ms', linestyle='-')
#plt.plot(dt, dw_shifted2, label='A=0.027, tau=7 ms, shift=-4 ms', linestyle='-')
plt.plot(dt, dw_twopart, label='A+=0.027, A-=0.02, tau+=7 ms, tau-=7 ms, shift=-4 ms', linestyle='-')
plt.axhline(0, color='gray', linewidth=0.8)
plt.axvline(0, color='gray', linewidth=0.8)
plt.title("STDP Learning Windows")
plt.xlabel("Δt (ms) = t_post - t_pre")
plt.ylabel("Δw (synaptic change)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

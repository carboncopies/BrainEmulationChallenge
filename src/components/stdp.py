import numpy as np

def stdp_update(dt, A_pos=0.005, A_neg=0.005, tau_pos=20.0, tau_neg=20.0):
    """
    Computes the synaptic weight change using an exponential STDP rule.

    Parameters:
    - dt: float or np.ndarray
        Time difference(s) between post- and presynaptic spikes (post - pre), in milliseconds.
    - A_pos: float
        Amplitude of potentiation (LTP).
    - A_neg: float
        Amplitude of depression (LTD).
    - tau_pos: float
        Time constant for potentiation (LTP), in milliseconds.
    - tau_neg: float
        Time constant for depression (LTD), in milliseconds.

    Returns:
    - dw: float or np.ndarray
        Change in synaptic weight(s).
    """
    dt = np.asarray(dt)
    dw = np.where(
        dt > 0,
        A_pos * np.exp(-dt / tau_pos),
        -A_neg * np.exp(dt / tau_neg)
    )
    return dw

# Time difference between post- and presynaptic spikes
dts = np.linspace(-50, 50, 1000)  # ms

# Compute weight changes
dw = stdp_update(dts, A_pos=0.01, A_neg=0.01, tau_pos=20, tau_neg=20)

# Plot (optional)
import matplotlib.pyplot as plt

plt.plot(dts, dw)
plt.axhline(0, color='black', linestyle='--')
plt.xlabel("Post - Pre Spike Time (ms)")
plt.ylabel("Δw (Synaptic Change)")
plt.title("STDP Curve")
plt.grid(True)
plt.show()

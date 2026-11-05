"""dp_codec.py: encoder and decoder for the spiking double-pendulum controller.

Kept separate from the network so either side can be swapped (the NES harness in
~/pendulum_work/harness/pend_nes_harness.py has the same shape: Encoder.spike_trains(state)
-> input trains per window, Decoder.decode(n_a, n_b) -> force). Differences from that
harness: this encoder is DIFFERENTIAL, not rectified (see below), and its per-variable
ranges come from the closed-loop statistics in weights_recipe.json.

Encoder: each state variable i has a 'pos' and a 'neg' population of n_in neurons. Their
common rate is
    r_pos = r0 + g_i s_i,   r_neg = r0 - g_i s_i,   clipped to [0, 2 r0],  g_i = r0 / range_i.
Because r0 is a baseline, pos and neg together carry s_i linearly and each output side
receives exactly one of the pair (excitatory routing only). Spikes are REGULAR (a phase
accumulator per input neuron, stratified phases, integer-ms grid, phase carried across
ticks) which is what SetSpecificAPTimes can deliver. Decoder: force = c (n_push - n_pull),
clipped to +/-F_max.
"""
import numpy as np


class DifferentialEncoder:
    def __init__(self, ranges, r0_hz, n_in, seed=0, dt_ms=1.0):
        self.ranges = np.asarray(ranges, float)
        self.r0 = float(r0_hz)
        self.g = self.r0 / self.ranges          # Hz per unit state
        self.n_in = int(n_in)
        self.dt = dt_ms
        self.rng = np.random.default_rng(seed)
        # populations 0-5 pos, 6-11 neg. Phases are evenly spaced within a population (plus one
        # seeded random offset per population): all neurons of a population share one rate so the
        # spacing is kept for ever and the population spike count is exact to about one spike.
        u = self.rng.random((12, 1))
        self.phase = (np.arange(self.n_in)[None, :] + u) / self.n_in
        self.n_clipped = 0
        self.n_calls = 0

    def rates(self, s, clip=True):
        s = np.asarray(s, float)
        d = self.g * s
        r = np.concatenate([self.r0 + d, self.r0 - d])
        if clip:
            self.n_calls += 1
            self.n_clipped += int((np.abs(d) > self.r0).any())
            r = np.clip(r, 0.0, 2 * self.r0)
        return r

    def spike_trains(self, s, steps):
        """bool array (12*n_in, steps): spike of input neuron j in ms-step t."""
        r = self.rates(s)
        inc = (r * self.dt * 1e-3)[:, None]
        out = np.zeros((12, self.n_in, steps), bool)
        for t in range(steps):
            self.phase += inc
            f = self.phase >= 1.0
            out[:, :, t] = f
            self.phase -= f
        return out.reshape(12 * self.n_in, steps)


class CountDecoder:
    def __init__(self, c_N_per_spike, f_max=20.0):
        self.c = float(c_N_per_spike)
        self.f_max = float(f_max)

    def decode(self, n_push, n_pull):
        return float(np.clip(self.c * (n_push - n_pull), -self.f_max, self.f_max))

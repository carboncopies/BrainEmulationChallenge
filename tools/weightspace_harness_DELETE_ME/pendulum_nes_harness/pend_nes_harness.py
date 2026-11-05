#!/usr/bin/env python3
"""pend_nes_harness.py: spiking-controller harness for the cart + double pendulum.

Pieces (README.md maps each one onto the Pong code in pong_netmorph):
  Encoder      6-dim state -> input spike trains, signed population code
  Decoder      (push-left, push-right) spike counts per window -> force in N, capped at F_MAX_N
  ControlLoop  encoder -> network -> decoder, with a pluggable 6-input weight vector W
  LIFStandIn   pure-Python LIF pair of output groups, for smoke tests without NES

Pure stdlib. Nothing here starts, stops or talks to NES.
"""
import math

CONTROL_WINDOW_MS = 10
F_MAX_N = 20.0
STATE_DIM = 6
N_POP = 8                  # neurons per (variable, sign) group
R_MAX_HZ = 200.0           # input rate at encoder value |z| = 1
N_FULL_COUNTS = 100        # net spikes per window that decode to F_MAX_N
N_OUT = 32                 # neurons per output group in the stand-in
REFRACTORY_MS = 2.0

# LQR row from crosscheck.py output (demo only; the harness does not import crosscheck)
K_LQR_DEMO = [3.1623, -174.5504, 240.6806, 7.7604, -1.3573, 31.1108]
SCALES_DEMO = [0.5, 0.2, 0.2, 1.0, 2.0, 2.0]   # expected operating envelope per variable


class Encoder:
    """Signed population code.

    z_i = clip(state_i / scale_i, -1, 1). Group (i, +) carries max(z_i, 0), group (i, -) carries max(-z_i, 0).
    Each group has n_pop neurons with hat-shaped tuning on [0, 1], centres c_k = (k+1)/n_pop.
    The hats interpolate the identity, so sum_k c_k * rate_k / r_max == the group's value exactly.
    Input index = (i * 2 + sign) * n_pop + k, sign 0 = positive group, 1 = negative group.
    """

    def __init__(self, scales, n_pop=N_POP, r_max_hz=R_MAX_HZ, window_ms=CONTROL_WINDOW_MS):
        assert len(scales) == STATE_DIM and all(s > 0 for s in scales)
        self.scales = list(scales)
        self.n_pop = n_pop
        self.r_max = r_max_hz
        self.window_ms = window_ms
        self.centres = [(k + 1) / n_pop for k in range(n_pop)]
        self.n_inputs = STATE_DIM * 2 * n_pop
        self.phase = [0.0] * self.n_inputs    # fractional spikes carried between windows
        self.n_clipped = 0

    def z_of(self, state):
        zs = []
        for s, sc in zip(state, self.scales):
            z = s / sc
            if abs(z) > 1.0:
                self.n_clipped += 1
                z = max(-1.0, min(1.0, z))
            zs.append(z)
        return zs

    def rates(self, state):
        """Rate in Hz for every input neuron, in index order."""
        h = 1.0 / self.n_pop
        out = []
        for z in self.z_of(state):
            for zz in (max(z, 0.0), max(-z, 0.0)):
                for c in self.centres:
                    out.append(self.r_max * max(0.0, 1.0 - abs(zz - c) / h))
        return out

    def spike_trains(self, state):
        """Integer-ms spike times (relative to window start) for every input neuron, one control window."""
        T = self.window_ms
        trains = []
        for n, r in enumerate(self.rates(state)):
            self.phase[n] += r * T / 1000.0
            count = int(self.phase[n])
            self.phase[n] -= count
            trains.append([int((j + 0.5) * T / count) for j in range(count)])
        return trains


class Decoder:
    """Net spike count (right minus left) per window -> force in N, clipped to +/- f_max.
    Positive force pushes the cart to +x (same sign convention as F = -K s in crosscheck.py)."""

    def __init__(self, n_full_counts=N_FULL_COUNTS, f_max=F_MAX_N):
        self.n_per_count = f_max / n_full_counts
        self.f_max = f_max
        self.n_capped = 0

    def decode(self, n_left, n_right):
        f = self.n_per_count * (n_right - n_left)
        if abs(f) > self.f_max:
            self.n_capped += 1
            f = math.copysign(self.f_max, f)
        return f


def weights_from_gain(K, scales, gain, n_per_count):
    """W[i] in counts per unit encoder value z_i, so that n_per_count * (n_right - n_left) = -gain * K.s
    when no clipping happens. K is the 1x6 LQR row (list of 6)."""
    return [-gain * K[i] * scales[i] / n_per_count for i in range(STATE_DIM)]


def synapse_routes(W, enc):
    """Per input index: (side, weight per input spike), side 'L' or 'R'.

    W >= 0: positive group -> R, negative group -> L. W < 0: the other way round.
    Weight per spike = |W_i| * c_k / (r_max * T), so the expected net drive from group (i, sign) is |W_i| * z_group.
    Net drive R minus L equals sum_i W_i * z_i."""
    T_s = enc.window_ms / 1000.0
    routes = []
    for i in range(STATE_DIM):
        pos_side = 'R' if W[i] >= 0 else 'L'
        neg_side = 'L' if pos_side == 'R' else 'R'
        for side in (pos_side, neg_side):
            for c in enc.centres:
                routes.append((side, abs(W[i]) * c / (enc.r_max * T_s)))
    return routes


class LIFStandIn:
    """Pure-Python LIF pair (push-left, push-right), n_out neurons per side.

    Membrane: dv/dt = (v_rest - v) / tau_m, plus a jump of weight * jump_mv for each input spike.
    Thresholds are spread over th_spread_mv so the neurons do not fire in lockstep.
    Not a model of NES. It checks routing and decoding, not calibration."""

    def __init__(self, n_out=N_OUT, dt_ms=0.5, tau_m_ms=20.0, v_rest=-70.0, v_reset=-70.0, v_th=-50.0,
                 t_ref_ms=REFRACTORY_MS, jump_mv=1.0, th_spread_mv=2.0):
        self.n_out = n_out
        self.dt = dt_ms
        self.tau = tau_m_ms
        self.v_rest = v_rest
        self.v_reset = v_reset
        self.t_ref = t_ref_ms
        self.jump_mv = jump_mv
        per_side = [v_th + th_spread_mv * j / max(1, n_out - 1) for j in range(n_out)]
        self.th = per_side + per_side
        self.v = [v_rest] * (2 * n_out)
        self.ref = [0.0] * (2 * n_out)
        self.routes = None

    def set_routes(self, routes):
        self.routes = routes

    def run_window(self, trains, window_ms):
        """trains[idx] = spike times (ms, relative to window start). Returns (n_left, n_right)."""
        n_steps = int(round(window_ms / self.dt))
        events = [[] for _ in range(n_steps)]
        for idx, times in enumerate(trains):
            for t in times:
                step = int(round(t / self.dt))
                if 0 <= step < n_steps:
                    events[step].append(idx)
        counts = [0, 0]
        for step in range(n_steps):
            for idx in events[step]:
                side, w = self.routes[idx]
                base = 0 if side == 'L' else self.n_out
                jump = w * self.jump_mv
                for j in range(base, base + self.n_out):
                    self.v[j] += jump
            for n in range(2 * self.n_out):
                if self.ref[n] > 0.0:
                    self.ref[n] -= self.dt
                    continue
                self.v[n] += self.dt / self.tau * (self.v_rest - self.v[n])
                if self.v[n] >= self.th[n]:
                    self.v[n] = self.v_reset
                    self.ref[n] = self.t_ref
                    counts[n // self.n_out] += 1
        return counts[0], counts[1]


class ControlLoop:
    """Encoder -> network -> decoder once per control window. W is the pluggable 6-input weight vector."""

    def __init__(self, encoder, decoder, network, W):
        self.enc = encoder
        self.dec = decoder
        self.net = network
        self.set_weights(W)

    def set_weights(self, W):
        assert len(W) == STATE_DIM, 'W must have 6 entries (one per state variable)'
        self.W = list(W)
        self.net.set_routes(synapse_routes(self.W, self.enc))

    def step(self, state):
        trains = self.enc.spike_trains(state)
        n_left, n_right = self.net.run_window(trains, self.enc.window_ms)
        return self.dec.decode(n_left, n_right)


class StubPlant:
    """Kinematic stand-in for smoke tests. Thetas follow a fixed sinusoid, the cart is a 1 kg free mass driven by F."""

    def __init__(self):
        self.t = 0.0
        self.s = [0.0, 0.02, 0.0, 0.0, 0.0, 0.0]

    def state(self):
        return list(self.s)

    def apply(self, F, dt):
        self.t += dt
        self.s[3] += F * dt
        self.s[0] += self.s[3] * dt
        self.s[1] = 0.02 * math.sin(math.pi * self.t)
        self.s[4] = 0.02 * math.pi * math.cos(math.pi * self.t)


def selftest(K, scales):
    """Checks decode and routing identities with no network. Raises AssertionError on failure."""
    enc = Encoder(scales)
    dec = Decoder()
    W = weights_from_gain(K, scales, 1.0, dec.n_per_count)
    routes = synapse_routes(W, enc)
    T_s = enc.window_ms / 1000.0
    for state in ([0.1 * sc for sc in scales], [-0.37 * scales[0], 0.5 * scales[1], -0.9 * scales[2], 0.0, 0.2 * scales[4], -0.05 * scales[5]], [0.0] * STATE_DIM):
        zs = enc.z_of(state)
        rates = enc.rates(state)
        for i in range(STATE_DIM):
            for sign, zz in ((0, max(zs[i], 0.0)), (1, max(-zs[i], 0.0))):
                base = (i * 2 + sign) * enc.n_pop
                decoded = sum(c * rates[base + k] for k, c in enumerate(enc.centres)) / enc.r_max
                assert abs(decoded - zz) < 1e-9, ('decode', i, sign, decoded, zz)
        drive = 0.0
        for (side, w), r in zip(routes, rates):
            drive += (1.0 if side == 'R' else -1.0) * w * r * T_s
        ideal = sum(W[i] * zs[i] for i in range(STATE_DIM))
        assert abs(drive - ideal) < 1e-9, ('routing', drive, ideal)
    print('selftest ok: population decode exact, routed drive equals W.z')


def gain_table(K, scales, gains):
    """Per gain: force (N) when only one variable is at its scale, and the full-corner force."""
    print('force at encoder full scale (z = +/-1), F_MAX = %.0f N' % F_MAX_N)
    for g in gains:
        per_var = [g * abs(K[i]) * scales[i] for i in range(STATE_DIM)]
        corner = sum(per_var)
        s_at_cap = [F_MAX_N / (g * abs(K[i])) for i in range(STATE_DIM)]
        print('  gain %6.1f: per-variable force at +/-scale %s N; corner sum %.1f N; '
              'state excursion alone reaching cap %s' % (
                  g, ['%.2f' % v for v in per_var], corner,
                  ['%.2g' % v for v in s_at_cap]))


def smoke(K, scales, gain, windows):
    enc = Encoder(scales)
    dec = Decoder()
    net = LIFStandIn()
    W = weights_from_gain(K, scales, gain, dec.n_per_count)
    loop = ControlLoop(enc, dec, net, W)
    plant = StubPlant()
    F_log, ideal_log, spikes_tot, max_side = [], [], 0, 0
    for _ in range(windows):
        s = plant.state()
        trains = enc.spike_trains(s)
        spikes_tot += sum(len(t) for t in trains)
        nL, nR = net.run_window(trains, enc.window_ms)
        max_side = max(max_side, nL, nR)
        F = dec.decode(nL, nR)
        F_log.append(F)
        ideal_log.append(-gain * sum(K[i] * s[i] for i in range(STATE_DIM)))
        plant.apply(F, enc.window_ms / 1000.0)
    mean_abs = sum(abs(f) for f in F_log) / len(F_log)
    err = sum(abs(f - g) for f, g in zip(F_log, ideal_log)) / len(F_log)
    print('gain %g, %d windows (%.1f s): mean |F| %.3f N, max |F| %.3f N, mean |F - (-gain K s)| %.3f N' % (
        gain, windows, windows * enc.window_ms / 1000.0, mean_abs, max(abs(f) for f in F_log), err))
    print('  input spikes %d, max single-side count per window %d, encoder clipped %d, decoder capped %d' % (
        spikes_tot, max_side, enc.n_clipped, dec.n_capped))


def main():
    selftest(K_LQR_DEMO, SCALES_DEMO)
    gain_table(K_LQR_DEMO, SCALES_DEMO, (5, 200))
    for g in (1.0, 5.0):
        smoke(K_LQR_DEMO, SCALES_DEMO, g, windows=200)


if __name__ == '__main__':
    main()

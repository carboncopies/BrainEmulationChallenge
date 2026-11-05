"""dp_spiking.py: spiking stand-in for the hand-derived double-pendulum controller.

Network (all weights from weights_recipe.json, written by dp_derive.py):
  12 input populations (6 states x pos/neg, n_in neurons each, spikes from the encoder in
  dp_codec.py) --AMPA--> push group / pull group (n_out LIF neurons each).
  Each input population feeds exactly ONE side (force = push - pull), excitatory only.
  Every output neuron receives k_i synapses of weight w_i nS from population i (consecutive
  entries of a seeded permutation, so every presynaptic neuron has the same fan-out +/-1).
Neuron = clean LIFC as in Pong step 1 (Vrest -70, Vreset -55, Vth -50 mV, R 100 MOhm,
C 100 pF so tau 10 ms, 2 ms refractory, reset 'Onset' style, no adaptation), conductance
synapse AMPA E = 0 mV, decay 3 ms, one step (1 ms) delivery delay. dt = 1 ms (NES RunFor dt).
Idealised vs NES: single-exponential synapse (NES AMPA has 0.5 ms rise), exact ExpEuler
update in numpy, spike counts read directly (no GetSpikeTimes round trip), perfectly
regular input trains, no HTTP/step latency, every receptor set to an arbitrary nS value.

One control tick = 10 ms: obs -> encode -> 10 steps -> count spikes -> force. The force
is available at the END of the window, so with dp_env it acts one tick later: LATENCY = 1
tick (+ the lag of the membrane/synapse, measured by dp_phase2.py --latency).
"""
import json
import os

import numpy as np

from dp_codec import DifferentialEncoder, CountDecoder

HERE = os.path.dirname(os.path.abspath(__file__))
NEURON = dict(EL=-70.0, Vth=-50.0, Vreset=-55.0, Ee=0.0, R_MOhm=100.0, C_pF=100.0,
              t_ref_ms=2.0, tau_syn_ms=3.0, dt_ms=1.0)
STEPS = 10


def gL_nS(p=NEURON):
    return p['C_pF'] / (p['R_MOhm'] * p['C_pF'] * 1e-3)   # C/tau, tau = R C


def tau_syn_eff_ms(p=NEURON):
    """Integral of the discrete synaptic conductance per unit weight (nS ms per nS)."""
    a = np.exp(-p['dt_ms'] / p['tau_syn_ms'])
    return p['dt_ms'] / (1 - a)


def nu_meanfield(G, p=NEURON):
    """Rate (Hz) of the LIF under a constant excitatory conductance G (nS): closed form
    nu = 1 / (t_ref + tau_eff ln((Vinf - Vreset)/(Vinf - Vth)))."""
    G = np.atleast_1d(np.asarray(G, float))
    gl = gL_nS(p)
    g = gl + G
    Vi = (gl * p['EL'] + G * p['Ee']) / g
    tau = p['C_pF'] / g
    out = np.zeros_like(G)
    ok = Vi > p['Vth'] + 1e-9
    out[ok] = 1000.0 / (p['t_ref_ms'] + tau[ok] * np.log((Vi[ok] - p['Vreset']) / (Vi[ok] - p['Vth'])))
    return out


def load_recipe(path=None):
    with open(path or os.path.join(HERE, 'weights_recipe.json')) as f:
        return json.load(f)


class SpikingNet:
    """Two groups of n_out LIF neurons; step(spikes[12*n_in, STEPS]) -> (n_push, n_pull)."""

    def __init__(self, rec, seed=0):
        self.rec = rec
        n_in, n_out = rec['n_in'], rec['n_out']
        self.n_in, self.n_out = n_in, n_out
        rng = np.random.default_rng(rec['connect_seed'])
        W = np.zeros((2 * n_out, 12 * n_in), np.float32)   # rows: push 0..n_out-1, pull after
        self.n_synapses = 0
        for p in rec['pops']:
            row0 = 0 if p['side'] == 'push' else n_out
            perm = rng.permutation(n_in)     # balanced fan-out: every presynaptic neuron gets
            for j in range(n_out):           # the same number of targets (+/-1)
                pre = perm[(j * p['k'] + np.arange(p['k'])) % n_in]
                W[row0 + j, p['index'] * n_in + pre] = p['w_nS']
                self.n_synapses += p['k']
        self.W = W
        P = NEURON
        self.a_syn = float(np.exp(-P['dt_ms'] / P['tau_syn_ms']))
        self.gl = gL_nS(P)
        self.ref_steps = int(round(P['t_ref_ms'] / P['dt_ms']))
        self.rng = np.random.default_rng(seed + 1000)
        self.reset()

    def reset(self):
        n = 2 * self.n_out
        # random initial Vm between reset and threshold (seeded), as NES neurons would differ
        self.V = self.rng.uniform(NEURON['Vreset'], NEURON['Vth'] - 1.0, n)
        self.g = np.zeros(n)
        self.ref = np.zeros(n, int)
        self.prev = np.zeros(12 * self.n_in, np.float32)

    def run_window(self, spikes):
        P = NEURON
        steps = spikes.shape[1]
        # input spike of step t is delivered at step t+1
        arr = np.concatenate([self.prev[:, None], spikes[:, :-1].astype(np.float32)], axis=1)
        drive = self.W @ arr                      # (2 n_out, steps) nS delivered per step
        self.prev = spikes[:, -1].astype(np.float32)
        counts = np.zeros(2 * self.n_out)
        e1 = P['dt_ms'] / P['C_pF']
        for t in range(steps):
            self.g = self.a_syn * self.g + drive[:, t]
            gt = self.gl + self.g
            Vi = (self.gl * P['EL'] + self.g * P['Ee']) / gt
            self.V = Vi + (self.V - Vi) * np.exp(-gt * e1)
            inref = self.ref > 0
            self.ref[inref] -= 1
            self.V[inref] = P['Vreset']
            fire = (self.V >= P['Vth']) & ~inref
            self.V[fire] = P['Vreset']
            self.ref[fire] = self.ref_steps - 1
            counts += fire
        return counts[:self.n_out].sum(), counts[self.n_out:].sum()


class SpikingController:
    """Callable for dp_env.run: obs(6) -> force (N). Seeded; keeps last counts."""

    def __init__(self, rec=None, seed=0):
        self.rec = rec or load_recipe()
        r = self.rec
        self.enc = DifferentialEncoder(r['ranges'], r['r0_hz'], r['n_in'], seed=seed)
        self.net = SpikingNet(r, seed=seed)
        self.dec = CountDecoder(r['c_N_per_spike'], r['F_max'])
        self.last = (0, 0)
        self.n_spikes = 0

    def __call__(self, obs):
        sp = self.enc.spike_trains(obs, STEPS)
        npush, npull = self.net.run_window(sp)
        self.last = (npush, npull)
        self.n_spikes += npush + npull
        return self.dec.decode(npush, npull)

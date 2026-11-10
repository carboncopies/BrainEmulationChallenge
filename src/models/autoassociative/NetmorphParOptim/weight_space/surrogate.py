#!/usr/bin/env python3
"""Explicit conductance-based LIF surrogate of the NES LIFCNeuron network (offline).

Mirrors the Netmorph->LIFC converter defaults (NetmorphManagerThread.cpp LIFCNeuronPars /
LIFCReceptorPars) and the receptor conductance rule in Neuron.cpp:150-157:
    g_k(t) = min(g_peak_sum, weight * g_peak_sum * g_norm(t))      (NMDA additionally * B_NMDA(Vm))
with g_norm a peak-normalized double exponential (Receptor.cpp:19-37).

Neuron: Vrest -70, Vreset -55, Vth -50 mV, Rm 100 MOhm, Cm 100 pF (tau_m 10 ms), abs. refractory 2 ms,
exponential-Euler (Cm form) update.  Receptors: AMPA E 0, tau 0.5/3 ms; GABA E -70, tau 0.5/10 ms;
NMDA E 0, tau 2/100 ms, Mg block B(V) = 1/(1+0.33*exp(-0.062 V)).
fAHP (3 nS peak, clip 5 nS, tau 2.5/30 ms) and sAHP (1 nS, clip 2 nS, tau 30/300 ms; principal cells only),
E_AHP = -90 mV, per spike, as in the converter defaults (AHPCLIP model).
ASSUMPTIONS (not in the server defaults or unknown offline): uniform 1.0 ms synaptic onset delay;
ADP, adaptive threshold and fatigue (threshold 300 spikes, 1000 ms recovery) are OMITTED. Weights are the
as-built 0.2 unless overridden by the programmed ops.
"""
import numpy as np
from reservoir import AMPA, GABA, NMDA

PARS = dict(Vrest=-70.0, Vreset=-55.0, Vth=-50.0, Rm_MOhm=100.0, Cm_pF=100.0, refr_ms=2.0, delay_ms=1.0,
            E_AHP=-90.0, fAHP=(3.0, 5.0, 2.5, 30.0), sAHP=(1.0, 2.0, 30.0, 300.0))
REC = {AMPA: dict(E=0.0, tr=0.5, td=3.0), GABA: dict(E=-70.0, tr=0.5, td=10.0), NMDA: dict(E=0.0, tr=2.0, td=100.0)}


def _norm(tr, td):
    tp = (tr * td / (td - tr)) * np.log(td / tr)
    return np.exp(-tp / td) - np.exp(-tp / tr)


def B_NMDA(V, Mg=1.0):
    return 1.0 / (1.0 + 0.33 * Mg * np.exp(-0.062 * V))


class Net:
    def __init__(self, G, W, N, dt=0.1, pars=PARS, is_principal=None, ahp=True):
        """G, W: dicts type -> (N,N) matrices [pre, post]; nS at weight 1 and weights in [0,1]."""
        self.N, self.dt, self.p = N, dt, dict(pars)
        self.G, self.W = G, W
        self.ahp = ahp
        self.is_principal = np.ones(N, dtype=bool) if is_principal is None else np.asarray(is_principal, dtype=bool)
        self.types = [t for t in (AMPA, GABA, NMDA) if (W[t] * G[t]).any()]
        self.WG = {t: np.minimum(G[t], W[t] * G[t]) for t in self.types}  # effective peak per pair
        self.norm = {t: _norm(REC[t]['tr'], REC[t]['td']) for t in self.types}

    def run(self, T_ms, forced=None, record_V=False):
        """forced: list of (t_ms, neuron_id) forced spikes (SetSpecificAPTimes analogue).
        Returns dict neuron -> list of spike times (ms)."""
        N, dt, p = self.N, self.dt, self.p
        gL = 1000.0 / p['Rm_MOhm']  # nS
        Cm = p['Cm_pF']             # pF ; tau = Cm/g in ms when g in nS
        V = np.full(N, p['Vrest'])
        refr = np.zeros(N)
        xr = {t: np.zeros(N) for t in self.types}
        xd = {t: np.zeros(N) for t in self.types}
        pending = []  # (arrival_time, neuron)
        forced = sorted(forced or [])
        fi = 0
        spikes = {i: [] for i in range(N)}
        steps = int(round(T_ms / dt))
        Vrec = np.zeros((steps, N)) if record_V else None
        er = {t: np.exp(-dt / REC[t]['tr']) for t in self.types}
        ed = {t: np.exp(-dt / REC[t]['td']) for t in self.types}
        # AHP traces (per neuron): (g_peak, g_max, tr, td)
        ahp_specs = []
        if self.ahp:
            ahp_specs.append((p['fAHP'], np.ones(N, dtype=bool)))
            ahp_specs.append((p['sAHP'], self.is_principal))
        ahp_state = [[np.zeros(N), np.zeros(N), _norm(s[2], s[3]), np.exp(-dt / s[2]), np.exp(-dt / s[3]), s, mask]
                     for s, mask in ahp_specs]
        for k in range(steps):
            t = k * dt
            # deliver delayed spikes to presynaptic traces
            while pending and pending[0][0] <= t + 1e-9:
                _, j = pending.pop(0)
                for tt in self.types:
                    xr[tt][j] += 1.0
                    xd[tt][j] += 1.0
            # conductances onto each post neuron
            gsum = np.full(N, gL)
            gE = np.full(N, gL * p['Vrest'])
            for tt in self.types:
                s = (xd[tt] - xr[tt]) / self.norm[tt]       # normalized trace per pre (peak 1 for a single spike)
                g = np.minimum(self.G[tt], self.WG[tt] * s[:, None]).sum(axis=0)
                if tt == NMDA:
                    g = g * B_NMDA(V)
                gsum += g
                gE += g * REC[tt]['E']
            for st in ahp_state:
                xr_a, xd_a, nrm, _, _, spec, mask = st
                g = np.minimum(spec[0] * (xd_a - xr_a) / nrm, spec[1]) * mask
                gsum += g
                gE += g * p['E_AHP']
            Vinf = gE / gsum
            tau = Cm / gsum
            Vnew = Vinf + (V - Vinf) * np.exp(-dt / tau)
            active = refr <= 0
            V = np.where(active, Vnew, p['Vreset'])
            refr = np.maximum(refr - dt, 0.0)
            # forced spikes at this step
            fired = np.zeros(N, dtype=bool)
            while fi < len(forced) and forced[fi][0] <= t + 1e-9:
                fired[forced[fi][1]] = True
                fi += 1
            fired |= (V >= p['Vth']) & active
            for i in np.where(fired)[0]:
                spikes[int(i)].append(round(t, 3))
                pending.append((t + p['delay_ms'], int(i)))
            pending.sort()
            V[fired] = p['Vreset']
            refr[fired] = p['refr_ms']
            for tt in self.types:
                xr[tt] *= er[tt]
                xd[tt] *= ed[tt]
            for st in ahp_state:
                st[0][fired] += 1.0
                st[1][fired] += 1.0
                st[0] *= st[3]
                st[1] *= st[4]
            if record_V:
                Vrec[k] = V
        return (spikes, Vrec) if record_V else spikes


def threshold_conductance(ampa_only=True, nmda_ratio=0.0, dt=0.05):
    """Minimal total synchronous AMPA g_peak (weight 1) from one volley that makes a resting LIF spike.
    nmda_ratio: NMDA g_peak as a fraction of AMPA g_peak delivered with the same volley (weight 1)."""
    def spikes_for(g):
        G = {AMPA: np.array([[0.0, g], [0.0, 0.0]]), GABA: np.zeros((2, 2)), NMDA: np.array([[0.0, g * nmda_ratio], [0.0, 0.0]])}
        W = {AMPA: np.ones((2, 2)), GABA: np.zeros((2, 2)), NMDA: np.ones((2, 2))}
        net = Net(G, W, 2, dt=dt)
        sp = net.run(40.0, forced=[(5.0, 0)])
        return len(sp[1]) > 0
    lo, hi = 0.0, 200.0
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if spikes_for(mid):
            hi = mid
        else:
            lo = mid
    return hi

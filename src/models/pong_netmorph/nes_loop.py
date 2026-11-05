"""nes_loop.py: helper for driving a NES simulation in a closed loop.

Differences from Simulation.RunAndWait: no spinner, ~2 ms status polling,
new-spike slicing (GetSpikeTimes returns the whole history on every call),
and per-tick latency statistics.
"""
import os
import sys
import time
import numpy as np

_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_here, '..', '..', 'components'))
sys.path.insert(0, os.path.join(_here, '..', 'autoassociative'))
import BrainGenix.NES as NES  # noqa: E402  (BrainGenix symlink in this dir)


def connect(host, port, use_https=False):
    """Connect with the same credentials vbpcommon.ClientFromArgs uses."""
    cfg = NES.Client.Configuration()
    cfg.Mode = NES.Client.Modes.Remote
    cfg.Host = host
    cfg.Port = port
    cfg.UseHTTPS = use_https
    cfg.AuthenticationMethod = NES.Client.Authentication.Password
    cfg.Username = "Admonishing"
    cfg.Password = "Instruction"
    client = NES.Client.Client(cfg)
    if not client.IsReady():
        raise RuntimeError('NES client not ready at %s:%s' % (host, port))
    return client


def new_simulation(client, name, seed=0):
    cfg = NES.Simulation.Configuration()
    cfg.Name = name
    cfg.Seed = seed
    return client.CreateSimulation(cfg)


class ClosedLoop:
    def __init__(self, sim, neuron_ids, poll_s=0.002):
        """neuron_ids: list of neuron IDs whose new spikes should be reported."""
        self.sim = sim
        self.ids = list(neuron_ids)
        self.poll_s = poll_s
        self.counts = {i: 0 for i in self.ids}
        self.lat_ms = []          # per-tick wall time of run_tick
        self.t_ms = self.sim_time()

    def sim_time(self):
        st = self.sim.GetStatus()
        assert st['StatusCode'] == 0, st
        return st['InSimulationTime_ms']

    def schedule(self, pairs):
        """pairs: [[t_abs_ms, neuron_id], ...], non-decreasing, >= current time."""
        if pairs:
            r = self.sim.SetSpecificAPTimes([[float(t), int(n)] for t, n in pairs])
            assert r.get('StatusCode', 0) == 0, r

    def run_tick(self, tick_ms, dt_ms=1.0):
        """Advance tick_ms, wait with fast polling, return {id: [new spike times]}."""
        t0 = time.perf_counter()
        r = self.sim.RunFor(tick_ms, dt_ms)
        assert r.get('StatusCode', 0) == 0, r
        while self.sim.GetStatus()['IsSimulating']:
            time.sleep(self.poll_s)
        new = self.new_spikes()
        self.lat_ms.append((time.perf_counter() - t0) * 1000.0)
        self.t_ms += tick_ms
        return new

    def new_spikes(self):
        resp = self.sim.GetSpikeTimes()
        assert resp['StatusCode'] == 0, resp
        data = resp.get('SpikeTimes', resp.get('Spikes', {}))
        out = {}
        for nid in self.ids:
            allt = data.get(str(nid), [])
            if isinstance(allt, dict):
                allt = allt.get('tSpike_ms', [])
            k = self.counts[nid]
            out[nid] = list(allt[k:])
            self.counts[nid] = len(allt)
        return out

    def latency_stats(self):
        a = np.array(self.lat_ms) if self.lat_ms else np.array([float('nan')])
        return {'mean_ms': float(a.mean()), 'p95_ms': float(np.percentile(a, 95)),
                'max_ms': float(a.max()), 'n': len(self.lat_ms)}

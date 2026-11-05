"""dp_nes.py: the phase-2 spiking controller built and run in BrainGenix NES (phase 3a).

Same encoder (dp_codec.DifferentialEncoder), decoder (CountDecoder) and wiring (the
SpikingNet weight matrix, same connect_seed) as the Python stand-in dp_spiking.py; only the
network is now NES: 3072 input LIFC neurons driven by SetSpecificAPTimes, 222 clean LIFC
output neurons, 1998 AMPA receptors.

Control tick = one RunFor(10 ms, dt 1 ms). The loop is LOCKSTEP: dp_env.run calls
controller(obs) and blocks until it returns the force, so the plant never advances while
NES is computing. Wall time per tick costs only wall-clock. The simulated latency is the
one window (inputs scheduled for t0+1..t0+10, output spikes counted over the same
window) plus the network lag; the actuation `delay` passed to dp_env.run models it.

NES specifics handled here (see README Phase 3a):
 - conductance of a pair = min(PeakConductance, Weight*PeakConductance*gnorm), gnorm = sum of
   per-spike peak-normalised double exponentials. PeakConductance is therefore set to a
   large cap (CAP_NS) and Weight = w_eff/CAP_NS, so the cap never clips (Pong used
   Weight 1, where the cap clips a pair at one spike's peak).
 - the double exponential (rise 0.5, decay 3 ms) carries 4.29 ms*nS of charge per nS of
   peak; the stand-in's single exponential carries 3.53 ms*nS. w_eff = w_nS * 3.528/4.29
   so the integrated drive per input spike is the same (mechanical unit conversion, A2).
 - SetSpecificAPTimes appends to the neuron's list (absolute times, must be non-decreasing
   per neuron: we only ever schedule the next window).
 - GetSpikeTimes returns the FULL history of ALL neurons, including the input sources.
"""
import math
import os
import sys
import time

sys.dont_write_bytecode = True
PYTHONCLIENT = os.environ.get('DP_PYTHONCLIENT',
                              os.path.expanduser('~/BrainGenix/wt/bec-pong/PythonClient'))
if PYTHONCLIENT not in sys.path:
    sys.path.insert(0, PYTHONCLIENT)

import numpy as np  # noqa: E402

import BrainGenix.NES as NES  # noqa: E402
from BrainGenix.NES.Models.Neurons import LIFC as NeuronLIFC  # noqa: E402
from BrainGenix.NES.Models.Connections import LIFCReceptor as RecLIFC  # noqa: E402

from dp_codec import DifferentialEncoder, CountDecoder  # noqa: E402
from dp_spiking import SpikingNet, load_recipe, STEPS  # noqa: E402

HOST, PORT = '127.0.0.1', 8100          # private stack only
CAP_NS = 20.0                           # PeakConductance of every receptor (never reached)
RISE_MS, DECAY_MS, ONSET_MS = 0.5, 3.0, 1.0
CHUNK = 400
WINDOW_OFFSET_MS = float(os.environ.get('DP_WINDOW_OFFSET_MS', 0.0))   # SinceTime_ms = tick start + this (0.0 exact, 0.5 drops ~10%: dp_nes_check_window.py)
# Hand adjustment A2 (weightspace_log.md): decoder constant x 1/1.6906. Measured on the NES net with
# the stand-in's A1 recipe (24 random states ~ N(0,(0.5 sigma)^2), seed 7, 2-tick means): measured
# force / target force = 1.6906 (rmse 0.34 N after the slope). Set DP_NES_C_ADJUST=1 for the raw net.
C_NES_ADJUST = float(os.environ.get('DP_NES_C_ADJUST', 1.0 / 1.6906))


def psp_peak_norm(rise=RISE_MS, decay=DECAY_MS):
    tp = rise * decay / (decay - rise) * math.log(decay / rise)
    return math.exp(-tp / decay) - math.exp(-tp / rise)


# charge of the NES PSP per nS of peak (ms), vs the stand-in's discrete single exponential
NES_CHARGE_MS = (DECAY_MS - RISE_MS) / psp_peak_norm()
STANDIN_CHARGE_MS = 3.5277264731571294      # tau_e_ms in weights_recipe.json
CHARGE_SCALE = STANDIN_CHARGE_MS / NES_CHARGE_MS


def connect(host=HOST, port=PORT):
    assert port not in (8000, 8001, 7999), 'not my stack'
    cfg = NES.Client.Configuration()
    cfg.Mode = NES.Client.Modes.Remote
    cfg.Host, cfg.Port, cfg.UseHTTPS = host, port, False
    cfg.AuthenticationMethod = NES.Client.Authentication.Password
    cfg.Username, cfg.Password = 'Admonishing', 'Instruction'
    client = NES.Client.Client(cfg)
    if not client.IsReady():
        raise RuntimeError('NES client not ready at %s:%s' % (host, port))
    return client


def new_simulation(client, name, seed=0):
    cfg = NES.Simulation.Configuration()
    cfg.Name, cfg.Seed = name, seed
    return client.CreateSimulation(cfg)


def _neuron_cfg(name, soma, axon):
    c = NES.Models.Neurons.LIFC.Configuration()
    c.Name = name
    c.SomaIDs, c.DendriteIDs, c.AxonIDs = [soma], [], [axon]
    c.RestingPotential_mV, c.ResetPotential_mV, c.SpikeThreshold_mV = -70, -55, -50
    c.MembraneResistance_MOhm, c.MembraneCapacitance_pF = 100, 100
    c.RefractoryPeriod_ms = 2
    c.SpikeDepolarization_mV = 30
    c.UpdateMethod, c.ResetMethod = 'ExpEulerCm', 'Onset'
    c.AfterHyperpolarizationReversalPotential_mV = -90
    c.FastAfterHyperpolarizationRise_ms = 2.5
    c.FastAfterHyperpolarizationDecay_ms = 30
    c.FastAfterHyperpolarizationPeakConductance_nS = 0
    c.FastAfterHyperpolarizationMaxPeakConductance_nS = 0
    c.FastAfterHyperpolarizationHalfActConstant = 1.5
    c.SlowAfterHyperpolarizationRise_ms = 30
    c.SlowAfterHyperpolarizationDecay_ms = 300
    c.SlowAfterHyperpolarizationPeakConductance_nS = 0
    c.SlowAfterHyperpolarizationMaxPeakConductance_nS = 0
    c.SlowAfterHyperpolarizationHalfActConstant = 0.3
    c.AfterHyperpolarizationSaturationModel = 'clip'
    c.FatigueThreshold = 0
    c.FatigueRecoveryTime_ms = 1000
    c.AfterDepolarizationReversalPotential_mV = -20
    c.AfterDepolarizationRise_ms = 20
    c.AfterDepolarizationDecay_ms = 200
    c.AfterDepolarizationPeakConductance_nS = 0
    c.AfterDepolarizationSaturationMultiplier = 2.0
    c.AfterDepolarizationRecoveryTime_ms = 300
    c.AfterDepolarizationDepletion = 0.3
    c.AfterDepolarizationSaturationModel = 'clip'
    c.AdaptiveThresholdDiffPerSpike = 0.0
    c.AdaptiveTresholdRecoveryTime_ms = 50
    c.AdaptiveThresholdDiffPotential_mV = 10
    c.AdaptiveThresholdFloor_mV = -50      # = Vth (0 would be a 0 mV floor and silence the cell)
    c.AdaptiveThresholdFloorDeltaPerSpike_mV = 0
    c.AdaptiveThresholdFloorRecoveryTime_ms = 500
    return c


def _batch(sim, module, cfgs, key):
    """Batch create through the module's BuildQuery. The client's own BatchCreate for LIFC
    neurons/receptors references undefined classes (SCNeuron / Receptor), so build the
    request list here and read the IDs from the responses."""
    import importlib
    bq = importlib.import_module(module).BuildQuery
    resp = sim.RequestHandler.BuildPostQuery([bq(c, sim.ID) for c in cfgs], '/NES')
    assert resp is not None and len(resp) == len(cfgs)
    for r in resp:
        assert r.get('StatusCode', 0) == 0 and key in r, r
    return [r[key] for r in resp]


def _chunks(lst, n=CHUNK):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def build_net(sim, rec=None, log=print):
    """Build the recipe's network in sim. Returns dict(in_ids[3072], push_ids, pull_ids,
    n_receptors, build_s, w_eff_range)."""
    rec = rec or load_recipe()
    t0 = time.perf_counter()
    n_in, n_out = rec['n_in'], rec['n_out']
    n_neu = 12 * n_in + 2 * n_out
    sim.SetLIFCAbstractedFunctional(_AbstractedFunctional=True)   # before receptors
    sim.SetSTDP(_DoSTDP=False)

    # geometry: spheres (somas) and cylinders (axons) on a plane grid, boxes for receptors
    side = int(math.ceil(math.sqrt(n_neu)))
    pos = [[40.0 * (i % side), 40.0 * (i // side), 0.0] for i in range(n_neu)]
    sph, cyl = [], []
    for i in range(n_neu):
        c = NES.Shapes.Sphere.Configuration()
        c.Name, c.Radius_um, c.Center_um = 'S%d' % i, 8, pos[i]
        sph.append(c)
        c = NES.Shapes.Cylinder.Configuration()
        c.Name = 'A%d' % i
        c.Point1Position_um = pos[i]
        c.Point2Position_um = [pos[i][0] + 20, pos[i][1], pos[i][2]]
        c.Point1Radius_um, c.Point2Radius_um = 2, 1
        cyl.append(c)
    sph_ids = [o.ID for ch in _chunks(sph) for o in sim.AddSpheres(ch)]
    cyl_ids = [o.ID for ch in _chunks(cyl) for o in sim.AddCylinders(ch)]
    log('shapes %d+%d  %.1fs' % (len(sph_ids), len(cyl_ids), time.perf_counter() - t0))

    def comp_cfg(name, shape):
        c = NES.Models.Compartments.LIFC.Configuration()
        c.Name = name
        c.RestingPotential_mV, c.ResetPotential_mV, c.SpikeThreshold_mV = -70, -55, -50
        c.MembraneResistance_MOhm, c.MembraneCapacitance_pF = 100, 100
        c.AfterHyperpolarizationAmplitude_mV = -90
        c.Shape = shape
        return c
    sc_cfg = [comp_cfg('SC%d' % i, sph_ids[i]) for i in range(n_neu)]
    ac_cfg = [comp_cfg('AC%d' % i, cyl_ids[i]) for i in range(n_neu)]
    soma_ids = [o.ID for ch in _chunks(sc_cfg) for o in sim.AddLIFCCompartments(ch)]
    axon_ids = [o.ID for ch in _chunks(ac_cfg) for o in sim.AddLIFCCompartments(ch)]
    log('compartments %d  %.1fs' % (len(soma_ids) + len(axon_ids), time.perf_counter() - t0))

    ncfg = [_neuron_cfg('N%d' % i, soma_ids[i], axon_ids[i]) for i in range(n_neu)]
    nids = []
    for ch in _chunks(ncfg):
        nids += _batch(sim, NeuronLIFC.LIFCNeuron.__module__, ch, 'NeuronID')
    log('neurons %d  %.1fs' % (len(nids), time.perf_counter() - t0))
    in_ids = nids[:12 * n_in]
    push_ids = nids[12 * n_in:12 * n_in + n_out]
    pull_ids = nids[12 * n_in + n_out:]

    # wiring: exactly the stand-in's weight matrix (same connect_seed)
    W = SpikingNet(rec, seed=0).W            # rows push(n_out) then pull(n_out); cols 12*n_in
    rows, cols = np.nonzero(W)
    out_ids = push_ids + pull_ids
    boxes, rcfg, w_eff_all = [], [], []
    for r, c_ in zip(rows, cols):
        w_eff = float(W[r, c_]) * CHARGE_SCALE
        w_eff_all.append(w_eff)
        bc = NES.Shapes.Box.Configuration()
        bc.Name = 'B%d_%d' % (c_, r)
        post_pos = pos[12 * n_in + int(r)]
        bc.CenterPosition_um = post_pos
        bc.Dimensions_um, bc.Rotation_rad = [0.1, 0.1, 0.1], [0, 0, 0]
        boxes.append(bc)
    box_ids = [o.ID for ch in _chunks(boxes) for o in sim.AddBoxes(ch)]
    for k, (r, c_) in enumerate(zip(rows, cols)):
        rc = NES.Models.Connections.LIFCReceptor.Configuration()
        rc.Name = 'R%d' % k
        rc.SourceCompartment = axon_ids[int(c_)]
        rc.DestinationCompartment = soma_ids[12 * n_in + int(r)]
        rc.Neurotransmitter = 'AMPA'
        rc.ReversalPotential_mV = 0
        rc.PSPRise_ms, rc.PSPDecay_ms = RISE_MS, DECAY_MS
        rc.PeakConductance_nS = CAP_NS
        rc.Weight = w_eff_all[k] / CAP_NS
        rc.OnsetDelay_ms = ONSET_MS
        rc.STDP_Method = 'None'
        rc.STDP_A_pos = rc.STDP_A_neg = rc.STDP_Tau_pos = rc.STDP_Tau_neg = 0
        rc.STDP_Shift = 0.01
        rc.voltage_gated = False
        rc.ReceptorMorphology = box_ids[k]
        rcfg.append(rc)
    for ch in _chunks(rcfg):
        _batch(sim, RecLIFC.LIFCReceptor.__module__, ch, 'ReceptorID')
    build_s = time.perf_counter() - t0
    log('receptors %d  total build %.1fs' % (len(rcfg), build_s))
    return dict(in_ids=in_ids, push_ids=push_ids, pull_ids=pull_ids, n_receptors=len(rcfg),
                n_neurons=n_neu, build_s=build_s,
                w_eff_min=min(w_eff_all), w_eff_max=max(w_eff_all))


class NESLoop:
    """Lockstep tick: schedule input spikes, RunFor, poll, read new output spikes."""

    def __init__(self, sim, net, poll_s=0.002, read='full'):
        self.sim = sim
        self.net = net
        self.poll_s = poll_s
        self.read = read
        self.t_ms = int(round(self._time()))
        self.out_ids = net['push_ids'] + net['pull_ids']
        self.n_push = len(net['push_ids'])
        self.counts = {i: 0 for i in self.out_ids}
        self.in_hist_len = 0
        self.bytes_hist = []
        self.total_hist_len = 0
        self.t_sched, self.t_run, self.t_read, self.n_pairs = [], [], [], []

    def _time(self):
        st = self.sim.GetStatus()
        assert st['StatusCode'] == 0, st
        return st['InSimulationTime_ms']

    def tick(self, spikes):
        """spikes: bool (3072, STEPS). Returns (n_push, n_pull) new output spikes this window."""
        t0 = self.t_ms
        a = time.perf_counter()
        pairs = []
        in_ids = self.net['in_ids']
        for t in range(spikes.shape[1]):
            idx = np.nonzero(spikes[:, t])[0]
            tt = float(t0 + t + 1)
            pairs += [[tt, in_ids[i]] for i in idx.tolist()]
        r = self.sim.SetSpecificAPTimes(pairs)
        assert r.get('StatusCode', 0) == 0, r
        b = time.perf_counter()
        r = self.sim.RunFor(float(STEPS), 1.0)
        assert r.get('StatusCode', 0) == 0, r
        deadline = time.perf_counter() + 120
        while self.sim.GetStatus()['IsSimulating']:
            if time.perf_counter() > deadline:
                raise TimeoutError('simulation busy > 120 s')
            time.sleep(self.poll_s)
        c = time.perf_counter()
        npush, npull = (0, 0) if self.read == 'none' else self._read_new()
        d = time.perf_counter()
        self.t_ms = t0 + STEPS
        self.t_sched.append(b - a)
        self.t_run.append(c - b)
        self.t_read.append(d - c)
        self.n_pairs.append(len(pairs))
        return npush, npull

    def _windowed_request(self, since_ms):
        """Simulation/GetSpikeTimes with SinceTime_ms and NeuronIDs (the PythonClient's
        GetSpikeTimes has neither argument), built like the client does. Returns (response
        dict, response bytes)."""
        import requests
        h = self.sim.RequestHandler
        body = [dict(ReqID=h.RequestID, **{'Simulation/GetSpikeTimes': {
            'SimulationID': self.sim.ID, 'SinceTime_ms': float(since_ms), 'NeuronIDs': self.out_ids}})]
        h.RequestID += 1
        resp = requests.post('%s/NES?AuthKey=%s' % (h.URIBase, h.Token), json=body)
        return resp.json()[0], len(resp.content)

    def _read_new(self):
        if self.read == 'window':
            return self._read_window()
        resp = self.sim.GetSpikeTimes()
        assert resp['StatusCode'] == 0, resp
        data = resp.get('SpikeTimes') or {}
        self.total_hist_len = len(data)
        npush = npull = 0
        for k, nid in enumerate(self.out_ids):
            v = data.get(str(nid))
            allt = v.get('tSpike_ms', []) if isinstance(v, dict) else (v or [])
            new = len(allt) - self.counts[nid]
            self.counts[nid] = len(allt)
            if k < self.n_push:
                npush += new
            else:
                npull += new
        return npush, npull

    def _read_window(self):
        # window = the tick just run: simulation times t0 .. t0+STEPS (t0 = tick start, self.t_ms
        # is only advanced after the read). Spikes of the tick are stamped t0 .. t0+STEPS-1, so
        # SinceTime_ms = t0 is exact (verified against the full read, dp_nes_check_window.py).
        t0 = self.t_ms
        resp, nbytes = self._windowed_request(t0 + WINDOW_OFFSET_MS)
        assert resp['StatusCode'] == 0, resp
        data = resp.get('SpikeTimes') or {}
        self.last_bytes = nbytes
        self.bytes_hist.append(nbytes)
        self.last_window = {nid: data[str(nid)]['tSpike_ms'] for nid in self.out_ids}
        npush = sum(len(self.last_window[i]) for i in self.out_ids[:self.n_push])
        npull = sum(len(self.last_window[i]) for i in self.out_ids[self.n_push:])
        return npush, npull

    def raw_history_probe(self):
        """One extra GetSpikeTimes (not timed in the loop): response bytes, number of neurons
        listed, number of spikes of input sources and of output neurons in the history."""
        h = self.sim.RequestHandler
        import requests
        body = [dict(ReqID=h.RequestID, **{'Simulation/GetSpikeTimes': {'SimulationID': self.sim.ID}})]
        h.RequestID += 1
        t = time.perf_counter()
        resp = requests.post('%s/NES?AuthKey=%s' % (h.URIBase, h.Token), json=body)
        dt = time.perf_counter() - t
        data = resp.json()[0].get('SpikeTimes') or {}
        ins = set(self.net['in_ids'])
        n_in = sum(len(v.get('tSpike_ms', [])) for k, v in data.items() if int(k) in ins)
        n_out = sum(len(v.get('tSpike_ms', [])) for k, v in data.items() if int(k) not in ins)
        return dict(bytes=len(resp.content), seconds=dt, neurons_listed=len(data),
                    input_spikes=n_in, other_spikes=n_out)


class NESController:
    """Callable for dp_env.run: obs(6) -> force (N). Same encoder/decoder as the stand-in."""

    def __init__(self, sim, net, rec=None, seed=0, read='full'):
        self.rec = rec or load_recipe()
        r = self.rec
        self.enc = DifferentialEncoder(r['ranges'], r['r0_hz'], r['n_in'], seed=seed)
        self.dec = CountDecoder(r['c_N_per_spike'] * C_NES_ADJUST, r['F_max'])
        self.loop = NESLoop(sim, net, read=read)
        self.last = (0, 0)
        self.n_spikes = 0
        self.t_total = []

    def __call__(self, obs):
        a = time.perf_counter()
        sp = self.enc.spike_trains(obs, STEPS)
        npush, npull = self.loop.tick(sp)
        self.last = (npush, npull)
        self.n_spikes += npush + npull
        f = self.dec.decode(npush, npull)
        self.t_total.append(time.perf_counter() - a)
        return f


def make_controller(name, seed=0, rec=None, log=print, read='full'):
    client = connect()
    sim = new_simulation(client, name, seed=seed)
    net = build_net(sim, rec, log=log)
    return NESController(sim, net, rec=rec, seed=seed, read=read), net

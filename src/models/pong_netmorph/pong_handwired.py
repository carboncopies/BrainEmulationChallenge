#!/usr/bin/env python3
# pong_handwired.py
'''
Hand-wired ("weight-space programmed") LIFC Pong controller for BrainGenix NES.

Architecture (N bins, y increases upward; bin = floor(y*N)):

   B_i (ball-y place cell)  --AMPA--> U_i , D_i
   P_j (paddle place cell)  --GABA--> U_i for every j >= i
                            --GABA--> D_i for every j <= i
   U_i --AMPA--> UP          D_i --AMPA--> DOWN

   U_i fires iff ball bin == i and paddle bin  < i ... see below.

Careful with the spec's sign convention: U_i is inhibited by P_j with j>=i, so
U_i can only fire when the paddle is in a bin j < i, i.e. strictly BELOW the ball
=> UP.  D_i is inhibited by P_j with j<=i, so it fires only when the paddle is
strictly ABOVE the ball => DOWN.  When j == i both are inhibited => no action.

Inputs B_*/P_* are driven only through SetSpecificAPTimes: per tick the active
paddle bin gets a 3-spike burst (2 ms apart) starting at +1 ms, the active ball
bin a burst starting at +3 ms (so inhibition arrives before excitation).
Action per tick = sign(new UP spikes - new DOWN spikes).
'''
import os
import sys
import json
import argparse
import random
import numpy as np

import nes_loop as NL
import BrainGenix.NES as NES
from pong_env import PongEnv, random_policy, oracle_policy, run_policy

N = 8

# ---- Calibrated parameters (see "Calibration notes" below) ------------------
# Neuron: LIF, Vrest -70, Vreset -55, Vth -50 mV, R 100 MOhm, C 100 pF (tau 10 ms),
# 2 ms refractory; no sAHP/ADP so no slow state leaks across 20 ms ticks.
G_AMPA_IN = 10.0    # nS peak, B_i -> U_i/D_i (weight 1.0)
G_GABA = 60.0      # nS peak, P_j -> U_i/D_i (shunting, weight 1.0)
G_AMPA_OUT = 20.0   # nS peak, U_i/D_i -> UP/DOWN
W_AMPA_IN = 1.0
W_GABA = 1.0
W_AMPA_OUT = 1.0
AMPA = dict(E=0, rise=0.5, decay=3.0)
GABA = dict(E=-70, rise=0.5, decay=6.0)
ONSET_MS = 1.0
BURST_SPIKES = 3
BURST_ISI_MS = 2
PADDLE_OFFSET_MS = 1
BALL_OFFSET_MS = 3
# -----------------------------------------------------------------------------


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Hand-wired LIFC Pong controller")
    p.add_argument("-Host", default="localhost", type=str)
    p.add_argument("-Port", default=8100, type=int)
    p.add_argument("-UseHTTPS", default=False, type=bool)
    p.add_argument("-Mode", default="truthtable", choices=["truthtable", "play"])
    p.add_argument("-Ticks", default=500, type=int)
    p.add_argument("-TickMs", default=20, type=int)
    p.add_argument("-Seed", default=1, type=int)
    p.add_argument("-SpacingMs", default=100, type=int, help="truthtable combo spacing")
    p.add_argument("-Out", default="output", type=str)
    p.add_argument("-Model", default=None, type=str,
                   help="load this saved (Netmorph grown / tuned) model instead of building the hand-wired net")
    for k in ("G_AMPA_IN", "G_GABA", "G_AMPA_OUT", "W_AMPA_IN", "W_GABA", "W_AMPA_OUT"):
        p.add_argument("-" + k, type=float, default=None)
    return p.parse_args(argv)


class Net:
    pass


def build(sim, n=N):
    """Create the LIFC network in sim; returns Net with neuron-id dicts."""
    sim.SetLIFCAbstractedFunctional(_AbstractedFunctional=True)  # before receptors
    sim.SetSTDP(_DoSTDP=False)
    net = Net()

    def sphere(name, r, c):
        cfg = NES.Shapes.Sphere.Configuration()
        cfg.Name, cfg.Radius_um, cfg.Center_um = name, r, c
        return sim.AddSphere(cfg)

    def cylinder(name, p1, p2, r1, r2):
        cfg = NES.Shapes.Cylinder.Configuration()
        cfg.Name = name
        cfg.Point1Position_um, cfg.Point2Position_um = p1, p2
        cfg.Point1Radius_um, cfg.Point2Radius_um = r1, r2
        return sim.AddCylinder(cfg)

    def box(name, c):
        cfg = NES.Shapes.Box.Configuration()
        cfg.Name, cfg.CenterPosition_um = name, c
        cfg.Dimensions_um, cfg.Rotation_rad = [0.1, 0.1, 0.1], [0, 0, 0]
        return sim.AddBox(cfg)

    def compartment(name, shape):
        cfg = NES.Models.Compartments.LIFC.Configuration()
        cfg.Name = name
        cfg.RestingPotential_mV, cfg.ResetPotential_mV, cfg.SpikeThreshold_mV = -70, -55, -50
        cfg.MembraneResistance_MOhm, cfg.MembraneCapacitance_pF = 100, 100
        cfg.AfterHyperpolarizationAmplitude_mV = -90
        cfg.Shape = shape
        return sim.AddLIFCCompartment(cfg)

    def neuron(name, soma, axon):
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
        c.FastAfterHyperpolarizationPeakConductance_nS = 0  # no fAHP: it carried over between 20 ms ticks
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
        c.AdaptiveThresholdFloor_mV = -50  # = Vth; 0 would mean a 0 mV floor and silence the cell
        c.AdaptiveThresholdFloorDeltaPerSpike_mV = 0
        c.AdaptiveThresholdFloorRecoveryTime_ms = 500
        return sim.AddLIFCNeuron(c)

    comps = {}   # name -> (soma_comp, axon_comp)
    pos = {}

    def make(name, p, radius):
        s = sphere(name + '_Soma', radius, p)
        a = cylinder(name + '_Axon', p, [p[0] + 20, p[1], p[2]], 2, 1)
        sc, ac = compartment(name + '_Soma_LIFC', s.ID), compartment(name + '_Axon_LIFC', a.ID)
        pos[name] = p
        return neuron(name, sc.ID, ac.ID), sc, ac

    net.B, net.P, net.U, net.D = {}, {}, {}, {}
    for i in range(n):
        y = 20 * i
        net.B[i], *comps_b = make('B%d' % i, [-90, y, 0], 8)
        comps['B%d' % i] = comps_b
        net.P[i], *comps_p = make('P%d' % i, [-90, y, 200], 8)
        comps['P%d' % i] = comps_p
        net.U[i], *comps_u = make('U%d' % i, [-30, y, 0], 5)
        comps['U%d' % i] = comps_u
        net.D[i], *comps_d = make('D%d' % i, [-30, y, 100], 5)
        comps['D%d' % i] = comps_d
    net.UP, *c_up = make('UP', [30, 160, 0], 10)
    comps['UP'] = c_up
    net.DOWN, *c_dn = make('DOWN', [30, 0, 0], 10)
    comps['DOWN'] = c_dn

    def receptor(src, dst, kind, g, w):
        prm = AMPA if kind == 'AMPA' else GABA
        name = '%s_%s_%s' % (src, dst, kind)
        b = box(name, pos[dst])
        c = NES.Models.Connections.LIFCReceptor.Configuration()
        c.Name = name
        c.SourceCompartment = comps[src][1].ID    # axon of source
        c.DestinationCompartment = comps[dst][0].ID  # soma of target
        c.Neurotransmitter = kind
        c.ReversalPotential_mV = prm['E']
        c.PSPRise_ms, c.PSPDecay_ms = prm['rise'], prm['decay']
        c.PeakConductance_nS = g
        c.Weight = w
        c.OnsetDelay_ms = ONSET_MS
        c.STDP_Method = 'None'
        c.STDP_A_pos = c.STDP_A_neg = c.STDP_Tau_pos = c.STDP_Tau_neg = 0
        c.STDP_Shift = 0.01
        c.voltage_gated = False
        c.ReceptorMorphology = b.ID
        sim.AddLIFCReceptor(c)

    nrec = 0
    for i in range(n):
        for tgt in ('U%d' % i, 'D%d' % i):
            receptor('B%d' % i, tgt, 'AMPA', G_AMPA_IN, W_AMPA_IN); nrec += 1
        for j in range(n):
            if j >= i:
                receptor('P%d' % j, 'U%d' % i, 'GABA', G_GABA, W_GABA); nrec += 1
            if j <= i:
                receptor('P%d' % j, 'D%d' % i, 'GABA', G_GABA, W_GABA); nrec += 1
        receptor('U%d' % i, 'UP', 'AMPA', G_AMPA_OUT, W_AMPA_OUT); nrec += 1
        receptor('D%d' % i, 'DOWN', 'AMPA', G_AMPA_OUT, W_AMPA_OUT); nrec += 1
    print('Built %d neurons, %d receptors' % (4 * n + 2, nrec))
    return net


class Role:
    """Minimal stand-in for an AddLIFCNeuron result: only .ID is used by the harness."""
    def __init__(self, nid):
        self.ID = nid


def load_model_net(sim, model, n=N, recipe_dir='output'):
    """Load a saved model and map neurons to roles through the Netmorph region names
    (the grown config makes every role its own one-neuron region)."""
    sim.SetLIFCAbstractedFunctional(_AbstractedFunctional=True)  # before receptors are rebuilt
    sim.SetSTDP(_DoSTDP=False)
    sim.ModelLoad(model)  # for a tuned model this is the grown model; the recipe is applied below
    recipe_path = os.path.join(recipe_dir, '%s_recipe.json' % model)
    if os.path.exists(recipe_path):
        # ModelSave does not persist per-pair strength edits, so tuned models are grown model + recipe.
        import pong_netmorph_tune as TU
        TU.apply_recipe(sim, json.load(open(recipe_path)))
        print('Applied tuning recipe %s' % recipe_path)
    regions = sim.GetAbstractConnectome(Sparse=True)['Regions']
    for r in ['UP', 'DOWN'] + ['%s%d' % (c, i) for c in 'BPUD' for i in range(n)]:
        assert r in regions and len(regions[r]) == 1, 'role %s not found as a one-neuron region' % r
    net = Net()
    net.B = {i: Role(regions['B%d' % i][0]) for i in range(n)}
    net.P = {i: Role(regions['P%d' % i][0]) for i in range(n)}
    net.U = {i: Role(regions['U%d' % i][0]) for i in range(n)}
    net.D = {i: Role(regions['D%d' % i][0]) for i in range(n)}
    net.UP, net.DOWN = Role(regions['UP'][0]), Role(regions['DOWN'][0])
    print('Loaded model %s: %d neurons mapped to roles' % (model, sum(len(v) for v in regions.values())))
    return net


def tick_input_times(net, t0, ball_bin, paddle_bin):
    """Absolute [t, id] spike pairs for one tick starting at t0 (sorted)."""
    pairs = []
    for k in range(BURST_SPIKES):
        pairs.append([t0 + PADDLE_OFFSET_MS + k * BURST_ISI_MS, net.P[paddle_bin].ID])
        pairs.append([t0 + BALL_OFFSET_MS + k * BURST_ISI_MS, net.B[ball_bin].ID])
    pairs.sort(key=lambda p: p[0])
    return pairs


def action_from(new, net):
    d = len(new[net.UP.ID]) - len(new[net.DOWN.ID])
    return (d > 0) - (d < 0)


def truthtable(loop, net, spacing, n=N):
    combos = [(b, p) for b in range(n) for p in range(n)]
    t0 = loop.t_ms + 10
    pairs, starts = [], {}
    for k, (b, p) in enumerate(combos):
        starts[(b, p)] = t0 + k * spacing
        pairs += tick_input_times(net, starts[(b, p)], b, p)
    loop.schedule(sorted(pairs, key=lambda x: x[0]))
    end = t0 + len(combos) * spacing + spacing
    loop.sim.RunFor(end - loop.t_ms, 1.0)
    loop.wait_idle(timeout_s=300)
    resp = loop.sim.GetSpikeTimes()
    data = resp['SpikeTimes'] or {}
    up = np.array(spikes_of(data, net.UP.ID)); dn = np.array(spikes_of(data, net.DOWN.ID))
    rows, ok = [], 0
    for (b, p) in combos:
        s = starts[(b, p)]
        nu = int(((up >= s) & (up < s + spacing)).sum()) if up.size else 0
        nd = int(((dn >= s) & (dn < s + spacing)).sum()) if dn.size else 0
        act = (nu > 0) - (nd > 0) if (nu == 0 or nd == 0) else 2  # 2 = both (error)
        exp = (b > p) - (b < p)
        good = act == exp
        ok += good
        rows.append(dict(ball=b, paddle=p, up=nu, down=nd, action=act, expected=exp, ok=bool(good)))
    print('\nTruth table (rows ball bin, cols paddle bin): cell = UPspikes/DOWNspikes, * = wrong')
    print('ball\\pad ' + ' '.join('%6d' % p for p in range(n)))
    for b in range(n):
        cells = []
        for p in range(n):
            r = rows[b * n + p]
            cells.append('%3d/%-2d%s' % (r['up'], r['down'], '' if r['ok'] else '*'))
        print('%7d  ' % b + ' '.join(cells))
    print('\n%d/%d correct: %s' % (ok, len(combos), 'PASS' if ok == len(combos) else 'FAIL'))
    return dict(correct=ok, total=len(combos), rows=rows, passed=ok == len(combos))


def spikes_of(data, nid):
    v = data.get(str(nid), data.get(nid, []))
    if isinstance(v, dict):
        v = v.get('tSpike_ms', [])
    return list(v)


def play(loop, net, ticks, tick_ms, seed, n=N):
    env = PongEnv(seed)
    env.action_mismatches = 0  # ticks where the net disagreed with sign(ball_bin - paddle_bin)
    for k in range(ticks):
        t0 = loop.t_ms
        b, p = env.ball_bin(n), env.paddle_bin(n)
        loop.schedule(tick_input_times(net, t0, b, p))
        new = loop.run_tick(tick_ms)
        a = action_from(new, net)
        env.action_mismatches += (a != (b > p) - (b < p))
        env.step(a)
    return env


def main(argv=None):
    A = parse_args(argv)
    g = globals()
    for k in ("G_AMPA_IN", "G_GABA", "G_AMPA_OUT", "W_AMPA_IN", "W_GABA", "W_AMPA_OUT"):
        if getattr(A, k) is not None:
            g[k] = getattr(A, k)
    client = NL.connect(A.Host, A.Port, A.UseHTTPS)
    sim = NL.new_simulation(client, 'pong_handwired' if not A.Model else 'pong_' + A.Model, seed=A.Seed)
    net = build(sim) if not A.Model else load_model_net(sim, A.Model, recipe_dir=A.Out)
    tag = '' if not A.Model else A.Model + '_'
    ids = [net.UP.ID, net.DOWN.ID]
    loop = NL.ClosedLoop(sim, ids)
    os.makedirs(A.Out, exist_ok=True)
    params = dict(model=A.Model, G_AMPA_IN=G_AMPA_IN, G_GABA=G_GABA, G_AMPA_OUT=G_AMPA_OUT,
                  W_AMPA_IN=W_AMPA_IN, W_GABA=W_GABA, W_AMPA_OUT=W_AMPA_OUT,
                  AMPA=AMPA, GABA=GABA)
    if A.Mode == 'truthtable':
        res = truthtable(loop, net, A.SpacingMs)
        res['params'] = params
        res['spacing_ms'] = A.SpacingMs
        json.dump(res, open(os.path.join(A.Out, 'truthtable_%s%d.json' % (tag, A.SpacingMs)), 'w'), indent=1)
        return 0 if res['passed'] else 1
    # play
    env = play(loop, net, A.Ticks, A.TickMs, A.Seed)
    rnd = run_policy(random_policy, A.Ticks, A.Seed)
    ora = run_policy(oracle_policy, A.Ticks, A.Seed)
    lat = loop.latency_stats()
    res = dict(ticks=A.Ticks, tick_ms=A.TickMs, seed=A.Seed, params=params,
               network=dict(action_mismatches=env.action_mismatches, hits=env.hits, misses=env.misses, hit_rate=env.hit_rate()),
               random=dict(hits=rnd.hits, misses=rnd.misses, hit_rate=rnd.hit_rate()),
               oracle=dict(hits=ora.hits, misses=ora.misses, hit_rate=ora.hit_rate()),
               latency=lat)
    print(json.dumps(res, indent=1))
    print('\nNetwork: %d hits, %d misses, hit rate %.3f | random %.3f | oracle %.3f | %.1f ms/tick mean, %.1f p95'
          % (env.hits, env.misses, env.hit_rate(), rnd.hit_rate(), ora.hit_rate(), lat['mean_ms'], lat['p95_ms']))
    json.dump(res, open(os.path.join(A.Out, 'play_%ss%d_n%d.json' % (tag, A.Seed, A.Ticks)), 'w'), indent=1)
    return 0


if __name__ == '__main__':
    sys.exit(main())

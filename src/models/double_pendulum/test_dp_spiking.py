import numpy as np

from dp_env import run, DisturbanceCfg
from dp_lqr import dlqr, StateFeedback
from dp_spiking import (SpikingController, SpikingNet, load_recipe, NEURON, nu_meanfield,
                        gL_nS)
from dp_codec import DifferentialEncoder

REC = load_recipe()
K = np.array(REC['K'])
SG = np.array(REC['sigma'])


def _drive(ctl, s, warm=8, n=30):
    for _ in range(warm):
        ctl(s)
    return np.array([ctl(s) for _ in range(n)])


def test_recipe_k_is_the_10ms_gain():
    assert np.allclose(K, dlqr(ctrl_dt=0.01)[0].reshape(-1), atol=1e-6)


def test_deterministic_by_seed():
    s = 0.7 * SG
    a = _drive(SpikingController(REC, 3), s)
    b = _drive(SpikingController(REC, 3), s)
    c = _drive(SpikingController(REC, 4), s)
    assert np.array_equal(a, b)
    assert not np.array_equal(a, c)


def test_static_force_matches_minus_K_s():
    """Static states s ~ N(0, (0.5 sigma)^2): decoded force vs -K s.
    Tolerance: regression slope within 8 % of 1 and RMSE <= 0.35 N (measured 1.006 / 0.13 N
    at write time; the RMSE is mostly count noise ~0.25 N/sqrt(30 ticks) plus input
    quantisation)."""
    rs = np.random.default_rng(11)
    ctl = SpikingController(REC, 5)
    want, got = [], []
    for _ in range(16):
        s = rs.normal(0, 0.5 * SG)
        want.append(-K @ s)
        got.append(_drive(ctl, s).mean())
    want, got = np.array(want), np.array(got)
    slope = want @ got / (want @ want)
    rmse = np.sqrt(np.mean((got - want) ** 2))
    print('slope %.3f rmse %.3f N' % (slope, rmse))
    assert abs(slope - 1) < 0.08
    assert rmse < 0.35


def test_zero_state_force_is_small():
    f = _drive(SpikingController(REC, 1), np.zeros(6), n=60)
    assert abs(f.mean()) < 0.5   # fixed random connectivity: per-seed offset of a few spikes (c = 0.085 N); measured -0.33 N, sd 0.3-0.5 N


def test_each_state_sign_and_direction():
    for i in range(6):
        s = np.zeros(6)
        s[i] = 1.0 * SG[i]
        f = _drive(SpikingController(REC, 2), s).mean()
        assert np.sign(f) == np.sign(-K[i]), (i, f)


def test_encoder_never_saturates_over_lqr_closed_loop():
    """Encoder rates r0 +/- g s stay inside [0, 2 r0] over 60 s of the 10 ms LQR closed loop
    with disturbance (seed 0, not the seed the ranges were derived from)."""
    m, tr = run(StateFeedback(K), T=60, seed=0, ctrl_dt=0.01, delay=1,
                disturbance=DisturbanceCfg(), trace=True)
    S = tr['s'][::2]
    enc = DifferentialEncoder(REC['ranges'], REC['r0_hz'], REC['n_in'])
    worst = max(np.abs(enc.g * s).max() for s in S)
    assert worst <= REC['r0_hz'], worst / REC['r0_hz']
    print('peak rate fraction of r0: %.3f' % (worst / REC['r0_hz']))


def test_weights_within_cap_and_routing_is_excitatory_one_side():
    cap = REC['w_max_nS']
    assert all(0 < p['w_nS'] <= cap for p in REC['pops'])
    sides = {}
    for p in REC['pops']:
        assert p['side'] in ('push', 'pull')
        sides[p['index']] = p['side']
    assert len(sides) == 12
    for i in range(6):
        assert sides[i] != sides[6 + i]        # pos and neg of a state feed opposite sides
        assert (sides[i] == 'pull') == (K[i] > 0)
    net = SpikingNet(REC)
    assert (net.W >= 0).all()
    assert net.n_synapses == REC['n_receptors']


def test_operating_point_is_mid_range():
    nu = nu_meanfield(REC['Ge0_nS'])[0]
    assert abs(nu - REC['nu_cap_Hz'] / 2) < 1.0
    # baseline conductance from the signal populations equals Ge0 (no bias population)
    tot = sum(p['k'] * p['w_nS'] for p in REC['pops'] if p['side'] == 'push')
    base = tot * REC['r0_hz'] * 1e-3 * REC['tau_e_ms']
    assert abs(base - REC['Ge0_nS']) < 1e-6

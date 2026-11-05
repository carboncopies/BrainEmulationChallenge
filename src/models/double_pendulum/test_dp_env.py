import math
import numpy as np
from dp_env import (Params, DoublePendulumEnv, DisturbanceCfg, run, energy,
                    dynamics)
from dp_lqr import (linearize, linearize_fd, controllability_rank, dlqr, clqr,
                    StateFeedback)


def test_determinism():
    K = dlqr(ctrl_dt=0.005)[0]
    d = DisturbanceCfg(sensor_noise=(0, 1e-3, 1e-3, 0, 0, 0))
    a = run(StateFeedback(K), T=20, seed=3, disturbance=d, trace=True)
    b = run(StateFeedback(K), T=20, seed=3, disturbance=d, trace=True)
    c = run(StateFeedback(K), T=20, seed=4, disturbance=d, trace=True)
    assert a[0] == b[0] and np.array_equal(a[1]['s'], b[1]['s'])
    assert not np.array_equal(a[1]['s'], c[1]['s'])


def _energy_drift(dt, s0=(0, 0.1, -0.05, 0, 0, 0), T=10.0):
    p = Params(bc=0.0, bj1=0.0, bj2=0.0)
    env = DoublePendulumEnv(p, dt=dt, ctrl_dt=dt, disturbance=None)
    env.reset(list(s0))
    e0 = energy(env.s, p)
    scale = 2 * p.g * ((p.m1 * p.lc1 + p.m2 * p.l1) + p.m2 * p.lc2)  # PE range
    worst = 0.0
    for _ in range(int(round(T / dt))):
        env.substep(0.0, external=False)
        worst = max(worst, abs(energy(env.s, p) - e0) / scale)
    return worst


def test_energy_conservation():
    # Unforced upright start is unstable, so the 10 s run is a violent chaotic
    # fall (links spin several turns): RK4 error is largest here.
    d5 = _energy_drift(0.005)
    d125 = _energy_drift(0.00125)
    print('relative energy drift over 10 s: dt=5ms %.3e, dt=1.25ms %.3e' % (d5, d125))
    assert d5 < 1e-3
    assert d125 < 1e-5
    assert d125 < d5 / 16  # converges at least like a 4th-order method


def test_linearization_matches_finite_difference():
    p = Params()
    A, B = linearize(p)
    Af, Bf = linearize_fd(p)
    assert np.allclose(A, Af, atol=1e-5, rtol=1e-5)
    assert np.allclose(B, Bf, atol=1e-5, rtol=1e-5)
    # also: linear model tracks the nonlinear one for a tiny state
    s = np.array([0.0, 1e-4, -2e-4, 1e-3, 0, 0])
    assert np.allclose(dynamics(s, 0.01, p), A @ s + (B * 0.01).ravel(), atol=1e-6)
    assert controllability_rank(A, B)[0] == 6


def test_lqr_holds_180s():
    K = dlqr(ctrl_dt=0.005)[0]
    m = run(StateFeedback(K), T=180, seed=0, disturbance=None,
            x0=[0, math.radians(2), math.radians(-2), 0, 0, 0])
    assert m['fall_time_s'] is None and m['upright_frac'] == 1.0
    assert m['max_cart_drift_m'] < 0.5


def test_continuous_and_discrete_gain_close():
    Kc = clqr()[0]
    Kd = dlqr(ctrl_dt=0.001)[0]
    assert np.allclose(Kc, Kd, rtol=0.05, atol=0.05)


def test_delay_and_saturation():
    p = Params(F_max=1.0)
    env = DoublePendulumEnv(p, delay=2)
    env.reset()
    forces = [env.step(5.0)[1][0][1] for _ in range(4)]
    assert forces == [0.0, 0.0, 1.0, 1.0]

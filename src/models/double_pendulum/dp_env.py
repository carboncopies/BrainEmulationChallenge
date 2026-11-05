"""dp_env.py: cart + inverted double pendulum, pure Python/numpy (no NES import).

Generalised coordinates q = [x, th1, th2]. x is the cart position on a
horizontal track (m); th1, th2 are the ABSOLUTE link angles measured from the
upright vertical (rad, upright = 0, positive = leaning toward +x). Link 1 is
pinned to the cart, link 2 is pinned to the tip of link 1. State vector is
s = [x, th1, th2, xd, th1d, th2d]. Input is a horizontal force F on the cart.

Lagrangian derivation (L = T - V)
---------------------------------
Uniform rods: link i has mass m_i, length l_i, centre of mass at lc_i = l_i/2
and inertia about its centre I_i = m_i l_i^2 / 12.
  p1 = (x + lc1 sin th1,            lc1 cos th1)
  p2 = (x + l1 sin th1 + lc2 sin th2, l1 cos th1 + lc2 cos th2)
  T = 1/2 mc xd^2 + sum_i [1/2 m_i |pdot_i|^2 + 1/2 I_i thdot_i^2]
  V = g (m1 lc1 cos th1 + m2 (l1 cos th1 + lc2 cos th2))
With a = m1 lc1 + m2 l1, b = m2 lc2, c = m2 l1 lc2, the mass matrix is
      [ mc+m1+m2   a cos th1        b cos th2          ]
  M = [ a cos th1  m1 lc1^2+m2 l1^2+I1   c cos(th1-th2) ]
      [ b cos th2  c cos(th1-th2)   m2 lc2^2 + I2      ]
and d/dt(dL/dqd) - dL/dq = Q gives  M qdd = rhs  with
  rhs_x   = F - bc xd + a sin th1 th1d^2 + b sin th2 th2d^2
  rhs_th1 = a g sin th1 - c sin(th1-th2) th2d^2 + Q1
  rhs_th2 = b g sin th2 + c sin(th1-th2) th1d^2 + Q2
Viscous friction: cart bc*xd; joint 1 (cart-link1) bj1*th1d; joint 2 relative
bj2*(th2d-th1d). Generalised torques: Q1 = -bj1 th1d + bj2 (th2d-th1d) + tau1,
Q2 = -bj2 (th2d-th1d) + tau2, where tau1/tau2 are external disturbance
torques (generalised forces on the absolute angles). Total energy T+V is
conserved when all friction, F and disturbances are zero.

Default parameters (tabletop scale, Params dataclass): cart 1.0 kg, link 1
0.5 m / 0.2 kg, link 2 0.5 m / 0.2 kg, g 9.81, cart friction 0.05 N s/m, joint
friction 0.002 N m s/rad, F_max 20 N.

Integration: RK4 at dt = 5 ms. Control runs every ctrl_dt (a multiple of dt)
with zero-order hold; an optional actuation delay of `delay` control ticks
means the force computed at tick k is applied during tick k+delay (zero
force before the first one arrives). Forces are saturated to |F| <= F_max
when they are applied.

Disturbances (DisturbanceCfg, seeded): Poisson kicks at `rate` Hz (default
1.0). Each kick lasts `duration` (20 ms) and draws a cart impulse
J ~ N(0, cart_impulse^2) N s (default 0.02 N s, i.e. about 1 N for 20 ms,
0.02 m/s of cart speed) and link torque impulses tau1,tau2 ~ N(0,
torque_impulse^2) N m s (default 0.001, about 0.05 N m for 20 ms). Kicks are
external and are not saturated. Optional Gaussian sensor noise (std per state
component, `sensor_noise`) is added to what the controller sees (default off).

Episode ends at the first time either |angle| > fall_deg (45 deg), or (if
track_limit is set) |x| > track_limit. The remaining time counts as not upright.
"""
from dataclasses import dataclass, field
import math

import numpy as np


@dataclass
class Params:
    mc: float = 1.0
    m1: float = 0.2
    m2: float = 0.2
    l1: float = 0.5
    l2: float = 0.5
    g: float = 9.81
    bc: float = 0.05      # cart viscous friction N s/m
    bj1: float = 0.002    # joint 1 viscous friction N m s/rad
    bj2: float = 0.002    # joint 2 (relative) viscous friction
    F_max: float = 20.0

    @property
    def lc1(self):
        return self.l1 / 2

    @property
    def lc2(self):
        return self.l2 / 2

    @property
    def I1(self):
        return self.m1 * self.l1 ** 2 / 12

    @property
    def I2(self):
        return self.m2 * self.l2 ** 2 / 12


@dataclass
class DisturbanceCfg:
    rate: float = 1.0               # kicks per second
    cart_impulse: float = 0.02      # N s (std)
    torque_impulse: float = 0.001   # N m s (std)
    duration: float = 0.02          # s
    sensor_noise: tuple = (0.0,) * 6  # std on [x, th1, th2, xd, th1d, th2d]


def mass_matrix(q, p):
    _, t1, t2 = q
    a = p.m1 * p.lc1 + p.m2 * p.l1
    b = p.m2 * p.lc2
    c = p.m2 * p.l1 * p.lc2
    return np.array([
        [p.mc + p.m1 + p.m2, a * math.cos(t1), b * math.cos(t2)],
        [a * math.cos(t1), p.m1 * p.lc1 ** 2 + p.m2 * p.l1 ** 2 + p.I1,
         c * math.cos(t1 - t2)],
        [b * math.cos(t2), c * math.cos(t1 - t2), p.m2 * p.lc2 ** 2 + p.I2]])


def dynamics(s, F, p, tau1=0.0, tau2=0.0):
    """Continuous dynamics sdot = f(s, F). F is the (already saturated) cart force."""
    x, t1, t2, xd, w1, w2 = s
    a = p.m1 * p.lc1 + p.m2 * p.l1
    b = p.m2 * p.lc2
    c = p.m2 * p.l1 * p.lc2
    s12 = math.sin(t1 - t2)
    rel = w2 - w1
    rhs = np.array([
        F - p.bc * xd + a * math.sin(t1) * w1 ** 2 + b * math.sin(t2) * w2 ** 2,
        a * p.g * math.sin(t1) - c * s12 * w2 ** 2 - p.bj1 * w1 + p.bj2 * rel + tau1,
        b * p.g * math.sin(t2) + c * s12 * w1 ** 2 - p.bj2 * rel + tau2])
    qdd = np.linalg.solve(mass_matrix(s[:3], p), rhs)
    return np.array([xd, w1, w2, qdd[0], qdd[1], qdd[2]])


def rk4(s, F, p, dt, tau1=0.0, tau2=0.0):
    k1 = dynamics(s, F, p, tau1, tau2)
    k2 = dynamics(s + 0.5 * dt * k1, F, p, tau1, tau2)
    k3 = dynamics(s + 0.5 * dt * k2, F, p, tau1, tau2)
    k4 = dynamics(s + dt * k3, F, p, tau1, tau2)
    return s + dt / 6.0 * (k1 + 2 * k2 + 2 * k3 + k4)


def energy(s, p):
    """Total energy T + V (J)."""
    x, t1, t2, xd, w1, w2 = s
    v1x = xd + p.lc1 * math.cos(t1) * w1
    v1y = -p.lc1 * math.sin(t1) * w1
    v2x = xd + p.l1 * math.cos(t1) * w1 + p.lc2 * math.cos(t2) * w2
    v2y = -p.l1 * math.sin(t1) * w1 - p.lc2 * math.sin(t2) * w2
    T = (0.5 * p.mc * xd ** 2 + 0.5 * p.m1 * (v1x ** 2 + v1y ** 2)
         + 0.5 * p.m2 * (v2x ** 2 + v2y ** 2)
         + 0.5 * p.I1 * w1 ** 2 + 0.5 * p.I2 * w2 ** 2)
    V = p.g * (p.m1 * p.lc1 * math.cos(t1)
               + p.m2 * (p.l1 * math.cos(t1) + p.lc2 * math.cos(t2)))
    return T + V


class DoublePendulumEnv:
    def __init__(self, params=None, dt=0.005, ctrl_dt=0.005, delay=0,
                 disturbance=None, track_limit=None, seed=0):
        self.p = params or Params()
        self.dt = dt
        self.n_sub = int(round(ctrl_dt / dt))
        assert self.n_sub >= 1 and abs(self.n_sub * dt - ctrl_dt) < 1e-9, \
            'ctrl_dt must be a multiple of dt'
        self.ctrl_dt = self.n_sub * dt
        self.delay = int(delay)
        self.dist = disturbance          # DisturbanceCfg or None
        self.track_limit = track_limit
        self.rng = np.random.default_rng(seed)
        self.reset()

    def reset(self, s0=None):
        self.s = np.zeros(6) if s0 is None else np.array(s0, dtype=float)
        self.t = 0.0
        self._queue = [0.0] * self.delay   # forces waiting to be applied
        self._kicks = []                   # [steps_left, J_force, tau1, tau2]
        self.last_force = 0.0
        return self.observe()

    def observe(self):
        o = self.s.copy()
        if self.dist is not None and any(self.dist.sensor_noise):
            o += self.rng.normal(0.0, 1.0, 6) * np.asarray(self.dist.sensor_noise)
        return o

    def _disturbance(self):
        """Per-substep external (cart force, tau1, tau2); may start a new kick."""
        d = self.dist
        if d is None or d.rate <= 0:
            return 0.0, 0.0, 0.0
        if self.rng.random() < d.rate * self.dt:
            n = max(1, int(round(d.duration / self.dt)))
            T = n * self.dt
            j = self.rng.normal(0.0, d.cart_impulse)
            t1, t2 = self.rng.normal(0.0, d.torque_impulse, 2)
            self._kicks.append([n, j / T, t1 / T, t2 / T])
        f = a1 = a2 = 0.0
        for k in self._kicks:
            f += k[1]
            a1 += k[2]
            a2 += k[3]
            k[0] -= 1
        self._kicks = [k for k in self._kicks if k[0] > 0]
        return f, a1, a2

    def substep(self, F, external=True):
        """One RK4 step of dt with force F (saturated here). Returns applied force."""
        F = max(-self.p.F_max, min(self.p.F_max, F))
        fe, a1, a2 = self._disturbance() if external else (0.0, 0.0, 0.0)
        self.s = rk4(self.s, F + fe, self.p, self.dt, a1, a2)
        self.t += self.dt
        return F

    def step(self, u):
        """One control tick: command u (N) goes through the delay line, then is
        held for ctrl_dt. Returns (obs, [(state, applied_force) per substep])."""
        self._queue.append(float(u))
        F = self._queue.pop(0)
        applied = []
        for _ in range(self.n_sub):
            f = self.substep(F)
            applied.append((self.s.copy(), f))
            if self.failed():
                break
        return self.observe(), applied

    def failed(self, fall_deg=45.0):
        lim = math.radians(fall_deg)
        if abs(self.s[1]) > lim or abs(self.s[2]) > lim:
            return True
        return self.track_limit is not None and abs(self.s[0]) > self.track_limit


def run(controller, T=180.0, seed=0, params=None, ctrl_dt=0.005, delay=0,
        disturbance=None, x0=None, upright_deg=10.0, fall_deg=45.0,
        track_limit=None, trace=False, dt=0.005):
    """Run one episode. controller(obs: ndarray(6)) -> force (N), called every
    ctrl_dt. x0 default: both links tilted 1 deg, rest zero. Returns metrics
    (and a trace dict of arrays at dt rate if trace=True)."""
    env = DoublePendulumEnv(params, dt, ctrl_dt, delay, disturbance, track_limit, seed)
    if x0 is None:
        x0 = [0, math.radians(1), math.radians(1), 0, 0, 0]
    obs = env.reset(x0)
    up = math.radians(upright_deg)
    n_total = int(round(T / dt))
    S, Fs = [], []
    done = False
    while len(Fs) < n_total and not done:
        obs, rec = env.step(controller(obs))
        for st, F in rec:
            if len(Fs) >= n_total:
                break
            S.append(st)
            Fs.append(F)
        done = env.failed(fall_deg)
    fall_t = None
    S = np.array(S)
    Fs = np.array(Fs)
    n = len(Fs)
    th = S[:, 1:3]
    bad = (np.abs(th) > math.radians(fall_deg)).any(axis=1)
    if track_limit is not None:
        bad |= np.abs(S[:, 0]) > track_limit
    if bad.any():
        i = int(np.argmax(bad))
        fall_t = (i + 1) * dt
        n_valid = max(i, 1)
    else:
        n_valid = n
    upright = (np.abs(th[:n_valid]) <= up).all(axis=1)
    m = {
        'seed': seed, 'T': T,
        'upright_frac': float(upright.sum() * dt / T),
        'fall_time_s': fall_t,
        'rms_th1_deg': float(np.degrees(np.sqrt(np.mean(th[:n_valid, 0] ** 2)))),
        'rms_th2_deg': float(np.degrees(np.sqrt(np.mean(th[:n_valid, 1] ** 2)))),
        'rms_force_N': float(np.sqrt(np.mean(Fs[:n_valid] ** 2))),
        'max_abs_force_N': float(np.abs(Fs[:n_valid]).max()),
        'max_cart_drift_m': float(np.abs(S[:n_valid, 0]).max()),
        'rms_x_m': float(np.sqrt(np.mean(S[:n_valid, 0] ** 2))),
    }
    if trace:
        return m, {'t': (np.arange(n) + 1) * dt, 's': S, 'F': Fs}
    return m

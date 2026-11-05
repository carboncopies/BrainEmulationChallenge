"""dp_lqr.py: linearisation about upright and LQR design for dp_env.

State s = [x, th1, th2, xd, th1d, th2d], input u = cart force (N).
Linearisation at s=0 (analytic): with M0 = M(0), G the gravity Jacobian
(rhs_th1 ~ a g th1, rhs_th2 ~ b g th2) and the viscous friction matrix Cf,
    sdot = A s + B u,  A = [[0, I], [M0^-1 G, M0^-1 Cf]],  B = [0; M0^-1 e_x].
Continuous LQR: solve CARE, K = R^-1 B' P, u = -K s.
Discrete LQR: ZOH discretisation of (A,B) over ctrl_dt (matrix exponential),
DARE, K_d. With an actuation delay of n ticks, `dlqr(..., delay=n)` designs on
the augmented state [s; u_{k-n}..u_{k-1}] (the pending forces), which needs the
controller to remember its last n commands; `DelayAwareLQR` does that.

Chosen weights: Q = diag(50, 100, 100, 5, 1, 1) on [x, th1, th2, xd, th1d,
th2d] (rad, m, SI), R = 2 (per N^2). Angles and cart position are weighted
for small excursions and little drift; R keeps the force modest. Compared with
other tried weights (60 s, disturbance on) this gave the smallest cart drift
for about the same force.
"""
import numpy as np
from scipy.linalg import solve_continuous_are, solve_discrete_are, expm

from dp_env import Params, mass_matrix, dynamics

# x, th1, th2, xd, th1d, th2d
DEFAULT_Q = np.diag([50.0, 100.0, 100.0, 5.0, 1.0, 1.0])
DEFAULT_R = np.array([[2.0]])


def linearize(p=None):
    """Analytic (A, B) at upright, zero velocity, zero force."""
    p = p or Params()
    M0 = mass_matrix(np.zeros(3), p)
    Mi = np.linalg.inv(M0)
    a = p.m1 * p.lc1 + p.m2 * p.l1
    b = p.m2 * p.lc2
    G = np.zeros((3, 3))
    G[1, 1] = a * p.g
    G[2, 2] = b * p.g
    Cf = np.array([[-p.bc, 0, 0],
                   [0, -p.bj1 - p.bj2, p.bj2],
                   [0, p.bj2, -p.bj2]])
    A = np.zeros((6, 6))
    A[:3, 3:] = np.eye(3)
    A[3:, :3] = Mi @ G
    A[3:, 3:] = Mi @ Cf
    B = np.zeros((6, 1))
    B[3:, 0] = Mi @ np.array([1.0, 0, 0])
    return A, B


def linearize_fd(p=None, eps=1e-6):
    """Central finite-difference Jacobians of dp_env.dynamics at upright."""
    p = p or Params()
    A = np.zeros((6, 6))
    for i in range(6):
        e = np.zeros(6)
        e[i] = eps
        A[:, i] = (dynamics(e, 0.0, p) - dynamics(-e, 0.0, p)) / (2 * eps)
    B = ((dynamics(np.zeros(6), eps, p) - dynamics(np.zeros(6), -eps, p))
         / (2 * eps)).reshape(6, 1)
    return A, B


def controllability_rank(A, B):
    n = A.shape[0]
    C = np.hstack([np.linalg.matrix_power(A, k) @ B for k in range(n)])
    return int(np.linalg.matrix_rank(C)), C


def clqr(p=None, Q=DEFAULT_Q, R=DEFAULT_R):
    A, B = linearize(p)
    P = solve_continuous_are(A, B, Q, R)
    K = np.linalg.solve(R, B.T @ P)
    return K, A, B, P


def discretize(A, B, h):
    n, m = B.shape
    M = np.zeros((n + m, n + m))
    M[:n, :n] = A * h
    M[:n, n:] = B * h
    E = expm(M)
    return E[:n, :n], E[:n, n:]


def dlqr(p=None, ctrl_dt=0.005, Q=DEFAULT_Q, R=DEFAULT_R, delay=0):
    """Discrete LQR for ZOH ctrl_dt. Returns (K, Ad, Bd, P). For delay=0 K is
    1x6 acting on s. For delay=n>0 K is 1x(6+n) acting on [s, u_{k-n}...u_{k-1}]
    (oldest pending command first)."""
    A, B = linearize(p)
    Ad, Bd = discretize(A, B, ctrl_dt)
    if delay == 0:
        P = solve_discrete_are(Ad, Bd, Q, R)
        K = np.linalg.solve(R + Bd.T @ P @ Bd, Bd.T @ P @ Ad)
        return K, Ad, Bd, P
    n = delay
    N = 6 + n
    Aa = np.zeros((N, N))
    Ba = np.zeros((N, 1))
    Aa[:6, :6] = Ad
    Aa[:6, 6:7] = Bd          # oldest pending command is applied next
    for i in range(n - 1):
        Aa[6 + i, 6 + i + 1] = 1.0
    Ba[-1, 0] = 1.0
    Qa = np.zeros((N, N))
    Qa[:6, :6] = Q
    P = solve_discrete_are(Aa, Ba, Qa, R)
    K = np.linalg.solve(R + Ba.T @ P @ Ba, Ba.T @ P @ Aa)
    return K, Aa, Ba, P


class StateFeedback:
    """Controller u = -K s (delay=0 or plain gain used under delay)."""
    def __init__(self, K):
        self.K = np.asarray(K).reshape(-1)[:6]

    def __call__(self, obs):
        return float(-self.K @ obs)


class DelayAwareLQR:
    """u = -K [s, pending commands]; remembers its last `delay` commands."""
    def __init__(self, K, delay):
        self.K = np.asarray(K).reshape(-1)
        self.delay = delay
        self.hist = [0.0] * delay

    def __call__(self, obs):
        z = np.concatenate([obs, self.hist])
        u = float(-self.K @ z)
        self.hist = self.hist[1:] + [u]
        return u


class ZeroForce:
    def __call__(self, obs):
        return 0.0


if __name__ == '__main__':
    K, A, B, P = clqr()
    r, _ = controllability_rank(A, B)
    print('open-loop poles', np.round(np.linalg.eigvals(A), 3))
    print('controllability rank', r, 'of 6')
    print('continuous K', np.round(K, 3))
    print('closed-loop poles', np.round(np.linalg.eigvals(A - B @ K), 3))
    for h in (0.005, 0.01, 0.02):
        Kd = dlqr(ctrl_dt=h)[0]
        print('discrete K h=%g' % h, np.round(Kd, 3))

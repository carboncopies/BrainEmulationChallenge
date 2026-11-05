"""Independent cross-check of an LQR-balanced inverted double pendulum on a cart.

Model: cart (mass M_CART) + two uniform rods (mass M_ROD, length L each), no friction.
State: s = [x, th1, th2, xdot, th1dot, th2dot], th1/th2 are absolute angles from upright.
Input: horizontal force F on the cart.
"""
import numpy as np
from scipy.linalg import solve_continuous_are

M_CART = 1.0
M_ROD = 0.1
L = 0.5
G = 9.81
A_C = L / 2                 # pivot -> rod centre of mass
I_C = M_ROD * L**2 / 12     # rod inertia about its own centre

Q = np.diag([1.0, 100.0, 100.0, 1.0, 1.0, 1.0])
R = np.array([[0.1]])

SIM_T = 180.0
DT = 5e-3
TH0 = 0.02
TILT_LIMIT = np.deg2rad(10.0)


def mass_matrix(q):
    th1, th2 = q[1], q[2]
    c1, c2, c12 = np.cos(th1), np.cos(th2), np.cos(th1 - th2)
    m, a = M_ROD, A_C
    return np.array([
        [M_CART + 2 * m, m * (a + L) * c1, m * a * c2],
        [m * (a + L) * c1, m * a * a + m * L * L + I_C, m * L * a * c12],
        [m * a * c2, m * L * a * c12, m * a * a + I_C],
    ])


def mass_derivs(q):
    # dM[j] = d M / d q_j
    th1, th2 = q[1], q[2]
    s1, s2, s12 = np.sin(th1), np.sin(th2), np.sin(th1 - th2)
    m, a = M_ROD, A_C
    dM = np.zeros((3, 3, 3))
    dM[1, 0, 1] = dM[1, 1, 0] = -m * (a + L) * s1
    dM[1, 1, 2] = dM[1, 2, 1] = -m * L * a * s12
    dM[2, 0, 2] = dM[2, 2, 0] = -m * a * s2
    dM[2, 1, 2] = dM[2, 2, 1] = m * L * a * s12
    return dM


def gravity_grad(q):
    # dV/dq for V = m g (y1 + y2), y1 = a cos th1, y2 = L cos th1 + a cos th2
    th1, th2 = q[1], q[2]
    m, a = M_ROD, A_C
    return np.array([0.0, -m * G * (a + L) * np.sin(th1), -m * G * a * np.sin(th2)])


def coriolis_term(q, qd):
    # h_k = sum_ij Gamma_kij qd_i qd_j, Gamma_kij = 1/2 (dM_ki/dq_j + dM_kj/dq_i - dM_ij/dq_k)
    dM = mass_derivs(q)
    t1 = np.einsum('jki,i,j->k', dM, qd, qd)
    t2 = np.einsum('ikj,i,j->k', dM, qd, qd)
    t3 = np.einsum('kij,i,j->k', dM, qd, qd)
    return 0.5 * (t1 + t2 - t3)


def dynamics(s, F):
    q, qd = s[:3], s[3:]
    rhs = np.array([F, 0.0, 0.0]) - coriolis_term(q, qd) - gravity_grad(q)
    qdd = np.linalg.solve(mass_matrix(q), rhs)
    return np.concatenate([qd, qdd])


def linear_model():
    m, a = M_ROD, A_C
    M0 = mass_matrix(np.zeros(3))
    K_grav = np.diag([0.0, m * G * (a + L), m * G * a])
    M0_inv = np.linalg.inv(M0)
    A = np.zeros((6, 6))
    A[:3, 3:] = np.eye(3)
    A[3:, :3] = M0_inv @ K_grav
    B = np.zeros((6, 1))
    B[3:, 0] = M0_inv[:, 0]
    return A, B


def main():
    A, B = linear_model()

    # Cross-check analytic A against a numerical Jacobian of the nonlinear model.
    eps = 1e-6
    A_num = np.zeros((6, 6))
    for i in range(6):
        e = np.zeros(6)
        e[i] = eps
        A_num[:, i] = (dynamics(e, 0.0) - dynamics(-e, 0.0)) / (2 * eps)
    print(f"max |A_analytic - A_numeric_jacobian| = {np.max(np.abs(A - A_num)):.3e}")

    ctrb = np.hstack([np.linalg.matrix_power(A, k) @ B for k in range(6)])
    rank = np.linalg.matrix_rank(ctrb)
    print(f"controllability rank = {rank} / 6  ->  {'controllable' if rank == 6 else 'NOT controllable'}")

    eig_ol = np.linalg.eigvals(A)
    eig_ol = eig_ol[np.argsort(eig_ol.real)]
    print("open-loop eigenvalues:", np.array2string(eig_ol, precision=4))

    P = solve_continuous_are(A, B, Q, R)
    K = np.linalg.solve(R, B.T @ P)
    print("LQR gain K =", np.array2string(K, precision=4))
    eig_cl = np.linalg.eigvals(A - B @ K)
    eig_cl = eig_cl[np.argsort(eig_cl.real)]
    print("closed-loop eigenvalues:", np.array2string(eig_cl, precision=4))

    n_steps = int(round(SIM_T / DT))
    s = np.zeros(6)
    s[1] = TH0
    states = np.empty((n_steps + 1, 6))
    forces = np.empty(n_steps + 1)
    states[0] = s
    forces[0] = -(K @ s).item()

    for k in range(n_steps):
        def f(y):
            return dynamics(y, -(K @ y).item())
        k1 = f(s)
        k2 = f(s + 0.5 * DT * k1)
        k3 = f(s + 0.5 * DT * k2)
        k4 = f(s + DT * k3)
        s = s + DT / 6.0 * (k1 + 2 * k2 + 2 * k3 + k4)
        states[k + 1] = s
        forces[k + 1] = -(K @ s).item()

    both_upright = (np.abs(states[:, 1]) <= TILT_LIMIT) & (np.abs(states[:, 2]) <= TILT_LIMIT)
    frac = both_upright.mean()
    rms_F = np.sqrt(np.mean(forces**2))
    max_x = np.max(np.abs(states[:, 0]))

    print(f"simulated {SIM_T:.0f} s, RK4 dt={DT*1e3:.1f} ms, {n_steps} steps")
    print(f"fraction of time both links within 10 deg = {frac:.4f}")
    print(f"RMS force = {rms_F:.4f} N")
    print(f"max |x| = {max_x:.4f} m")
    print("final state:", np.array2string(states[-1], precision=5))


if __name__ == "__main__":
    main()

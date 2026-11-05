# Cross-check notes: cart + double inverted pendulum (LQR)

Implementation: `crosscheck.py` (numpy + scipy only).

## Parameters

- Cart mass M = 1.0 kg
- Rod mass m = 0.1 kg each, rod length L = 0.5 m each
- Pivot to rod centre a = L/2 = 0.25 m
- Rod inertia about its centre I_c = m L²/12
- Gravity g = 9.81 m/s² (assumed; not given in the brief)
- Friction-free; no actuator saturation

## Coordinates

- q = [x, θ1, θ2], s = [q, q̇]
- θ1, θ2 are absolute angles of each rod from upright (θ = 0 is upright)
- Rod 1 centre: (x + a sin θ1, a cos θ1)
- Rod 2 pivot: (x + L sin θ1, L cos θ1); rod 2 centre: pivot + (a sin θ2, a cos θ2)

## Equations of motion

Lagrangian with T = ½ q̇ᵀ M(q) q̇ and V = m g [(a + L) cos θ1 + a cos θ2].

Mass matrix:

- M11 = M + 2m
- M12 = m (a + L) cos θ1
- M13 = m a cos θ2
- M22 = m a² + m L² + I_c
- M23 = m L a cos(θ1 − θ2)
- M33 = m a² + I_c

Full nonlinear model:

M(q) q̈ + h(q, q̇) + ∂V/∂q = [F, 0, 0]ᵀ

- h_k = Σᵢⱼ Γ_kij q̇ᵢ q̇ⱼ, with Γ_kij = ½(∂M_ki/∂qⱼ + ∂M_kj/∂qᵢ − ∂M_ij/∂q_k)
- ∂V/∂q = [0, −m g (a + L) sin θ1, −m g a sin θ2]

Equations of motion are solved as q̈ = M⁻¹([F,0,0]ᵀ − h − ∂V/∂q).

## Linearisation about upright (q = 0, q̇ = 0)

h is quadratic in q̇ and vanishes at linear order. The gravity term linearises to −K_g q with

K_g = diag(0, m g (a + L), m g a)

With M0 = M(0):

- q̈ = M0⁻¹ (K_g q + B F), B = [1, 0, 0]ᵀ
- A = [[0₃, I₃], [M0⁻¹ K_g, 0₃]]
- B_s = [0₃; M0⁻¹ B]

The analytic A is checked against a central-difference Jacobian of the nonlinear model. Max difference is 1.7e-10.

## Controllability

Controllability matrix [B, AB, …, A⁵B], checked by `matrix_rank`.

## LQR

- Q = diag(1, 100, 100, 1, 1, 1), R = 0.1
- P from the continuous algebraic Riccati equation (`scipy.linalg.solve_continuous_are`)
- K = R⁻¹ Bᵀ P, control law F = −K s (s includes x)

## Simulation

- Nonlinear model, RK4, dt = 5 ms, duration 180 s (36 000 steps)
- Initial state: θ1 = 0.02 rad, all other states zero
- Force evaluated from the feedback law at each RK4 stage
- Metrics over all recorded states:
  - fraction of samples with |θ1| ≤ 10° and |θ2| ≤ 10°
  - RMS of F = −K s over the samples
  - max |x|

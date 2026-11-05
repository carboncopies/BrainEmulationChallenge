"""pong_spec.py: the step-1 wiring spec as data, shared by step 2 scripts.

Roles: B0..B{N-1} ball-y place cells, P0..P{N-1} paddle-y place cells,
U0..U{N-1} / D0..D{N-1} comparators, UP, DOWN.
Intended edges (pre, post, sign):
  B_i -> U_i, D_i                 AMPA (+1)
  P_j -> U_i  for j >= i          GABA (-1)
  P_j -> D_i  for j <= i          GABA (-1)
  U_i -> UP, D_i -> DOWN          AMPA (+1)
"""
N = 8


def roles(n=N):
    return (['B%d' % i for i in range(n)] + ['P%d' % i for i in range(n)] +
            ['U%d' % i for i in range(n)] + ['D%d' % i for i in range(n)] + ['UP', 'DOWN'])


def edges(n=N, paddle='gaba'):
    """Returns list of (cls, pre_role, post_role, sign).

    paddle='gaba': step-1 spec (P_j inhibits U_i for j>=i and D_i for j<=i).
    paddle='ampa': excitatory coincidence variant (P_j excites U_i for j<i and D_i for j>i;
                   U_i/D_i fire only when B_i AND a suitable P_j arrive together).
                   Needed because NES can only SET AMPA strengths (see README).
    """
    e = []
    for i in range(n):
        e.append(('B->U', 'B%d' % i, 'U%d' % i, +1))
        e.append(('B->D', 'B%d' % i, 'D%d' % i, +1))
    for i in range(n):
        for j in range(n):
            if paddle == 'gaba':
                if j >= i:
                    e.append(('P->U', 'P%d' % j, 'U%d' % i, -1))
                if j <= i:
                    e.append(('P->D', 'P%d' % j, 'D%d' % i, -1))
            else:
                if j < i:
                    e.append(('P->U', 'P%d' % j, 'U%d' % i, +1))
                if j > i:
                    e.append(('P->D', 'P%d' % j, 'D%d' % i, +1))
    for i in range(n):
        e.append(('U->UP', 'U%d' % i, 'UP', +1))
        e.append(('D->DOWN', 'D%d' % i, 'DOWN', +1))
    return e


EDGE_CLASSES = ['B->U', 'B->D', 'P->U', 'P->D', 'U->UP', 'D->DOWN']


def role_class(r):
    return r.rstrip('0123456789') if r not in ('UP', 'DOWN') else r


# Soma layout (um) used by the Netmorph config: y encodes the bin.
# Every role is its own one-neuron Netmorph region named after the role, so
# the region name is the role label (no guessing from IDs).
Y_STEP = 50.0
X_STAGE = 300.0
Z_TOP, Z_BOT = -250.0, -450.0


def layout(n=N):
    pos = {}
    for i in range(n):
        y = Y_STEP * i
        pos['B%d' % i] = (0.0, y, Z_TOP)
        pos['P%d' % i] = (0.0, y, Z_BOT)
        pos['U%d' % i] = (X_STAGE, y, Z_TOP)
        pos['D%d' % i] = (X_STAGE, y, Z_BOT)
    pos['UP'] = (2 * X_STAGE, Y_STEP * (n - 1), Z_TOP)
    pos['DOWN'] = (2 * X_STAGE, 0.0, Z_BOT)
    return pos

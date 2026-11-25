import sys, json, numpy as np
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/ripple_overlap_j')
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/lp_weights')
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/fresh_learn')
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/partial_cue')
import ovlib as O
SEEDS = [11111, 16180, 22222, 27182, 31415, 33333, 44444, 55555, 66666, 77777]
T = 16.5; THETA = T - 4.125; CAP = 6.86; THR = 4.125
def G(seed):
    D, P = O.load('s%d' % seed); P = np.array(P, float); np.fill_diagonal(P, 0); return P

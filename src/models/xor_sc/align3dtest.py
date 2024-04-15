#!/usr/bin/env python3
# align3dtest.py
# Randal A. Koene, 20240415

'''
These are 3D alignment tests between reported neuron centers in the
ground-truth and in the emulation.

Alignment is the first step to validation, because once there is a
clear mapping between ground-truth neurons and emulation neurons,
then a detailed and informative validation of structural and
functional differences is much easier and better.
'''

import argparse
from datetime import datetime

import vbpcommon
from BrainGenix.BG_API import Credentials, SimClient

import BrainGenix.NES as NES
import BrainGenix

from connectomes import get_connectomes

Parser = argparse.ArgumentParser(description="test 3D alignment of point clouds")
Parser.add_argument("-Local", action='store_true', help="Run on local NES server")
Parser.add_argument("-Remote", action='store_true', help="Run on remote NES server")
Args = Parser.parse_args()

runtime_ms=500.0
savefolder = 'output/'+str(datetime.now()).replace(":", "_")+'-validation'
figspecs = {
    'figsize': (6,6),
    'linewidth': 0.5,
    'figext': 'pdf',
}

groundtruth, emulation = get_connectomes(Args, user='Admonishing', passwd='Instruction')

# The first test will use pyCPD, a Python package on PiPy that used CPD for
# point cloud registration.
# Starting with the example at https://github.com/siavashk/pycpd/blob/master/examples/fish_deformable_3D.py


from functools import partial
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from pycpd import DeformableRegistration, RigidRegistration
import numpy as np


def visualize(iteration, error, X, Y, ax):
    plt.cla()
    ax.scatter(X[:, 0],  X[:, 1], X[:, 2], color='red', label='Target')
    ax.scatter(Y[:, 0],  Y[:, 1], Y[:, 2], color='blue', label='Source')
    ax.text2D(0.87, 0.92, 'Iteration: {:d}'.format(
        iteration), horizontalalignment='center', verticalalignment='center', transform=ax.transAxes, fontsize='x-large')
    ax.legend(loc='upper left', fontsize='x-large')
    plt.draw()
    #plt.pause(0.5)
    plt.pause(0.001)


def main(fish_target=None, fish_source=None):
    if fish_target is None:
        fish_target = np.loadtxt('./fishtarget.txt')
        fish_source = np.loadtxt('./fishsource.txt')
        # Proving that this registration method is robust to changes in
        # the way point clouds are sorted and to missing points, as well
        # as rotation:
        # Let's pretend that 2 points were missed:
        fish_source = np.delete(fish_source, slice(10, 13), 0)
        print(fish_source[0:5,:])
        # Let's shuffle the points:
        np.random.shuffle(fish_source)
        # Rotation
        theta = np.radians(30)
        c, s = np.cos(theta), np.sin(theta)
        R = np.array(((c, -s), (s, c)))
        # Define resulting zero array B.
        rotated_fish_source = np.zeros(fish_source.shape)
        # Loop over rows and determine rotated vectors.
        #for ra,rb in zip(fish_source, rotated_fish_source):
        #    rb = np.dot(R, ra)
        for i in range(fish_source.shape[0]):
            rotated_fish_source[i,:] = R.dot(fish_source[i, :])
        fish_source = rotated_fish_source
        print(fish_source[0:5,:])

    print('Points in fishtarget.txt: '+str(fish_target.shape))
    X1 = np.zeros((fish_target.shape[0], fish_target.shape[1] + 1))
    X1[:, :-1] = fish_target
    X2 = np.ones((fish_target.shape[0], fish_target.shape[1] + 1))
    X2[:, :-1] = fish_target
    X = np.vstack((X1, X2))

    print('Points in fishsource.txt: '+str(fish_source.shape))
    Y1 = np.zeros((fish_source.shape[0], fish_source.shape[1] + 1))
    Y1[:, :-1] = fish_source
    Y2 = np.ones((fish_source.shape[0], fish_source.shape[1] + 1))
    Y2[:, :-1] = fish_source
    Y = np.vstack((Y1, Y2))

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    callback = partial(visualize, ax=ax)

    reg = DeformableRegistration(**{'X': X, 'Y': Y})
    reg.register(callback)
    plt.show()

def rigid_main(fish_target=None, fish_source=None, true_rigid=True):
    if fish_target is None:
        fish_target = np.loadtxt('./fishtarget.txt')
        fish_source = np.loadtxt('./fishsource.txt')
        X1 = np.zeros((fish_target.shape[0], fish_target.shape[1] + 1))
        X1[:, :-1] = fish_target
        X2 = np.ones((fish_target.shape[0], fish_target.shape[1] + 1))
        X2[:, :-1] = fish_target
        X = np.vstack((X1, X2))

        if true_rigid is True:
            theta = np.pi / 6.0
            R = np.array([[np.cos(theta), -np.sin(theta), 0], [np.sin(theta), np.cos(theta), 0], [0, 0, 1]])
            t = np.array([0.5, 1.0, 0.0])
            Y = np.dot(X, R) + t
        else:
            Y1 = np.zeros((fish_source.shape[0], fish_source.shape[1] + 1))
            Y1[:, :-1] = fish_source
            Y2 = np.ones((fish_source.shape[0], fish_source.shape[1] + 1))
            Y2[:, :-1] = fish_source
            Y = np.vstack((Y1, Y2))

    else:
        X = fish_target
        Y = fish_source

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    callback = partial(visualize, ax=ax)

    reg = RigidRegistration(**{'X': X, 'Y': Y}) #, tolerance=0.00001)
    reg.register(callback)
    plt.show()

all_groundtruth_somas = groundtruth.get_all_soma_coords()
print('\nNumber of Somas in ground-truth system: '+str(len(all_groundtruth_somas)))

all_emulation_somas = emulation.get_all_soma_coords()
print('Number of Somas in emulation system   : '+str(len(all_emulation_somas)))


#main(np.array(all_groundtruth_somas), np.array(all_emulation_somas))
#main()
rigid_main(np.array(all_groundtruth_somas), np.array(all_emulation_somas), true_rigid=False)

def distance(p:np.array, q:np.array)->float:
    return np.linalg.norm(p-q)

def find_nearest(p:np.array, candidates:np.array)->tuple:
    smallest = 999999999.0
    smallest_idx = -1
    for row in range(candidates.shape[0]):
        d = distance(p, candidates[row,:])
        if d < smallest:
            smallest = d
            smallest_idx = row
    return (smallest_idx, smallest)

def proximity_score(set_a:np.array, set_b:np.array)->float:
    tot_distance = 0.0
    for row in range(set_a.shape[0]):
        idx, d = find_nearest(set_a[row,:], set_b)
        tot_distance += d
    return tot_distance

g = np.array(all_groundtruth_somas)
e = np.array(all_emulation_somas)
# initial_score = proximity_score(g, e)
# print(initial_score)

def vis(X, Y, ax):
    plt.cla()
    ax.scatter(X[:, 0],  X[:, 1], X[:, 2], color='red', label='Target')
    ax.scatter(Y[:, 0],  Y[:, 1], Y[:, 2], color='blue', label='Source')
    ax.text2D(0.87, 0.92, 'Rotated', horizontalalignment='center', verticalalignment='center', transform=ax.transAxes, fontsize='x-large')
    ax.legend(loc='upper left', fontsize='x-large')
    plt.draw()
    #plt.pause(0.5)
    plt.pause(0.00001)

def RotZMat(angle:float)->np.array:
    theta = np.radians(angle)
    c, s = np.cos(theta), np.sin(theta)
    return np.array([[c, -s, 0],
                     [s,  c, 0],
                     [0,  0, 1]])

smallest_score = 999999999.0
smallest_score_angle = 0
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
angle = 0
e_rotated = e
for i in range(0, 36):
    score = proximity_score(g, e_rotated)
    if score < smallest_score:
        smallest_score = score
        smallest_score_angle = angle
    vis(g, e_rotated, ax)
    angle += 10
    rotz = RotZMat(angle)
    e_rotated = e.dot(rotz)

print('Smallest proximity score is %.2f at angle %d.' % (smallest_score, smallest_score_angle))
rotz = RotZMat(smallest_score_angle)
e_rotated = e.dot(rotz)
vis(g, e_rotated, ax)
plt.show()

# The second test will use the PCL (Point Cloud Library) and possibly an ICP
# implementation in C++.

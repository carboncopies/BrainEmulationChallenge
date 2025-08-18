#!../../venv/bin/python
# A little tool to more flexibly visualize cells from
# acquisition.
#
# Remember, this needs: source BrainEmulationChallenge/venv/bin/activate
#
# Randal A. Koene, 20250819

import numpy as np
import argparse
import os
import pickle
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # needed for 3D projection
#from matplotlib.animation import FuncAnimation, PillowWriter

Parser = argparse.ArgumentParser(description="Visualize cells from acquisition")
Parser.add_argument("-f", type=str, help="Data file path")
Parser.add_argument("-x", default=12, type=float, help="Figure width (inches)")
Parser.add_argument("-y", default=12, type=float, help="Figure height (inches)")
Args = Parser.parse_args()

if not Args.f:
    datapath = input('Data path: ')
    Args.f = str(datapath)

if not os.path.exists(Args.f):
    print('File not found at '+str(Args.f))
    exit(1)

with open(Args.f, 'rb') as f:
    data = pickle.load(f)

print('Loaded data.')

FIGSIZE=(Args.x, Args.y)

def plot_neuron_somas(pyramidal, interneurons, point_size=30, color='blue'):
    """
    Plot neuron soma centers given a list or array of 3D coordinates.

    Parameters:
        coords (list or np.ndarray): List/array of shape (N, 3) with x, y, z coordinates.
        point_size (int): Size of scatter points.
        color (str): Color of scatter points.
    """
    pyramidal = np.array(pyramidal)
    interneurons = np.array(interneurons)

    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection='3d')

    ax.scatter(pyramidal[:, 0], pyramidal[:, 1], pyramidal[:, 2], 
               s=point_size, c='blue', alpha=0.7)
    ax.scatter(interneurons[:, 0], interneurons[:, 1], interneurons[:, 2], 
               s=point_size, c='red', alpha=0.7)

    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.set_title("Neuron Soma Centers")

    plt.show()

pyramidal = []
interneuron = []
for n in range(len(data['SomaCenters'])):
    if data['SomaTypes'][n] == 1:
        pyramidal.append(data['SomaCenters'][n])
    else:
        interneuron.append(data['SomaCenters'][n])

plot_neuron_somas(pyramidal, interneuron)

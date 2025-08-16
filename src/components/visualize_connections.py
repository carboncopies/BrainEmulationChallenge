#!../../venv/bin/python
# A little tool to more flexibly visualize connections from
# acquisition.
#
# Remember, this needs: source BrainEmulationChallenge/venv/bin/activate
#
# Randal A. Koene, 20250816

import numpy as np
import argparse
import os
import pickle
import matplotlib.pyplot as plt
#from matplotlib.animation import FuncAnimation, PillowWriter

Parser = argparse.ArgumentParser(description="Visualize connections from acquisition")
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

#colors = plt.cm.tab10(np.linspace(0, 1, len(Vm_cells))) # Using 'tab10' colormap

def plot_connections(pre_list:list, post_list:list, vmin=None, vmax=None, cmap='viridis'):
    # Alternative way to write it: connectionmatrix = data[cell_list,:][:,cell_list]
    connectionmatrix = data[np.ix_(pre_list, post_list)]

    if vmin is None:
        vmin = np.min(connectionmatrix)
    if vmax is None:
        vmax = np.max(connectionmatrix)

    plt.figure(figsize=FIGSIZE)
    im = plt.imshow(connectionmatrix, origin='lower', aspect='auto',
                    vmin=vmin, vmax=vmax, cmap=cmap)
    plt.colorbar(im, label='value')
    plt.xlabel('Postsynaptic neuron index')
    plt.ylabel('Presynaptic neuron index')
    plt.title('Connections Matrix')
    plt.tight_layout()
    plt.show()
    #plt.draw()


# Show all cells first (static or animated)
cell_indices = list(range(data.shape[0]))
plot_connections(cell_indices, cell_indices)

# Then allow user to pick subset
pre_indices = eval(input('From presynaptic neurons (empty list=all): '))
if len(pre_indices)==0:
    pre_indices = list(range(data.shape[0]))
post_indices = eval(input('To postsynaptic neurons (empty list=all): '))
if len(post_indices)==0:
    post_indices = list(range(data.shape[0]))
print(pre_indices)
print(post_indices)
plot_connections(pre_indices, post_indices)

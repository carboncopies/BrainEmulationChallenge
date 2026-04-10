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
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

Parser = argparse.ArgumentParser(description="Visualize cells from acquisition")
Parser.add_argument("-f", type=str, help="Data file path")
Parser.add_argument("-c", type=str, help="Connections file path")
Parser.add_argument("-x", default=12, type=float, help="Figure width (inches)")
Parser.add_argument("-y", default=12, type=float, help="Figure height (inches)")
Parser.add_argument("-Shape", default='box', type=str, help="Soma as box or sphere")
Parser.add_argument("-Ring", default=None, type=str, help="Ring display: id, proximity")
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

def plot_neuron_somas(pyramidal, pyramidal_size, interneurons, interneurons_size):
    """
    Plot neuron soma centers given a list or array of 3D coordinates.

    Parameters:
        coords (list or np.ndarray): List/array of shape (N, 3) with x, y, z coordinates.
        point_size (int): Size of scatter points.
        color (str): Color of scatter points.
    """
    pyramidal = np.array(pyramidal)
    interneurons = np.array(interneurons)
    pyramidal_size = np.array(pyramidal_size)
    interneurons_size = np.array(interneurons_size)

    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection='3d')

    # Get the current axes limits
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()

    # Calculate the scaling factor (using x-axis)
    x_range = xmax - xmin
    fig_width, fig_height = fig.get_size_inches()
    dpi = fig.dpi
    x_scale = (fig_width * dpi) / x_range

    # Scale the data sizes to pixel units
    pyramidal_size = pyramidal_size * x_scale  # Or use y_scale if you prefer
    interneurons_size = interneurons_size * x_scale


    ax.scatter(pyramidal[:, 0], pyramidal[:, 1], pyramidal[:, 2], 
               s=pyramidal_size, c='blue', alpha=0.7)
    ax.scatter(interneurons[:, 0], interneurons[:, 1], interneurons[:, 2], 
               s=interneurons_size, c='red', alpha=0.7)

    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.set_title("Neuron Soma Centers")

    plt.show()

def plot_sphere(ax, center, radius, color="blue", alpha=0.3):
    """Plot a sphere at given center with given radius."""
    u = np.linspace(0, 2 * np.pi, 12) #24)
    v = np.linspace(0, np.pi, 6) #12)
    x = center[0] + radius * np.outer(np.cos(u), np.sin(v))
    y = center[1] + radius * np.outer(np.sin(u), np.sin(v))
    z = center[2] + radius * np.outer(np.ones_like(u), np.cos(v))
    ax.plot_surface(x, y, z, color=color, alpha=alpha, linewidth=0)

def plot_box(ax, center, size, color="red", alpha=0.3):
    """Plot an axis-aligned box given center and (dx, dy, dz) size."""
    dx, dy, dz = size
    # Corner points
    x = [center[0] - dx/2, center[0] + dx/2]
    y = [center[1] - dy/2, center[1] + dy/2]
    z = [center[2] - dz/2, center[2] + dz/2]
    # 8 vertices of the cube
    vertices = np.array([[x[i], y[j], z[k]] for i in [0,1] for j in [0,1] for k in [0,1]])
    # 6 faces
    faces = [[vertices[j] for j in [0,1,3,2]],
             [vertices[j] for j in [4,5,7,6]],
             [vertices[j] for j in [0,1,5,4]],
             [vertices[j] for j in [2,3,7,6]],
             [vertices[j] for j in [0,2,6,4]],
             [vertices[j] for j in [1,3,7,5]]]
    ax.add_collection3d(Poly3DCollection(faces, facecolors=color, alpha=alpha, linewidths=0.5))

def set_axes_equal(ax):
    """Set 3D plot axes to equal scale so a sphere or cube looks correct."""
    x_limits = ax.get_xlim3d()
    y_limits = ax.get_ylim3d()
    z_limits = ax.get_zlim3d()

    x_range = abs(x_limits[1] - x_limits[0])
    x_middle = np.mean(x_limits)
    y_range = abs(y_limits[1] - y_limits[0])
    y_middle = np.mean(y_limits)
    z_range = abs(z_limits[1] - z_limits[0])
    z_middle = np.mean(z_limits)

    plot_radius = 0.5*max([x_range, y_range, z_range])

    ax.set_xlim3d([x_middle - plot_radius, x_middle + plot_radius])
    ax.set_ylim3d([y_middle - plot_radius, y_middle + plot_radius])
    ax.set_zlim3d([z_middle - plot_radius, z_middle + plot_radius])


def plot_connections(ax, objects, conn_matrix, color="k", alpha=0.3):
    """
    Plot straight-line connections between neuron centers.
    conn_matrix[i,j] != 0 means a connection from i -> j.
    """
    n = len(objects)
    for i in range(n):
        for j in range(n):
            if conn_matrix[i, j] != 0:  # connection exists
                p1 = np.array(objects[i]["center"])
                p2 = np.array(objects[j]["center"])
                ax.plot(*zip(p1, p2), color=color, alpha=alpha, linewidth=1)


def plot_neurons(objects, connectionmatrix=None):
    """objects: list of dicts with type='sphere' or 'box'"""
    fig = plt.figure(figsize=(8,8))
    ax = fig.add_subplot(111, projection='3d')

    for obj in objects:
        if obj["type"] == "sphere":
            plot_sphere(ax, obj["center"], obj["radius"], obj.get("color","blue"))
        elif obj["type"] == "box":
            plot_box(ax, obj["center"], obj["size"], obj.get("color","red"))

    # Set equal aspect ratio
    all_points = []
    for obj in objects:
        if obj["type"] == "sphere":
            r = obj["radius"]
            all_points.append(np.array(obj["center"]) + r)
            all_points.append(np.array(obj["center"]) - r)
        elif obj["type"] == "box":
            dx,dy,dz = obj["size"]
            all_points.append(np.array(obj["center"]) + np.array([dx/2,dy/2,dz/2]))
            all_points.append(np.array(obj["center"]) - np.array([dx/2,dy/2,dz/2]))

    all_points = np.array(all_points)
    mins, maxs = all_points.min(axis=0), all_points.max(axis=0)
    for i, (mn,mx) in enumerate(zip(mins,maxs)):
        getattr(ax, f"set_{'xyz'[i]}lim")((mn, mx))

    if connectionmatrix is not None:
        plot_connections(ax, objects, connectionmatrix)

    set_axes_equal(ax)

    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    plt.show()


def ring_positions(N, radius=100, z=0):
    """
    Return N equidistant positions on a ring of given radius at height z.
    """
    angles = np.linspace(0, 2*np.pi, N, endpoint=False)
    positions = []
    for theta in angles:
        x = radius * np.cos(theta)
        y = radius * np.sin(theta)
        positions.append([x, y, z])
    return positions

def sum_squared_distance(p1, p2)->float:
    return (p2[0]-p1[0])**2 + (p2[1]-p1[1])**2 + (p2[2]-p1[2])**2

def find_nearest(neurons, this_id, ids)->tuple:
    p1 = neurons[this_id]['center']
    nearest = -1
    nearest_idx = -1
    proximity_squared = 999999999999.9
    for i in range(len(ids)):
        that_id = ids[i]
        that_prox = sum_squared_distance(p1, neurons[that_id]['center'])
        if that_prox < proximity_squared:
            proximity_squared = that_prox
            nearest = that_id
            nearest_idx = i
    return nearest, nearest_idx

# pyramidal = []
# pyramidal_size = []
# interneuron = []
# interneuron_size = []
# for n in range(len(data['SomaCenters'])):
#     if data['SomaTypes'][n] == 1:
#         pyramidal.append(data['SomaCenters'][n])
#         pyramidal_size.append(data['SomaRadius'][n]*2)
#     else:
#         interneuron.append(data['SomaCenters'][n])
#         interneuron_size.append(data['SomaRadius'][n]*2)

# plot_neuron_somas(pyramidal, pyramidal_size, interneuron, interneuron_size)


shape = Args.Shape
neurons = []
for n in range(len(data['SomaCenters'])):

    r = data['SomaRadius'][n]
    if data['SomaTypes'][n] == 1: # pyramidal
        _neuron = {
            'id': n,
            'type': shape,
            'center': data['SomaCenters'][n],
            'radius': r,
            'size': [2*r, 2*r, 2*r],
            'color': 'blue',
        }
    else:
        _neuron = {
            'id': n,
            'type': shape,
            'center': data['SomaCenters'][n],
            'radius': r,
            'size': [2*r, 2*r, 2*r],
            'color': 'red',
        }
    neurons.append(_neuron)

if Args.Ring:
    ringpositions = ring_positions(len(neurons), radius=200)
    if Args.Ring == 'id':
        for n in range(len(neurons)):
            neurons[n]['center'] = ringpositions[n]
    elif Args.Ring == 'proximity':
        ids = list(range(len(neurons)))
        pos_id = []
        this_id = ids.pop(0)
        pos_id.append( (this_id, ringpositions.pop(0)) )
        while len(ids)>0:
            nearest, nearest_idx = find_nearest(neurons, this_id, ids)
            this_id = nearest
            ids.pop(nearest_idx)
            pos_id.append( (this_id, ringpositions.pop(0)) )
        for posid in pos_id:
            n, xyz = posid
            neurons[n]['center'] = xyz


if Args.c:
    with open(Args.c, 'rb') as f:
        connectionmatrix = pickle.load(f)
    print('Loaded connections.')
else:
    connectionmatrix = None

plot_neurons(neurons, connectionmatrix)

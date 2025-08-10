#!../../venv/bin/python
# A little tool to more flexibly visualize recorded data from
# acquisition.
#
# Remember, this needs: source BrainEmulationChallenge/venv/bin/activate
#
# Randal A. Koene, 20250805

import numpy as np
import argparse
import os
import pickle
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter

Parser = argparse.ArgumentParser(description="Visualize recorded data from acquisition")
Parser.add_argument("-f", type=str, help="Data file path")
Parser.add_argument("--animate", action="store_true", help="Animate the plots over time")
Parser.add_argument("--save", type=str, help="Save animation to file (mp4 or gif)")
Args = Parser.parse_args()

if not Args.f:
    datapath = input('Data path: ')
    Args.f = str(datapath)

if not os.path.exists(Args.f):
    print('File not found at '+str(Args.f))
    exit(1)

with open(Args.f, 'rb') as f:
    data_dict = pickle.load(f)

print('Loaded data.')

t_ms = data_dict['t_ms']
Vm_cells = data_dict['Vm_cells']

colors = plt.cm.tab10(np.linspace(0, 1, len(Vm_cells))) # Using 'tab10' colormap

def plot_subset(cell_indices:list):
    fig, axs = plt.subplots(len(cell_indices), 1, figsize=(18, 12), sharex=True)
    if len(cell_indices) == 1:
        axs = [axs]  # make iterable

    for i, idx in enumerate(cell_indices):
        axs[i].plot(t_ms, Vm_cells[idx], label=str(idx), color=colors[i])
        axs[i].legend()
        axs[i].grid(True)

    plt.suptitle("Recorded acquisition data")
    plt.tight_layout()
    plt.show()

def animate_subset(cell_indices:list):
    fig, axs = plt.subplots(len(cell_indices), 1, figsize=(18, 12), sharex=True)
    if len(cell_indices) == 1:
        axs = [axs]  # make iterable

    lines = []
    for i, idx in enumerate(cell_indices):
        line, = axs[i].plot([], [], label=str(idx), color=colors[i])
        axs[i].set_xlim(t_ms[0], t_ms[-1])
        axs[i].set_ylim(min(Vm_cells[idx]), max(Vm_cells[idx]))
        axs[i].legend()
        axs[i].grid(True)
        lines.append(line)

    plt.suptitle("Animated acquisition data")
    plt.tight_layout()

    def init():
        for line in lines:
            line.set_data([], [])
        return lines

    def update(frame):
        for line, idx in zip(lines, cell_indices):
            line.set_data(t_ms[:frame], Vm_cells[idx][:frame])
        return lines

    ani = FuncAnimation(fig, update, frames=len(t_ms), init_func=init,
                        interval=20, blit=True, repeat=False)

    # Save animation if requested
    if Args.save:
        ext = os.path.splitext(Args.save)[1].lower()
        if ext == ".mp4":
            ani.save(Args.save, fps=50, extra_args=['-vcodec', 'libx264'])
            print(f"Animation saved to {Args.save}")
        elif ext == ".gif":
            ani.save(Args.save, writer=PillowWriter(fps=50))
            print(f"Animation saved to {Args.save}")
        else:
            print("Unsupported format. Use .mp4 or .gif")
    
    plt.show()

# Show all cells first (static or animated)
cell_list = list(range(len(Vm_cells)))
if Args.animate:
    animate_subset(cell_list)
else:
    plot_subset(cell_list)

# Then allow user to pick subset
cell_indices = eval(input('List of cells to show with brackets: '))
if Args.animate:
    animate_subset(cell_indices)
else:
    plot_subset(cell_indices)


# import numpy as np
# import argparse
# import os
# import pickle
# import matplotlib.pyplot as plt

# Parser = argparse.ArgumentParser(description="Visualize recorded data from acquisition")
# Parser.add_argument("-f", type=str, help="Data file path")
# Args = Parser.parse_args()

# if not Args.f:
# 	datapath = input('Data path: ')
# 	Args.f = str(datapath)

# if not os.path.exists(Args.f):
# 	print('File not found at '+str(Args.f))
# 	exit(1)

# with open(Args.f, 'rb') as f:
# 	data_dict = pickle.load(f)

# print('Loaded data.')

# t_ms = data_dict['t_ms']
# Vm_cells = data_dict['Vm_cells']

# colors = plt.cm.tab10(np.linspace(0, 1, len(Vm_cells))) # Using 'tab10' colormap

# def plot_subset(cell_indices:list):
# 	fig, axs = plt.subplots(len(cell_indices), 1, figsize=(18, 12), sharex=True) # was 2 and (12, 7)

# 	for i in range(len(cell_indices)):
# 		axs[i].plot(t_ms, Vm_cells[cell_indices[i]], label=str(cell_indices[i]), color=colors[i])
# 		#axs[i].set_ylabel("mV")
# 		axs[i].legend()
# 		axs[i].grid(True)

# 	plt.suptitle("Recorded acquisition data")
# 	plt.tight_layout()
# 	plt.show()

# plot_subset(list(range(len(Vm_cells))))

# cell_indices = eval(input('List of cells to show with brackets: '))

# plot_subset(cell_indices)

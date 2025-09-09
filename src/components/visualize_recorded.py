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

Parser = argparse.ArgumentParser(description="Visualize recorded data from acquisition")
Parser.add_argument("-f", type=str, help="Data file path")
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
	fig, axs = plt.subplots(len(cell_indices), 1, figsize=(18, 12), sharex=True) # was 2 and (12, 7)

	for i in range(len(cell_indices)):
		axs[i].plot(t_ms, Vm_cells[cell_indices[i]], label=str(cell_indices[i]), color=colors[i])
		#axs[i].set_ylabel("mV")
		axs[i].legend()
		axs[i].grid(True)

	plt.suptitle("Recorded acquisition data")
	plt.tight_layout()
	plt.show()

plot_subset(list(range(len(Vm_cells))))

cell_indices = eval(input('List of cells to show with brackets: '))

plot_subset(cell_indices)

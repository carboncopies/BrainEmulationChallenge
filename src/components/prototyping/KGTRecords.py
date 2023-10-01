# KGTRecords.py
# Randal A. Koene, 20230623

'''
Utility functions used with known ground-truth recorded data.
'''

import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

def plot_recorded(data:dict):
	if 't_ms' not in data:
		raise Exception('plot_recorded: Missing t_ms record.')
	t_ms = data['t_ms']
	Vm_cells = []
	for region in data:
		if region!='t_ms':
			region_data = data[region]
			for cell in region_data:
				cell_data = region_data[cell]
				if 'Vm' in cell_data:
					Vm_cells.append(cell_data['Vm'])
	fig = plt.figure(figsize=(4,4))
	plt.title('Recorded data')
	for c in range(len(Vm_cells)):
		plt.plot(t_ms, Vm_cells[c])
	plt.show()

def plot_electrodes(data:dict):
	if 't_ms' not in data:
		raise Exception('plot_electrodes: Missing t_ms record.')
	t_ms = data['t_ms']
	matchlen = len('electrode')
	for k in data.keys():
		if k[0:matchlen] == 'electrode':
			electrode_data = data[k]
			fig = plt.figure(figsize=(4,4))
			plt.title('Electrode %s' % k)
			E_mV = electrode_data['E']
			for site in range(len(E_mV)):
				plt.plot(t_ms, E_mV[site])
			plt.show()

def plot_calcium(data:dict):
	if 't_ms' not in data:
		raise Exception('plot_calcium: Missing t_ms record.')
	t_ms = data['t_ms']
	matchlen = len('calcium')
	for k in data.keys():
		if k[0:matchlen] == 'calcium':
			calcium_data = data[k]
			for indicator in calcium_data:
				image_stack = calcium_data[indicator]
				image_stack_size = len(image_stack)
				print('%s image stack size: %d' % (indicator, image_stack_size))
				for i in range(image_stack_size):
					print('Image %d (%s), sum of values = %f' % (i, str(image_stack[i].shape), image_stack[i].sum()))
					#img = Image.fromarray(image_stack[i])
					#plt.imshow(img)
					plt.imshow(image_stack[i], cmap='gray', vmin=0, vmax=255)
					plt.show()

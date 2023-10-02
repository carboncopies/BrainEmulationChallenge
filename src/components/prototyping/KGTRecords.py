# KGTRecords.py
# Randal A. Koene, 20230623

'''
Utility functions used with known ground-truth recorded data.
'''

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
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

# frames = [Image.open(image) for image in glob.glob(f"{frame_folder}/*.JPG")]
# frame_one = frames[0]
# frame_one.save("my_awesome.gif", format="GIF", append_images=frames, save_all=True, duration=100, loop=0)

def plot_calcium(data:dict, gifpath:str, show_all=False):
	if 't_ms' not in data:
		raise Exception('plot_calcium: Missing t_ms record.')
	N = 256
	vals = np.ones((N, 4))
	vals[:, 0] = 0 #np.linspace(90/256, 1, N)
	vals[:, 1] = np.linspace(0, 1, N)
	vals[:, 2] = 0 #np.linspace(41/256, 1, N)
	fluorescent_colormap = ListedColormap(vals)
	ms_between_frames = 100
	t_ms = data['t_ms']
	matchlen = len('calcium')
	for k in data.keys():
		if k[0:matchlen] == 'calcium':
			calcium_data = data[k]
			for indicator in calcium_data:
				image_stack = calcium_data[indicator]
				image_stack_size = len(image_stack)
				print('%s image stack size: %d' % (indicator, image_stack_size))
				frames = [ Image.fromarray(np.uint8(fluorescent_colormap(image.astype(float)/255.0)*255)).resize((512,512)) for image in image_stack ]
				#frames = [ Image.fromarray(image) for image in image_stack ]
				frames[0].save(gifpath, format="GIF", append_images=frames, save_all=True, duration=ms_between_frames, loop=0)
				if show_all:
					for i in range(image_stack_size):
						print('Image %d (%s), sum of values = %f' % (i, str(image_stack[i].shape), image_stack[i].sum()))
						plt.imshow(image_stack[i], cmap=fluorescent_colormap, vmin=0, vmax=255) # was camp='gray'
						plt.show()

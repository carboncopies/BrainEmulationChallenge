# KGTRecords.py
# Randal A. Koene, 20230623

'''
Utility functions used with known ground-truth recorded data.
'''

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import matplotlib.gridspec as gridspec
from PIL import Image

def plot_recorded(savefolder: str, data:dict, figspecs:dict={'figsize':(6,6),'linewidth':0.5}):
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

    fig = plt.figure(figsize=figspecs['figsize'])
    gs = fig.add_gridspec(len(Vm_cells),1, hspace=0)
    axs = gs.subplots(sharex=True, sharey=True)
    fig.suptitle("God's eye recorded data")
    for c in range(len(Vm_cells)):
        # if c == 0:
        #   ax = fig.add_subplot(gs[0])
        # else:
        #   ax = fig.add_subplot(gs[c], sharex=ax)
        axs[c].plot(t_ms, Vm_cells[c], linewidth=figspecs['linewidth'])
    for ax in axs:
        ax.label_outer()
    plt.draw()
    plt.savefig(savefolder+'/groundtruth-Vm.'+figspecs['figext'], dpi=300)

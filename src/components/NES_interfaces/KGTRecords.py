# KGTRecords.py
# Randal A. Koene, 20230623

'''
Utility functions used with known ground-truth recorded data.
'''

#import numpy as np
import matplotlib.pyplot as plt
#from matplotlib.colors import ListedColormap
#import matplotlib.gridspec as gridspec
#from PIL import Image
from os.path import isdir
from os import makedirs

import datetime
import pandas as pd
import pickle

def extract_t_Vm(data:dict)->tuple:
    if 't_ms' not in data:
        print('extract_t_Vm Error: Missing t_ms record.')
        return None, None

    # Get the list of time points:
    t_ms = data['t_ms']

    Vm_cells = []
    # If data was recorded in circuits, then unpack cell recordings:
    if "circuits" in data:
        data = data["circuits"]
        for region in data:
            if region!='t_ms':
                region_data = data[region]
                for cell in region_data:
                    cell_data = region_data[cell]
                    if 'Vm_mV' in cell_data:
                        Vm_cells.append(cell_data['Vm_mV'])
    elif "neurons" in data:
        data = data["neurons"]
        # Find largest ID in the data:
        maxID = 0
        for neuron_id in data:
            if int(neuron_id)>maxID:
                maxID = int(neuron_id)
        # Find neurons in order:
        for n_id in range(0, maxID+1):
            neuron_id = str(n_id)
            if neuron_id in data:
                if 'Vm_mV' not in data[neuron_id]:
                    print('Missing Vm_mV at neuron '+str(neuron_id))
                else:
                    Vm_cells.append(data[neuron_id]['Vm_mV'])
    else:
        print('extract_t_Vm Error: Missing cells membrane potential data.')
        return None, None
    return t_ms, Vm_cells

def save_t_Vm_pickled(t_ms, Vm_cells, savefolder: str):
    if not isdir(savefolder):
        makedirs(savefolder)
    try:
        with open(savefolder+'/groundtruth-Vm.pkl', 'wb') as f:
            pickle.dump({'t_ms': t_ms, 'Vm_cells': Vm_cells}, f)
    except:
        print('save_t_Vm_pickled Error: Unable to store data in '+savefolder+'/groundtruth-Vm.pkl')

def plot_t_Vm(t_ms, Vm_cells, savefolder: str, figspecs:dict={'figsize':(6,6),'linewidth':0.5}, cell_titles:list=None):
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
        if cell_titles:
            #axs[c].title.set_text(cell_titles[c], y=1.0, pad=-14)
            axs[c].set_title(cell_titles[c], y=1.0, pad=-14)
    for i in range(len(axs)):
        if i==0:
            axs[i].set(xlabel='t (ms)', ylabel='v_m (mV)')
        else:
            axs[i].set(xlabel='t (ms)')
    for ax in axs:
        ax.label_outer()
    plt.draw()

    all_data = []

    for i in range(len(Vm_cells)):
        all_data.append(Vm_cells[i])

    all_data.append(t_ms)
    df = pd.DataFrame(all_data)
    df = df.T
    
    cell = pd.DataFrame(cell_titles)
    cell = cell.T

    df = pd.concat([cell, df], ignore_index=True)
    df.to_csv(savefolder+'data.csv', index=False)

    if not isdir(savefolder):
        makedirs(savefolder)

    try:
        plt.savefig(savefolder+'/groundtruth-Vm.'+figspecs['figext'], dpi=300)
    except:
        print('plot_t_Vm Error: Unable to store plot in '+savefolder+'/groundtruth-Vm')

def plot_recorded(savefolder: str, data:dict, figspecs:dict={'figsize':(6,6),'linewidth':0.5}, cell_titles:list=None):

    t_ms, Vm_cells = extract_t_Vm(data)
    if not t_ms:
        print('plot_recorded Error: No data to plot.')
        return

    plot_t_Vm(t_ms, Vm_cells, savefolder, figspecs, cell_titles)

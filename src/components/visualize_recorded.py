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
Parser.add_argument("-t1", type=str, help="Start time")
Parser.add_argument("-t2", type=str, help="End time")
Parser.add_argument("--animate", action="store_true", help="Animate the plots over time")
Parser.add_argument("-framesize", default=100, type=int, help="Number of time points per frame")
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
spikes_cells = data_dict['spikes_cells']

SPIKE_PLOT_LEVEL=30.0

FIGSIZE=(8, 6) # (18, 12)
MP4FPS=50
GIFFPS=15
ANIMATE_INTERVAL=1 # 20
FRAMES_SIZE=Args.framesize
IDX_START=0
IDX_END=len(t_ms)
SHOW_SPIKES=True
TMAX=t_ms[-1]
print('t_max: %f' % TMAX)

if Args.t1:
    IDX_START = int(len(t_ms)*float(Args.t1)/TMAX)
    IDX_START = max(0, min(IDX_START, len(t_ms)-1))
    print('IDX_START: %d' % IDX_START)
if Args.t2:
    IDX_END = int(len(t_ms)*float(Args.t2)/TMAX)
    IDX_END = max(1, min(IDX_END, len(t_ms)))
    print('IDX_END: %d' % IDX_END)
if not (IDX_START==0 and IDX_END==len(t_ms)):
    SHOW_SPIKES=False


colors = plt.cm.tab10(np.linspace(0, 1, len(Vm_cells))) # Using 'tab10' colormap

def plot_subset(cell_indices:list):
    fig, axs = plt.subplots(len(cell_indices), 1, figsize=FIGSIZE, sharex=True)
    if len(cell_indices) == 1:
        axs = [axs]  # make iterable

    for i, idx in enumerate(cell_indices):
        axs[i].plot(t_ms[IDX_START:IDX_END], Vm_cells[idx][IDX_START:IDX_END], label=str(idx), color=colors[i])
        try:
            if spikes_cells and SHOW_SPIKES:
                axs[i].scatter(
                    spikes_cells[idx],
                    [ SPIKE_PLOT_LEVEL for i in range(len(spikes_cells[idx])) ],
                    #s=[ 0.01 for i in range(len(spikes_cells[idx])) ],
                    color='red', zorder=5, marker='.') # , label='Spikes'
        except Exception as e:
            print('Spike plotting error: '+str(e))
        axs[i].legend()
        axs[i].grid(True)

    plt.suptitle("Recorded acquisition data")
    plt.tight_layout()
    plt.show()

def reduce_size(giffile:str):
    print('Reducing color palette in GIF')
    from PIL import Image
    im = Image.open(giffile)
    im = im.convert("P", palette=Image.ADAPTIVE, colors=64)  # reduce to 64 colors
    im.save(giffile, optimize=True)

def gifsicle_optimise(giffile:str):
    print('Optimizing GIF')
    import subprocess

    # Example: Optimize a GIF with lossy compression and specific colors
    input_gif = giffile
    output_gif = giffile
    gifsicle_command = [
        "gifsicle",  # Or the full path to gifsicle.exe if not in PATH
        "-O3",
        "--lossy=80",
        "--colors", "128",
        #"-t", "#FFFFFF",
        input_gif,
        "-o",
        output_gif
    ]

    try:
        subprocess.run(gifsicle_command, check=True)
        print(f"GIF optimized successfully: {output_gif}")
    except subprocess.CalledProcessError as e:
        print(f"Error optimizing GIF: {e}")
        print(f"Gifsicle output: {e.stderr.decode()}")
    except FileNotFoundError:
        print("Error: 'gifsicle' command not found. Make sure Gifsicle is installed and in your system's PATH.")

def animate_subset(cell_indices:list):
    fig, axs = plt.subplots(len(cell_indices), 1, figsize=FIGSIZE, sharex=True)
    if len(cell_indices) == 1:
        axs = [axs]  # make iterable

    lines = []
    for i, idx in enumerate(cell_indices):
        line, = axs[i].plot([], [], label=str(idx), color=colors[i])
        axs[i].set_xlim(t_ms[IDX_START], t_ms[IDX_END-1])
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
            line.set_data(t_ms[IDX_START:frame*FRAMES_SIZE], Vm_cells[idx][IDX_START:frame*FRAMES_SIZE])
        return lines

    print('Generating animation')
    ani = FuncAnimation(fig, update, frames=IDX_END//FRAMES_SIZE, init_func=init,
                        interval=ANIMATE_INTERVAL, blit=True, repeat=False)

    # Save animation if requested
    if Args.save:
        print('Saving '+str(Args.save))
        ext = os.path.splitext(Args.save)[1].lower()
        if ext == ".mp4":
            ani.save(Args.save, fps=MP4FPS, extra_args=['-vcodec', 'libx264'])
            print(f"Animation saved to {Args.save}")
        elif ext == ".gif":
            ani.save(Args.save, writer=PillowWriter(fps=GIFFPS))
            print(f"Animation saved to {Args.save}")
            gifsicle_optimise(Args.save)
            #reduce_size(Args.save)
        else:
            print("Unsupported format. Use .mp4 or .gif")
    
    print('Displaying animation')
    plt.show()


# Show all cells first (static or animated)
cell_list = list(range(len(Vm_cells)))
if Args.animate:
    animate_subset(cell_list)
else:
    plot_subset(cell_list)

# Then allow user to pick subset
SHOW_SPIKES=False
timeinterval = eval(input('Time interval in brackets: '))
IDX_START = int(len(t_ms)*float(timeinterval[0])/TMAX)
IDX_START = max(0, min(IDX_START, len(t_ms)-1))
IDX_END = int(len(t_ms)*float(timeinterval[1])/TMAX)
IDX_END = max(1, min(IDX_END, len(t_ms)))
cell_indices = eval(input('List of cells to show with brackets (empty list=all): '))
if len(cell_indices)==0:
    cell_indices = list(range(len(Vm_cells)))
if Args.animate:
    animate_subset(cell_indices)
else:
    plot_subset(cell_indices)

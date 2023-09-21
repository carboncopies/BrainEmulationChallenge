# KGTRecords.py
# Randal A. Koene, 20230623

"""
Utility functions used with known ground-truth recorded data.
"""

import numpy as np
import matplotlib.pyplot as plt


def plot_recorded(data: dict):
    if "t_ms" not in data:
        raise Exception("plot_recorded: Missing t_ms record.")
    t_ms = data["t_ms"]
    Vm_cells = []
    for region in data:
        if region != "t_ms":
            region_data = data[region]
            for cell in region_data:
                cell_data = region_data[cell]
                if "Vm" in cell_data:
                    Vm_cells.append(cell_data["Vm"])
    fig = plt.figure(figsize=(4, 4))
    plt.title("Recorded data")
    for c in range(len(Vm_cells)):
        plt.plot(t_ms, Vm_cells[c])
    plt.show()

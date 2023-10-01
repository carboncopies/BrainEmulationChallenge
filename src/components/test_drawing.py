#!/usr/bin/env python3
# test_drawing.py
# Randal A. Koene, 20230930

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

from prototyping.Spatial import PlotInfo
from prototyping.Geometry import Sphere, Box, plot_voxel

def show_voxel(center:tuple, pltinfo):
    voxel_definition = {
        'xyz': np.array(list(center)),
        'size': 1.0,
    }
    plot_voxel(voxel_definition, pltinfo=pltinfo)

def show_voxels(voxel_centers:list, pltinfo):
    for voxel_center in voxel_centers:
        show_voxel(voxel_center, pltinfo)

if __name__ == '__main__':
    pltinfo = PlotInfo('Test')

    test_option=1

    if test_option==1:
        sphere = Sphere(center_um=(0,1,0), radius_um=1.0)
        sphere.show(pltinfo=pltinfo)

        voxel_centers = [ (0, 1, 0) ]
        show_voxels(voxel_centers, pltinfo)

    else:
        x, y, z = np.indices((4, 3, 3))
        cube = (x < 2) & (y > 0) & (z <= 0)
        link = abs(x - y) + abs(y - z) + abs(z - x) <= 1
        voxelarray = cube | link
        colors = np.empty(voxelarray.shape, dtype=object)
        colors[link] = 'red'
        colors[cube] = 'blue'
        pltinfo.ax.voxels(voxelarray, facecolors=colors, edgecolor='k')

        voxel_centers = [ (-1, 0, 1), (0, 0, 1) ]
        show_voxels(voxel_centers, pltinfo)
        
        box = Box()
        box.show(pltinfo=pltinfo)

    pltinfo.ax.set_aspect('equal')

    plt.show()

    exit(0)

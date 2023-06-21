# Geometry.py
# Randal A. Koene, 20230621

'''
Definitions of geometric shapes and their utility methods.
'''

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

class Geometry:
    def __init__(self):
        pass

class Box(Geometry):
    '''
    A box-like geometry defined by depth, width, length.
    '''
    def __init__(self, dims_um = ( 5.0, 10.0, 10.0 ) ):
        self.dims_um = dims_um

    def volume_um3(self) ->float:
        return self.dims_um[0]*self.dims_um[1]*self.dims_um[2]

    def equal_slice_bounds(self, n_slices:int, slice:int)->list:
        '''
        Return 1 of n equally sliced subpartitions of the Box
        shape, when lined up from left to right along the width.
        '''
        p_width = self.dims_um[1]/n_slices
        x0 = -self.dims_um[1]/2
        x = x0 + slice*p_width
        z = self.dims_um[0]/2
        y = self.dims_um[2]/2
        topleft = ( -z, x, -y )
        bottomright = ( z, x+p_width, y )
        return [ topleft, bottomright ]

    def sides(self)->np.ndarray:
        return np.array(list(self.dims_um))

    def int_sides(self)->np.ndarray:
        return np.array(list(self.dims_um), dtype=np.uint32)

    def show(self):
        fig = plt.figure(figsize=(4,4))
        ax = fig.add_subplot(111, projection='3d')
        data = np.ones(self.int_sides())
        ax.voxels(data, facecolors="yellow")
        plt.show()

class Sphere(Geometry):
    '''
    A sphere-like geometry defined by center an radius.
    '''
    def __init__(self, center_um:tuple, radius_um:float):
        self.center_um = center_um
        self.radius_um = radius_um

    def show(self, fig=None):
        if fig is None:
            fig = plt.figure(figsize=(4,4))
        ax = fig.add_subplot(projection='3d')
        u, v = np.mgrid[0:2*np.pi:50j, 0:np.pi:50j]
        x = self.radius_um*np.cos(u)*np.sin(v)
        y = self.radius_um*np.sin(u)*np.sin(v)
        z = self.radius_um*np.cos(v)
        ax.plot_surface(
            x-self.center_um[0],
            y-self.center_um[1],
            z-self.center_um[2],
            color=np.random.choice(['g','b']),
            alpha=0.5*np.random.random()+0.5)

class Cylinder(Geometry):
    '''
    A cylinder-like geometry defined by two circular end planes.
    '''
    def __init__(self, end0_um:tuple, end1_um:tuple, radius_um:float):
        self.end0_um = end0_um
        self.end1_um = end1_um
        self.radius_um = radius_um

    def show(self):
        print('SHOWING CYLINDER NOT YET IMPLEMENTED')

# Geometry.py
# Randal A. Koene, 20230621

'''
Definitions of geometric shapes and their utility methods.
'''

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from scipy.linalg import norm

class PlotInfo:
    def __init__(self, title:str):
        self.fig = plt.figure(figsize=(4,4))
        plt.title(title)
        self.ax = self.fig.add_subplot(111, projection='3d')

class Geometry:
    def __init__(self):
        pass

class Box(Geometry):
    '''
    A box-like geometry defined by depth, width, length.
    '''
    def __init__(self,
        center_um = ( 0, 0, 0 ),
        dims_um = ( 5.0, 10.0, 10.0 ),
        rotations_rad = (0, 0, 0) ):
        self.center_um = center_um
        self.dims_um = dims_um
        self.rotations_rad = rotations_rad

    def volume_um3(self) ->float:
        return self.dims_um[0]*self.dims_um[1]*self.dims_um[2]

    def equal_slice_bounds(self, n_slices:int, slice:int)->list:
        '''
        Return 1 of n equally sliced subpartitions of the Box
        shape, when lined up from left to right along the width.
        '''
        p_width = self.dims_um[1]/n_slices
        y0 = self.center_um[1] - (self.dims_um[1]/2)
        y = y0 + slice*p_width
        half_x = self.dims_um[0]/2
        half_z = self.dims_um[2]/2
        topleft = ( self.center_um[0]-half_x, y, self.center_um[2]-half_z )
        bottomright = ( self.center_um[0]+half_x, y+p_width, self.center_um[2]+half_z )
        return [ topleft, bottomright ]

    def sides(self)->np.ndarray:
        return np.array(list(self.dims_um))

    def int_sides(self)->np.ndarray:
        return np.array(list(self.dims_um), dtype=np.uint32)

    def show(self, pltinfo=None):
        if pltinfo is None: pltinfo = PlotInfo('Box shape')
        def get_cube_from_spherical_coords():   
            phi = np.arange(1,10,2)*np.pi/4
            Phi, Theta = np.meshgrid(phi, phi)
            x = np.cos(Phi)*np.sin(Theta)
            y = np.sin(Phi)*np.sin(Theta)
            z = np.cos(Theta)/np.sqrt(2)
            return x,y,z
        x,y,z = get_cube_from_spherical_coords()
        pltinfo.ax.plot_surface(
            x*self.dims_um[0]+self.center_um[0],
            y*self.dims_um[1]+self.center_um[1],
            z*self.dims_um[2]+self.center_um[2],
            color=(1.0, 1.0, 0.0, 0.1))

class Sphere(Geometry):
    '''
    A sphere-like geometry defined by center an radius.
    '''
    def __init__(self, center_um:tuple, radius_um:float):
        self.center_um = center_um
        self.radius_um = radius_um

    def show(self, pltinfo=None):
        if pltinfo is None: pltinfo = PlotInfo('Sphere shape')
        u, v = np.mgrid[0:2*np.pi:50j, 0:np.pi:50j]
        x = self.radius_um*np.cos(u)*np.sin(v)
        y = self.radius_um*np.sin(u)*np.sin(v)
        z = self.radius_um*np.cos(v)
        pltinfo.ax.plot_surface(
            x-self.center_um[0],
            y-self.center_um[1],
            z-self.center_um[2],
            color=np.random.choice(['g','b']),
            alpha=0.5*np.random.random()+0.5)

class Cylinder(Geometry):
    '''
    A cylinder-like geometry defined by two circular end planes.
    '''
    def __init__(self, end0_um:tuple, end0_radius_um:float, end1_um:tuple, end1_radius_um:float):
        self.end0_um = end0_um
        self.end1_um = end1_um
        self.end0_radius_um = end0_radius_um
        self.end1_radius_um = end1_radius_um

    def R_at_position(self, xi:float)->float:
        if xi<=0.0: return self.end0_radius_um
        if xi>=1.0: return self.end1_radius_um
        rdiff = self.end1_radius_um - self.end0_radius_um
        return self.end0_radius_um + xi*rdiff

    def show(self, pltinfo=None):
        if pltinfo is None: pltinfo = PlotInfo('Cylinder shape')
        # axis and radius
        p0 = np.array(self.end0_um)
        p1 = np.array(self.end1_um)
        # unit vector in direction of axis
        v = p1 - p0
        mag = norm(v)
        v = v / mag
        # make some vector not in the same direction as v
        not_v = np.array([1, 0, 0])
        if (v == not_v).all():
            not_v = np.array([0, 1, 0])
        # make vector perpendicular to v and normalize
        n1 = np.cross(v, not_v)
        n1 /= norm(n1)
        # make unit vector perpendicular to v and n1
        n2 = np.cross(v, n1)
        # surface ranges over t from 0 to length of axis and 0 to 2*pi
        t = np.linspace(0, mag, 100)
        theta = np.linspace(0, 2 * np.pi, 100)
        # use meshgrid to make 2d arrays
        t, theta = np.meshgrid(t, theta)
        # generate coordinates for surface
        # X, Y, Z = [
        #     p0[i] +
        #     v[i] * t +
        #     R * np.sin(theta) * n1[i] +
        #     R * np.cos(theta) * n2[i] for i in [0, 1, 2]]
        X, Y, Z = [
            p0[i] +
            v[i] * t +
            [self.R_at_position(xi=x/mag) for x in t[0]] * np.sin(theta) * n1[i] +
            [self.R_at_position(xi=x/mag) for x in t[0]] * np.cos(theta) * n2[i]
            for i in [0, 1, 2] ]
        pltinfo.ax.plot_surface(X, Y, Z)
        #plot axis
        #ax.plot(*zip(p0, p1), color = 'red')

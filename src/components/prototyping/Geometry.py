# Geometry.py
# Randal A. Koene, 20230621

'''
Definitions of geometric shapes and their utility methods.
'''

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from scipy.linalg import norm

from .Spatial import PlotInfo, VecBox, plot_voxel
from .Neuron import Neuron

class Geometry:
    def __init__(self):
        pass

def voxel_containing_point(point:np.array, voxel_um:float)->dict:
    indices = ( int(point[0]//voxel_um),
                int(point[1]//voxel_um),
                int(point[2]//voxel_um))
    voxel_center = np.array(list(indices))*voxel_um
    return {
        'center': voxel_center,
        'indices': indices,
        'key': '%d_%d_%d' % indices,
    }

class fluorescent_voxel:
    def __init__(self, xyz:np.array, voxel_um:float, neuron:Neuron, adj_dist_ratio=0):
        '''
        See: https://docs.google.com/document/d/1t1bPin-7YHswiNs4z7tSqFOLp7a1RQBXQQdhumkoOpQ/edit
        Note that adj_dist_ratio is d/adjacent_radius_um, where d is the distance
        from a specific voxel where adjacents were searched to this adjacent xyz.
        '''
        self.xyz = xyz
        self.voxel_um = voxel_um
        self.neuron_ref = neuron
        self.intersects = adj_dist_ratio==0 # If False then adjacent.
        self.act_brightness = 1.0-adj_dist_ratio # Reduce when adjacent at some distance.
        self.depth_brightness = 1.0
        self.image_pixels = []
        self.fifo_ref = None

    def get_adjacent_dict(self, adjacent_radius_um:float)->dict:
        '''
        Walk through the virtual voxels in a 3D box centered on self.xyz.
        For each location determine if it is within adjacent_radius_um
        of self.xyz. If so, then create an adjacent voxel object and
        add it to the dict that is returned with an integer indices key.
        '''
        adjacent_voxels_dict = {}
        radius_steps = int(adjacent_radius_um // self.voxel_um)
        if radius_steps==0: return {}
        for x in range(-radius_steps, radius_steps+1):
            for y in range(-radius_steps, radius_steps+1):
                for z in range(-radius_steps, radius_steps+1):
                    if not (x==0 and y==0 and z==0):
                        v = np.array([x*self.voxel_um, y*self.voxel_um, z*self.voxel_um])
                        r = np.sqrt(v.dot(v))
                        if r <= adjacent_radius_um: # Was: <
                            voxelspecs = voxel_containing_point(self.xyz + v, self.voxel_um)
                            adj = fluorescent_voxel(
                                voxelspecs['center'],
                                self.voxel_um,
                                self.neuron_ref,
                                adj_dist_ratio=r/adjacent_radius_um)
                            adjacent_voxels_dict[voxelspecs['key']] = adj
                            #print('DEBUG(fluorescent_voxel.get_adjacent_dict) == Adjacent voxel pos: '+str(adj.xyz))
        return adjacent_voxels_dict

    def set_depth_dimming(self, subvolume:VecBox):
        top_center = subvolume.center + (subvolume.half[2]*subvolume.dz)
        bottom_center = subvolume.center - (subvolume.half[2]*subvolume.dz)
        d_top = np.linalg.norm(top_center-self.xyz)
        d_bottom = np.linalg.norm(bottom_center-self.xyz)
        depth_dimming = d_top / (d_top + d_bottom)
        self.depth_brightness = 1.0 - depth_dimming

    def set_image_pixels(self, subvolume:VecBox, image_dims_px:tuple):
        '''
        TODO: See the TODO note in Calcium_Imaging.initialize_projection_circles().
        '''
        dxyz = (1/self.voxel_um)*(self.xyz - subvolume.center)
        xy = (int(dxyz[0])+image_dims_px[0]//2, int(dxyz[1]+image_dims_px[1]//2))
        if xy[0] >= 0 and xy[1] >= 0 and xy[0] < image_dims_px[0] and xy[1] < image_dims_px[1]:
            self.image_pixels.append(xy)

    def record_fluorescence(self, image_t:np.array):
        '''
        Use the FIFO queue data, as well as self.act_brightness and
        self.depth_brightness to add fluorescence value to the set
        of pixels in image_t that are affected by this voxel.
        The equation applies the fluorescence response to the calcium
        concentration that is a delayed representation of the membrane
        activity. This is the convolution of a response kernel with
        the history of the membrane activity. The kernel may be a
        double exponential with specific rise and decay time
        constants.
        On top of that, we take a snapshot only at specific sample
        intervals.
        TODO: Make sure this equation actually produces something like
              what calcium imaging shows through fluorescence, both
              when membrane potential is low and high (corresponding
              calcium concentrations).
        '''
        lum = 60.0*self.neuron_ref.Ca_samples[-1] * self.act_brightness * self.depth_brightness
        for pixel in self.image_pixels:
            image_t[int(pixel[0]),int(pixel[1])] += lum

    def show(self, pltinfo=None):
        if pltinfo is None: pltinfo = PlotInfo('Voxel')
        voxel_definition = {
            'xyz': self.xyz,
            'size': self.voxel_um
        }
        plot_voxel(voxel_definition, pltinfo=pltinfo) # force_scaling=True,

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
        doshow = pltinfo is None
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
            color=pltinfo.colors['boxes'])
        if doshow: plt.show()

class Sphere(Geometry):
    '''
    A sphere-like geometry defined by center and radius.
    '''
    def __init__(self, center_um:tuple, radius_um:float):
        self.center_um = center_um
        self.radius_um = radius_um

    def get_voxels(self, voxel_um:float, neuron:Neuron)->dict:
        # TODO: Do the full process. (For now, as a test, we just return
        #       a voxel for the soma center.)
        voxels_dict = {}
        voxelspecs = voxel_containing_point(self.center_um, voxel_um)
        #print('DEBUG(Sphere.get_voxels) == Voxel indices key: '+voxelspecs['key'])
        #print('DEBUG(Sphere.get_voxels) == Sphere voxel center: '+str(self.center_um))
        voxels_dict[voxelspecs['key']] = fluorescent_voxel(
            voxelspecs['center'],
            voxel_um,
            neuron)
        #print('DEBUG(Sphere.get_voxels) == Voxel xyz: '+str(voxels_dict[voxelspecs['key']].xyz))
        return voxels_dict

    def show(self, pltinfo=None):
        if pltinfo is None: pltinfo = PlotInfo('Sphere shape')
        u, v = np.mgrid[0:2*np.pi:50j, 0:np.pi:50j]
        x = self.radius_um*np.cos(u)*np.sin(v)
        y = self.radius_um*np.sin(u)*np.sin(v)
        z = self.radius_um*np.cos(v)
        pltinfo.ax.plot_surface(
            x+self.center_um[0],
            y+self.center_um[1],
            z+self.center_um[2],
            color=pltinfo.colors['spheres'],)
            #alpha=0.5*np.random.random()+0.5)

class Cylinder(Geometry):
    '''
    A cylinder-like geometry defined by two circular end planes.
    '''
    def __init__(self, end0_um:tuple, end0_radius_um:float, end1_um:tuple, end1_radius_um:float):
        self.end0_um = end0_um
        self.end1_um = end1_um
        self.end0_radius_um = end0_radius_um
        self.end1_radius_um = end1_radius_um

    def get_voxels(self, voxel_um:float, neuron:Neuron)->dict:
        # TODO: Implement this.
        voxels_dict = {}
        return voxels_dict

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
        pltinfo.ax.plot_surface(X, Y, Z, color=pltinfo.colors['cylinders'])
        #plot axis
        #ax.plot(*zip(p0, p1), color = 'red')

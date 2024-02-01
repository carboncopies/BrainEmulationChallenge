# _Geometry.py
# Randal A. Koene, 20230621

'''
Definitions of geometric shapes and their utility methods.
'''

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from scipy.linalg import norm

from .Spatial import PlotInfo, VecBox, plot_voxel, point_is_within_box, Plane, SixPlanesBox
from .Neuron import Neuron

def plane_distance(p:Plane, point:np.array)->float:
    d = point - p.point
    return d.dot(p.direction)

# s:Sphere
def sphere_inside_plane(s, p:Plane)->bool:
    return (-plane_distance(p, np.array(list(s.center_um)))) > s.radius_um

# s:Sphere
def sphere_outside_plane(s, p:Plane)->bool:
    return plane_distance(p, np.array(list(s.center_um))) > s.radius_um

# s:Sphere
def sphere_intersects_plane(s, p:Plane)->bool:
    return abs(plane_distance(p, np.array(list(s.center_um)))) <= s.radius_um

# s:Sphere
def sphere_inside_outside_intersects_plane(s, p:Plane)->int:
    pdist = plane_distance(p, np.array(list(s.center_um)))
    if pdist > s.radius_um: return 1
    if (-pdist) > s.radius_um: return -1
    return 0

# s:Sphere
def sphere_inside_box(s, b:SixPlanesBox)->bool:
    for plane in b.sides.values():
        if not sphere_inside_plane(s, plane): return False
    return True

# s:Sphere
def sphere_intersects_plane_point(s, p:Plane)->dict:
    d = plane_distance(p, np.array(list(s.center_um)))
    proj = p.direction*d
    return {
        'point': np.array(list(s.center_um))-proj,
        'radius': np.sqrt(max(s.radius_um*s.radius_um - d*d, 0)),
        'intersects': abs(d) <= s.radius_um,
    }

check = {
    'top': [ 'left', 'right', 'front', 'back', ],
    'bottom': [ 'left', 'right', 'front', 'back', ],
    'left': [ 'top', 'bottom', 'front', 'back', ],
    'right': [ 'top', 'bottom', 'front', 'back', ],
    'front': [ 'top', 'bottom', 'left', 'right', ],
    'back': [ 'top', 'bottom', 'left', 'right', ],
}

# s:Sphere
def sphere_intersects_box(s, b:SixPlanesBox)->bool:
    for intersect_side in check:
        res = sphere_intersects_plane_point(s, b.sides[intersect_side])
        if res['intersects']:
            and_res = True
            for side in check[intersect_side]:
                if plane_distance(b.sides[side], res['point']) > res['radius']:
                    and_res = False
                    break
            if and_res: return True
    return False

# s:Sphere
def sphere_outside_box(s, b:SixPlanesBox)->bool:
    return not (sphere_inside_box(s, b) or sphere_intersects_box(s, b))

# c:Cylinder
def cylinder_outside_box(c, b:VecBox)->bool:
    return not point_is_within_box(np.array(list(c.end0_um)), b) and not point_is_within_box(np.array(list(c.end1_um)), b)

class Geometry:
    def __init__(self):
        self.id = None

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
    def __init__(self, xyz:np.array, voxel_um:float, neuron:Neuron, adj_dist_ratio=0, type_brightness=1.0):
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
        self.type_brightness = type_brightness
        self.image_pixels = []
        self.fifo_ref = None

    def get_adjacent_dict(self, adjacent_radius_um:float)->dict:
        '''
        Walk through the virtual voxels in a 3D box centered on self.xyz.
        For each location determine if it is within adjacent_radius_um
        of self.xyz. If so, then create an adjacent voxel object and
        add it to the dict that is returned with an integer indices key.
        TODO: Probably use the same search method here as in Sphere.get_voxels()
              instead of having two different ones, which can be confusing.
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
                                adj_dist_ratio=r/adjacent_radius_um,
                                type_brightness=self.type_brightness)
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

    def set_image_pixels(self, subvolume:VecBox, image_dims_px:tuple, pixel_contributions:np.array):
        '''
        TODO: See the TODO note in Calcium_Imaging.initialize_projection_circles().
        '''
        dxyz = (1/self.voxel_um)*(self.xyz - subvolume.center)
        xy = (int(dxyz[0])+image_dims_px[0]//2, int(dxyz[1]+image_dims_px[1]//2))
        if xy[0] >= 0 and xy[1] >= 0 and xy[0] < image_dims_px[0] and xy[1] < image_dims_px[1]:
            self.image_pixels.append(xy)
            pixel_contributions[xy] += 1

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
        This function carries out image generation during simulation.
        TODO: Make sure this equation actually produces something like
              what calcium imaging shows through fluorescence, both
              when membrane potential is low and high (corresponding
              calcium concentrations).
        '''
        lum = 60.0*self.neuron_ref.Ca_samples[-1] * self.act_brightness * self.depth_brightness * self.type_brightness
        for pixel in self.image_pixels:
            image_t[int(pixel[0]),int(pixel[1])] += lum

    def record_fluorescence_aposteriori(self, images:list, max_Ca:float):
        '''
        This function creates images after simulation.
        '''
        amp = (255.0/max_Ca)*self.act_brightness*self.depth_brightness*self.type_brightness
        for i in range(len(self.neuron_ref.Ca_samples)):
            lum = amp*self.neuron_ref.Ca_samples[i]
            for pixel in self.image_pixels:
                images[i][int(pixel[0]),int(pixel[1])] += lum

    def show(self, pltinfo=None, linewidth=0.5):
        if pltinfo is None: pltinfo = PlotInfo('Voxel')
        voxel_definition = {
            'xyz': self.xyz,
            'size': self.voxel_um
        }
        plot_voxel(voxel_definition, pltinfo=pltinfo, linewidth=linewidth) # force_scaling=True,

class _Box(Geometry):
    '''
    A box-like geometry defined by depth, width, length.
    '''
    def __init__(self,
        center_um = ( 0, 0, 0 ),
        dims_um = ( 5.0, 10.0, 10.0 ),
        rotations_rad = (0, 0, 0) ):
        super().__init__()
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

    def to_dict(self)->dict:
        return {
            'geometry': 'box',
            'center_um': self.center_um,
            'dims_um': self.dims_um,
            'rotations_rad': self.rotations_rad,
        }

    def from_dict(self, data:dict):
        self.center_um = data['center_um']
        self.dims_um = data['dims_um']
        self.rotations_rad = data['rotations_rad']
        return self

    def show(self, pltinfo=None, linewidth=0.5):
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
            color=pltinfo.colors['boxes'],
            linewidth=linewidth)
        if doshow: plt.show()

class _Sphere(Geometry):
    '''
    A sphere-like geometry defined by center and radius.
    '''
    def __init__(self,
        center_um=( 0, 0, 0 ),
        radius_um=1.0):
        super().__init__()
        self.center_um = center_um
        self.radius_um = radius_um

    def get_voxels(self, voxel_um:float, subvolume:VecBox, neuron:Neuron)->dict:
        # TODO: There has to be a faster way to do this in the optimized implementation.
        voxels_dict = {}
        if sphere_outside_box(self, SixPlanesBox(subvolume)): return voxels_dict

        print('Getting sphere voxels...')
        center = np.array(list(self.center_um))
        # 1. Carry out raster search for points.
        raster = np.arange(-self.radius_um, self.radius_um+0.001, voxel_um)
        square_radius = self.radius_um*self.radius_um
        for z in range(0, len(raster)):
            for y in range(0, len(raster)):
                for x in range(0, len(raster)):
                    # 2. Determine if point is within sphere.
                    xyz = np.array([ raster[x], raster[y], raster[z]])
                    square_dist = xyz.dot(xyz)
                    if square_dist <= square_radius:
                        # 3. Get corresponding voxel.
                        voxelspecs = voxel_containing_point(self.center_um+xyz, voxel_um)
                        voxels_dict[voxelspecs['key']] = fluorescent_voxel(
                            voxelspecs['center'],
                            voxel_um,
                            neuron,
                            type_brightness=1.0)
        return voxels_dict

    def to_dict(self)->dict:
        return {
            'geometry': 'sphere',
            'center_um': self.center_um,
            'radius_um': self.radius_um,
        }

    def from_dict(self, data:dict):
        self.center_um = data['center_um']
        self.radius_um = data['radius_um']
        return self

    def show(self, pltinfo=None, linewidth=0.5):
        if pltinfo is None: pltinfo = PlotInfo('Sphere shape')
        u, v = np.mgrid[0:2*np.pi:50j, 0:np.pi:50j]
        x = self.radius_um*np.cos(u)*np.sin(v)
        y = self.radius_um*np.sin(u)*np.sin(v)
        z = self.radius_um*np.cos(v)
        pltinfo.ax.plot_surface(
            x+self.center_um[0],
            y+self.center_um[1],
            z+self.center_um[2],
            color=pltinfo.colors['spheres'],
            linewidth=linewidth,)
            #alpha=0.5*np.random.random()+0.5)

class _Cylinder(Geometry):
    '''
    A cylinder-like geometry defined by two circular end planes.
    '''
    def __init__(self,
        end0_um=(0,0,0),
        end0_radius_um=0.1,
        end1_um=(1,0,0),
        end1_radius_um=0.1):
        super().__init__()
        self.end0_um = end0_um
        self.end1_um = end1_um
        self.end0_radius_um = end0_radius_um
        self.end1_radius_um = end1_radius_um

    def get_voxels(self, voxel_um:float, subvolume:VecBox, neuron:Neuron)->dict:
        # TODO: There has to be a faster way to do this in the optimized implementation.
        voxels_dict = {}
        if cylinder_outside_box(self, subvolume): return voxels_dict

        print('Getting cylinder voxels...')
        xyz_start = np.array(list(self.end0_um))
        xyz_end = np.array(list(self.end1_um))
        dxyz = xyz_end - xyz_start
        mag_dxyz = np.sqrt(dxyz.dot(dxyz))
        dxyz = (voxel_um/mag_dxyz)*dxyz
        xyz = xyz_start
        d = 0
        while d < mag_dxyz:
            voxelspecs = voxel_containing_point(xyz, voxel_um)
            voxels_dict[voxelspecs['key']] = fluorescent_voxel(
                voxelspecs['center'],
                voxel_um,
                neuron,
                type_brightness=3.0)
            xyz += dxyz
            d += voxel_um
        return voxels_dict

    def R_at_position(self, xi:float)->float:
        if xi<=0.0: return self.end0_radius_um
        if xi>=1.0: return self.end1_radius_um
        rdiff = self.end1_radius_um - self.end0_radius_um
        return self.end0_radius_um + xi*rdiff

    def to_dict(self)->dict:
        return {
            'geometry': 'cylinder',
            'end0_um': self.end0_um,
            'end1_um': self.end1_um,
            'end0_radius_um': self.end0_radius_um,
            'end1_radius_um': self.end1_radius_um,
        }

    def from_dict(self, data:dict):
        self.end0_um = data['end0_um']
        self.end1_um = data['end1_um']
        self.end0_radius_um = data['end0_radius_um']
        self.end1_radius_um = data['end1_radius_um']
        return self

    def show(self, pltinfo=None, linewidth=0.5):
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
        pltinfo.ax.plot_surface(X, Y, Z, color=pltinfo.colors['cylinders'], linewidth=linewidth)
        #plot axis
        #ax.plot(*zip(p0, p1), color = 'red')

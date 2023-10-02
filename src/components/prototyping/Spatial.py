# Spatial.py
# Randal A. Koene, 20230929

'''
Definitions of spatial objects and operations.
This is more basic than Geometry.py.
'''

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection, Line3DCollection
import numpy as np

colset0 = [
    (0,1,0,0.5),
    (0,0,1,0.5),
]

colset1 = [
    (1,0,0,0.5),
    (0,1,0,0.5),
]

colset2 = [
    (1.0, 1.0, 0.0, 0.1),
    (0.0, 1.0, 1.0, 0.1),
]

colset3 = [
    (0,0,1,0.1),
    (1,0,1,0.6),
]

class PlotInfo:
    def __init__(self, title:str):
        self.fig = plt.figure(figsize=(4,4))
        plt.title(title)
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.colors = {
            'spheres': colset0[np.random.choice([0, 1])],
            'cylinders': colset1[np.random.choice([0, 1])],
            'boxes': colset2[0],
            'voxels': colset3[1],
        }

def vec3add(v1:tuple, v2:tuple)->tuple:
    return ( v1[0]+v2[0], v1[1]+v2[1], v1[2]+v2[2] )

def vec3sub(v:tuple, vsub:tuple)->tuple:
    return ( v1[0]-v2[0], v1[1]-v2[1], v1[2]-v2[2] )

def get_cube_vertices(cube_definition:list)->np.array:
    # Interpret the minimal cube definition:
    cube_definition_array = [
        np.array(list(item))
        for item in cube_definition
    ]

    # Expand to all cube vertices:
    vertices = []
    vertices += cube_definition_array
    vectors = [
        cube_definition_array[1] - cube_definition_array[0],
        cube_definition_array[2] - cube_definition_array[0],
        cube_definition_array[3] - cube_definition_array[0]
    ]

    vertices += [cube_definition_array[0] + vectors[0] + vectors[1]]
    vertices += [cube_definition_array[0] + vectors[0] + vectors[2]]
    vertices += [cube_definition_array[0] + vectors[1] + vectors[2]]
    vertices += [cube_definition_array[0] + vectors[0] + vectors[1] + vectors[2]]

    vertices = np.array(vertices)
    return vertices

def get_cube_edges(vertices:np.array)->list:
    edges = [
        [vertices[0], vertices[3], vertices[5], vertices[1]],
        [vertices[1], vertices[5], vertices[7], vertices[4]],
        [vertices[4], vertices[2], vertices[6], vertices[7]],
        [vertices[2], vertices[6], vertices[3], vertices[0]],
        [vertices[0], vertices[2], vertices[4], vertices[1]],
        [vertices[3], vertices[6], vertices[7], vertices[5]]
    ]
    return edges

def plot_cube(cube_definition:list, facecolor=(0,0,1,0.1), force_scaling=False, pltinfo=None):
    '''
    Expects four points: cube_definition = [
        (0,0,0), (0,1,0), (1,0,0), (0,0,1)
    ]
    '''
    #doshow = pltinfo is None
    if pltinfo is None: force_scaling = True
    if pltinfo is None: pltinfo = PlotInfo('Cube')

    vertices = get_cube_vertices(cube_definition)
    edges = get_cube_edges(vertices)
    faces = Poly3DCollection(edges, linewidths=1, edgecolors='k')
    faces.set_facecolor(facecolor)

    pltinfo.ax.add_collection3d(faces)

    if force_scaling:
        # Plot the points themselves to force the scaling of the axes
        pltinfo.ax.scatter(vertices[:,0], vertices[:,1], vertices[:,2], s=0)
        pltinfo.ax.set_aspect('equal')

def plot_voxel(voxel_definition:dict, force_scaling=False, pltinfo=None):
    '''
    Expects dict with 'xyz' a 3 element tuple, list or np.array and 'size' a float.
    '''
    xyz = voxel_definition['xyz']
    #print('DEBUG(plot_voxel) == Voxel center: %s' % (str(xyz)))
    half = voxel_definition['size']/2
    cube_definition = [
        (xyz[0]-half, xyz[1]-half, xyz[2]-half),
        (xyz[0]-half, xyz[1]+half, xyz[2]-half),
        (xyz[0]+half, xyz[1]-half, xyz[2]-half),
        (xyz[0]-half, xyz[1]-half, xyz[2]+half),
    ]
    #print('DEBUG(plot_voxel) == Cube def: %s' % (str(cube_definition)))
    plot_cube(cube_definition, pltinfo.colors['voxels'], force_scaling, pltinfo)

class VecBox:
    '''
    Note that this box is defined differently than Box below,
    but a conversion can be made between VecBox and Box.
    '''
    def __init__(self, center:np.array, half:np.array, dx=None, dy=None, dz=None):
        self.center = center    # 3D point.
        self.half = half        # Sizes/2 of the box in its three dimensions.
        self.dx = dx
        self.dy = dy
        self.dz = dz

    # TODO: Add functions to initialize dx, dy and dz from 8 points or from
    #       surfaces or other ways to define a box, e.g. Box below.

    def show(self, force_scaling=False, pltinfo=None):
        # TODO: Make this also work for subvolumes where dx, dy, and dz are not
        #       parallel to axes x, y and z.
        half_x = self.half[0]*self.dx
        half_y = self.half[1]*self.dy
        half_z = self.half[2]*self.dz
        cube_definition = [
            self.center - half_x - half_y - half_z,
            self.center - half_x + half_y - half_z,
            self.center + half_x - half_y - half_z,
            self.center - half_x - half_y + half_z,
        ]
        #print('DEBUG(VecBox.show) == Cube def: %s' % (str(cube_definition)))
        plot_cube(cube_definition, (0.0, 1.0, 1.0, 0.2), force_scaling, pltinfo)

def point_is_within_box(point:np.array, box:VecBox)->bool:
    '''
    The point must be a 3D vector.
    '''
    d = point - box.center
    return (abs(np.dot(d, box.dx)) <= box.half[0]) and (abs(np.dot(d, box.dy)) <= box.half[1]) and (abs(np.dot(d, box.dz)) <= box.half[2])

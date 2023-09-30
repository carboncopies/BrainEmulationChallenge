# Spatial.py
# Randal A. Koene, 20230929

'''
Definitions of spatial objects and operations.
This is more basic than Geometry.py.
'''

import numpy as np

def vec3add(v1:tuple, v2:tuple)->tuple:
    return ( v1[0]+v2[0], v1[1]+v2[1], v1[2]+v2[2] )

def vec3sub(v:tuple, vsub:tuple)->tuple:
    return ( v1[0]-v2[0], v1[1]-v2[1], v1[2]-v2[2] )

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

def point_is_within_box(point:np.array, box:VecBox)->bool:
    '''
    The point must be a 3D vector.
    '''
    d = point - box.center
    return (abs(np.dot(d, box.dx)) <= box.half[0]) and (abs(np.dot(d, box.dy)) <= box.half[1]) and (abs(np.dot(d, box.dz)) <= box.half[2])

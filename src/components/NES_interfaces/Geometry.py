# Geometry.py
# Randal A. Koene, 20230621

'''
Definitions of geometric shapes and their utility methods.
'''

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from scipy.linalg import norm

import common.glb as glb
from .common._Geometry import _Cylinder, _Sphere, _Box

class Box(_Box):
    '''
    A box-like geometry defined by depth, width, length.
    '''
    def __init__(self,
        center_um = ( 0, 0, 0 ),
        dims_um = ( 5.0, 10.0, 10.0 ),
        rotations_rad = (0, 0, 0) ):

        super().__init__(
            center_um=center_um,
            dims_um=dims_um,
            rotations_rad=rotations_rad,
            )
        self.id = glb.bg_api.BGNES_box_create(
            CenterPosition_um=center_um,
            Dimensions_um=dims_um,
            Rotation_rad=rotations_rad)

class Sphere(_Sphere):
    '''
    A sphere-like geometry defined by center and radius.
    '''
    def __init__(self,
        center_um=( 0, 0, 0 ),
        radius_um=1.0):

        super().__init__(
            center_um=center_um,
            radius_um=radius_um,
            )
        self.id = glb.bg_api.BGNES_sphere_create(
            radius_um=radius_um,
            center_um=center_um,
            )

class Cylinder(_Cylinder):
    '''
    A cylinder-like geometry defined by two circular end planes.
    '''
    def __init__(self,
        end0_um=(0,0,0),
        end0_radius_um=0.1,
        end1_um=(1,0,0),
        end1_radius_um=0.1):

        super().__init__(
            end0_um=end0_um,
            end0_radius_um=end0_radius_um,
            end1_um=end1_um,
            end1_radius_um=end1_radius_um,
            )
        self.id = glb.bg_api.BGNES_cylinder_create(
            Point1Radius_um=end0_radius_um,
            Point1Position_um=end0_um,
            Point2Radius_um=end1_radius_um,
            Point2Position_um=end1_um,
            )

# BSMorphology.py
# Randal A. Koene, 20230624

'''
Helper functions to generate morphology components for
ball-and-stick neurons.
'''

from .common._Geometry import Geometry
from .Geometry import Box, Sphere, Cylinder

def BS_Soma(domain_bounds:list, align:str, radius_um=0.5)->Sphere:
    if align=='left':
        center = (
            (domain_bounds[0][0]+domain_bounds[1][0])/2,
            domain_bounds[0][1]+radius_um,
            (domain_bounds[0][2]+domain_bounds[1][2])/2,
        )
    elif align=='right':
        center = (
            (domain_bounds[0][0]+domain_bounds[1][0])/2,
            domain_bounds[1][1]-radius_um,
            (domain_bounds[0][2]+domain_bounds[1][2])/2,
        )
    elif align=='center':
        center = (
            (domain_bounds[0][0]+domain_bounds[1][0])/2,
            (domain_bounds[0][1]+domain_bounds[1][1])/2,
            (domain_bounds[0][2]+domain_bounds[1][2])/2,
        )
    return Sphere(center, radius_um)

def BS_Axon(
    domain_bounds:list,
    align:str,
    soma_radius_um=0.5,
    end0_radius_um=0.1,
    end1_radius_um=0.1)->Cylinder:
    if align=='right':
        end0 = (
            (domain_bounds[0][0]+domain_bounds[1][0])/2,
            domain_bounds[0][1],
            (domain_bounds[0][2]+domain_bounds[1][2])/2,
        )
        end1 = (
            end0[0],
            domain_bounds[1][1]-(soma_radius_um*2),
            end0[2],
        )
    elif align=='left':
        end0 = (
            (domain_bounds[0][0]+domain_bounds[1][0])/2,
            domain_bounds[1][1],
            (domain_bounds[0][2]+domain_bounds[1][2])/2,
        )
        end1 = (
            end0[0],
            domain_bounds[0][1]+(soma_radius_um*2),
            end0[2],
        )
    return Cylinder(end0, end0_radius_um, end1, end1_radius_um)

def BS_Receptor(
    cells_list:list,
    src_cell:int,
    )->Box:
    receptor_location = cells_list[src_cell].morphology['soma'].center_um
    return Box(receptor_location, (0.1, 0.1, 0.1))

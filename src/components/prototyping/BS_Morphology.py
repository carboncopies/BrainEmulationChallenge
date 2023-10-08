# BSMorphology.py
# Randal A. Koene, 20230624

'''
Helper functions to generate morphology components for
ball-and-stick neurons.
'''

from .Geometry import Geometry, Box, Sphere, Cylinder

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
    if align=='left':
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
    elif align=='right':
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
    src_cell_id:str,
    )->Box:
    receptor_location = cells_list[src_cell_id].morphology['soma'].center_um
    return Box(receptor_location, (0.1, 0.1, 0.1))

# def BS_Morphology(morph:str, data:dict)->Geometry:
#     '''
#     Generate a morphology component from its description and data.
#     '''
#     if morph=='soma':
#         return Sphere(data['center'], data['radius_um'])
#     elif morph=='axon':
#         return Cylinder(data['end0_um'], data['end0_radius_um'], data['end1_um'], data['end1_radius_um'])
#     elif morph=='receptor':
#         return Box(data['receptor_location'], data['dims_um'])
#     elif morph=='region':
#         if data['geometry']=='box':
#             return Box().from_dict(data)
#         elif data['geometry']=='sphere':
#             return Sphere().from_dict(data)
#         elif data['geometry']=='cylinder':
#             return Cylinder().from_dict(data)
#     else:
#         return None

def BS_Morphology(data:dict)->Geometry:
    '''
    Generate a morphology component from its description and data.
    '''
    if data['geometry']=='box':
        return Box().from_dict(data)
    elif data['geometry']=='sphere':
        return Sphere().from_dict(data)
    elif data['geometry']=='cylinder':
        return Cylinder(None, None, None, None).from_dict(data)
    else:
        return None

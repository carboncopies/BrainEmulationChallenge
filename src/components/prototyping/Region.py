# Region.py
# Randal A. Koene, 20230621

'''
Definitions of brain region descriptors.
'''

from .Geometry import Geometry
from .NeuralCircuit import NeuralCircuit

class Region:
    def __init__(self, id:str):
        self.id = id

class BrainRegion(Region):
    '''
    Define the characteristics of a brain region, such as geometric shape and
    physiological content.
    '''
    def __init__(self,
        id:str,
        shape:Geometry,
        content:NeuralCircuit,):
        super().__init__(id=id)
        self.shape = shape
        self.content = content
        self.content.init_cell_structure(domain=self.shape)

    def show(self):
        self.shape.show()
        self.content.show()

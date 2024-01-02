# Region.py
# Randal A. Koene, 20230621

'''
Definitions of brain region descriptors.
'''

import matplotlib.pyplot as plt

from .common.Spatial import PlotInfo
from .common._Geometry import Geometry
from .common.NeuralCircuit import NeuralCircuit
from .BS_Morphology import BS_Morphology
from .BS_Aligned_NC import BS_Aligned_NC

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
        if self.content is not None:
            self.content.init_cells(domain=self.shape)

    def to_dict(self)->dict:
        region_data = {
            'id': self.id,
            'shape': self.shape.to_dict(),
            'content': self.content.to_dict(),
        }
        return region_data

    def from_dict(self, region_data):
        self.id = region_data['id']
        self.shape = BS_Morphology(data=region_data['shape'])
        circuit = BS_Aligned_NC('')
        circuit.from_dict(region_data['content'])
        self.content = circuit

    def show(self, show:dict, pltinfo=None, linewidth=0.5):
        doshow = pltinfo is None
        if pltinfo is None: pltinfo = PlotInfo('Brain region %s' % str(self.id))
        if show['regions']: self.shape.show(pltinfo, linewidth=linewidth)
        if show['cells']: self.content.show(pltinfo, linewidth=linewidth)
        if doshow: plt.draw()

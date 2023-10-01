# Region.py
# Randal A. Koene, 20230621

'''
Definitions of brain region descriptors.
'''

import matplotlib.pyplot as plt

from .Geometry import Geometry, PlotInfo
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
        self.content.init_cells(domain=self.shape)

    def show(self, show:dict, pltinfo=None):
        doshow = pltinfo is None
        if pltinfo is None: pltinfo = PlotInfo('Brain region %s' % str(self.id))
        if show['regions']: self.shape.show(pltinfo)
        if show['cells']: self.content.show(pltinfo)
        if doshow: plt.show()

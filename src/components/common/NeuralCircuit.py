# NeuralCircuit.py
# Randal A. Koene, 20230621

'''
Definitions of neural circuits.
'''

from .Neuron import Neuron

class NeuralCircuit:
    def __init__(self,
        id:str,
        num_cells:int=2,):
    
        self.id = id
        self.num_cells = num_cells
        self.cells = {}

    def add_cell(self, cell:Neuron):
        self.cells[cell.id] = cell

    def get_neurons(self)->list:
        return list(self.cells.values())

    def get_neurons_by_IDs(self, listofIDs:list)->list:
        listed_neurons = []
        for cell_id in listofIDs:
            if cell_id in self.cells:
                listed_neurons.append(self.cells[cell_id])
        return listed_neurons

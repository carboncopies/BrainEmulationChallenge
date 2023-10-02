# BS_Aligned_NC.py
# Randal A. Koene, 20230624

'''
Definitions of linearly aligned ball-and-stick neural circuits.
'''

from .Geometry import PlotInfo, Geometry
from .NeuralCircuit import NeuralCircuit
from .BS_Morphology import BS_Soma, BS_Axon, BS_Receptor
from .BS_Neuron import BS_Neuron

class BS_Aligned_NC(NeuralCircuit):
    '''
    Generate a neural circuit composed of ball-and-stick neurons that are
    connected.
    '''
    def __init__(self,
        id:str,
        num_cells:int=2,):

        super().__init__(id=id)
        self.num_cells = num_cells
        self.cells = {}

    def init_cells(self, domain:Geometry):
        for n in range(self.num_cells):
            domain_bounds = domain.equal_slice_bounds(self.num_cells, n)
            soma = BS_Soma(domain_bounds, align='left')
            axon = BS_Axon(domain_bounds, align='right', soma_radius_um=soma.radius_um)
            cell_id = str(n)
            cell = BS_Neuron(
                cell_id,
                soma,
                axon,
            )
            self.cells[cell_id] = cell

    def get_neurons(self)->list:
        return list(self.cells.values())

    def get_neurons_by_IDs(self, listofIDs:list)->list:
        listed_neurons = []
        for cell_id in listofIDs:
            if cell_id in self.cells:
                listed_neurons.append(self.cells[cell_id])
        return listed_neurons

    def get_cell_centers(self)->list:
        cell_centers = []
        for cell_id in self.cells:
            cell_centers.append(self.cells[cell_id].get_cell_center())
        return cell_centers

    def Set_Weight(self, from_to:tuple, method:str):
        print('Setting up connection from %s to %s.' % from_to)
        if method=='binary':
            to_cell = from_to[1]
            if to_cell not in self.cells:
                raise Exception('BS_Aligned_NC.Set_Weight: Unknown target cell %s.' % to_cell)
            from_cell = from_to[0]
            if from_cell not in self.cells:
                raise Exception('BS_Aligned_NC.Set_Weight: Unknown source cell %s.' % from_cell)
            target_cell = self.cells[to_cell]
            from_cell_ref = self.cells[from_cell]
            target_cell.receptors.append( (from_cell_ref, 1.0) ) # source and weight
            target_cell.morphology['receptor'] = BS_Receptor(self.cells, from_cell)

    def Encode(self,
        pattern_set: list,
        encoding_method:str,
        synapse_weight_method:str):
        if encoding_method=='instant':
            for pattern in pattern_set:
                self.Set_Weight(pattern, synapse_weight_method)

    def attach_direct_stim(self, tstim_ms:list):
        for stim in tstim_ms:
            t, cell_id = stim
            if cell_id not in self.cells:
                raise Exception('BS_Aligned_NC.attach_direct_stim: Cell %d not found.' % cell_id)
            self.cells[cell_id].attach_direct_stim(t)

    def set_spontaneous_activity(self, spont_spike_settings:list):
        '''
        Expects a list of tuples where each tuple associates a mean and stdev
        spike interval with a neuron identified by its ID string.
        E.g. [ ((280, 140), '0'), ... ]
        '''
        for mean_stdev, cell_id in spont_spike_settings:
            if cell_id in self.cells:
                self.cells[cell_id].set_spontaneous_activity(mean_stdev)

    def show(self, pltinfo=None):
        if pltinfo is None: pltinfo = PlotInfo('Neural circuit %s.' % str(self.id))
        for cell_id in self.cells:
            #print('DEBUG(BS_Aligned_NC.show) == Displaying cell %s.' % cell_id)
            self.cells[cell_id].show(pltinfo)

    def update(self, t_ms:float, recording:bool):
        for cell_id in self.cells:
            self.cells[cell_id].update(t_ms, recording)

    def get_recording(self)->dict:
        data = {}
        for cell_id in self.cells:
            data[cell_id] = self.cells[cell_id].get_recording()
        return data

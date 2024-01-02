# _BSAlignedNC.py
# Randal A. Koene, 20240101

'''
Common parts of the definitions of linearly algined ball-and-stick
neural circuits.
'''

from ._Geometry import Geometry
from .NeuralCircuit import NeuralCircuit

class _BSAlignedNC(NeuralCircuit):
    '''
    Generate a neural circuit composed of ball-and-stick neurons that are
    connected.
    '''
    def __init__(self,
        id:str,
        num_cells:int=2,):

        super().__init__(id=id, num_cells=num_cells)
        self.compObjRef = {
            'soma': None,
            'axon': None,
            'neuron': None,
        }

    def init_cells(self, domain:Geometry):
        for n in range(self.num_cells):
            domain_bounds = domain.equal_slice_bounds(self.num_cells, n)
            soma = self.compObjRef['soma'](domain_bounds, align='left')
            axon = self.compObjRef['axon'](domain_bounds, align='right', soma_radius_um=soma.radius_um)
            cell = self.compObjRef['neuron'](
                str(n),
                soma,
                axon,
            )
            self.add_cell(cell=cell)

    def get_cell_centers(self)->list:
        cell_centers = []
        for cell_id in self.cells:
            cell_centers.append(self.cells[cell_id].get_cell_center())
        return cell_centers

    def prepare_Set_Weight(self, from_to:tuple, method:str)->tuple:
        print('Setting up connection from %s to %s.' % from_to)
        if method=='binary':
            to_cell = from_to[1]
            if to_cell not in self.cells:
                raise Exception('_BSAlignedNC.prepare_Set_Weight: Unknown target cell %s.' % to_cell)
            from_cell = from_to[0]
            if from_cell not in self.cells:
                raise Exception('_BSAlignedNC.prepare_Set_Weight: Unknown source cell %s.' % from_cell)
            target_cell = self.cells[to_cell]
            from_cell_ref = self.cells[from_cell]
            weight = 1.0
            return from_cell, target_cell, from_cell_ref, weight
        else:
            return ()

    # Set_Weight() is specific to prototyping/NES_interface

    def Encode(self,
        pattern_set: list,
        encoding_method:str,
        synapse_weight_method:str):
        if encoding_method=='instant':
            for pattern in pattern_set:
                self.Set_Weight(pattern, synapse_weight_method)

    # attach_direct_stim() is specific to prototyping/NES_interface

    def set_spontaneous_activity(self, spont_spike_settings:list):
        '''
        Expects a list of tuples where each tuple associates a mean and stdev
        spike interval with a neuron identified by its ID string.
        E.g. [ ((280, 140), '0'), ... ]
        '''
        for mean_stdev, cell_id in spont_spike_settings:
            if cell_id not in self.cells:
                raise Exception('_BSAlignedNC.set_spontaneous_activity: Cell %d not found.' % cell_id)
            self.cells[cell_id].set_spontaneous_activity(mean_stdev)

    def to_dict(self)->dict:
        cells = {}
        for cell in self.cells:
            cells[cell] = self.cells[cell].to_dict()
        circuit_data = {
            'id': self.id,
            'num_cells': self.num_cells,
            'cells': cells,
        }
        return circuit_data

    def from_dict(self, circuit_data:dict):
        self.id = circuit_data['id']
        self.num_cells = circuit_data['num_cells']
        self.cells = {}
        for cell_id in circuit_data['cells']:
            cell = self.compObjRef['neuron']('', None, None)
            cell.from_dict(circuit_data['cells'][cell_id])
            self.add_cell(cell=cell)

    def show(self, pltinfo=None, linewidth=0.5):
        if pltinfo is None: pltinfo = PlotInfo('Neural circuit %s.' % str(self.id))
        for cell_id in self.cells:
            #print('DEBUG(BS_Aligned_NC.show) == Displaying cell %s.' % cell_id)
            self.cells[cell_id].show(pltinfo, linewidth=linewidth)

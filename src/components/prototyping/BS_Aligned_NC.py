# BS_Aligned_NC.py
# Randal A. Koene, 20230624

'''
Definitions of linearly aligned ball-and-stick neural circuits.
'''

import numpy as np

from .Geometry import PlotInfo, Geometry, Sphere, Cylinder
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

    def add_cell(self, cell_id:str, soma:Geometry, axon:Geometry):
        cell = BS_Neuron(
            cell_id,
            soma,
            axon,
        )
        self.cells[cell_id] = cell

    def init_cells(self, domain:Geometry):
        for n in range(self.num_cells):
            domain_bounds = domain.equal_slice_bounds(self.num_cells, n)
            soma = BS_Soma(domain_bounds, align='left')
            axon = BS_Axon(domain_bounds, align='right', soma_radius_um=soma.radius_um)
            self.add_cell(cell_id=str(n), soma=soma, axon=axon)

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
        for cell_id in circuit_data['cells']:
            cell = BS_Neuron('', None, None)
            cell.from_dict(circuit_data['cells'][cell_id])
            self.add_cell(cell_id=cell.id, soma=cell.morphology['soma'], axon=cell.morphology['axon'])

    def show(self, pltinfo=None, linewidth=0.5):
        if pltinfo is None: pltinfo = PlotInfo('Neural circuit %s.' % str(self.id))
        for cell_id in self.cells:
            #print('DEBUG(BS_Aligned_NC.show) == Displaying cell %s.' % cell_id)
            self.cells[cell_id].show(pltinfo, linewidth=linewidth)

    def update(self, t_ms:float, recording:bool):
        for cell_id in self.cells:
            self.cells[cell_id].update(t_ms, recording)

    def get_recording(self)->dict:
        data = {}
        for cell_id in self.cells:
            data[cell_id] = self.cells[cell_id].get_recording()
        return data

class BS_Uniform_Random_NC(BS_Aligned_NC):
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
        soma_radius_um = 0.5
        end0_radius_um = 0.1
        end1_radius_um = 0.1
        dist_threshold = 4*soma_radius_um*soma_radius_um
        soma_positions = []
        somas = []

        def find_soma_position()->np.array:
            need_position = True
            while need_position:
                xyz = np.random.uniform(-0.5, 0.5, 3)
                xyz = xyz*np.array(list(domain.dims_um)) + np.array(list(domain.center_um))
                # 2. Check it isn't too close to other neurons already placed.
                need_position = False
                for soma_pos in soma_positions:
                    v = xyz - soma_pos
                    d_squared = v.dot(v)
                    if d_squared <= dist_threshold:
                        need_position = True
                        break
            soma_positions.append(xyz)
            return xyz

        def find_nearest(idx:int, axons_to:np.array)->int:
            min_dist_squared = max(domain.dims_um)**2
            nearest = -1
            for i in range(len(soma_positions)):
                if i != idx:
                    if axons_to[i] != idx:
                        v = soma_positions[idx] - soma_positions[i]
                        d_squared = v.dot(v)
                        if d_squared < min_dist_squared:
                            min_dist_squared = d_squared
                            nearest = i
            return nearest

        for n in range(self.num_cells):
            # 1. Pick a random location.
            xyz = find_soma_position()
            # 3. Create and place a soma.
            soma = Sphere(tuple(xyz), soma_radius_um)
            somas.append(soma)

        axons_to = -1*np.ones(self.num_cells, dtype=int)
        for n in range(self.num_cells):
            # 4. Create an axon and direct it.
            idx_to = find_nearest(n, axons_to)
            axons_to[n] = idx_to
            dv_axon = soma_positions[idx_to] - soma_positions[n]
            mag = np.sqrt(dv_axon.dot(dv_axon))
            dv_axon = (1/mag)*dv_axon
            end0 = soma_positions[n] + (soma_radius_um*dv_axon)
            end1 = soma_positions[idx_to] - (soma_radius_um*dv_axon)
            axon = Cylinder(tuple(end0), end0_radius_um, tuple(end1), end1_radius_um)
            # 5. Create cell ID and make neuron.
            cell_id = str(n)
            cell = BS_Neuron(
                cell_id,
                somas[n],
                axon,
            )
            self.cells[cell_id] = cell

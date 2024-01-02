# BS_Aligned_NC.py
# Randal A. Koene, 20230624

'''
Definitions of linearly aligned ball-and-stick neural circuits.
'''

import numpy as np

from .Geometry import PlotInfo, Geometry, Sphere, Cylinder
from .common._BSAlignedNC import _BSAlignedNC
from .BS_Morphology import BS_Soma, BS_Axon, BS_Receptor
from .BS_Neuron import BS_Neuron

class BS_Aligned_NC(_BSAlignedNC):
    '''
    Generate a neural circuit composed of ball-and-stick neurons that are
    connected.
    '''
    def __init__(self,
        id:str,
        num_cells:int=2,):

        super().__init__(id=id, num_cells=num_cells)
        self.compObjRef['soma'] = BS_Soma
        self.compObjRef['axon'] = BS_Axon
        self.compObjRef['neuron'] = BS_Neuron

    def Set_Weight(self, from_to:tuple, method:str):
        from_cell, target_cell, from_cell_ref, weight = self.prepare_Set_Weight(from_to, method)

        target_cell.receptors.append( (from_cell_ref, 1.0) ) # source and weight
        target_cell.morphology['receptor'] = BS_Receptor(self.cells, from_cell)

    def attach_direct_stim(self, tstim_ms:list):
        for stim in tstim_ms:
            t, cell_id = stim
            if cell_id not in self.cells:
                raise Exception('BS_Aligned_NC.attach_direct_stim: Cell %d not found.' % cell_id)
            self.cells[cell_id].attach_direct_stim(t)

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

        super().__init__(id=id, num_cells=num_cells)

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
            cell = self.compObjRef['neuron'](
                cell_id,
                somas[n],
                axon,
            )
            self.cells[cell_id] = cell

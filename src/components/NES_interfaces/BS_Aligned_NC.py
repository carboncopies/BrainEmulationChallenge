# BS_Aligned_NC.py
# Randal A. Koene, 20230624

'''
Definitions of linearly aligned ball-and-stick neural circuits.
'''

from .Geometry import PlotInfo, Geometry
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

        from_cell_id = from_cell_ref.axon_id
        to_cell_id = target_cell.soma_id
        receptor_location = target_cell.morphology['soma'].center_um
        receptor_conductance = target_cell.vPSP * weigth
        time_constants = [ target_cell.tau_PSPr, target_cell.tau_PSPd ]
        receptor_id = BGNES_BS_receptor_create(from_cell_id, to_cell_id, receptor_conductance, json.dumps(time_constants), receptor_location)
        target_cell.receptors.append( (from_cell_ref, weigth, receptor_id) )
        target_cell.morphology['receptor'] = BS_Receptor(self.cells, from_cell)

    def attach_direct_stim(self, tstim_ms:list):
        for stim in tstim_ms:
            t, cell_num = stim
            if cell_id not in self.cells:
                raise Exception('BS_Aligned_NC.attach_direct_stim: Cell %d not found.' % cell_num)
            # First, we create the DACs where they haven't yet been created and cache cell-specific stimulation times.
            self.cells[cell_num].attach_direct_stim(t)
        for cell in self.cells:
            # Then, initialize the DACs with their respective data lists.
            cell.register_DAC_data_list()

    # update() is carried out in the backend

    # get_recording() is carried out in the backend

class BS_Uniform_Random_NC(BS_Aligned_NC):
    '''
    Generate a neural circuit composed of ball-and-stick neurons that are
    connected.
    '''
    def __init__(self,
        id:str,
        num_cells:int=2,):

        super().__init__(id=id, num_cells=num_cells)


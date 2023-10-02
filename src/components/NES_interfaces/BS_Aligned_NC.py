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
        self.cells = []

    def init_cells(self, domain:Geometry):
        for n in range(self.num_cells):
            domain_bounds = domain.equal_slice_bounds(self.num_cells, n)
            soma = BS_Soma(domain_bounds, align='left')
            axon = BS_Axon(domain_bounds, align='right', soma_radius_um=soma.radius_um)
            cell = BS_Neuron(
                str(n),
                soma,
                axon,
            )
            self.cells.append(cell)

    def Set_Weight(self, from_to:tuple, method:str):
        print('Setting up connection from %d to %d.' % from_to)
        if method=='binary':
            to_cell = from_to[1]
            if to_cell >= len(self.cells):
                raise Exception('BS_Aligned_NC.Set_Weight: Unknown target cell %d.' % to_cell)
            from_cell = from_to[0]
            if from_cell >= len(self.cells):
                raise Exception('BS_Aligned_NC.Set_Weight: Unknown source cell %d.' % from_cell)
            target_cell = self.cells[from_to[1]]
            from_cell_ref = self.cells[from_cell]
            weigth = 1.0
            from_cell_id = from_cell_ref.axon_id
            to_cell_id = target_cell.soma_id
            receptor_location = target_cell.morphology['soma'].center_um
            receptor_conductance = target_cell.vPSP * weigth
            time_constants = [ target_cell.tau_PSPr, target_cell.tau_PSPd ]
            receptor_id = BGNES_BS_receptor_create(from_cell_id, to_cell_id, receptor_conductance, json.dumps(time_constants), receptor_location)
            target_cell.receptors.append( (from_cell_ref, weigth, receptor_id) )
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
            t, cell_num = stim
            if cell_num >= len(self.cells):
                raise Exception('BS_Aligned_NC.attach_direct_stim: %d exceeds number of cells.' % cell_num)
            # First, we create the DACs where they haven't yet been created and cache cell-specific stimulation times.
            self.cells[cell_num].attach_direct_stim(t)
        for cell in self.cells:
            # Then, initialize the DACs with their respective data lists.
            cell.register_DAC_data_list()

    def show(self, pltinfo=None):
        if pltinfo is None: pltinfo = PlotInfo('Neural circuit %s.' % str(self.id))
        for cell_id in range(len(self.cells)):
            #print('DEBUG(BS_Aligned_NC.show) == Displaying cell number %d.' % cell_id)
            self.cells[cell_id].show(pltinfo)

    # def update(self, t_ms:float, recording:bool):
    #     for cell in self.cells:
    #         cell.update(t_ms, recording)

    # def get_recording(self)->dict:
    #     data = {}
    #     for cell in self.cells:
    #         data[cell.id] = cell.get_recording()
    #     return data

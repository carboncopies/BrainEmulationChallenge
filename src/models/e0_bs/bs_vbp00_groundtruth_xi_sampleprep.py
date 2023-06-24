#!/usr/bin/env python3
# bs_vbp00_groundtruth_xi_sampleprep.py
# Randal A. Koene, 20230621

'''
The ball-and-stick example is intended to provide the simplest in-silico case with the smallest
number of variables to address while still demonstrating the full process and dependencies
chain for whole brain emulation.

This file implements an in-silico fully known ground-truth system.

VBP process step 00: groundtruth
WBE topic-level XI: sample preparation / preservation (in-silico)
'''

import numpy as np

import vbpcommon
from prototyping.System import System
from prototyping.Geometry import PlotInfo, Geometry, Box, Sphere, Cylinder
from prototyping.Neuron import Neuron
from prototyping.NeuralCircuit import NeuralCircuit
from prototyping.Region import BrainRegion
from prototyping.KGTRecords import plot_recorded

def BS_Soma(domain_bounds:list, align:str, radius_um=0.5)->Sphere:
    #print('Domain bounds: '+str(domain_bounds))
    if align=='left':
        center = (
            (domain_bounds[0][0]+domain_bounds[1][0])/2,
            domain_bounds[0][1]+radius_um,
            (domain_bounds[0][2]+domain_bounds[1][2])/2,
        )
    elif align=='right':
        center = (
            (domain_bounds[0][0]+domain_bounds[1][0])/2,
            domain_bounds[1][1]-radius_um,
            (domain_bounds[0][2]+domain_bounds[1][2])/2,
        )
    elif align=='center':
        center = (
            (domain_bounds[0][0]+domain_bounds[1][0])/2,
            (domain_bounds[0][1]+domain_bounds[1][1])/2,
            (domain_bounds[0][2]+domain_bounds[1][2])/2,
        )
    #print('Center: '+str(center))
    return Sphere(center, radius_um)

def BS_Axon(
    domain_bounds:list,
    align:str,
    soma_radius_um=0.5,
    end0_radius_um=0.1,
    end1_radius_um=0.1)->Cylinder:
    if align=='right':
        end0 = (
            (domain_bounds[0][0]+domain_bounds[1][0])/2,
            domain_bounds[0][1],
            (domain_bounds[0][2]+domain_bounds[1][2])/2,
        )
        end1 = (
            end0[0],
            domain_bounds[1][1]-(soma_radius_um*2),
            end0[2],
        )
    elif align=='left':
        end0 = (
            (domain_bounds[0][0]+domain_bounds[1][0])/2,
            domain_bounds[1][1],
            (domain_bounds[0][2]+domain_bounds[1][2])/2,
        )
        end1 = (
            end0[0],
            domain_bounds[0][1]+(soma_radius_um*2),
            end0[2],
        )
    return Cylinder(end0, end0_radius_um, end1, end1_radius_um)

def BS_Receptor(
    cells_list:list,
    src_cell:int,
    )->Box:
    receptor_location = cells_list[src_cell].morphology['soma'].center_um
    return Box(receptor_location, (0.1, 0.1, 0.1))

class BS_Neuron(Neuron):
    '''
    A ball-and-stick neuron with 3D physical geometry and integrate-and-fire
    function.
    '''
    def __init__(self, id:str, soma:Sphere, axon:Cylinder):
        super().__init__(id)
        self.Vm_mV = -60.0      # Membrane potential
        self.Vrest_mV = -60.0   # Resting membrane potential
        self.Vact_mV = -50.0    # Action potential firing threshold
        self.Vahp_mV = -20.0
        self.tau_AHP_ms = 30.0
        self.morphology = {
            'soma': soma,
            'axon': axon,
        }
        self.receptors = []
        self.t_directstim_ms = []

        self.t_ms = 0
        self.t_act_ms = []

        self.t_recorded_ms = []
        self.Vm_recorded = []

    def attach_direct_stim(self, t_ms:float):
        self.t_directstim_ms.append(t_ms)

    def show(self, pltinfo=None):
        if pltinfo is None: pltinfo = PlotInfo('Neuron %s.' % str(self.id))
        for cellcomp in self.morphology:
            self.morphology[cellcomp].show(pltinfo)

    def record(self, t_ms:float):
        self.t_recorded_ms.append(t_ms)
        self.Vm_recorded.append(self.Vm_mV)

    def update_Vm(self, t_ms:float, recording:bool):
        # WARNING: The following does not include PSP yet...
        if len(self.t_act_ms)==0:
            self.Vm_mV = self.Vrest_mV
            if recording: self.record(t_ms)
            return
        t_act_last_ms = self.t_act_ms[-1]
        tdiff_ms = t_ms - t_act_last_ms
        if tdiff_ms<=1.0:
            self.Vm_mV = 0.0 # The spike.
            if recording: self.record(t_ms)
            return
        # vm(t) = Vrest + vahp(t)
        # vahp(t) = Vahp*exp(- (t-tA)/tau_ahp )
        vahp_t = self.Vahp_mV * np.exp(-tdiff_ms/self.tau_AHP_ms)
        self.Vm_mV = self.Vrest_mV + vahp_t
        if recording: self.record(t_ms)

    def update(self, t_ms:float, recording:bool):
        tdiff_ms = t_ms - self.t_ms
        if tdiff_ms<0: return

        if len(self.t_directstim_ms)>0:
            if self.t_directstim_ms[0]<=t_ms:
                tfire_ms = self.t_directstim_ms.pop(0)
                self.t_act_ms.append(tfire_ms)

        self.update_Vm(t_ms, recording)

        self.t_ms = t_ms

    def get_recording(self)->dict:
        return {
            'Vm': self.Vm_recorded,
        }

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
            target_cell.receptors.append( (from_cell, 1.0) ) # source and weight
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
            self.cells[cell_num].attach_direct_stim(t)

    def show(self, pltinfo=None):
        if pltinfo is None: pltinfo = PlotInfo('Neural circuit %s.' % str(self.id))
        for cell_id in range(len(self.cells)):
            print('Displaying cell number %d.' % cell_id)
            self.cells[cell_id].show(pltinfo)

    def update(self, t_ms:float, recording:bool):
        for cell in self.cells:
            cell.update(t_ms, recording)

    def get_recording(self)->dict:
        data = {}
        for cell in self.cells:
            data[cell.id] = cell.get_recording()
        return data

INITTEXT1='''
1. Defining a 2-neuron system:
   a. Scale: The number of principal nodes.
   b. Functional: The type of network arrangment
      (aligned ball-and-stick).
   c. Physical: A specific volume (a box region).
   Defaults are applied to other parameters.
'''

def init(show_all=False)->System:

    bs_system = System()

    print(INITTEXT1)

    NUM_NODES=2
    bs_net = bs_system.add_circuit( BS_Aligned_NC(id='BS NC', num_cells=NUM_NODES) )
    bs_region = bs_system.add_region( BrainRegion(
        id='BS',
        shape=Box( dims_um=(20.0, 20.0, 20.0) ),
        content=bs_net) )

    if show_all: bs_region.show()

    # 2. Initialize the connection between the 2 neurons:
    bs_net.Encode(
        pattern_set=[ ( 0, 1 ), ], # From cell 0 to cell 1.
        encoding_method='instant',
        synapse_weight_method='binary'
        )

    if show_all: bs_region.show()

    return bs_system

STIMTEXT1='''
Dynamic activity:
The imagined nature of the 2-neuron ball-and-stick circuit
provides no differentiation of dendritic input sources to
the neurons. Activity is elicited exclusively by generating
potential at or near a soma to the point where a cell fires
and action potential.

God's eye direct access to every aspect of the in-silico
ground-truth system includes the ability to specifically
cause a somatic action potential at any time.
'''

# ----------------------------------------------------------------------------

HELP='''
Usage: bs_vbp00_groundtruth_xi_sampleprep.py [-h] [-v] [-t ms]

       -h         Show this usage information.
       -v         Be verbose, show all diagrams.
       -t         Run for ms milliseconds.

       VBP process step 00: This script specifies a known ground-truth system.
       WBE topic-level XI: sample preparation / preservation (in-silico).

'''

def parse_command_line()->tuple:
    from sys import argv

    show_all = False
    runtime_ms = 500.0

    cmdline = argv.copy()
    scriptpath = cmdline.pop(0)
    while len(cmdline) > 0:
        arg = cmdline.pop(0)
        if arg == '-h':
            print(HELP)
            exit(0)
        elif arg== '-v':
            show_all = True
        elif arg== '-t':
            runtime_ms = float(cmdline.pop(0))

    return (show_all, runtime_ms)

if __name__ == '__main__':

    show_all, runtime_ms = parse_command_line()

    bs_kgt_system = init(show_all=show_all)

    print(STIMTEXT1)
    t_soma_fire_ms = [
        (100.0, 0),
        (200.0, 0),
        (300.0, 0),
        (400.0, 0),
    ]
    print('Directed somatic firing: '+str(t_soma_fire_ms))

    bs_kgt_system.attach_direct_stim(t_soma_fire_ms)

    bs_kgt_system.set_record_all()

    bs_kgt_system.run_for(runtime_ms)

    data = bs_kgt_system.get_recording()

    plot_recorded(data)

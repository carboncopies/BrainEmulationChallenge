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

import vbpcommon
from prototyping.Geometry import Geometry, Box, Sphere, Cylinder
from prototyping.Neuron import Neuron
from prototyping.NeuralCircuit import NeuralCircuit
from prototyping.Region import BrainRegion


class BS_Neuron(Neuron):
    '''
    A ball-and-stick neuron with 3D physical geometry and integrate-and-fire
    function.
    '''
    def __init__(self, id:str):
        super().__init__(id)
        self.Vm_mV = -70.0      # Membrane potential
        self.Vact_mV = -50.0    # Action potential firing threshold
        self.morphology = {}

    def set_morphology_soma(self, domain_bounds:list, align:str, radius_um=0.5):
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
        self.morphology['soma'] = Sphere(center, radius_um)

    def set_morphology_axon(self, domain_bounds:list, align:str, radius_um=0.01):
        if 'soma' not in self.morphology:
            raise Exception('BS_Neuron.set_morphology_axon: Missing soma definition.')
        if align=='left':
            end0 = (
                (domain_bounds[0][0]+domain_bounds[1][0])/2,
                domain_bounds[0][1],
                (domain_bounds[0][2]+domain_bounds[1][2])/2,
            )
            end1 = (
                end0[0],
                domain_bounds[1][1]-(self.morphology['soma'].radius_um*2),
                end0[2],
            )
        elif align=='right':
            end0 = (
                (domain_bounds[0][0]+domain_bounds[1][0])/2,
                domain_bounds[1][1],
                (domain_bounds[0][2]+domain_bounds[1][2])/2,
            )
            end1 = (
                end0[0],
                domain_bounds[0][1]+(self.morphology['soma'].radius_um*2),
                end0[2],
            )
        self.morphology['axon'] = Cylinder(end0, end1, radius_um)

    def show(self):
        for cellcomp in self.morphology:
            self.morphology[cellcomp].show()

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
        self.init_cell_function()

    def init_cell_function(self):
        self.cells = [ BS_Neuron(str(n)) for n in range(self.num_cells) ]

    def init_cell_structure(self, domain:Geometry):
        for n in range(self.num_cells):
            domain_bounds = domain.equal_slice_bounds(self.num_cells, n)
            self.cells[n].set_morphology_soma(domain_bounds, align='left')
            self.cells[n].set_morphology_axon(domain_bounds, align='right')

    def show(self):
        for cell in self.cells:
            cell.show()


def init(show_all=False)->dict:

    # 1. Define the 2-neuron system:
    #    a. Scale: A number of principal nodes.
    #    b. Functional: A type of network arrangement.
    #    c. Physical: A specific volume.
    #    Defaults are applied for other parameters.

    NUM_NODES=2
    bs_net = BS_Aligned_NC(id='BS NC', num_cells=NUM_NODES)
    bs_region = BrainRegion(
        id='BS',
        shape=Box( dims_um=(20.0, 20.0, 20.0) ),
        content=bs_net)

    if show_all: bs_region.show()

    # 2. Initialize the connection between the 2 neurons:

    # 3. Specify system I/O:

    # 4. Specify known ground-truth "God's eye" data output:

    bs_system = {

    }
    return bs_system

# ----------------------------------------------------------------------------

HELP='''
Usage: bs_vbp00_groundtruth_xi_sampleprep.py [-h]

       -h         Show this usage information.

       VBP process step 00: This script specifies a known ground-truth system.
       WBE topic-level XI: sample preparation / preservation (in-silico).

'''

def parse_command_line():
    from sys import argv

    cmdline = argv.copy()
    scriptpath = cmdline.pop(0)
    while len(cmdline) > 0:
        arg = cmdline.pop(0)
        if arg == '-h':
            print(HELP)
            exit(0)

if __name__ == '__main__':

    parse_command_line()

    bs_kgt_system = init(show_all=True)

    bs_kgt_system['regions']['cue'].random_selection(
        num_sets=3,
        cue_pattern_ratio=0.4,
        cue_sequence_length=3)

    bs_kgt_system['inspectors']['dyn'].show()


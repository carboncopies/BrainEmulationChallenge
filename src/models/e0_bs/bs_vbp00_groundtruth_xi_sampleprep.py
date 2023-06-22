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
from prototyping.Geometry import PlotInfo, Geometry, Box, Sphere, Cylinder
from prototyping.Neuron import Neuron
from prototyping.NeuralCircuit import NeuralCircuit
from prototyping.Region import BrainRegion

def BS_Soma(domain_bounds:list, align:str, radius_um=0.5)->Sphere:
    print('Domain bounds: '+str(domain_bounds))
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
    print('Center: '+str(center))
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

class BS_Neuron(Neuron):
    '''
    A ball-and-stick neuron with 3D physical geometry and integrate-and-fire
    function.
    '''
    def __init__(self, id:str, soma:Sphere, axon:Cylinder):
        super().__init__(id)
        self.Vm_mV = -70.0      # Membrane potential
        self.Vact_mV = -50.0    # Action potential firing threshold
        self.morphology = {
            'soma': soma,
            'axon': axon,
        }

    def show(self, pltinfo=None):
        if pltinfo is None: pltinfo = PlotInfo('Neuron %s.' % str(self.id))
        for cellcomp in self.morphology:
            self.morphology[cellcomp].show(pltinfo)

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

    def show(self, pltinfo=None):
        if pltinfo is None: pltinfo = PlotInfo('Neural circuit %s.' % str(self.id))
        for cell_id in range(len(self.cells)):
            print('Displaying cell number %d.' % cell_id)
            self.cells[cell_id].show(pltinfo)

INITTEXT1='''
1. Defining a 2-neuron system:
   a. Scale: The number of principal nodes.
   b. Functional: The type of network arrangment
      (aligned ball-and-stick).
   c. Physical: A specific volume (a box region).
   Defaults are applied to other parameters.
'''

def init(show_all=False)->dict:

    print(INITTEXT1)

    NUM_NODES=2
    bs_net = BS_Aligned_NC(id='BS NC', num_cells=NUM_NODES)
    bs_region = BrainRegion(
        id='BS',
        shape=Box( dims_um=(20.0, 20.0, 20.0) ),
        content=bs_net)

    if show_all: bs_region.show()

    # 2. Initialize the connection between the 2 neurons:

    # 3. Specify system I/O:
    #bs_cue = 

    # 4. Specify known ground-truth "God's eye" data output:

    bs_system = {
        'regions': { 'cue': '', },
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

    #bs_kgt_system['regions']['cue'].

    #bs_kgt_system['inspectors']['dyn'].show()


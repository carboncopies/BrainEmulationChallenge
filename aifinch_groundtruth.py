#!/usr/bin/env python3
# aifinch_groundtruth.py
# Randal A. Koene, 20230215

'''
AIFinch is a specification for an imaginary artificial Finch's song memory and its ability
to retrieve and sing songs. This is loosely based on the Zebra Finch song memory.

This file is used to generate a ground-truth model network and system.
'''

# TODO:
# - Extract parts of this that are reusable and create modules to import here.
# - Add specs for more of the required class methods.
#   - Add in simplest way to generate the network, starting with basic neural operations.
#   - Identify the API cut and describe it as per the doc that Thomas shared.

import json

# == Helpers: ===========================================================================================

global be_verbose
be_verbose=True

def verbose(msg:str):
    if be_verbose:
        print(msg)

class ToDo:
    def __init__(self, who:str, what:str, init_visibly=True):
        self.who = who
        self.what = what
        if init_visibly:
            self.show()
    def show(self):
        verbose('[TODO: %s] %s' % (str(self.who), str(self.what)))

# == Geometry: ==========================================================================================

class Geometry:
    def __init__(self):
        pass

class Box(Geometry):
    def __init__(self, dims_um = ( 5.0, 10.0, 10.0 ) ):
        self.dims_um = dims_um

    def volume_um3(self) ->float:
        return self.dims_um[0]*self.dims_um[1]*self.dims_um[2]

class Cube(Box):
    def __init__(self, side_um=10.0):
        super().__init__( dims_um = (side_um, side_um, side_um) )

# == Data Preparation: ==================================================================================

class Sequence:
    '''
    A sequence of patterns.
    '''
    def __init__(self,
        list_of_ids:list=[ 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, ],
        pattern_size_mean:float=10,
        pattern_size_stdev:float=2,
        overlap_ratio_mean:float=0.1,
        overlap_ratio_stdev:float=0.01,):
        self.list_of_ids = list_of_ids
        self.patterns = []
        self.generate_patterns()

    def generate_patterns(self):
        pass

# == Neuronal Circuit Types: ============================================================================

class NeuralCircuit:
    def __init__(self, id:str):
        self.id = id
        verbose('Init neural circuit: %s...' % str(self.id))

class ArbitraryCells_NC(NeuralCircuit):
    '''
    Generate a neural circuit composed of an arbitrary collection of cell types.
    '''
    def __init__(self,
        id:str,
        num_cells:int=100,):
        super().__init__(id=id)
        self.num_cells = num_cells
        self.distribution_specs = {}

    def show(self):
        pass

class AIF_DistributedAutoAssociative_NC(NeuralCircuit):
    '''
    Generate a neural circuit that is able to encode auto-associative pattern memories.
    Inspired by Zebra Finch long term memory.
    '''
    def __init__(self,
        id:str,
        num_nodes:int=1000,):
        super().__init__(id=id)
        self.num_nodes = num_nodes
        self.distribution_specs = {}
        ToDo('Randal', 'Review Zebra Finch literature to extract gist of song memory structure.')
        ToDo('Randal', 'Produce a simplified auto-associative NN structure inspired by ZF song memory.')
        ToDo('Randal', 'Outline structure, encoding and retrieval methods for AI Finch LTM.')
        ToDo('VBP Team', 'Implement LTM user class based on specs, using proposed low-level modeling resources.')
        ToDo('NES Team', 'Implement low-level modeling resources and API as required by AI Finch LTM VBP specs.')

    def Encode(self,
        pattern_set=[ Sequence(), ],
        encoding_method='instant',
        synapse_weight_method='binary',):
        pass
        # TODO:
        # - Implement a variety of encoding methods and synapse weight methods.

    def show(self):
        pass

# == Brain Layout: ======================================================================================

class Region:
    def __init__(self, id:str):
        self.id = id
        verbose('Init brain region: %s...' % str(self.id))

class BrainRegion(Region):
    '''
    Define the characteristics of a brain region, such as geometric shape and physiological
    content.
    '''
    def __init__(self,
        id:str,
        shape:Geometry=Cube(side_um=10.0),
        content:NeuralCircuit=ArbitraryCells_NC(id='Arbitrary NC', num_cells=100),):
        super().__init__(id=id)
        self.shape = shape
        self.content = content
        # TODO:
        # - More parameters that affect the make-up of a brain region.

    def show(self):
        '''
        Print significant characteristics of the brain region, its content structure
        and function, its history
        '''
        ToDo('VBP Team', 'Implement showing of brain region characteristics.')

class PatternGenerator(Region):
    '''
    An abstract alternative to a Brain Region intended as an input activity generator.
    '''
    def __init__(self,
        id:str,
        pattern_set=[ Sequence(), ],):
        super().__init__(id=id)
        self.pattern_set = pattern_set

    def random_selection(self,
        num_sets=1,
        cue_pattern_ratio=0.5,
        cue_sequence_length=1,):
        pass

    def all(self,
        cue_pattern_ratio=0.5,
        cue_sequence_length=1,):
        pass

class SpikeMonitor(Region):
    '''
    An abstract alternative to a Brain Region intended as an output receiver.
    '''
    def __init__(self, id:str):
        super().__init__(id=id)

class NotesToSound(Region):
    '''
    An abstract alternative to a Brain Region that interprets note identifiers and
    produces corresponding sound.
    '''
    def __init__(self,
        id:str,
        soundlib='notes.wav'):
        super().__init__(id=id)
        self.soundlib = soundlib

# == Pathways: ==========================================================================================

class RegionPath:
    '''
    A specification of connections from one Brain Region to another.
    '''
    def __init__(self,
        src:Region,
        dst:Region,
        method):
        pass

    def show(self):
        pass

class PatternMapper:
    '''
    An abstract mapper from an input pattern arrangement to an output pattern arrangement.
    '''
    def __init__(self,
        src:Region,
        dst:Region,
        method='nearest',):
        self.src = src
        self.dst = dst
        self.method = method

# == Inspectors: ========================================================================================

class Imager2D:
    '''
    Display requested 2D sections of one or more of a list of brain regions.
    '''
    def __init__(self,
        list_of_regions:list,):
        self.list_of_regions = list_of_regions

    def show(self):
        pass

class StateReader:
    '''
    Display parameter states of the components of one or more of a list of brain regions.
    '''
    def __init__(self,
        list_of_regions:list,):
        self.list_of_regions = list_of_regions

    def show(self):
        pass

class ActivityRecorder:
    '''
    Display the timeline of recorded activity of one or more of a list of brain regions.
    '''
    def __init__(self,
        list_of_regions:list,):
        self.list_of_regions = list_of_regions

    def show(self):
        pass

# == Initialize: ========================================================================================

def init(melodies:list)->dict:
    # 1. Define the aifinch long-term memory neuronal storage:
    #    A specific volume, type of network arrangement, and number of principal nodes.
    #    Defaults are applied for other parameters.
    NUM_NODES=10000
    aif_mem = AIF_DistributedAutoAssociative_NC(id='AI Finch LTM NC', num_nodes=NUM_NODES)
    aif_mem_region = BrainRegion(
        id='AI Finch LTM',
        shape=Box( dims_um=(6.0, 20.0, 20.0) ),
        content=aif_mem)

    aif_mem_region.show()

    # 2. Initialize the stored patterns for a selection of song melodies:
    #    The notes contained in a set of melodies are converted into sequences of patterns
    #    with a specific representation size and mean/stdev of overlap between patterns.
    songs = [ Sequence(
        notes,
        pattern_size_mean=80,
        pattern_size_stdev=20,
        overlap_ratio_mean=0.15,
        overlap_ratio_stdev=0.05,
        ) for notes in melodies ]
    aif_mem.Encode(
        pattern_set=songs,
        encoding_method='instant',
        synapse_weight_method='binary')

    aif_mem.show()

    # 3. Specify a semi-abstract method of memory retrieval:
    #    Input cues are produced by a pattern generator that generates patterns based
    #    on a specific requested melody or random selection. The input is delivered
    #    directly, by patch-clamp, to the principal nodes in the memory network.
    #    Full insight into resulting output activity is obtained by direct recording,
    #    patch-clamp, from the principal nodes in the memory network. Only spike times
    #    are retained for use in output production.
    aif_cue = PatternGenerator(id='Song cue generator', pattern_set=songs)
    aif_in = RegionPath(
        src=aif_cue,
        dst=aif_mem_region,
        method=[ '1-1', 'patchclamp' ])
    aif_resp = SpikeMonitor(id='Song retrieval spike monitor')
    aif_out = RegionPath(
        src=aif_mem_region,
        dst=aif_resp,
        method=[ '1-1', 'patchclamp' ])

    aif_in.show()
    aif_out.show()

    # 4. Specify melody sound production:
    singing_finch = NotesToSound(id='AI Finch singing voice', soundlib='finch_trills.wav')
    aif_vocalization = PatternMapper(
        src=aif_resp,
        dst=singing_finch,
        method='nearest')

    # 5. Specify known ground-truth "God's eye" data output:
    godseye_struc = Imager2D([ aif_mem_region, ])
    godseye_state = StateReader([ aif_mem_region, ])
    godseye_dyn = ActivityRecorder([ aif_mem_region, ])

    aif_system = {
        'neuralcircuits': { 'ltm': aif_mem, },
        'regions': { 'ltm': aif_mem_region, 'cue': aif_cue, 'resp': aif_resp, 'singing': singing_finch, },
        'pathways': { 'cue': aif_in, 'resp': aif_out, 'singing': aif_vocalization, },
        'inspectors': { 'struc': godseye_struc, 'state': godseye_state, 'dyn': godseye_dyn, },
    }
    return aif_system

default_melodies = [
    # Default melody 1:
    [ 'E', 'D#', 'E', 'D#', 'E', 'B', 'D', 'C', 'A', ],
    # Default melody 2:
    [ 'E', 'E', 'F', 'G', 'G', 'F', 'E', 'D', 'C', 'C', 'D', 'E', 'E', 'D', 'D', ],
]

global melodies_notes
melodies_notes = default_melodies

HELP='''
Usage: aifinch_groundtruth.py [-h] [melodies=<JSON-string>]

       -h         Show this usage information.
       melodies=  Use data in the provided JSON string as AI Finch song
                  melodies.

       This script specifies a known ground-truth system.

       Note that data acquisition is carried out in aifinch_acquisition.py,
       system identification and translation are carred out in
       aifinch_translation, and that emulation building and evaluation are
       carred out in aifinch_emulation.py.

'''

def parse_command_line():
    from sys import argv
    global melodies_notes

    cmdline = argv.copy()
    scriptpath = cmdline.pop(0)
    while len(cmdline) > 0:
        arg = cmdline.pop(0)
        if arg == '-h':
            print(HELP)
            exit(0)
        elif arg[0:9] == 'melodies=':
            melodies_notes = json.loads(arg[9])

if __name__ == '__main__':

    parse_command_line()

    aif_kgt_system = init(melodies_notes)

    # 6. Default KGT run:
    #    In sequence, select 3 of the available song cues at random. Deliver cues of
    #    approximately 40% of pattern size and consisting of the first 3 patterns.
    #    The responses will play as audible sound.
    #    The dynamic God's eye inspector shows the history of activity.
    aif_kgt_system['regions']['cue'].random_selection(
        num_sets=3,
        cue_pattern_ratio=0.4,
        cue_sequence_length=3)
    aif_kgt_system['inspectors']['dyn'].show()

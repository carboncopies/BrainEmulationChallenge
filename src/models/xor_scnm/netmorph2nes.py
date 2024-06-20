#!/usr/bin/python3
#
# Randal A. Koene, 20240617

modelname = '/home/randalk/src/nnmodels/netmorph/examples/nesvbp/nesvbp_202406181110'

datafiles = [
    'bifurcationnodes',
    'continuationnodes',
    'growthcones',
    'header',
    'neurons',
    'obliquenodes',
    'rootnodes',
    'synapses',
    'tuftnodes',
]

def make_filenames(modelname:str)->dict:
    filenames = {}
    for dfile in datafiles:
        filenames[dfile] = modelname+'_net.txt.'+dfile
    return filenames

def alt_load_data_from_file(dfile:str, filenames:dict)->dict:
    with open(filenames[dfile], 'r') as f:
        content = f.read()
    lines = content.split('\n')
    labels = lines[0].split(',')
    filedata = {}
    for label in labels:
        filedata[label] = []
    for i in range(1, len(lines)):
        linedata = lines[i].split(',')
        if len(linedata)>1:
            for j in range(len(labels)):
                filedata[labels[j]].append(linedata[j])
    return filedata

class nodedata:
    def __init__(self, _nodetype:str, dataline:list):
        self.nodetype = _nodetype
        self.node_idx = int(dataline[0])
        self.fiberpiece_label = dataline[1]
        self.fiberstructure_type = dataline[2]
        self.x = float(dataline[3])
        self.y = float(dataline[4])
        self.z = float(dataline[5])
        self.somaneuron_label = dataline[6]
        if len(dataline)>8:
            self.parent_idx = int(dataline[7])
            self.diameter = float(dataline[8])
            self.t_genesis = float(dataline[9])
        else:
            self.parent_idx = None
            self.diameter = None
            self.t_genesis = float(dataline[7])

def load_data_from_file(dfile:str, filenames:dict)->dict:
    with open(filenames[dfile], 'r') as f:
        content = f.read()
    lines = content.split('\n')
    filedata = {}
    for i in range(1, len(lines)):
        linedata = lines[i].split(',')
        if len(linedata)>7:
            filedata[int(linedata[0])] = nodedata(dfile, linedata)
    return filedata

def load_netmorph_data(filenames:dict)->dict:
    data = {}
    for dfile in datafiles:
        if dfile in ['bifurcationnodes', 'continuationnodes', 'growthcones', 'rootnodes']:
            data[dfile] = load_data_from_file(dfile, filenames)
        else:
            data[dfile] = alt_load_data_from_file(dfile, filenames)
    return data

class vec3d:
    def __init__(self, source):
        self.x = source.x
        self.y = source.y
        self.z = source.z
    def point(self)->list:
        return [ self.x, self.y, self.z ]

class segment:
    def __init__(self, node1:nodedata, node2:nodedata):
        self.start = vec3d(node1)
        self.end = vec3d(node2)
        self.startradius = node1.diameter
        self.endradius = node2.diameter
        if self.startradius is None:
            self.startradius = self.endradius
        if self.endradius is None:
            self.endradius = self.startradius
        self.startradius /= 2.0
        self.endradius /= 2.0
        if self.startradius == 0.0:
            self.startradius = 0.5
        if self.endradius == 0.0:
            self.endradius = 0.5
        self.data = node2

# Use the bifurcationnodes, continuationnodes, growthcones and rootnodes
# to make all the segments.
def make_segments(data:dict)->list:
    allnodes = {}
    allnodes.update(data['rootnodes'])
    allnodes.update(data['continuationnodes'])
    allnodes.update(data['bifurcationnodes'])
    allnodes.update(data['growthcones'])
    segments = []
    for nodeidx, nodedata in allnodes.items():
        if nodedata.parent_idx is not None:
            parentdata = allnodes[nodedata.parent_idx]
            segments.append(segment(parentdata, nodedata))
    return segments

class soma:
    def __init__(self, data:dict, idx:int):
        keyslist = list(data.keys())
        self.idx = int(data[keyslist[0]][idx])
        self.label = data[keyslist[1]][idx]
        self.type = data[keyslist[2]][idx]
        self.region = data[keyslist[3]][idx]
        self.x = float(data[keyslist[4]][idx])
        self.y = float(data[keyslist[5]][idx])
        self.z = float(data[keyslist[6]][idx])
        self.radius = float(data[keyslist[7]][idx])
    def point(self)->list:
        return [ self.x, self.y, self.z ]

def make_somas(data:dict)->list:
    somas = []
    neurondata = data['neurons']
    numneurons = len(neurondata[list(neurondata.keys())[0]])
    for idx in range(numneurons):
        neuron_soma = soma(neurondata, idx)
        somas.append(neuron_soma)
    return somas

class synapse:
    def __init__(self, data:dict, idx:int):
        print('Importing synapse number %d.' % idx)
        keyslist = list(data.keys())
        self.idx = int(data[keyslist[0]][idx])
        self.type = data[keyslist[1]][idx]
        self.presyn_x = float(data[keyslist[2]][idx])
        self.presyn_y = float(data[keyslist[3]][idx])
        self.presyn_z = float(data[keyslist[4]][idx])
        self.postsyn_x = float(data[keyslist[5]][idx])
        self.postsyn_y = float(data[keyslist[6]][idx])
        self.postsyn_z = float(data[keyslist[7]][idx])
        self.preaxon_piece = data[keyslist[8]][idx]
        self.postdendrite_piece = data[keyslist[9]][idx]
        self.presyn_neuron = data[keyslist[10]][idx]
        self.postsyn_neuron = data[keyslist[11]][idx]
        self.t_synaptogenesis = data[keyslist[12]][idx]
        self.basalapical = data[keyslist[13]][idx]
    def postsyn_receptor_point()->list:
        return [self.postsyn_x, self.postsyn_y, self.postsyn_z]

def make_synapses(data:dict)->list:
    synapses = []
    synapsedata = data['synapses']
    numsynapses = len(synapsedata[list(synapsedata.keys())[0]])
    for idx in range(numsynapses):
        syn = synapse(synapsedata, idx)
        synapses.append(syn)
    return synapses

def netmorph_to_somas_segments_synapses(modelname:str)->tuple:
    filenames = make_filenames(modelname)
    data = load_netmorph_data(filenames)
    segments = make_segments(data)
    somas = make_somas(data)
    synapses = make_synapses(data)
    return somas, segments, synapses

if __name__ == '__main__':
    print('Loading data from netmorph output files into dict of dict of lists...')
    somas, segments, synapses = netmorph_to_somas_segments_synapses(modelname)
    print('Found %d somas.' % len(somas))
    print('Found %d segments.' % len(segments))
    print('Found %d synapses.' % len(synapses))

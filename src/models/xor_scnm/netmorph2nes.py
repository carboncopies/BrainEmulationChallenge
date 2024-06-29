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

def make_somas(data:dict)->tuple:
    somas = []
    somasdict = {}
    neurondata = data['neurons']
    numneurons = len(neurondata[list(neurondata.keys())[0]])
    for idx in range(numneurons):
        neuron_soma = soma(neurondata, idx)
        somas.append(neuron_soma)
        somasdict[neuron_soma.label] = neuron_soma
    return somas, somasdict

class synapse:
    def __init__(self, data:dict, idx:int, somasdict:dict):
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

        self.presyn_soma = somasdict[self.presyn_neuron]
        self.postsyn_soma = somasdict[self.postsyn_neuron]
    def postsyn_receptor_point(self)->list:
        return [self.postsyn_x, self.postsyn_y, self.postsyn_z]
    def presyn_spine_point(self)->list:
        return [self.presyn_x, self.presyn_y, self.presyn_z]

def make_synapses(data:dict, somasdict:dict)->list:
    synapses = []
    synapsedata = data['synapses']
    numsynapses = len(synapsedata[list(synapsedata.keys())[0]])
    for idx in range(numsynapses):
        syn = synapse(synapsedata, idx, somasdict)
        synapses.append(syn)
    return synapses

def netmorph_to_somas_segments_synapses(modelname:str)->tuple:
    filenames = make_filenames(modelname)
    data = load_netmorph_data(filenames)
    segments = make_segments(data)
    somas, somasdict = make_somas(data)
    synapses = make_synapses(data, somasdict)
    return somas, segments, synapses

class neuron:
    def __init__(self, _label:str, _region:str):
        self.label = _label
        self.region = _region
        self.pre = set()
        self.post = set()
        self.shown = False

class connectome:
    def __init__(self, synapse_list:list):
        self.neuron_dict = {}
        for syn in synapse_list:
            if syn.presyn_neuron not in self.neuron_dict:
                self.neuron_dict[syn.presyn_neuron] = neuron(syn.presyn_neuron, syn.presyn_soma.region)
            if syn.postsyn_neuron not in self.neuron_dict:
                self.neuron_dict[syn.postsyn_neuron] = neuron(syn.postsyn_neuron, syn.postsyn_soma.region)
            presyn = self.neuron_dict[syn.presyn_neuron]
            postsyn = self.neuron_dict[syn.postsyn_neuron]
            presyn.post.add(postsyn.label)
            postsyn.pre.add(presyn.label)
    def inputs(self)->list:
        theinputs = []
        for nkey in self.neuron_dict:
            if len(self.neuron_dict[nkey].pre)==0:
                theinputs.append(nkey)
        return theinputs
    def clear_shown(self):
        for nkey in self.neuron_dict:
            self.neuron_dict[nkey].shown = False
    def show_connections(self, nkey:str, prestr:str='')->str:
        if nkey not in self.neuron_dict:
            return ''
        outstr = prestr + self.neuron_dict[nkey].region+':'+self.neuron_dict[nkey].label +'('+str(len(self.neuron_dict[nkey].post))+')\n'
        prestr += '    '
        self.neuron_dict[nkey].shown = True
        for postkey in self.neuron_dict[nkey].post:
            if not self.neuron_dict[postkey].shown:
                outstr += self.show_connections(postkey, prestr)
        return outstr
    def show_connections_depth(self, nkey:str, maxdepth:int, depth=0, prestr:str='')->str:
        if nkey not in self.neuron_dict:
            return ''
        outstr = prestr + self.neuron_dict[nkey].region+':'+self.neuron_dict[nkey].label +'('+str(len(self.neuron_dict[nkey].post))+')\n'
        prestr += '    '
        for postkey in self.neuron_dict[nkey].post:
            if depth < maxdepth:
                outstr += self.show_connections_depth(postkey, maxdepth, depth+1, prestr)
        return outstr

if __name__ == '__main__':
    print('Loading data from netmorph output files into dict of dict of lists...')
    somas, segments, synapses = netmorph_to_somas_segments_synapses(modelname)
    print('Found %d somas.' % len(somas))
    print('Found %d segments.' % len(segments))
    print('Found %d synapses.' % len(synapses))

#!/usr/bin/python3
#
# Randal A. Koene, 20240617

modelname = 'nesvbp_202406151142'

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
            self.t_genesis = float(dataline[8])
        else:
            self.parent_idx = None
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
        self.startradius = 1.0
        self.endradius = 1.0
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

def netmorph_to_segments(modelname:str)->list:
    filenames = make_filenames(modelname)
    data = load_netmorph_data(filenames)
    segments = make_segments(data)
    return segments

if __name__ == '__main__':
    print('Loading data from netmorph output files into dict of dict of lists...')
    segments = netmorph_to_segments(modelname)
    print('Found %d segments.' % len(segments))

# connectomes.py
# Randal A. Koene, 20240415

'''
Common code used to reload both ground-truth and emulated systems
and to extract from the build-code relevant connectome data for
validation.
'''

import json

import vbpcommon
from BrainGenix.BG_API import Credentials, SimClient

import BrainGenix.NES as NES
import BrainGenix

RPCpath = {
    'compartment': 'Simulation/Compartments/SC/Create',
    'neuron': 'Simulation/Neuron/SC/Create',
    'receptor': 'Simulation/Receptor/Create',
    'sphere': 'Simulation/Geometry/Sphere/Create',
    'cylinder': 'Simulation/Geometry/Cylinder/Create',
    'box': 'Simulation/Geometry/Box/Create',
}

# A simplified System class used just for validation.
class System:
    def __init__(self, retrieved_file:list):
        self.compartments = self.find_compartments(retrieved_file)
        self.neurons = self.find_neurons(retrieved_file)
        self.receptors = self.find_receptors(retrieved_file)
        self.shapes = self.find_shapes(retrieved_file)
        self.compartments_by_id = self.index_requests_by_id(
            self.compartments,
            RPCpath['compartment'],
            ('ID', 'Id', 'id', 'CompartmentID'),
        )
        self.shapes_by_id = self.index_shapes_by_id(self.shapes)

    def get_request_id(self, NESrequest:dict, RPC:str, IDKeys:tuple, FallbackID:int):
        for IDKey in IDKeys:
            if IDKey in NESrequest[RPC]:
                return NESrequest[RPC][IDKey]
        return FallbackID

    def index_requests_by_id(self, NESrequests:list, RPC:str, IDKeys:tuple)->dict:
        RequestsByID = {}
        for Index, NESrequest in enumerate(NESrequests):
            RequestID = self.get_request_id(NESrequest, RPC, IDKeys, Index)
            RequestsByID[RequestID] = NESrequest
        return RequestsByID

    def index_shapes_by_id(self, shapes:list)->dict:
        ShapesByID = {}
        for Index, Shape in enumerate(shapes):
            ShapeType, NESrequest = Shape
            RPC = RPCpath[ShapeType]
            ShapeID = self.get_request_id(NESrequest, RPC, ('ID', 'Id', 'id', 'ShapeID'), Index)
            ShapesByID[ShapeID] = Shape
        return ShapesByID

    def find_compartments(self, retrieved_file:list):
        RPC = RPCpath['compartment']
        compartments = []
        for NESrequest in retrieved_file:
            if RPC in NESrequest:
                compartments.append( NESrequest )
        return compartments

    def find_neurons(self, retrieved_file:list):
        RPC = RPCpath['neuron']
        neurons = []
        for NESrequest in retrieved_file:
            if RPC in NESrequest:
                neurons.append( NESrequest )
        return neurons

    def get_compartment(self, compartment_id:int)->dict:
        compartment = self.compartments_by_id.get(compartment_id)
        if compartment is not None:
            return compartment
        try:
            if compartment_id >= len(self.compartments):
                return None
        except TypeError:
            return None
        return self.compartments[compartment_id]

    def get_shape(self, shape_id:int):
        shape = self.shapes_by_id.get(shape_id)
        if shape is not None:
            return shape
        try:
            if shape_id >= len(self.shapes):
                return None
        except TypeError:
            return None
        return self.shapes[shape_id]

    def find_receptors(self, retrieved_file:list):
        RPC = RPCpath['receptor']
        receptors = []
        for NESrequest in retrieved_file:
            if RPC in NESrequest:
                receptors.append( NESrequest )
        return receptors

    def find_shapes(self, retrieved_file:list):
        RPCsphere = RPCpath['sphere']
        RPCcylinder = RPCpath['cylinder']
        RPCbox = RPCpath['box']
        shapes = []
        for NESrequest in retrieved_file:
            if RPCsphere in NESrequest:
                shapes.append( ('sphere', NESrequest) )
            elif RPCcylinder in NESrequest:
                shapes.append( ('cylinder', NESrequest) )
            elif RPCbox in NESrequest:
                shapes.append( ('box', NESrequest) )
        return shapes

    def get_neuron_by_compartment(self, compartment_id:int)->int:
        RPC = RPCpath['neuron']
        for i in range(len(self.neurons)):
            if compartment_id in self.neurons[i][RPC]['SomaIDs']:
                return i
            if compartment_id in self.neurons[i][RPC]['DendriteIDs']:
                return i
            if compartment_id in self.neurons[i][RPC]['AxonIDs']:
                return i
        return None

    def get_receptor_neurons(self, receptor_id:int)->tuple:
        RPC = RPCpath['receptor']
        if receptor_id >= len(self.receptors):
            return None
        #src_compartment = self.get_compartment(self.receptors[receptor_id][RPC]['SourceCompartmentID'])
        #dst_compartment = self.get_compartment(self.receptors[receptor_id][RPC]['DestinationCompartmentID'])
        src_compartment = self.receptors[receptor_id][RPC]['SourceCompartmentID']
        dst_compartment = self.receptors[receptor_id][RPC]['DestinationCompartmentID']
        src_neuron = self.get_neuron_by_compartment(src_compartment)
        dst_neuron = self.get_neuron_by_compartment(dst_compartment)
        return (src_neuron, dst_neuron)

    def get_connectivity(self)->list:
        RPC = RPCpath['receptor']
        connectivity = []
        for i in range(len(self.receptors)):
            weight = self.receptors[i][RPC]['Conductance_nS']
            connectivity.append( list(self.get_receptor_neurons(i)) + [ weight ] )
        return connectivity

    def get_all_neurons(self)->list:
        return self.neurons

    def get_all_somas(self)->list:
        somas = []
        for n in self.neurons:
            soma_compartment_id = n[RPCpath['neuron']]['SomaIDs'][0]
            soma_compartment = self.get_compartment(soma_compartment_id)
            if soma_compartment is None:
                print('Warning: Soma compartment with ID '+str(soma_compartment_id)+' was not found! Skipped.')
                continue
            soma_shape_id = soma_compartment[RPCpath['compartment']]['ShapeID']
            soma_shape = self.get_shape(soma_shape_id)
            if soma_shape is None:
                print('Warning: Soma shape with ID '+str(soma_shape_id)+' was not found! Skipped.')
                continue
            if soma_shape[0] == 'sphere':
                somas.append( soma_shape[1][RPCpath['sphere']] )
            else:
                print('Warning: Shape with ID '+str(soma_shape_id)+' is not a sphere! Skipped.')
        return somas

    def get_all_soma_coords(self)->list:
        somas = self.get_all_somas()
        soma_coords = []
        for s in somas:
            soma_coords.append( [s['CenterPosX_um'], s['CenterPosY_um'], s['CenterPosZ_um']] )
        return soma_coords

def get_connectomes(Args, user:str, passwd:str)->tuple:
    #default:
    api_is_local=True
    if Args.Remote:
        api_is_local=False
    if Args.Local:
        api_is_local=True

    # 1. Init NES connection

    credentials = Credentials(user=user, passwd=passwd)
    client = SimClient(credentials, api_is_local)

    # 2. Get ground-truth network

    simulation_sys_name=None
    with open(".SimulationHandle", "r") as f:
        simulation_sys_name = f.read()

    print(f"\nRetrieving simulation with handle '{simulation_sys_name}'")

    simulation_sys_path='./'+simulation_sys_name+'-simulation'
    client.Instance.DownloadSimulation(_SaveHandle=simulation_sys_name, _FilePath=simulation_sys_path)

    with open(simulation_sys_path+'.NES', 'r') as f:
        retrieved_file = json.load(f)

    print('Number of requests found in retrieved savefile: '+str(len(retrieved_file)))

    groundtruth = System(retrieved_file)

    # 3. Get emulation network

    emulation_sys_name=None
    with open(".EmulationHandle", "r") as f:
        emulation_sys_name = f.read()

    print(f"\nRetrieving emulation with handle '{emulation_sys_name}'")

    emulation_sys_path='./'+emulation_sys_name+'-simulation'
    client.Instance.DownloadSimulation(_SaveHandle=emulation_sys_name, _FilePath=emulation_sys_path)

    with open(emulation_sys_path+'.NES', 'r') as f:
        retrieved_file = json.load(f)

    print('Number of requests found in retrieved savefile: '+str(len(retrieved_file)))

    emulation = System(retrieved_file)

    # -- 4. Retrieve ground-truth simulation data to get structure

    print('\nNumber of neurons in ground-truth: '+str(len(groundtruth.neurons)))
    print('Number of receptors in ground-truth: '+str(len(groundtruth.receptors)))

    #print('Connectivity in ground-truth:'+str(groundtruth.get_connectivity()))

    # -- 5. Retrieve emuation data to get structure

    print('\nNumber of neurons in circuit emulation: '+str(len(emulation.neurons)))
    print('Number of receptors in circuit emulation: '+str(len(emulation.receptors)))

    #print('Connectivity in circuit emulation:'+str(emulation.get_connectivity()))

    return (groundtruth, emulation)

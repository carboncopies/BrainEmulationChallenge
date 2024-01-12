#!/usr/bin/env python3
# BG_API.py
# Randal A. Koene, 20230624

'''
Common utilities for making REST API requests through the
BrainGenix API.
'''

import requests
import json
import random

import BrainGenix.NES as NES

# These are used to select the host and port for
# pyBrainGenixClient calls.
local_host='localhost'
local_port=8000
remote_host='api.braingenix.org'
remote_port=443
global uri_host
global uri_port

# This is used by BGAPI_call() and API_call_raw().
global BGAPI_BASE_URI

# global AUTHKEY
# AUTHKEY=''

# global SIMID
# SIMID=''

global DEBUG_API
DEBUG_API=True

#global SessionToken

global autonames
autonames = [ ]

def make_bgapi_base_uri(host:str, port:int, use_https:bool):
    global BGAPI_BASE_URI
    global uri_host
    global uri_port
    uri_host = host
    uri_port = port
    if use_https:
        BGAPI_BASE_URI='https://%s:%s' % (host,str(port))
    else:
        BGAPI_BASE_URI='http://%s:%s' % (host,str(port))

# Initializing the default URI
make_bgapi_base_uri(remote_host, remote_port, True)

class SimClientInstance:
    def __init__(self, user:str, passwd:str, simname:str, host:str='api.braingenix.org', port:int=443, use_https:bool=True):
        self.ClientCfg = NES.Client.Configuration()
        self.ClientCfg.Mode = NES.Client.Modes.Remote
        self.ClientCfg.Host = host
        self.ClientCfg.Port = port
        self.ClientCfg.UseHTTPS = use_https
        self.ClientCfg.AuthenticationMethod = NES.Client.Authentication.Password
        self.ClientCfg.Username = user
        self.ClientCfg.Password = passwd
        self.ClientInstance = NES.Client.Client(self.ClientCfg)
        assert(self.ClientInstance.IsReady())

        self.SimulationCfg = NES.Simulation.Configuration()
        self.SimulationCfg.Name = simname
        self.Sim = self.ClientInstance.CreateSimulation(self.SimulationCfg)

global Simulation

def generate_autoname(prepend:str)->str:
    global autonames
    r = random.random()
    r_str = prepend+str(r)
    autonames.append(r_str)
    return r_str

def API_call_raw(uri:str)->requests.Response:
    '''
    Make a raw call through the Braingenix API.
    The REST URI must already be prepared.
    '''
    return requests.get(uri)

def BGAPI_call(rq:str)->requests.Response:
    if DEBUG_API: print('Request is: '+str(rq))
    response = requests.get(BGAPI_BASE_URI+rq)
    if DEBUG_API: print('Response is: '+str(response.text))
    return response

def BGNES_handle_response(
        response:requests.Response,
        caller=str,
        retstrings:list=['StatusCode']
    )->list:

    if response.status_code==200:
        try:
            data = response.json()
            #if data['StatusCode']==0:
            if data['StatusCode']==0 or data['StatusCode']==3: # This is temporary!
                retdata = []
                for retstr in retstrings:
                    retdata.append(data[retstr])
                return retdata
            else:
                raise Exception('%s: API returned status code %s.' % (caller, data['StatusCode']))
        except Exception as e:
            raise Exception('%s: API did not return expected JSON data.' % caller)
    else:
        raise Exception('%s: Failed with GET status %s.' % (caller, response.status_code))

def BGNES_Version()->str:
    response = BGAPI_call('/Diagnostic/Version')
    return BGNES_handle_response(response, 'BGNES_Version', ['Version'])[0]

def BGNES_Status()->list:
    response = BGAPI_call('/Diagnostic/Status')
    return BGNES_handle_response(response, 'BGNES_Status', ['SystemState', 'ServiceStateNES'])

# def BGNES_GetToken(user:str, passwd:str)->str:
#     # previously: response = BGAPI_call('/Auth/GetToken?Username=%s&Password=%s' % (user, passwd))
#     # previously: return BGNES_handle_response(response, 'BGNES_GetToken', ['AuthKey'])[0]
#     global SessionToken
#     SessionToken = NES.Client.GetInsecureToken(_Username=user, _Password=passwd)
#     return SessionToken

def BGNES_simulation_create(user:str, passwd:str, name:str, host:str, port:int, is_local:bool):
    global SessionToken
    global Simulation
    Simulation = SimClientInstance(
        user=user,
        passwd=passwd,
        simname=name,
        host=host,
        port=port,
        use_https=not is_local,
    )
    return Simulation

def BGNES_simulation_reset()->str:
    global Simulation
    return Simulation.Sim.Reset()['StatusCode']

def BGNES_simulation_runfor(Runtime_ms:float)->str:
    global Simulation
    return Simulation.Sim.RunFor(Runtime_ms)['StatusCode']

def BGNES_get_simulation_status()->str:
    global Simulation
    return Simulation.Sim.GetStatus()
    # seeking = [
    #     'IsSimulating',
    #     'RealWorldTimeRemaining_ms',
    #     'RealWorldTimeElapsed_ms',
    #     'InSimulationTime_ms',
    #     'InSimulationTimeRemaining_ms',
    #     'PercentComplete'
    # ]

def BGNES_simulation_recordall(MaxRecordTime_ms:float)->str:
    global Simulation
    return Simulation.Sim.RecordAll(MaxRecordTime_ms)['StatusCode']

def BGNES_get_recording()->dict:
    global Simulation
    return Simulation.Sim.GetRecording()

def BGNES_sphere_create(radius_um:float, center_um:tuple, name=None):
    SphereCfg = NES.Shapes.Sphere.Configuration()
    if name is None:
        name = generate_autoname('sphere-')
    SphereCfg.Name = name
    SphereCfg.Radius_um = radius_um
    SphereCfg.Center_um = list(center_um)
    global Simulation
    sphere = Simulation.Sim.AddSphere(SphereCfg)
    return sphere

def BGNES_cylinder_create(
    Point1Radius_um:float,
    Point1Position_um: tuple,
    Point2Radius_um:float,
    Point2Position_um: tuple,
    name=None)->str:
    global AUTHKEY
    if name is None:
        name = generate_autoname('cylinder-')
    CylinderCfg = NES.Shapes.Cylinder.Configuration()
    CylinderCfg.Name = name
    CylinderCfg.Point1Position_um = list(Point1Position_um)
    CylinderCfg.Point2Position_um = list(Point2Position_um)
    CylinderCfg.Point1Radius_um = Point1Radius_um
    CylinderCfg.Point2Radius_um = Point2Radius_um
    global Simulation
    cylinder = Simulation.Sim.AddCylinder(CylinderCfg)
    return cylinder


def BGNES_box_create(
    CenterPosition_um:tuple,
    Dimensions_um:tuple,
    Rotation_rad:tuple,
    name=None)->str:
    global Simulation
    if name is None:
        name = generate_autoname('box-')
    BoxCfg = NES.Shapes.Box.Configuration()
    BoxCfg.Name = name
    BoxCfg.CenterPosition_um = list(CenterPosition_um)
    BoxCfg.Dimensions_um = list(Dimensions_um)
    BoxCfg.Rotation_rad = list(Rotation_rad)
    box = Simulation.Sim.AddBox(BoxCfg)
    return box

def BGNES_BS_compartment_create(
    ShapeID:str,
    MembranePotential_mV:float,
    RestingPotential_mV:float,
    SpikeThreshold_mV:float,
    DecayTime_ms:float,
    AfterHyperpolarizationAmplitude_mV:float,
    name=None)->str:
    global Simulation
    if name is None:
        name = generate_autoname('compartment-')
    Cfg = NES.Models.Compartments.BS.Configuration()
    Cfg.Name = name
    Cfg.SpikeThreshold_mV = SpikeThreshold_mV
    Cfg.DecayTime_ms = DecayTime_ms
    Cfg.MembranePotential_mV = MembranePotential_mV
    Cfg.AfterHyperpolarizationAmplitude_mV = AfterHyperpolarizationAmplitude_mV
    Cfg.RestingPotential_mV = RestingPotential_mV
    Cfg.Shape = ShapeID
    compartment = Simulation.Sim.AddBSCompartment(Cfg)
    return compartment

def BGNES_connection_staple_create(
    SourceCompartmentID:str,
    DestinationCompartmentID:float,
    name=None)->str:
    global Simulation
    if name is None:
        name = generate_autoname('staple-')
    Cfg = NES.Models.Connections.Staple.Configuration()
    Cfg.Name = name
    Cfg.SourceCompartment = SourceCompartmentID
    Cfg.DestinationCompartment = DestinationCompartmentID
    staple = Simulation.Sim.AddStaple(Cfg)
    return staple

def BGNES_BS_receptor_create(
    SourceCompartmentID:str,
    DestinationCompartmentID:float,
    Conductance_nS:float,
    TimeConstant_ms:float,
    ReceptorLocation_um:tuple,
    name=None)->str:
    global Simulation
    if name is None:
        name = generate_autoname('receptor-')
    Cfg = NES.Models.Connections.Receptor.Configuration()
    Cfg.Name = name
    Cfg.SourceCompartment = SourceCompartmentID
    Cfg.DestinationCompartment = DestinationCompartmentID
    Cfg.Conductance_nS = Conductance_nS
    Cfg.TimeConstant_ms = TimeConstant_ms
    Cfg.ReceptorLocation_um = ReceptorLocation_um
    receptor = Simulation.Sim.AddReceptor(Cfg)
    return receptor

def BGNES_BS_neuron_create(
    Soma,
    Axon,
    MembranePotential_mV:float,
    RestingPotential_mV:float,
    SpikeThreshold_mV:float,
    DecayTime_ms:float,
    AfterHyperpolarizationAmplitude_mV:float,
    PostsynapticPotentialRiseTime_ms:float,
    PostsynapticPotentialDecayTime_ms:float,
    PostsynapticPotentialAmplitude_mV:float,
    name=None)->str:
    global Simulation
    if name is None:
        name = generate_autoname('neuron-')
    Cfg = NES.Models.Neurons.BS.Configuration()
    Cfg.Name = name
    Cfg.Soma = Soma
    Cfg.Axon = Axon
    Cfg.MembranePotential_mV = MembranePotential_mV
    Cfg.RestingPotential_mV = RestingPotential_mV
    Cfg.SpikeThreshold_mV = SpikeThreshold_mV
    Cfg.DecayTime_ms = DecayTime_ms
    Cfg.AfterHyperpolarizationAmplitude_mV = AfterHyperpolarizationAmplitude_mV
    Cfg.PostsynapticPotentialRiseTime_ms = PostsynapticPotentialRiseTime_ms
    Cfg.PostsynapticPotentialDecayTime_ms = PostsynapticPotentialDecayTime_ms
    Cfg.PostsynapticPotentialAmplitude_mV = PostsynapticPotentialAmplitude_mV
    neuron = Simulation.Sim.AddBSNeuron(Cfg)
    return neuron

def BGNES_DAC_create(
    DestinationCompartmentID:str,
    ClampLocation_um:tuple,
    name=None)->str:
    global Simulation
    if name is None:
        name = generate_autoname('DAC-')
    Cfg = NES.Tools.PatchClampDAC.Configuration()
    Cfg.Name = name
    Cfg.DestinationCompartment = DestinationCompartmentID
    Cfg.ClampLocation_um = ClampLocation_um
    DAC = Simulation.Sim.AddPatchClampDAC(Cfg)
    return DAC

def BGNES_DAC_set_output_list(
    TargetDAC,
    DACVoltages_mV:list,
    Timestep_ms:float)->str:
    return TargetDAC.SetOutputList(Timestep_ms, DACVoltages_mV)

def BGNES_ADC_create(
    SourceCompartmentID:str,
    ClampLocation_um:tuple,
    name=None)->str:
    global Simulation
    if name is None:
        name = generate_autoname('ADC-')
    Cfg = NES.Tools.PatchClampADC.Configuration()
    Cfg.Name = name
    Cfg.SourceCompartment = SourceCompartmentID
    Cfg.ClampLocation_um = ClampLocation_um
    ADC = Simulation.Sim.AddPatchClampADC(Cfg)
    return ADC

def BGNES_ADC_set_sample_rate(
    TargetADC,
    Timestep_ms:float)->str:
    return TargetADC.SetSampleRate(Timestep_ms)

def BGNES_ADC_get_recorded_data(
    TargetADC)->list:
    responsedict = TargetADC.GetRecordedData()
    data = responsedict['RecordedData_mV']
    statuscode = responsedict['StatusCode']
    timestep = responsedict['Timestep_ms']
    if statuscode != 0:
        return None, None
    return data, timestep

# -- Higher level functions: ------------------------------------

def BGNES_QuickStart(user:str, passwd:str, scriptversion:str, versionmustmatch:bool, verbose=False)->bool:
    '''
    Check system version compatibility, check system status, and
    obtain authentication token in a single call.
    '''
    version = BGNES_Version()
    if verbose: print('BGNES Version: '+str(version))
    if versionmustmatch:
        if version != scriptversion:
            print('Version mismatch. Script version is %s.' % scriptversion)
            return False

    systemstate, servicestate = BGNES_Status()
    if systemstate != 'Healthy':
        print('System state: '+str(systemstate))
        return False
    if servicestate != 0:
        print('NES service status: '+str(servicestate))
        return False

    # previously: global AUTHKEY
    # previously: AUTHKEY = BGNES_GetToken(user,passwd)
    global SessionToken
    SessionToken = NES.Client.GetInsecureToken(_Username="Admonishing", _Password="Instruction")
    return True

# -- Testing API calls: -----------------------------------------

if __name__ == '__main__':

    from sys import argv
    local_backend = False
    cmdline = argv.copy()
    scriptpath = cmdline.pop(0)
    while len(cmdline) > 0:
        arg = cmdline.pop(0)
        if arg == '-L':
            local_backend = True
            make_bgapi_base_uri(local_host, local_port, use_https=False)

    print('Getting version...')
    version = BGNES_Version()
    print('Version: '+str(version))

    print('Getting status...')
    systemstate, servicestate = BGNES_Status()
    print('System state: '+str(systemstate))
    print('Service state: '+str(servicestate))

    # print('Getting authentication token...')
    # AUTHKEY = BGNES_GetToken()
    # print('Authentication key: '+str(AUTHKEY))

    print('Calling BGNES_simulation_create...')
    global Simulation
    Simulation = BGNES_simulation_create(
        user='Admonishing',
        passwd='Instruction',
        name='test',
        host=uri_host,
        port=uri_port,
        is_local=local_backend,
    )
    print('Simulation: '+str(Simulation.Sim.ID))

    print('Calling BGNES_sphere_create...')
    sphere = BGNES_sphere_create(
        radius_um=10, 
        center_um=(0,0,0)
    )
    print('Shape ID: '+str(sphere.ID))

    print('Calling BGNES_cylinder_create...')
    cylinder = BGNES_cylinder_create(
        Point1Radius_um=10,
        Point1Position_um=(0,0,0),
        Point2Radius_um=20,
        Point2Position_um=(10,10,10)
    )
    print('Shape ID: '+str(cylinder.ID))

    print('Calling BGNES_box_create...')
    box = BGNES_box_create(
        CenterPosition_um=(0,0,0),
        Dimensions_um=(10,10,10),
        Rotation_rad=(0,0,0)
    )
    print('Shape ID: '+str(box.ID))

    print('Calling BGNES_BS_compartment_create...')
    compartment = BGNES_BS_compartment_create(
        ShapeID=sphere.ID,
        MembranePotential_mV=-60.0,
        RestingPotential_mV=-50.0,
        SpikeThreshold_mV=30.0,
        DecayTime_ms=30.0,
        AfterHyperpolarizationAmplitude_mV=-20.0
    )
    print('Compartment ID: '+str(compartment.ID))

    print('Calling BGNES_BS_compartment_create for second compartment...')
    second_compartment = BGNES_BS_compartment_create(
        ShapeID=cylinder.ID,
        MembranePotential_mV=-60.0,
        RestingPotential_mV=-50.0,
        SpikeThreshold_mV=30.0,
        DecayTime_ms=30.0,
        AfterHyperpolarizationAmplitude_mV=-20.0
    )
    print('Second Compartment ID: '+str(second_compartment.ID))

    print('Calling BGNES_connection_staple_create...')
    staple = BGNES_connection_staple_create(
        SourceCompartmentID=compartment.ID,
        DestinationCompartmentID=second_compartment.ID
    )
    print('Staple ID: '+str(staple.ID))

    print('Calling BGNES_BS_receptor_create...')
    receptor = BGNES_BS_receptor_create(
        SourceCompartmentID=compartment.ID, 
        DestinationCompartmentID=second_compartment.ID,
        Conductance_nS=50.0,
        TimeConstant_ms=30.0,
        ReceptorLocation_um=(5,5,5),
    )
    print('Receptor ID: '+str(receptor.ID))

    print('Calling BGNES_BS_neuron_create...')
    neuron = BGNES_BS_neuron_create(
        Soma=sphere.ID, 
        Axon=cylinder.ID,
        MembranePotential_mV=-60.0,
        RestingPotential_mV=-60.0,
        SpikeThreshold_mV=-50.0,
        DecayTime_ms=30.0,
        AfterHyperpolarizationAmplitude_mV=-20.0,
        PostsynapticPotentialRiseTime_ms=5.0,
        PostsynapticPotentialDecayTime_ms=25.0,
        PostsynapticPotentialAmplitude_mV=20.0,
    )
    print('Neuron ID: '+str(neuron.ID))

    print('Calling BGNES_DAC_create...')
    DAC = BGNES_DAC_create(
        DestinationCompartmentID=compartment.ID,
        ClampLocation_um=(2,2,2),
    )
    print('DAC ID: '+str(DAC.ID))

    print('Calling BGNES_DAC_set_output_list...')
    status = BGNES_DAC_set_output_list(
        TargetDAC=DAC,
        DACVoltages_mV=[50.0, 60.0, 70.0],
        Timestep_ms=100.0,
    )
    print('Status code: '+str(status))

    print('Calling BGNES_ADC_create...')
    ADC = BGNES_ADC_create(
        SourceCompartmentID=compartment.ID,
        ClampLocation_um=(2,2,2),
    )
    print('ADC ID: '+str(ADC.ID))

    print('Calling BGNES_ADC_set_sample_rate...')
    status = BGNES_ADC_set_sample_rate(
        TargetADC=ADC,
        Timestep_ms=1.0
    )
    print('Status code: '+str(status))

    print('Calling BGNES_ADC_get_recorded_data...')
    data, timestep = BGNES_ADC_get_recorded_data(
        TargetADC=ADC
    )
    print('Data: '+str(data))
    print('Timestep: '+str(timestep))

    print('Setting record all...')
    status = BGNES_simulation_recordall(-1)
    print('Status: '+str(status))

    print('Running the simulation...')
    status = BGNES_simulation_runfor(500.0)
    print('Status: '+str(status))

    print('Checking simulation status...')
    while True:
        status = BGNES_get_simulation_status()
        print('Status: '+str(status))
        if not status['IsSimulating']:
            break
    print('Simulation done.')

    print('Retrieving recorded data...')
    data = BGNES_get_recording()
    print('Data: '+str(data))

    print('Resetting the simulation...')
    status = BGNES_simulation_reset()
    print('Status: '+str(status))

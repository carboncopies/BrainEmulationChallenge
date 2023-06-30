#!/usr/bin/env python3
# BG_API.py
# Randal A. Koene, 20230624

'''
Common utilities for making REST API requests through the
BrainGenix API.
'''

import requests
import json

BGAPI_BASE_URI='http://api.braingenix.org:8000'
#BGAPI_BASE_URI='http://localhost:8000'

global AUTHKEY
AUTHKEY=''

global SIMID
SIMID=''

def API_call_raw(uri:str)->requests.Response:
    '''
    Make a raw call through the Braingenix API.
    The REST URI must already be prepared.
    '''
    return requests.get(uri)

def BGAPI_call(rq:str)->requests.Response:
    #print('Request is: '+str(rq))
    response = requests.get(BGAPI_BASE_URI+rq)
    #print('Response is: '+str(response.text))
    return response

def BGNES_handle_response(
    response:requests.Response,
    caller=str,
    retstrings:list=['StatusCode'])->list:
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

def BGNES_GetToken(user:str, passwd:str)->str:
    response = BGAPI_call('/Auth/GetToken?Username=%s&Password=%s' % (user, passwd))
    return BGNES_handle_response(response, 'BGNES_GetToken', ['AuthKey'])[0]

def BGNES_simulation_create(name:str)->str:
    global AUTHKEY
    response = BGAPI_call('/NES/Simulation/Create?AuthKey=%s&SimulationName=%s' % (AUTHKEY, name))
    return BGNES_handle_response(response, 'BGNES_simulation_create', ['SimulationID'])[0]

def BGNES_simulation_reset()->str:
    global AUTHKEY
    reqstr = '/NES/Simulation/Reset?AuthKey=%s&SimulationID=%s' % (
            AUTHKEY,
            SIMID
        )
    response = BGAPI_call(reqstr)
    return BGNES_handle_response(response, 'BGNES_simulation_reset')[0]

def BGNES_simulation_runfor(Runtime_ms:float)->str:
    global AUTHKEY
    reqstr = '/NES/Simulation/RunFor?AuthKey=%s&SimulationID=%s&Runtime_ms=%s' % (
            AUTHKEY,
            SIMID,
            str(Runtime_ms)
        )
    response = BGAPI_call(reqstr)
    return BGNES_handle_response(response, 'BGNES_simulation_runfor')[0]

def BGNES_get_simulation_status()->str:
    global AUTHKEY
    reqstr = '/NES/Simulation/GetStatus?AuthKey=%s&SimulationID=%s' % (
            AUTHKEY,
            SIMID,
        )
    response = BGAPI_call(reqstr)
    seeking = [
        'IsSimulating',
        'RealWorldTimeRemaining_ms',
        'RealWorldTimeElapsed_ms',
        'InSimulationTime_ms',
        'InSimulationTimeRemaining_ms',
        'PercentComplete'
    ]
    return BGNES_handle_response(response, 'BGNES_simulation_runfor', seeking)

def BGNES_simulation_recordall(MaxRecordTime_ms:float)->str:
    global AUTHKEY
    reqstr = '/NES/Simulation/RecordAll?AuthKey=%s&SimulationID=%s&MaxRecordTime_ms=%s' % (
            AUTHKEY,
            SIMID,
            str(MaxRecordTime_ms)
        )
    response = BGAPI_call(reqstr)
    return BGNES_handle_response(response, 'BGNES_simulation_recordall')[0]

def BGNES_get_recording()->dict:
    global AUTHKEY
    reqstr = '/NES/Simulation/GetRecording?AuthKey=%s&SimulationID=%s' % (
            AUTHKEY,
            SIMID
        )
    response = BGAPI_call(reqstr)
    jsondatastr = BGNES_handle_response(response, 'BGNES_get_recording', ['Recording'])[0]
    return json.loads(jsondatastr)

def BGNES_sphere_create(radius_nm:float, center_nm:tuple, name=None)->str:
    global AUTHKEY
    namestr = '' if name is None else '&Name='+str(name)
    reqstr = '/NES/Geometry/Shape/Sphere/Create?AuthKey=%s&SimulationID=%s&Radius_nm=%s&Center_nm=%s%s' % (
            AUTHKEY,
            SIMID,
            str(radius_nm),
            json.dumps(list(center_nm)),
            namestr
        )
    response = BGAPI_call(reqstr)
    return BGNES_handle_response(response, 'BGNES_sphere_create', ['ShapeID'])[0]

def BGNES_cylinder_create(
    Point1Radius_nm:float,
    Point1Position_nm: tuple,
    Point2Radius_nm:float,
    Point2Position_nm: tuple,
    name=None)->str:
    global AUTHKEY
    namestr = '' if name is None else '&Name='+str(name)
    reqstr = '/NES/Geometry/Shape/Cylinder/Create?AuthKey=%s&SimulationID=%s&Point1Radius_nm=%s&Point1Position_nm=%s&Point2Radius_nm=%s&Point2Position_nm=%s%s' % (
            AUTHKEY,
            SIMID,
            str(Point1Radius_nm),
            json.dumps(list(Point1Position_nm)),
            str(Point2Radius_nm),
            json.dumps(list(Point2Position_nm)),
            namestr
        )
    response = BGAPI_call(reqstr)
    return BGNES_handle_response(response, 'BGNES_cylinder_create', ['ShapeID'])[0]

def BGNES_box_create(
    CenterPosition_nm:tuple,
    Dimensions_nm:tuple,
    Rotation_rad:tuple,
    name=None)->str:
    global AUTHKEY
    namestr = '' if name is None else '&Name='+str(name)
    reqstr = '/NES/Geometry/Shape/Box/Create?AuthKey=%s&SimulationID=%s&CenterPosition_nm=%s&Dimensions_nm=%s&Rotation_rad=%s%s' % (
            AUTHKEY,
            SIMID,
            json.dumps(list(CenterPosition_nm)),
            json.dumps(list(Dimensions_nm)),
            json.dumps(list(Rotation_rad)),
            namestr
        )
    response = BGAPI_call(reqstr)
    return BGNES_handle_response(response, 'BGNES_box_create', ['ShapeID'])[0]

def BGNES_BS_compartment_create(
    ShapeID:str,
    MembranePotential_mV:float,
    RestingPotential_mV:float,
    SpikeThreshold_mV:float,
    DecayTime_ms:float,
    AfterHyperpolarizationAmplitude_mV:float,
    name=None)->str:
    global AUTHKEY
    namestr = '' if name is None else '&Name='+str(name)
    reqstr = '/NES/Compartment/BS/Create?AuthKey=%s&SimulationID=%s&ShapeID=%s&MembranePotential_mV=%s&SpikeThreshold_mV=%s&DecayTime_ms=%s%s' % (
            AUTHKEY,
            SIMID,
            str(ShapeID),
            str(MembranePotential_mV),
            str(RestingPotential_mV),
            str(SpikeThreshold_mV),
            str(DecayTime_ms),
            str(AfterHyperpolarizationAmplitude_mV),
            namestr
        )
    response = BGAPI_call(reqstr)
    return BGNES_handle_response(response, 'BGNES_BS_compartment_create', ['CompartmentID'])[0]

def BGNES_connection_staple_create(
    SourceCompartmentID:str,
    DestinationCompartmentID:float,
    name=None)->str:
    global AUTHKEY
    namestr = '' if name is None else '&Name='+str(name)
    reqstr = '/NES/Connection/Staple/Create?AuthKey=%s&SimulationID=%s&SourceCompartmentID=%s&DestinationCompartmentID=%s%s' % (
            AUTHKEY,
            SIMID,
            str(SourceCompartmentID),
            str(DestinationCompartmentID),
            namestr
        )
    response = BGAPI_call(reqstr)
    return BGNES_handle_response(response, 'BGNES_connection_staple_create', ['ConnectionID'])[0]

def BGNES_BS_receptor_create(
    SourceCompartmentID:str,
    DestinationCompartmentID:float,
    Conductance_nS:float,
    TimeConstant_ms:float,
    ReceptorLocation_nm:tuple,
    name=None)->str:
    global AUTHKEY
    namestr = '' if name is None else '&Name='+str(name)
    reqstr = '/NES/Connection/Staple/Create?AuthKey=%s&SimulationID=%s&SourceCompartmentID=%s&DestinationCompartmentID=%s&Conductance_nS=%s&TimeConstant_ms=%s&ReceptorLocation_nm=%s%s' % (
            AUTHKEY,
            SIMID,
            str(SourceCompartmentID),
            str(DestinationCompartmentID),
            str(Conductance_nS),
            str(TimeConstant_ms),
            json.dumps(list(ReceptorLocation_nm)),
            namestr
        )
    response = BGAPI_call(reqstr)
    return BGNES_handle_response(response, 'BGNES_BS_receptor_create', ['ConnectionID'])[0]

def BGNES_DAC_create(
    DestinationCompartmentID:str,
    ClampLocation_nm:tuple,
    name=None)->str:
    global AUTHKEY
    namestr = '' if name is None else '&Name='+str(name)
    reqstr = '/NES/Tool/PatchClampDAC/Create?AuthKey=%s&SimulationID=%s&DestinationCompartmentID=%s&ClampLocation_nm=%s%s' % (
            AUTHKEY,
            SIMID,
            str(DestinationCompartmentID),
            json.dumps(list(ClampLocation_nm)),
            namestr
        )
    response = BGAPI_call(reqstr)
    return BGNES_handle_response(response, 'BGNES_DAC_create', ['PatchClampDACID'])[0]

def BGNES_DAC_set_output_list(
    TargetDAC:str,
    DACVoltages_mV:list,
    Timestep_ms:float)->str:
    global AUTHKEY
    reqstr = '/NES/Tool/PatchClampDAC/SetOutputList?AuthKey=%s&SimulationID=%s&TargetDAC=%s&DACVoltages_mV=%s&Timestep_ms=%s' % (
            AUTHKEY,
            SIMID,
            str(TargetDAC),
            json.dumps(DACVoltages_mV),
            str(Timestep_ms)
        )
    response = BGAPI_call(reqstr)
    return BGNES_handle_response(response, 'BGNES_DAC_set_output_list')[0]

def BGNES_ADC_create(
    SourceCompartmentID:str,
    ClampLocation_nm:tuple,
    name=None)->str:
    global AUTHKEY
    namestr = '' if name is None else '&Name='+str(name)
    reqstr = '/NES/Tool/PatchClampADC/Create?AuthKey=%s&SimulationID=%s&SourceCompartmentID=%s&ClampLocation_nm=%s%s' % (
            AUTHKEY,
            SIMID,
            str(SourceCompartmentID),
            json.dumps(list(ClampLocation_nm)),
            namestr
        )
    response = BGAPI_call(reqstr)
    return BGNES_handle_response(response, 'BGNES_ADC_create', ['PatchClampADCID'])[0]

def BGNES_ADC_set_sample_rate(
    TargetADC:str,
    Timestep_ms:float)->str:
    global AUTHKEY
    reqstr = '/NES/Tool/PatchClampADC/SetSampleRate?AuthKey=%s&SimulationID=%s&TargetADC=%s&Timestep_ms=%s' % (
            AUTHKEY,
            SIMID,
            str(TargetADC),
            str(Timestep_ms)
        )
    response = BGAPI_call(reqstr)
    return BGNES_handle_response(response, 'BGNES_ADC_set_sample_rate')[0]

def BGNES_ADC_get_recorded_data(
    TargetADC:str)->list:
    global AUTHKEY
    reqstr = '/NES/Tool/PatchClampADC/GetRecordedData?AuthKey=%s&SimulationID=%s&TargetADC=%s' % (
            AUTHKEY,
            SIMID,
            str(TargetADC)
        )
    response = BGAPI_call(reqstr)
    return BGNES_handle_response(response, 'BGNES_ADC_get_recorded_data', ['RecordedData_mV', 'Timestep_ms'])

# -- Testing API calls: -----------------------------------------

if __name__ == '__main__':

    print('Getting version...')
    version = BGNES_Version()
    print('Version: '+str(version))

    print('Getting status...')
    systemstate, servicestate = BGNES_Status()
    print('System state: '+str(systemstate))
    print('Service state: '+str(servicestate))

    print('Getting authentication token...')
    AUTHKEY = BGNES_GetToken('Admonishing','Instruction')
    print('Authentication key: '+str(AUTHKEY))

    print('Calling BGNES_simulation_create...')
    SIMID = BGNES_simulation_create('test')
    print('Simulation ID: '+str(SIMID))

    print('Calling BGNES_sphere_create...')
    sphere_id = BGNES_sphere_create(10, (0,0,0))
    print('Shape ID: '+str(sphere_id))

    print('Calling BGNES_cylinder_create...')
    cylinder_id = BGNES_cylinder_create(10, (0,0,0), 20, (10,10,10))
    print('Shape ID: '+str(cylinder_id))

    print('Calling BGNES_box_create...')
    box_id = BGNES_box_create((0,0,0), (10,10,10), (0,0,0))
    print('Shape ID: '+str(box_id))

    print('Calling BGNES_BS_compartment_create...')
    compartment_id = BGNES_BS_compartment_create(sphere_id, -60.0, -50.0, 30.0)
    print('Compartment ID: '+str(compartment_id))

    print('Calling BGNES_BS_compartment_create for second compartment...')
    second_compartment_id = BGNES_BS_compartment_create(cylinder_id, -60.0, -50.0, 30.0)
    print('Second Compartment ID: '+str(second_compartment_id))

    print('Calling BGNES_connection_staple_create...')
    staple_id = BGNES_connection_staple_create(compartment_id, second_compartment_id)
    print('Staple ID: '+str(staple_id))

    print('Calling BGNES_BS_receptor_create...')
    receptor_id = BGNES_BS_receptor_create(compartment_id, second_compartment_id, 50.0, 30.0, (5,5,5))
    print('Receptor ID: '+str(receptor_id))

    print('Calling BGNES_DAC_create...')
    DAC_id = BGNES_DAC_create(compartment_id, (2,2,2))
    print('DAC ID: '+str(DAC_id))

    print('Calling BGNES_DAC_set_output_list...')
    status = BGNES_DAC_set_output_list(DAC_id, [50.0, 60.0, 70.0], 100.0)
    print('Status code: '+str(status))

    print('Calling BGNES_ADC_create...')
    ADC_id = BGNES_ADC_create(compartment_id, (2,2,2))
    print('ADC ID: '+str(ADC_id))

    print('Calling BGNES_ADC_set_sample_rate...')
    status = BGNES_ADC_set_sample_rate(ADC_id, 1.0)
    print('Status code: '+str(status))

    print('Calling BGNES_ADC_get_recorded_data...')
    data, timestep = BGNES_ADC_get_recorded_data(ADC_id)
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
        if not status[0]:
            break
    print('Simulation done.')

    print('Retrieving recorded data...')
    data = BGNES_get_recording()
    print('Data: '+str(data))

    print('Resetting the simulation...')
    status = BGNES_simulation_reset()
    print('Status: '+str(status))

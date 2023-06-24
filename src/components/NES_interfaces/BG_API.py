#!/usr/bin/env python3
# BG_API.py
# Randal A. Koene, 20230624

'''
Common utilities for making REST API requests through the
BrainGenix API.
'''

import requests

BGAPI_BASE_URI='http://api.braingenix.org:80'

def API_call_raw(uri:str)->requests.Response:
    '''
    Make a raw call through the Braingenix API.
    The REST URI must already be prepared.
    '''
    return requests.get(uri)

def BGAPI_call(rq:str)->requests.Response:
    return requests.get(BGAPI_BASE_URI+rq)

def BGNES_simulation_create(name:str)->str:
    response = BGAPI_call('/NES/Simulation/Create?SimulationName='+name)
    if response.status_code==200:
        try:
            data = response.json()
            if data['StatusCode']==0:
                return data['SimulationID']
            else:
                raise Exception('BGNES_simulation_create: API returned status code %s.' % data['StatusCode'])
        except Exception as e:
            raise Exception('BGNES_simulation_create: API did not return expected JSON data.')
    else:
        raise Exception('BGNES_simulation_create: Failed with GET status %s.' % response.status_code)

def BGNES_sphere_create(radius_nm:float, center_nm:tuple, name=None)->str:
    if name is None:
        response = BGAPI_call('/NES/Geometry/Shape/Sphere/Create?Radius_nm=%s&Center_nm=%s' % (
            str(radius_nm),
            str(center_nm)
            ))
    else:
        response = BGAPI_call('/NES/Geometry/Shape/Sphere/Create?Radius_nm=%s&Center_nm=%s&Name=%s' % (
            str(radius_nm),
            str(center_nm),
            str(name)
            ))
    if response.status_code==200:
        try:
            data = response.json()
            if data['StatusCode']==0:
                return data['ShapeID']
            else:
                raise Exception('BGNES_sphere_create: API returned status code %s.' % data['StatusCode'])
        except Exception as e:
            raise Exception('BGNES_sphere_create: API did not return expected JSON data.')
    else:
        raise Exception('BGNES_sphere_create: Failed with GET status %s.' % response.status_code)


# -- Testing API calls: -----------------------------------------

if __name__ == '__main__':
    
    print('Calling BGNES_sphere_create...')
    sphere_id = BGNES_sphere_create(10, (0,0,0))
    print('Shape ID: '+str(sphere_id))

    print('Calling BGNES_simulation_create...')
    simulation_id = BGNES_simulation_create('test')
    print('Simulation ID: '+str(simulation_id))

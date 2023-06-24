#!/usr/bin/env python3
# BG_API.py
# Randal A. Koene, 20230624

'''
Common utilities for making REST API requests through the
BrainGenix API.
'''

import requests

BGAPI_BASE_URI='http://api.braingenix.org:8000'

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

# -- Testing API calls: -----------------------------------------

if __name__ == '__main__':
    print('Calling BGNES_simulation_create...')
    simulation_id = BGNES_simulation_create('test')
    print('Simulation ID: '+str(simulation_id))

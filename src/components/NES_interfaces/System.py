# System.py
# Randal A. Koene, 20230623

'''
Definitions of in-silico ground-truth systems.
'''

import matplotlib.pyplot as plt
from time import sleep
import json

import common.glb as glb
from .common.Spatial import PlotInfo
from .common.NeuralCircuit import NeuralCircuit
from .Region import Region

class System:
    def __init__(self, name:str):
        self.name=name

        # Cached references:
        self.neuralcircuits = {}
        self.regions = {}

        # Cached state:
        self.dt_ms = 1.0
        self.t_ms = 0

        self.t_recordall_start_ms = 0
        self.t_recordall_max_ms = 0

        # Create through API call:
        glb.bg_api.BGNES_simulation_create(name=name)

    def add_circuit(self, circuit:NeuralCircuit)->NeuralCircuit:
        self.neuralcircuits[circuit.id] = circuit
        return circuit

    def add_region(self, region:Region)->Region:
        self.regions[region.id] = region
        return region

    def attach_direct_stim(self, tstim_ms:list):
        for circuit in self.neuralcircuits:
            self.neuralcircuits[circuit].attach_direct_stim(tstim_ms)

    def set_record_all(self, t_max_ms=-1):
        '''
        Record all dynamically calculated values for a maximum of t_max_ms
        milliseconds. Setting t_max_ms effectively turns off recording.
        Setting t_max_ms to -1 means record forever.
        '''
        glb.bg_api.BGNES_simulation_recordall(t_max_ms)

    def get_recording(self)->dict:
        return glb.bg_api.BGNES_get_recording()

    def run_for(self, t_run_ms:float, blocking=True):
        glb.bg_api.BGNES_simulation_runfor(t_run_ms)
        if not blocking: return
        # TODO: *** Beware that the following can get stuck.
        while glb.bg_api.BGNES_get_simulation_status()[0]:
            sleep(0.005)

    def to_dict(self)->dict:
        # neuralcircuits = {}
        # for circuit in self.neuralcircuits:
        #     neuralcircuits[circuit.id] = circuit.to_dict()
        regions = {}
        for region in self.regions:
            regions[region] = self.regions[region].to_dict()
        system_data = {
            'name': self.name,
            #'neuralcircuits': neuralcircuits, # Already included in region.
            'regions': regions,
            'dt_ms': self.dt_ms,
            't_ms': self.t_ms,
            't_recordall_start_ms': self.t_recordall_start_ms,
            't_recordall_max_ms': self.t_recordall_max_ms,
            # TODO: Should we include defined instruments?
        }
        return system_data

    def save(self, file:str):
        with open(file, 'w') as f:
            # tmp = self.to_dict()
            # print(str(tmp))
            json.dump(self.to_dict(), f)

    def show(self, show:dict, pltinfo=None, linewidth=0.5):
        doshow = pltinfo is None
        if pltinfo is None: pltinfo = PlotInfo('System %s' % str(self.name))
        for region in self.regions.values():
            region.show(show=show, pltinfo=pltinfo, linewidth=linewidth)
        if doshow: plt.draw()

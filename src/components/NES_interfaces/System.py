# System.py
# Randal A. Koene, 20230623

'''
Definitions of in-silico ground-truth systems.
'''

from time import sleep

from .BG_API import BGNES_simulation_create, BGNES_simulation_recordall, BGNES_get_recording, BGNES_simulation_runfor, BGNES_get_simulation_status

from .NeuralCircuit import NeuralCircuit
from .Region import Region

class System:
    def __init__(self, name:str, user:str, passwd:str):
        # Cached references:
        self.neuralcircuits = {}
        self.regions = {}

        # Cached state:
        self.t_ms = 0

        # Create through API call:
        self.id = BGNES_simulation_create(name)

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
        BGNES_simulation_recordall(t_max_ms)

    def get_recording(self)->dict:
        return BGNES_get_recording()

    def run_for(self, t_run_ms:float, blocking=True):
        BGNES_simulation_runfor(t_run_ms)
        if not blocking: return
        while BGNES_get_simulation_status()[0]:
            sleep(0.005)

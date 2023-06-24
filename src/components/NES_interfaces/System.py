# System.py
# Randal A. Koene, 20230623

'''
Definitions of in-silico ground-truth systems.
'''

from .BG_API import BGNES_simulation_create

from .NeuralCircuit import NeuralCircuit
from .Region import Region

class System:
    def __init__(self, name:str):
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
        recording_was_off = self.t_recordall_max_ms == 0
        self.t_recordall_max_ms = t_max_ms
        if self.t_recordall_max_ms != 0:
            self.t_recordall_start_ms = self.t_ms

    def is_recording(self)->bool:
        if self.t_recordall_max_ms < 0: return True
        return self.t_ms < (self.t_recordall_start_ms+self.t_recordall_max_ms)

    def get_recording(self)->dict:
        data = { 't_ms': self.t_recorded_ms }
        for circuit in self.neuralcircuits:
            data[circuit] = self.neuralcircuits[circuit].get_recording()
        return data

    def run_for(self, t_run_ms:float):
        t_end_ms = self.t_ms + t_run_ms
        while self.t_ms < t_end_ms:
            recording = self.is_recording()
            if recording: self.t_recorded_ms.append(self.t_ms)
            for circuit in self.neuralcircuits:
                self.neuralcircuits[circuit].update(self.t_ms, recording)
            self.t_ms += self.dt_ms

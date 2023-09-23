# System.py
# Randal A. Koene, 20230623

'''
Definitions of in-silico ground-truth systems.
'''

from .NeuralCircuit import NeuralCircuit
from .Region import Region
from .Electrodes import Recording_Electrode
from .Calcium_Imaging import Calcium_Imaging

class System:
    def __init__(self, name:str):
        self.name=name
        self.neuralcircuits = {}
        self.regions = {}
        self.dt_ms = 1.0
        self.t_ms = 0
        self.t_recordall_start_ms = 0
        self.t_recordall_max_ms = 0

        self.t_recorded_ms = []

        self.recording_electrodes = []
        self.calcium_imaging = None

    def component_by_id(self, component_id:str, component_function:str):
        '''
        Runs a specified function in any component in the System that matches id.
        '''
        # TODO: Complete this.
        component = None
        result = None
        return result

    def add_circuit(self, circuit:NeuralCircuit)->NeuralCircuit:
        self.neuralcircuits[circuit.id] = circuit
        return circuit

    def add_region(self, region:Region)->Region:
        self.regions[region.id] = region
        return region

    def get_geo_center(self)->tuple:
        '''
        Find and return the geometric center of the system.
        This is done by finding the centroid of all the cell centers.
        '''
        x, y, z = 0, 0, 0
        num_cells = 0
        for circuit in self.neuralcircuits:
            circuit_cell_centers = self.neuralcircuits[circuit].get_cell_centers()
            for cell_center in circuit_cell_centers:
                x += cell_center[0]
                y += cell_center[1]
                z += cell_center[2]
                num_cells += 1
        x /= num_cells
        y /= num_cells
        z /= num_cells
        return x, y, z

    def attach_direct_stim(self, tstim_ms:list):
        for circuit in self.neuralcircuits:
            self.neuralcircuits[circuit].attach_direct_stim(tstim_ms)

    def set_spontaneous_activity(self, spont_spike_settings:list):
        '''
        Expects a list of tuples where each tuple associates a mean and stdev
        spike interval with a neuron identified by its ID string.
        E.g. [ ((280, 140), '0'), ... ]
        '''
        for circuit in self.neuralcircuits:
            self.neuralcircuits[circuit].set_spontaneous_activity(spont_spike_settings)

    def attach_recording_electrodes(self, set_of_electrode_specs:list):
        for electrode_specs in set_of_electrode_specs:
            self.recording_electrodes.append(Recording_Electrode(electrode_specs))

    def attach_calcium_imaging(self, calcium_specs:dict):
        self.calcium_imaging = Calcium_Imaging(calcium_specs)

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

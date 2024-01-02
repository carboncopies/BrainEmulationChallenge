# System.py
# Randal A. Koene, 20230623

'''
Definitions of in-silico ground-truth systems.
'''

import matplotlib.pyplot as plt
import json

from .common.Spatial import PlotInfo
from .common.NeuralCircuit import NeuralCircuit
from .Region import Region, BrainRegion
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

        self.t_instruments_start_ms = 0
        self.t_instruments_max_ms = 0

        self.t_instruments_ms = []

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

    def get_all_neurons(self)->list:
        '''
        Collects a list of references to all neurons in all neural circuits.
        '''
        all_neurons = []
        for circuit in self.neuralcircuits:
            all_neurons += self.neuralcircuits[circuit].get_neurons()
        return all_neurons

    def get_neurons_by_IDs(self, listofIDs:list)->list:
        listed_neurons = []
        for circuit in self.neuralcircuits:
            listed_neurons += self.neuralcircuits[circuit].get_neurons_by_IDs(listofIDs)
        return listed_neurons

    def get_all_neuron_IDs(self)->list:
        all_neurons = self.get_all_neurons()
        all_neuron_IDs = [ n.id for n in all_neurons ]
        return all_neuron_IDs

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
            self.recording_electrodes.append(Recording_Electrode(electrode_specs, self))

    def attach_calcium_imaging(self, calcium_specs:dict, pars):
        self.calcium_imaging = Calcium_Imaging(calcium_specs, self, pars=pars)

    def set_record_all(self, t_max_ms=-1):
        '''
        Record all dynamically calculated values for a maximum of t_max_ms
        milliseconds. Setting t_max_ms=0 effectively turns off recording.
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

    def set_record_instruments(self, t_max_ms=-1):
        '''
        Record with specified simulated recording instruments for a maximum
        of t_max_ms milliseconds.
        Setting t_max_ms=0 effectively turns off instrument recording.
        Setting t_max_ms to -1 means record forever.
        '''
        instruments_were_off = self.t_instruments_max_ms == 0
        self.t_instruments_max_ms = t_max_ms
        if self.t_instruments_max_ms != 0:
            self.t_instruments_start_ms = self.t_ms

    def instruments_are_recording(self)->bool:
        if self.t_instruments_max_ms < 0: return True
        return self.t_ms < (self.t_instruments_start_ms+self.t_instruments_max_ms)

    def get_instrument_recordings(self)->dict:
        data = { 't_ms': self.t_instruments_ms }
        for electrode in self.recording_electrodes:
            data[electrode.id] = electrode.get_recording()
        if self.calcium_imaging:
            data[self.calcium_imaging.id] = self.calcium_imaging.get_recording()
        return data

    def get_em_stack(self, em_specs:dict)->dict:
        return {}

    def run_for(self, t_run_ms:float):
        t_end_ms = self.t_ms + t_run_ms
        while self.t_ms < t_end_ms:
            recording = self.is_recording()
            if recording: self.t_recorded_ms.append(self.t_ms)
            for circuit in self.neuralcircuits:
                self.neuralcircuits[circuit].update(self.t_ms, recording)
            instruments = self.instruments_are_recording()
            if instruments:
                self.t_instruments_ms.append(self.t_ms)
                for electrode in self.recording_electrodes:
                    electrode.record(self.t_ms)
                if self.calcium_imaging:
                    self.calcium_imaging.record(self.t_ms)
            self.t_ms += self.dt_ms

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

    def from_dict(self, system_data:dict):
        self.name = system_data['name']
        self.dt_ms = system_data['dt_ms']
        self.t_ms = system_data['t_ms']
        self.t_recordall_start_ms = system_data['t_recordall_start_ms']
        self.t_recordall_max_ms = system_data['t_recordall_max_ms']
        # self.neuralcircuits = {}
        # for circuit_id in system_data['neuralcircuits']:
        #     circuit = BS_Aligned_NC('')
        #     circuit.from_dict(system_data['neuralcircuits'][circuit_id])
        #     self.add_circuit(circuit)
        self.regions = {}
        for region_id in system_data['regions']:
            region = BrainRegion('', None, None)
            region.from_dict(system_data['regions'][region_id])
            self.add_region(region)
        self.neuralcircuits = {}
        for region in self.regions:
            self.add_circuit(self.regions[region].content)
        # Convert connection data to contain references to neurons:
        all_neurons = self.get_all_neurons()
        for neuron in all_neurons:
            receptors_with_references = []
            for receptor in neuron.receptors:
                n_id, weight = receptor
                n_ref = self.get_neurons_by_IDs([ n_id, ])[0]
                receptors_with_references.append( (n_ref, weight) )
            neuron.receptors = receptors_with_references                
        # TODO: Should we include defined instruments?

    def save(self, file:str):
        with open(file, 'w') as f:
            # tmp = self.to_dict()
            # print(str(tmp))
            json.dump(self.to_dict(), f)

    def load(self, file:str):
        with open(file, 'r') as f:
            system_data = json.load(f)
        self.from_dict(system_data)

    def show(self, show:dict, pltinfo=None, linewidth=0.5):
        doshow = pltinfo is None
        if pltinfo is None: pltinfo = PlotInfo('System %s' % str(self.name))
        for region in self.regions.values():
            region.show(show=show, pltinfo=pltinfo, linewidth=linewidth)
        if doshow: plt.draw()


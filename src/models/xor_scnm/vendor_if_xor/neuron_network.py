# Vendored from IFneuron-model/In_Domain/In_Domain_Data_Generation/NeuronNetwork.py

from . import ifneuron
import numpy as np
from typing import Dict, List, Tuple


class NeuronNetwork:
    def __init__(self, id: str):
        self.id: str = id
        self.all_neurons: Dict[str, ifneuron.IFneuron] = {}
        self._run_time_len: int = 0

    def add_neuron(self, neuron_id: str) -> None:
        if neuron_id in self.all_neurons:
            raise ValueError(f'Neuron "{neuron_id}" already exists in network')
        self.all_neurons[neuron_id] = ifneuron.IFneuron(neuron_id)

    def add_neuron_connection(
        self, presynaptic_neuron_id: str, postsynaptic_neuron_id: str, weight: float
    ) -> None:
        if presynaptic_neuron_id not in self.all_neurons:
            raise KeyError(f'Presynaptic neuron "{presynaptic_neuron_id}" not found')
        if postsynaptic_neuron_id not in self.all_neurons:
            raise KeyError(f'Postsynaptic neuron "{postsynaptic_neuron_id}" not found')
        connection = (self.all_neurons[presynaptic_neuron_id], weight)
        self.all_neurons[postsynaptic_neuron_id].receptors.append(connection)

    def set_direct_stimulation_time_ms(self, neuron_id: str, stimulation_time_ms: List[float]) -> None:
        if neuron_id not in self.all_neurons:
            raise KeyError(f'Neuron "{neuron_id}" not found')
        times_sorted = sorted(list(stimulation_time_ms))
        n = self.all_neurons[neuron_id]
        n.t_directstim_ms = list(times_sorted)
        n.t_directstim_ms_orig = list(times_sorted)

    def run_simulation(self, run_time_ms: int, record_membrane_potential: bool) -> None:
        self._run_time_len = int(run_time_ms)
        for step in range(self._run_time_len):
            for n in self.all_neurons.values():
                n.update(step, record_membrane_potential)

    def get_neuron_spike_times_ms(self, neuron_id: str) -> List[float]:
        if neuron_id not in self.all_neurons:
            raise KeyError(f'Neuron "{neuron_id}" not found')
        return self.all_neurons[neuron_id].t_act_ms

    def get_neuron_spike_train(self, neuron_id: str) -> np.ndarray:
        if neuron_id not in self.all_neurons:
            raise KeyError(f'Neuron "{neuron_id}" not found')
        T = self._run_time_len if self._run_time_len > 0 else len(self.get_neuron_run_time_ms(neuron_id))
        spike_train = np.zeros(T, dtype=int)
        for t in self.get_neuron_spike_times_ms(neuron_id):
            if 0 <= int(t) < T:
                spike_train[int(t)] = 1
        return spike_train

    def get_neuron_membrane_potentials(self, neuron_id: str) -> List[float]:
        if neuron_id not in self.all_neurons:
            raise KeyError(f'Neuron "{neuron_id}" not found')
        return self.all_neurons[neuron_id].Vm_recorded

    def get_neuron_run_time_ms(self, neuron_id: str) -> List[float]:
        if neuron_id not in self.all_neurons:
            raise KeyError(f'Neuron "{neuron_id}" not found')
        return self.all_neurons[neuron_id].t_recorded_ms

    def get_neuron_receptors(self, neuron_id: str) -> List[Tuple[str, float]]:
        if neuron_id not in self.all_neurons:
            raise KeyError(f'Neuron "{neuron_id}" not found')
        receptors = []
        for connection in self.all_neurons[neuron_id].receptors:
            receptors.append((connection[0].id, connection[1]))
        return receptors

    def get_all_neurons(self) -> List[ifneuron.IFneuron]:
        return list(self.all_neurons.values())

    def get_all_neuron_ids(self) -> List[str]:
        return list(self.all_neurons.keys())

    def get_network_id(self) -> str:
        return self.id

    def print_all_neurons(self) -> None:
        print(f"Network '{self.id}' neurons:", self.all_neurons)

    def get_neuron_stim_times(self, neuron_id: str) -> List[float]:
        if neuron_id not in self.all_neurons:
            raise KeyError(f'Neuron "{neuron_id}" not found')
        n = self.all_neurons[neuron_id]
        src = n.t_directstim_ms_orig if hasattr(n, "t_directstim_ms_orig") and n.t_directstim_ms_orig else n.t_directstim_ms
        return list(src)

    def get_neuron_stim_vector(self, neuron_id: str) -> np.ndarray:
        if neuron_id not in self.all_neurons:
            raise KeyError(f'Neuron "{neuron_id}" not found')
        T = self._run_time_len if self._run_time_len > 0 else len(self.get_neuron_run_time_ms(neuron_id))
        v = np.zeros(T, dtype=int)
        for t in self.get_neuron_stim_times(neuron_id):
            tt = int(t)
            if 0 <= tt < T:
                v[tt] = 1
        return v

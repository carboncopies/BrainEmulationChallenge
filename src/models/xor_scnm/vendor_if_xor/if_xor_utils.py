# Vendored from IFneuron-model/In_Domain/In_Domain_Data_Generation/utils.py
# (XOR trial helpers + single-trial simulation.)

import numpy as np
from .neuron_network import NeuronNetwork
from typing import Dict, List, Optional, Tuple, Union


def generate_random_stimulation_times_ms(
    num_stims: int,
    max_time_ms: float,
    min_time_between_stim_ms: float,
) -> List[int]:
    stimulation_times = []
    current_time = 0
    time_per_stim_slot = max_time_ms / num_stims

    for i in range(num_stims):
        min_current_stim_time = current_time + min_time_between_stim_ms
        upper_limit_from_distribution = int((i + 1) * time_per_stim_slot)
        remaining_stims_to_place = num_stims - (i + 1)
        upper_limit_from_remaining_space = max_time_ms - (remaining_stims_to_place * min_time_between_stim_ms)
        upper_bound = min(upper_limit_from_distribution, upper_limit_from_remaining_space)
        lower_bound = max(min_current_stim_time, current_time)

        if lower_bound > upper_bound:
            return stimulation_times

        if lower_bound == upper_bound:
            stim_time = lower_bound
        else:
            stim_time = np.random.randint(lower_bound, upper_bound + 1)

        stimulation_times.append(int(stim_time))
        current_time = stim_time

    return stimulation_times


def build_in_domain_trials(
    trials_per_type: int,
    trial_length_ms: int = 100,
    start_guard_ms: Optional[int] = 5,
    end_guard_ms: Optional[int] = 39,
    stim_guard_ms: Optional[int] = None,
    rng_seed: Optional[int] = 42,
) -> List[Dict[str, Union[int, None]]]:
    if trials_per_type <= 0:
        raise ValueError("trials_per_type must be positive")
    if trial_length_ms <= 0:
        raise ValueError("trial_length_ms must be positive")

    if end_guard_ms is None:
        g = stim_guard_ms if stim_guard_ms is not None else 5
        low, high = int(g), int(trial_length_ms - 1 - g)
    else:
        sg = 5 if start_guard_ms is None else int(start_guard_ms)
        low, high = sg, int(trial_length_ms - 1 - end_guard_ms)

    if not (0 <= low <= high < trial_length_ms):
        raise ValueError(f"Invalid stimulus window [{low}, {high}] for trial_length={trial_length_ms}")

    rng = np.random.default_rng(rng_seed) if rng_seed is not None else np.random.default_rng()

    trials = []
    for a_bit, b_bit in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        for _ in range(trials_per_type):
            a_time = int(rng.integers(low, high + 1)) if a_bit == 1 else None
            b_time = int(rng.integers(low, high + 1)) if b_bit == 1 else None
            trials.append({"a_bit": a_bit, "b_bit": b_bit, "a_time": a_time, "b_time": b_time})

    rng.shuffle(trials)
    return trials


def run_single_in_domain_trial(
    trial_def: Dict[str, Union[int, None]],
    trial_length_ms: int,
    weights: Optional[Dict[str, float]] = None,
) -> Tuple[NeuronNetwork, int, int, Optional[int], Optional[int]]:
    w = {
        "A_to_C": 0.7,
        "B_to_C": 0.7,
        "A_to_D": 1.0,
        "B_to_D": 1.0,
        "D_to_E": 1.0,
        "C_to_E": -1.0,
    }
    if weights:
        w.update(weights)

    nn = NeuronNetwork("InDomain_XOR_System")
    nn.add_neuron("Neuron_A")
    nn.add_neuron("Neuron_B")
    nn.add_neuron("Neuron_C")
    nn.add_neuron("Neuron_D")
    nn.add_neuron("Neuron_E")

    nn.add_neuron_connection("Neuron_A", "Neuron_C", w["A_to_C"])
    nn.add_neuron_connection("Neuron_B", "Neuron_C", w["B_to_C"])
    nn.add_neuron_connection("Neuron_A", "Neuron_D", w["A_to_D"])
    nn.add_neuron_connection("Neuron_B", "Neuron_D", w["B_to_D"])
    nn.add_neuron_connection("Neuron_D", "Neuron_E", w["D_to_E"])
    nn.add_neuron_connection("Neuron_C", "Neuron_E", w["C_to_E"])

    a_time = trial_def["a_time"]
    b_time = trial_def["b_time"]
    nn.set_direct_stimulation_time_ms("Neuron_A", [] if a_time is None else [a_time])
    nn.set_direct_stimulation_time_ms("Neuron_B", [] if b_time is None else [b_time])

    nn.run_simulation(int(trial_length_ms), record_membrane_potential=True)

    return nn, trial_def["a_bit"], trial_def["b_bit"], a_time, b_time

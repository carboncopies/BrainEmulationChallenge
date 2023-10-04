"""Tests for module System.py"""

import unittest
import pytest
import scipy.stats as stats
from . import context
from src.components.prototyping.System import (
    System,
    Common_Parameters,
    common_commandline_parsing,
)
from src.components.prototyping.Region import Region
from src.components.prototyping.NeuralCircuit import NeuralCircuit
from src.components.prototyping.Geometry import Box
from src.components.prototyping.BS_Aligned_NC import BS_Aligned_NC


class TestSystem(unittest.TestCase):
    """Tests for class System."""

    def setUp(self):
        name = "test"
        self.system = System(name)

        # Set up a neural circuit and add it to the system.
        domain = Box()
        circuit = BS_Aligned_NC("test_nc")
        circuit.init_cells(domain)
        self.system.add_circuit(circuit)

    def test_component_by_id(self):
        """component_by_id() is yet to be implemented."""
        # TODO: Update with API changes
        assert self.system.component_by_id("1", "attach_direct_stim") == None

    def test_add_circuit(self):
        """Test if a neural circuit is added to the system correctly."""
        circuit = NeuralCircuit("test")
        self.system.add_circuit(circuit)
        assert self.system.neuralcircuits[circuit.id] == circuit

    def test_add_region(self):
        """Test if a new region is added properly."""
        region = Region("test")
        self.system.add_region(region)
        assert self.system.regions[region.id] == region

    def test_get_all_neurons(self):
        """Test if all correct neurons are returned from the
        components of the system."""
        all_neurons = self.system.get_all_neurons()
        expected_neurons = [
            circuit.get_neurons() for circuit in self.system.neuralcircuits.values()
        ]
        expected_neurons = [
            val for neuron_list in expected_neurons for val in neuron_list
        ]
        assert len(all_neurons) == len(expected_neurons)
        for neuron in all_neurons:
            assert neuron in expected_neurons

    def test_get_neurons_by_IDs(self):
        """Test if all correct neurons are returned from the
        components of the system according to the list of neuron
        IDs supplied."""

        # Case 1: Empty list of IDs
        listed_neurons = self.system.get_neurons_by_IDs([])
        assert len(listed_neurons) == 0

        # Case 2: List of IDs contains neuron IDs not in system
        listed_neurons = self.system.get_neurons_by_IDs(["99", "98"])
        assert len(listed_neurons) == 0

        # Case 3: List of IDs is correct
        listed_neurons = self.system.get_neurons_by_IDs(["0", "1"])
        expected_neurons = [
            circuit.get_neurons_by_IDs(["0", "1"])
            for circuit in self.system.neuralcircuits.values()
        ]
        expected_neurons = [
            val for neuron_list in expected_neurons for val in neuron_list
        ]
        assert len(listed_neurons) == len(expected_neurons)
        for neuron in listed_neurons:
            assert neuron in expected_neurons

    def test_get_all_neuron_IDs(self):
        """Test if all correct neuron IDs are returned from the
        components of the system."""
        all_neuron_IDs = self.system.get_all_neuron_IDs()
        expected_neurons = [
            circuit.get_neurons() for circuit in self.system.neuralcircuits.values()
        ]
        expected_neurons = [
            val for neuron_list in expected_neurons for val in neuron_list
        ]
        expected_neuron_IDs = [neuron.id for neuron in expected_neurons]
        assert len(all_neuron_IDs) == len(expected_neuron_IDs)
        for neuron_ID in all_neuron_IDs:
            assert neuron_ID in expected_neuron_IDs

    def test_get_geo_center(self):
        """Test if the correct geometric center of the system is
        returned."""
        domain = Box(center_um=(1.0, -1.0, 1.0))
        circuit = BS_Aligned_NC("test_nc_2")
        circuit.init_cells(domain)
        self.system.add_circuit(circuit)

        geo_center = self.system.get_geo_center()
        assert geo_center == (0.5, -2.5, 0.5)

    def test_attach_direct_stim(self):
        """
        Test if the direct stimuli supplied are attached
        properly.
        """
        # Case 1: An empty list of stimuli
        self.system.attach_direct_stim([])
        for circuit_id in self.system.neuralcircuits:
            circuit = self.system.neuralcircuits[circuit_id]
            for cell_id in circuit.cells:
                assert len(circuit.cells[cell_id].t_directstim_ms) == 0

        # Case 2: A wrong cell_id is provided
        with pytest.raises(Exception) as excinfo:
            self.system.attach_direct_stim([(0.1, 99)])
        assert (
            excinfo.value.args[0]
            == "BS_Aligned_NC.attach_direct_stim: Cell 99 not found."
        )

        # Case 3: All arguments in list are correct
        self.system.attach_direct_stim([(0.1, "0"), (0.1, "1")])
        for circuit_id in self.system.neuralcircuits:
            circuit = self.system.neuralcircuits[circuit_id]
            for cell_id in circuit.cells:
                assert circuit.cells[cell_id].t_directstim_ms[-1] == 0.1

    def test_set_spontaneous_activity(self):
        """Test if spontaneous spike settings are correctly set."""
        # Case 1: An empty list is provided
        self.system.set_spontaneous_activity([])
        for circuit_id in self.system.neuralcircuits:
            circuit = self.system.neuralcircuits[circuit_id]
            for cell_id in circuit.cells:
                assert circuit.cells[cell_id].dt_spont_dist == None

        # Case 2: A wrong cell ID is provided
        spont_spike_settings = [((280, 140), "99")]
        self.system.set_spontaneous_activity(spont_spike_settings)
        for circuit_id in self.system.neuralcircuits:
            circuit = self.system.neuralcircuits[circuit_id]
            for cell_id in circuit.cells:
                assert circuit.cells[cell_id].dt_spont_dist == None

        # Case 3: All parameters are valid.
        spont_spike_settings = [((280, 140), "0")]
        self.system.set_spontaneous_activity(spont_spike_settings)
        for circuit_id in self.system.neuralcircuits:
            circuit = self.system.neuralcircuits[circuit_id]
            mu, sigma = 280, 140
            a, b = 0, 2 * mu
            truncnorm_test = stats.truncnorm(
                (a - mu) / sigma, (b - mu) / sigma, loc=mu, scale=sigma
            )
            assert circuit.cells["0"].dt_spont_dist.stats() == truncnorm_test.stats()

    def test_attach_recording_electrodes(self):
        """ """
        pass

    def test_attach_calcium_imaging(self):
        """"""
        pass

    def test_set_record_all(self):
        """
        Test if the time limit for recording simulation outputs
        is set correctly.
        """

        # Case 1: Record forever
        self.system.set_record_all(-1)
        assert self.system.t_recordall_max_ms == -1
        assert self.system.t_recordall_start_ms == self.system.t_ms

        # Case 2: Record for a finite time
        self.system.set_record_all(100)
        assert self.system.t_recordall_max_ms == 100
        assert self.system.t_recordall_start_ms == self.system.t_ms

        # Case 3: Record for zero time
        self.system.set_record_all(0)
        assert self.system.t_recordall_max_ms == 0
        assert self.system.t_recordall_start_ms == 0

    def test_is_recording(self):
        """Test if the correct state of the simulation in terms
        of the recording activity of the System is returned."""
        # Case 1: System is not set to record anything
        self.system.set_record_all(0)
        assert not self.system.is_recording()

        # Case 2: System is set to record for a finite time
        self.system.set_record_all(100)
        assert self.system.is_recording()

        # Case 3: System is set to record everything
        self.system.set_record_all(-1)
        assert self.system.is_recording()

    def test_get_recording(self):
        """"""
        pass

    def test_get_instrument_recordings(self):
        """"""
        pass

    def test_get_em_stack(self):
        """"""
        pass

    def test_run_for(self):
        """"""
        pass

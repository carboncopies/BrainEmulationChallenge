"""
Tests for module System.py.
"""

import unittest
from . import context
from src.components.NES_interfaces.System import System


class TestSystem(unittest.TestCase):
    """Tests for class System."""

    def setUp(self):
        name = "test"
        user = "Admonishing"
        password = "Instruction"
        self.system = System(name, user, password)

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

    def test_get_recording(self):
        """Test if the recorded data gathered during a simulation
        is returned correctly."""

        # Nothing has been recorded immediately after setup.
        data = self.system.get_recording()
        assert "t_ms" in data
        assert len(data["t_ms"]) == 0
        for circuit_id in self.system.neuralcircuits:
            assert circuit_id in data
            circuit_data = data[circuit_id]
            circuit = self.system.neuralcircuits[circuit_id]
            for cell_id in circuit.cells:
                assert cell_id in circuit_data
                assert len(circuit_data[cell_id]["Vm"]) == 0

        # After a simulation has been run, the data must be collected
        # and correctly returned.

        self.system.set_record_all(-1)
        self.system.run_for(10.0)
        assert len(data["t_ms"]) != 0
        for circuit_id in self.system.neuralcircuits:
            circuit_data = data[circuit_id]
            circuit = self.system.neuralcircuits[circuit_id]
            for cell_id in circuit.cells:
                assert len(circuit_data[cell_id]["Vm"]) != 0

    def test_run_for(self):
        """Test if the system is able to run a simulation properly
        for different supplied values of runtime."""
        self.system.set_record_all(-1)

        # Case 1: Time period to run simulation for is invalid (e.g. negative).
        self.system.run_for(-10)
        data = self.system.get_recording()
        assert len(data["t_ms"]) == 0
        for circuit_id in self.system.neuralcircuits:
            circuit_data = data[circuit_id]
            circuit = self.system.neuralcircuits[circuit_id]
            for cell_id in circuit.cells:
                assert len(circuit_data[cell_id]["Vm"]) == 0

        # Case 2: Time period to run simulation for is zero.
        self.system.run_for(0)
        data = self.system.get_recording()
        assert len(data["t_ms"]) == 0
        for circuit_id in self.system.neuralcircuits:
            circuit_data = data[circuit_id]
            circuit = self.system.neuralcircuits[circuit_id]
            for cell_id in circuit.cells:
                assert len(circuit_data[cell_id]["Vm"]) == 0

        # Case 3: Time period to run simulation for is positive.
        self.system.run_for(10)
        data = self.system.get_recording()
        assert len(data["t_ms"]) != 0
        for circuit_id in self.system.neuralcircuits:
            circuit_data = data[circuit_id]
            circuit = self.system.neuralcircuits[circuit_id]
            for cell_id in circuit.cells:
                assert len(circuit_data[cell_id]["Vm"]) != 0

"""
Tests for module BS_Neuron.py.
"""
import random
import unittest
from . import context
from src.components.NES_interfaces.BS_Neuron import BS_Neuron
from src.components.NES_interfaces.Geometry import Sphere, Cylinder


class TestBSNeuron(unittest.TestCase):
    """Tests for class BS_Neuron."""

    def setUp(self):
        soma = Sphere(center_um=(0, 0, 0), radius_um=5.0)
        axon = Cylinder(
            end0_um=(0, 0, 0),
            end0_radius_um=0.5,
            end1_um=(0, 10, 0),
            end1_radius_um=0.5,
        )
        self.neuron = BS_Neuron(str(random.randint(0, 100)), soma, axon)

    def test_attach_direct_stim(self):
        """Test if direct stimulus attachment time is recorded
        correctly."""
        self.neuron.attach_direct_stim(0.1)
        assert (
            self.neuron.patch_id != None
        )  # Patch ID is initialized in the first direct stimulus recording.
        assert self.neuron.t_directstim_ms[-1] == 0.1  # Time recorded successfully
        for count in range(5):
            self.neuron.attach_direct_stim(count * 0.15)
        assert (
            len(self.neuron.t_directstim_ms) == 6
        )  # Number of direct stimulus activities recorded.

    def test_register_DAC_data_list(self):
        pass

    def test_record(self):
        pass

    def test_has_spiked(self):
        pass

    def test_dt_act_ms(self):
        pass

    def test_vSpike_t(self):
        pass

    def test_vAHP_t(self):
        pass

    def test_vPSP_t(self):
        pass

    def test_update_Vm(self):
        pass

    def test_detect_threshold(self):
        pass

    def update(self):
        pass

    def get_recording(self):
        pass

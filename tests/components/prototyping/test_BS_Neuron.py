"""Tests for module BS_Neuron.py"""
import random
import unittest
import scipy.stats as stats
import numpy as np
from . import context
from src.components.prototyping.BS_Neuron import BS_Neuron, dblexp
from src.components.prototyping.Geometry import Sphere, Cylinder


def test_dblexp():
    """Test if the double-exponent expression is calculated correctly."""
    amp = 1.1
    tau_rise, tau_decay = 0.5, 0.1

    # Test for negative tdiff
    tdiff = -0.5
    assert dblexp(amp, tau_rise, tau_decay, tdiff) == 0.0

    # Test for non-negative tdiff
    tdiff = 0.5
    calc_dblexp = amp * (-np.exp(-tdiff / tau_rise) + np.exp(-tdiff / tau_decay))
    assert dblexp(amp, tau_rise, tau_decay, tdiff) == calc_dblexp


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

    def test_get_cell_center(self):
        """Test if the correct cell center is returned."""
        assert self.neuron.get_cell_center() == (0, 0, 0)

    def test_attach_direct_stim(self):
        """Test if direct stimulus attachment time is recorded
        correctly."""
        self.neuron.attach_direct_stim(0.1)
        assert self.neuron.t_directstim_ms[-1] == 0.1  # Time recorded successfully
        for count in range(5):
            self.neuron.attach_direct_stim(count * 0.15)
        assert (
            len(self.neuron.t_directstim_ms) == 6
        )  # Number of direct stimulus activities recorded.

    def test_set_spontaneous_activity(self):
        """Test if the spontaneous activity parameters are correctly set."""
        test_mu, test_std = 0.1, 0.5
        calc_dt_spont_dist = stats.truncnorm(
            -test_mu / test_std, test_mu / test_std, loc=test_mu, scale=test_std
        )
        self.neuron.set_spontaneous_activity((test_mu, test_std))
        assert self.neuron.tau_spont_mean_stdev_ms == (test_mu, test_std)
        assert self.neuron.dt_spont_dist.stats() == calc_dt_spont_dist.stats()

    def test_show(self):
        """"""
        pass

    def test_record(self):
        """Test if the current time and voltage are recorded correctly."""
        old_len_timesteps = len(self.neuron.t_recorded_ms)
        old_len_V_m_recorded = len(self.neuron.Vm_recorded)
        self.neuron.record(0.1)
        assert len(self.neuron.t_recorded_ms) == old_len_timesteps + 1
        assert len(self.neuron.Vm_recorded) == old_len_V_m_recorded + 1

    def test_has_spiked(self):
        """Test if the spike event is detected correctly."""
        # No spike event immediately after initialization
        assert self.neuron.has_spiked() == False
        # TODO: Add test for confirming spike event

    def test_dt_act_ms(self):
        """Test if the correct time delta for t_act_ms is returned."""
        # Immediately after startup, no spike event has been recorded.
        assert self.neuron.dt_act_ms(0.1) == 99999999.9
        # TODO: Add test for getting dt_act_ms after spike event

    def test_vSpike_t(self):
        """Test if the correct spike potential is returned depending on
        whether there has been a spike event."""
        # No spike event immediately after set up.
        assert self.neuron.vSpike_t(0.1) == 0.0
        # TODO: What happens after there is a spike event?

    def test_vAHP_t(self):
        """Test if the correct after hyper-polarization potential is
        returned."""
        # No spike event immediately after set up.
        assert self.neuron.vAHP_t(0.1) == 0.0

    def test_vPSP_t(self):
        """Test if the correct post-synaptic potential is returned."""
        # No spike event immediately after set up.
        assert self.neuron.vPSP_t(0.1) == 0.0
        # TODO: What happens after there is a spike event?

    def test_update_Vm(self):
        """Test if the correct membrane potential is returned."""
        # No spike event immediately after set up.
        old_len_timesteps = len(self.neuron.t_recorded_ms)
        old_len_V_m_recorded = len(self.neuron.Vm_recorded)
        self.neuron.update_Vm(0.1, True)
        assert len(self.neuron.t_recorded_ms) == old_len_timesteps + 1
        assert len(self.neuron.Vm_recorded) == old_len_V_m_recorded + 1

    def test_detect_threshold(self):
        """Test if the crossing of the action potential threshold has i
        been detected correctly."""
        # Action potential threshold will not be crossed immediately
        # after set up.
        old_t_act_ms_length = len(self.neuron.t_act_ms)
        self.neuron.detect_threshold(0.1)
        assert len(self.neuron.t_act_ms) == old_t_act_ms_length

    def test_spontaneous_activity(self):
        """ """
        # TODO
        pass

    def test_update(self):
        """
        Test if the update step leads to the correct values of
        membrane potential and the current simulation time and
        detects the crossing of the action potential threshold
        correctly.
        """
        # TODO
        pass

    def test_get_recording(self):
        """Test if the membrane potentials calculated by the
        simulation are returned correctly."""
        recording = self.neuron.get_recording()
        assert isinstance(recording, dict)
        assert "Vm" in recording

        # Immediately after set up no membrane potentials have
        # been recorded.
        assert len(recording["Vm"]) == 0

        # TODO: What happens after a spike event has been detected?

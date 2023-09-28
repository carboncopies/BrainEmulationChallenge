"""Tests for module AMPA_Receptor.py"""

import unittest
import pytest
from math import exp
import numpy as np
from . import context
from src.components.prototyping.AMPA_Receptor import AMPA_Receptor


class TestAMPAReceptor(unittest.TestCase):
    """Tests for class AMPA_Receptor."""

    def setUp(self):
        self.receptor = AMPA_Receptor()

    def test_set_psp_type(self):
        """Test if the correct value of np_Gsyn_t_pS is set
        for the supplied psp_type."""

        # Case 1: psp_type = dblexp
        self.receptor.set_psp_type("dblexp")
        assert self.receptor.np_Gsyn_t_pS == self.receptor.np_Gsyn_t_pS_dbl

        # Case 2: psp_type = mxh
        self.receptor.set_psp_type("mxh")
        assert self.receptor.np_Gsyn_t_pS == self.receptor.np_Gsyn_t_pS_mxh

        # Case 3: psp_type = foobar
        with pytest.raises(ValueError) as excinfo:
            self.receptor.set_psp_type("foobar")

    def test_postsyn_current_I(self):
        """Test if the postsynaptic current is calculated correctly."""
        calculated = self.receptor.Gsyn_pS * (
            self.receptor.Vm_mV - self.receptor.Esyn_mV
        )
        assert self.receptor.postsyn_current_I() == calculated
        assert self.receptor.Isyn_pA == calculated

    def test_conductance(self):
        """Test if the conductance is calculated correctly."""
        calculated = self.receptor.Isyn_pA / (
            self.receptor.Vm_mV - self.receptor.Esyn_mV
        )

        assert self.receptor.conductance() == calculated
        assert self.receptor.Gsyn_pS == calculated

        # TODO: Add check for zero division

    def test_Gsyn_t_pS_decay_zerorisetime(self):
        """Test if G_syn_pS is set correctly for zero rise time."""

        # Case 1: t_ms < 0
        t_ms = -0.1
        assert self.receptor.Gsyn_t_pS_decay_zerorisetime(t_ms) == 0
        assert self.receptor.Gsyn_pS == 0

        # Case 2: t_ms >= 0
        t_ms = 0.1
        calculated = self.receptor.g_peak_pS * exp(-t_ms / self.receptor.tau_d_ms)
        assert self.receptor.Gsyn_t_pS_decay_zerorisetime(t_ms) == calculated
        assert self.receptor.Gsyn_pS == calculated

        # TODO: Add check for zero division

    def test_Gsyn_t_pS_rise_decay(self):
        """Test if G_syn_pS is set correctly for non-zero rise time."""
        # Case 1: t_ms < 0
        t_ms = -0.1
        assert self.receptor.Gsyn_t_pS_rise_decay(t_ms) == 0
        assert self.receptor.Gsyn_pS == 0

        # Case 2: t_ms >= 0
        t_ms = 0.1
        t_ratio = t_ms / self.receptor.tau_r_ms
        calculated = self.receptor.g_peak_pS * t_ratio * exp(1.0 - t_ratio)
        assert self.receptor.Gsyn_t_pS_rise_decay(t_ms) == calculated
        assert self.receptor.Gsyn_pS == calculated

        # TODO: Add check for zero division

    def test_Gsyn_t_pS(self):
        """Test if G_syn_pS is set correctly for a double-exponential model."""
        # Case 1: t_ms < 0
        t_ms = -0.1
        assert self.receptor.Gsyn_t_pS(t_ms) == 0
        assert self.receptor.Gsyn_pS == 0

        # Case 2: t_ms >= 0
        t_ms = 0.1
        calculated = (
            self.receptor.g_peak_pS
            * (
                -exp(-t_ms / self.receptor.tau_r_ms)
                + exp(-t_ms / self.receptor.tau_d_ms)
            )
            / self.receptor.a_norm
        )
        assert self.receptor.Gsyn_t_pS(t_ms) == calculated
        assert self.receptor.Gsyn_pS == calculated

        # TODO: Add check for zero division

    def test_np_Gsyn_t_pS_dbl(self):
        """Test if g_syn_ps is set correctly for a double-exponential model with an array of time values as input."""
        t_ms = np.array([0.1, 0.2, -0.1, 0.0, -0.2])
        t_ms_copy = np.copy(t_ms)
        t_ms_copy = (t_ms >= 0.0) * t_ms_copy
        calculated = (
            self.receptor.g_peak_pS
            * (
                -np.exp(-t_ms / self.receptor.tau_r_ms)
                + np.exp(-t_ms / self.receptor.tau_d_ms)
            )
            / self.receptor.a_norm
        )
        assert np.allclose(self.receptor.np_Gsyn_t_pS_dbl, calculated)
        assert np.allclose(self.receptor.Gsyn_pS, calculated)

        # TODO: Add check for zero division.

    def test_np_Gsyn_t_pS_mxh(self):
        """Test if g_syn_ps is set correctly for a multi-exponential model with an array of time values as input."""
        t_ms = np.array([0.1, 0.2, -0.1, 0.0, -0.2])
        t_ms_copy = np.copy(t_ms)
        t_ms_copy = (t_ms >= 0.0) * t_ms_copy
        calculated = (
            self.receptor.g_peak_pS
            * np.power((1.0 - np.exp(-t_ms / self.receptor.tau_r_ms)), self.receptor.x)
            * (
                self.receptor.d1 * np.exp(-t_ms / self.receptor.tau_d_ms)
                + self.receptor.d2 * np.exp(-t_ms / self.receptor.tau_d2_ms)
                + self.receptor.d3 * np.exp(-t_ms / self.receptor.tau_d3_ms)
            )
            / self.receptor.a_norm
        )
        assert np.allclose(self.receptor.np_Gsyn_t_pS_dbl, calculated)
        assert np.allclose(self.receptor.Gsyn_pS, calculated)

        # TODO: Add check for zero division.

    def test_plot_it(self):
        """"""
        pass

    def test_numerical_find_a_norm(self):
        """Test if the a_norm is calculated correctly."""
        a_norm = self.receptor.numerical_find_a_norm()
        assert isinstance(a_norm, float)
        # TODO: Make this more robust

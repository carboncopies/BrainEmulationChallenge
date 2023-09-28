"""
Tests for the module NMDA_Receptor.py.
"""
from math import exp
import pytest
import unittest
from . import context
from src.components.NES_interfaces.NMDA_Receptor import NMDA_Receptor


class testNMDAReceptor(unittest.TestCase):
    """Tests for class NMDA_Receptor."""

    def setUp(self):
        self.receptor = NMDA_Receptor()

    def test_set_phi_V_type(self):
        """Test if the phi voltage is set correctly according to
        the type specified."""
        # Case 1: Bolzmann
        self.receptor.set_phi_V_type("Bolzmann")
        assert self.receptor.phi_V == self.receptor.phi_V_Bolzmann

        # Case 2: Woodhull_1
        self.receptor.set_phi_V_type("Woodhull_1")
        assert self.receptor.phi_V == self.receptor.phi_V_Woodhull_1

        # Case 3: Woodhull_2
        self.receptor.set_phi_V_type("Woodhull_2")
        assert self.receptor.phi_V == self.receptor.phi_V_Woodhull_2

        # Case 4: None of the above
        with pytest.raises(ValueError) as excinfo:
            self.receptor.set_phi_V_type("foobar")

    def test_phi_V_Bolzmann(self):
        """Test if the phi voltage is correctly calculated using the Bolzmann function."""
        calculated = 1.0 / (
            1.0
            + exp(
                -(self.receptor.Vm_mV - self.receptor.V_halfblocked) / self.receptor.k
            )
        )
        assert self.receptor.phi_V_Bolzmann() == calculated

    def test_Phi(self):
        """Test if the phi value is calculated correctly."""
        R = 8.31446261815324  # Gas constant (in J/(K*mol)).
        F = 96485.3321  # Faraday constant (in s*A/mol).
        z, T = 2.0, 343.0
        calculated = z * F / (R * T)
        assert self.receptor.Phi(T) == calculated

        # TODO: Check for zero division error

    def test_k_binding_rate(self):
        """Test if the k_binding_rate is calculated correctly."""
        Mg2plus_0, K_binding, delta, V, T = 0.1, 0.5, 0.1, 0.5, 343.0
        calculated = Mg2plus_0 * K_binding * exp(-delta * self.receptor.Phi(T) * V / 2)
        assert (
            self.receptor.k_binding_rate(Mg2plus_0, K_binding, delta, V, T)
            == calculated
        )

    def test_k_unbinding_rate(self):
        """Test if the k_unbinding_rate is calculated correctly."""
        K_unbinding, delta, V, T = 0.5, 0.1, 0.5, 343.0
        calculated = K_unbinding * exp(delta * self.receptor.Phi(T) * V / 2)
        assert self.receptor.k_unbinding_rate(K_unbinding, delta, V, T) == calculated

    def test_phi_V_Woodhull_1(self):
        """Test if the phi value calculated with a two-state Woodhull formalism is correct."""
        Mg2plus_0, K_binding, K_unbinding, delta, V, T = 0.1, 0.5, 0.4, 0.1, 0.5, 343.0
        k_binding = Mg2plus_0 * K_binding * exp(-delta * self.receptor.Phi(T) * V / 2)
        k_unbinding = K_unbinding * exp(delta * self.receptor.Phi(T) * V / 2)
        calculated = 1.0 / (1.0 + k_binding / k_unbinding)
        assert (
            self.receptor.phi_V_Woodhull_1(
                Mg2plus_0, K_binding, K_unbinding, delta, V, T
            )
            == calculated
        )

    def test_phi_V_Woodhull_2(self):
        """Test if the phi value calculated with a two-state Woodhull formalism is correct."""
        Mg2plus_0, K_dissociation_0mV, delta, V, T = 0.1, 0.5, 0.1, 0.5, 343.0
        K_d = K_dissociation_0mV * exp(delta * self.receptor.Phi(T) * V)
        calculated = 1.0 / (1.0 + (Mg2plus_0 / K_d))
        assert (
            self.receptor.phi_V_Woodhull_2(Mg2plus_0, K_dissociation_0mV, delta, V, T)
            == calculated
        )
        # TODO: Check for zero division error

    def test_Isyn(self):
        """Test if the synaptic current is calculated correctly."""
        calculated = self.receptor.phi_V() * self.receptor.postsyn_current_I()
        assert self.receptor.Isyn() == calculated

"""
Tests for module NES_AMPA_Receptor.py.
"""
import unittest
from . import context
from src.components.NES_interfaces.NES_AMPA_Receptor import NES_AMPA_Receptor


class TestNESAMPAReceptor(unittest.TestCase):
    """
    Tests for class NES_AMPA_Receptor.
    """

    def setUp(self):
        self.receptor = NES_AMPA_Receptor()

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

    def test_np_Gsyn_t_pS_dbl_withcallback(self):
        """"""
        pass

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

    def test_np_Gsyn_t_pS_mxh_withcallback(self):
        """"""
        pass

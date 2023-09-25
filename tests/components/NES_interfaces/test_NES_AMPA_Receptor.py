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
        """Test if PSP type is set correctly."""
        pass

    def test_np_Gsyn_t_pS_dbl(self):
        """"""
        pass

    def test_np_Gsyn_t_pS_dbl_withcallback(self):
        """"""
        pass

    def test_np_Gsyn_t_pS_mxh(self):
        """"""
        pass

    def test_np_Gsyn_t_pS_mxh_withcallback(self):
        """"""
        pass


if __name__ == "__main__":
    main()

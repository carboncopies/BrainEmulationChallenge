"""
Tests for class BS_Aligned_NC.py.
"""
import unittest
from . import context
from src.components.NES_interfaces.BS_Aligned_NC import BS_Aligned_NC


class TestBSAlignedNC(unittest.TestCase):
    """Tests for BS_Aligned_NC"""

    def setUp(self):
        self.neural_circuit = BS_Aligned_NC("test_id", 2)

    def test_Set_Weight(self):
        pass

    def test_Encode(self):
        pass

    def test_attach_direct_stim(self):
        pass

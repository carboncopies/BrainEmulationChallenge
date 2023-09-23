"""
Tests for class BS_Aligned_NC.py.
"""
import unittest
import context
from src.components.NES_interfaces.BS_Aligned_NC import BS_Aligned_NC


class TestBSAlignedNC(unittest.TestCase):
    """Tests for BS_Aligned_NC"""

    def setUp(self):
        self.neural_circuit = BS_Aligned_NC("test_id", 2)

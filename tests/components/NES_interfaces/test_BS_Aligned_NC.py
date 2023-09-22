"""
Tests for class BS_Aligned_NC.py.
"""
from src.components.NES_interfaces import BS_Aligned_NC


class TestBSAlignedNC:
    """Tests for BS_Aligned_NC"""

    def __init__(self):
        self.neural_circuit = BS_Aligned_NC("test_id", 2)

    def test_init_cells(self):
        raise NotImplementedError

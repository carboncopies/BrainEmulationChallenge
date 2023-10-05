"""Tests for module Region.py"""

import unittest
from . import context
from src.components.prototyping.BS_Aligned_NC import BS_Aligned_NC
from src.components.prototyping.Geometry import Box, Geometry
from src.components.prototyping.Region import Region, BrainRegion
from src.components.prototyping.NeuralCircuit import NeuralCircuit


class TestRegion(unittest.TestCase):
    """Tests for class Region."""

    def setUp(self):
        self.region = Region("SomeID")

    def test_id(self):
        """Test if the id of a region object is a string."""
        assert isinstance(self.region.id, str)


class TestBrainRegion(unittest.TestCase):
    """Tests for class BrainRegion."""

    def setUp(self):
        shape = Box()
        neural_circuit = BS_Aligned_NC("Test")
        brain_region = BrainRegion("TestID", shape, neural_circuit)
        assert isinstance(brain_region.shape, Geometry)
        assert isinstance(brain_region.content, NeuralCircuit)

"""
Tests for module Region.py.
"""

from . import context
from src.components.NES_interfaces.Region import Region, BrainRegion
from src.components.NES_interfaces.Geometry import Geometry, Box
from src.components.NES_interfaces.BS_Aligned_NC import BS_Aligned_NC
from src.components.NES_interfaces.NeuralCircuit import NeuralCircuit


def test_region_creation():
    """Test if a region object is correctly instantiated."""
    region = Region("SomeID")
    assert isinstance(region.id, str)


def test_brain_region_creation():
    """Test if a brain region object is successfully instantiated."""
    shape = Box()
    neural_circuit = BS_Aligned_NC("Test")
    brain_region = BrainRegion("TestID", shape, neural_circuit)
    assert isinstance(brain_region.shape, Geometry)
    assert isinstance(brain_region.content, NeuralCircuit)

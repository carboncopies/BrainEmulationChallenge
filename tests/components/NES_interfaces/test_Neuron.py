"""
Tests for module Neuron.py.
"""

from . import context
from src.components.NES_interfaces.Neuron import Neuron


def test_neuron_creation():
    """Test if a neuron object is instantiated successfully."""
    neuron = Neuron("SomeID")
    assert isinstance(neuron.id, str)

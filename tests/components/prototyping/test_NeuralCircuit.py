"""Tests for module NeuralCircuit.py"""

import unittest
from . import context
from src.components.prototyping.NeuralCircuit import NeuralCircuit


class TestNeuralCircuit(unittest.TestCase):
    """Tests for class NeuralCircuit."""

    def setUp(self):
        self.neural_circuit = NeuralCircuit("SomeID")

    def test_id(self):
        """Tests if the id of a neural circuit object is an int."""
        assert isinstance(self.neural_circuit.id, str)

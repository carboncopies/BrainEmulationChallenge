"""
Tests for module NeuralCircuit.py.
"""
import context
from src.components.NES_interfaces.NeuralCircuit import NeuralCircuit


def test_neural_circuit_creation():
    """Tests if a neural circuit object is instantiated successfully."""
    neural_circuit = NeuralCircuit("SomeID")
    assert isinstance(neural_circuit.id, str)

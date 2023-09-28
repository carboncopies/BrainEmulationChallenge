"""Tests for module Neuron.py"""

import unittest
from . import context
from src.components.prototyping.Neuron import Neuron


class TestNeuron(unittest.TestCase):
    """Tests for class Neuron."""

    def setUp(self):
        """"""
        self.neuron = Neuron("SomeID")

    def test_id(self):
        """Test if the id attribute of a neuron object is an int."""
        assert isinstance(self.neuron.id, str)

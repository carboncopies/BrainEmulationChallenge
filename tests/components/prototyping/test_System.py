"""Tests for module System.py"""

import unittest
from . import context
from src.components.prototyping.System import System


class TestSystem(unittest.TestCase):
    """Tests for class System."""

    def setUp(self):
        name = "test"
        self.system = System(name)

    def test_component_by_id(self):
        """"""
        pass

    def test_add_circuit(self):
        """"""
        pass

    def test_add_region(self):
        """"""
        pass

    def test_get_geo_center(self):
        """"""
        pass

    def test_attach_direct_stim(self):
        """"""
        pass

    def test_set_spontaneous_activity(self):
        """"""
        pass

    def test_attach_recording_electrodes(self):
        """"""
        pass

    def test_attach_calcium_imaging(self):
        """"""
        pass

    def test_set_record_all(self):
        """"""
        pass

    def test_is_recording(self):
        """"""
        pass

    def test_get_recording(self):
        """"""
        pass

    def test_run_for(self):
        """"""
        pass

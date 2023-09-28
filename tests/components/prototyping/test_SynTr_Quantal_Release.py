"""Tests for module SynTr_Quantal_Release.py"""

import unittest
from . import context
from src.components.prototyping.SynTr_Quantal_Release import SynTr_Quantal_Release


class TestSynTrQuantalRelease(unittest.TestCase):
    """Tests for class SynTr_Quantal_Release."""

    def setUp(self):
        self.instance = SynTr_Quantal_Release(5, 0.3)

    def test_quantal_content_m(self):
        """Test if the correct quantal content is returned."""
        assert self.instance.quantal_content_m() == 1.5

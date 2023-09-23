"""Tests for Geometry.py."""

import unittest
from math import pi
import context
from src.components.NES_interfaces.Geometry import (
    Box,
    Sphere,
    Cylinder,
    Geometry,
    PlotInfo,
)


class TestPlotInfo(unittest.TestCase):
    """Test the PlotInfo class."""

    def setUp(self):
        self.plot_info = PlotInfo("A test plot.")

    def test_figsize(self):
        """Tests if the figure size in the plotinfo object is
        of the appropriate dimensions."""
        assert self.plot_info.fig.get_figwidth() == 4.0
        assert self.plot_info.fig.get_figheight() == 4.0


class TestBox(unittest.TestCase):
    """Tests the Box class."""

    def setUp(self):
        self.box = Box(
            center_um=(10, 10, 10),
            dims_um=(5.5, 10.2, 6.7),
            rotations_rad=(pi / 4.0, pi / 4.0, pi / 2.0),
        )
        self.min_y, self.max_y = (
            self.center_um[1] - self.dims_um[1] / 2.0,
            self.center_um[1] + self.dims_um[1] / 2.0,
        )


class TestSphere(unittest.TestCase):
    """Tests the Sphere class."""

    def setUp(self):
        self.sphere = Sphere(center_um=(10, 10, 10), radius_um=2.32)


class TestCylinder(unittest.TestCase):
    """Tests the Cylinder class."""

    def setUp(self):
        self.cylinder = Cylinder(
            end0_um=(0.1, 0.2, 0.3),
            end0_radius_um=0.5,
            end1_um=(0.1, 10.2, 0.3),
            end1_radius_um=1.2,
        )

    def test_R_at_position(self):
        """Test if the correct radius is output for a value between 0.0 and 1.0."""
        assert self.cylinder.R_at_position(0.5) == (0.5 + 1.2) / 2.0
        assert self.cylinder.R_at_position(1.0) == 1.2
        assert self.cylinder.R_at_position(0.0) == 0.5

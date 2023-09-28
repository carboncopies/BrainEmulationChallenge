"""Tests for module Geometry.py"""

import unittest
from math import pi
from . import context
from src.components.prototyping.Geometry import (
    PlotInfo,
    Geometry,
    Box,
    Sphere,
    Cylinder,
)


class TestPlotInfo(unittest.TestCase):
    """Tests for class PlotInfo"""

    def setUp(self):
        self.plot_info = PlotInfo("A test plot.")

    def test_figsize(self):
        """Tests if the figure size in the plotinfo object is
        of the appropriate dimensions."""
        assert self.plot_info.fig.get_figwidth() == 4.0
        assert self.plot_info.fig.get_figheight() == 4.0


class TestGeometry(unittest.TestCase):
    """Tests for class Geometry."""

    def setUp(self):
        self.geometry = Geometry()


class TestBox(unittest.TestCase):
    """Tests for class Box."""

    def setUp(self):
        self.box = Box(
            center_um=(10, 10, 10),
            dims_um=(5.5, 10.2, 6.7),
            rotations_rad=(pi / 4.0, pi / 4.0, pi / 2.0),
        )
        self.min_y = self.box.center_um[1] - self.box.dims_um[1] / 2.0
        self.max_y = self.box.center_um[1] + self.box.dims_um[1] / 2.0

    def test_volume(self):
        """Test if the correct volume is calculated."""
        assert self.box.volume_um3() == (5.5 * 10.2 * 6.7)

    def test_equal_slice_bounds(self):
        """Test if the slice requested out of width-wise equally
        cut slices of the box is within the bounds of the box."""
        n_slices = 10
        topleft, bottomright = self.box.equal_slice_bounds(n_slices, n_slices + 1)
        assert self.min_y <= topleft[1] < self.max_y
        assert self.min_y <= bottomright[1] < self.max_y

    def test_sides(self):
        """Test if the correct dimensions are returned."""
        sides = self.box.sides()
        assert sides[0] == self.box.dims_um[0]
        assert sides[1] == self.box.dims_um[1]
        assert sides[2] == self.box.dims_um[2]

    def test_int_sides(self):
        """Test if the correct dimensions are returned."""
        int_sides = self.box.int_sides()
        assert int_sides[0] == int(self.box.dims_um[0])
        assert int_sides[1] == int(self.box.dims_um[1])
        assert int_sides[2] == int(self.box.dims_um[2])

    def test_show(self):
        """"""
        pass


class TestSphere(unittest.TestCase):
    """Tests for class Sphere."""

    def setUp(self):
        self.sphere = Sphere(center_um=(10, 10, 10), radius_um=2.32)

    def test_show(self):
        """"""
        pass


class TestCylinder(unittest.TestCase):
    """Tests for class Cylinder."""

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

    def test_show(self):
        """"""
        pass

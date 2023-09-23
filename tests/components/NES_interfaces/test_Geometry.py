"""Tests for Geometry.py."""

from math import pi
from src.components.NES_interfaces.Geometry import (
    Box,
    Sphere,
    Cylinder,
    Geometry,
    PlotInfo,
)


class TestPlotInfo:
    """Test the PlotInfo class."""

    def __init__(self):
        self.plot_info = PlotInfo("A test plot.")

    def test_figsize(self):
        """Tests if the figure size in the plotinfo object is
        of the appropriate dimensions."""
        assert self.fig.figsize == (4, 4)


class TestBox:
    """Tests the Box class."""

    def __init__(self):
        self.box = Box(
            id_val="232",
            center_um=(10, 10, 10),
            dims_um=(5.5, 10.2, 6.7),
            rotations_rad=(pi / 4.0, pi / 4.0, pi / 2.0),
        )
        self.min_y, self.max_y = (
            self.center_um[1] - self.dims_um[1] / 2.0,
            self.center_um[1] + self.dims_um[1] / 2.0,
        )

    def test_volume(self):
        """Test if the correct volume is calculated."""
        assert self.box.volume_um3() == (5.5 * 10.2 * 6.7)

    def test_slice_within_bounds(self):
        """Test if the slice requested out of width-wise equally
        cut slices of the box is within the bounds of the box."""
        n_slices = 10
        topleft, bottomright = self.box.equal_slice_bounds(n_slices, n_slices + 1)
        assert self.min_y <= topleft < self.max_y


class TestSphere:
    """Tests the Sphere class."""

    def __init__(self):
        self.sphere = Sphere(id_val="123", center_um=(10, 10, 10), radius_um=2.32)

    def test_volume(self):
        """Test if the volume calculated is correct."""
        assert self.sphere.volume_um3() == 4.0 / 3.0 * pi * (2.32**3)


class TestCylinder:
    """Tests the Cylinder class."""

    def __init__(self):
        self.cylinder = Cylinder(
            id_val="322",
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

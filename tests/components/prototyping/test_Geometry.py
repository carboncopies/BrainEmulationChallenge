"""Tests for module Geometry.py"""

import unittest
import pytest
import numpy as np
from math import pi
from . import context
from src.components.prototyping.BS_Neuron import BS_Neuron
from src.components.prototyping.BS_Morphology import BS_Axon, BS_Soma
from src.components.prototyping.Spatial import VecBox
from src.components.prototyping.Geometry import (
    PlotInfo,
    Geometry,
    Box,
    Sphere,
    Cylinder,
    voxel_containing_point,
    fluorescent_voxel,
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


class TestSphere(unittest.TestCase):
    """Tests for class Sphere."""

    def setUp(self):
        domain = Box()
        domain_bounds = domain.equal_slice_bounds(2, 1)
        soma = BS_Soma(domain_bounds, align="left")
        axon = BS_Axon(domain_bounds, align="right", soma_radius_um=soma.radius_um)
        self.neuron = BS_Neuron(str(1), soma, axon)

        self.sphere = Sphere(center_um=(10, 10, 10), radius_um=2.32)

    def test_get_voxels(self):
        """Test if the voxels associated with the sphere object are
        correctly returned."""
        voxel_dict = self.sphere.get_voxels(0.1, self.neuron)
        assert len(voxel_dict) != 0


class TestCylinder(unittest.TestCase):
    """Tests for class Cylinder."""

    def setUp(self):
        domain = Box()
        domain_bounds = domain.equal_slice_bounds(2, 1)
        soma = BS_Soma(domain_bounds, align="left")
        axon = BS_Axon(domain_bounds, align="right", soma_radius_um=soma.radius_um)
        self.neuron = BS_Neuron(str(1), soma, axon)
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

    def test_get_voxels(self):
        """Test if the voxels associated with the sphere object are
        correctly returned."""
        voxel_dict = self.cylinder.get_voxels(0.1, self.neuron)
        assert len(voxel_dict) != 0


class TestFluorescentVoxel(unittest.TestCase):
    """Tests for class fluorescent_voxel."""

    def setUp(self):
        domain = Box()
        domain_bounds = domain.equal_slice_bounds(2, 1)
        soma = BS_Soma(domain_bounds, align="left")
        axon = BS_Axon(domain_bounds, align="right", soma_radius_um=soma.radius_um)
        neuron = BS_Neuron(str(1), soma, axon)
        neuron.Ca_samples = [1.5, 1.6, 1.7]
        xyz = np.array([0.1, 0.2, 0.3])
        self.voxel = fluorescent_voxel(xyz, 0.1, neuron)

    def test_get_adjacent_dict(self):
        """Test if the walk process around a fixed location returns the
        correct set of neighboring voxels."""
        # Case 1: Walk radius = 0
        voxel_dict = self.voxel.get_adjacent_dict(0)
        assert len(voxel_dict) == 0

        # Case 2: Fixed walk radius
        voxel_dict = self.voxel.get_adjacent_dict(0.5)
        assert len(voxel_dict) != 0

    def test_set_depth_dimming(self):
        """Test the set_depth_dimming method of fluorescent_voxel"""

        subvolume = VecBox(
            center=np.array([0.0, 0.0, 0.0]),
            half=np.array([0.2, 0.3, 0.4]),
            dx=0.1,
            dy=0.1,
            dz=0.1,
        )
        self.voxel.set_depth_dimming(subvolume)
        assert round(self.voxel.depth_brightness, 4) == pytest.approx(0.5853)

    def test_set_image_pixels(self):
        """Test the set_image_pixels method."""
        subvolume = VecBox(np.array([0, 0, 0]), np.array([1, 1, 1]), 0.1)
        image_dims_px = (100, 100)
        pixel_contributions = np.zeros(image_dims_px)
        self.voxel.set_image_pixels(subvolume, image_dims_px, pixel_contributions)
        assert len(self.voxel.image_pixels) > 0

    def test_record_fluorescence(self):
        """Test the record_fluorescence method."""
        image_t = np.zeros((100, 100))
        lum = (
            60.0
            * self.voxel.neuron_ref.Ca_samples[-1]
            * self.voxel.act_brightness
            * self.voxel.depth_brightness
            * self.voxel.type_brightness
        )

        self.voxel.record_fluorescence(image_t)
        assert np.sum(image_t) > 0

    def test_record_fluorescence_aposteriori(self):
        """Test the record_fluorescence_aposteriori method."""

        images = [
            np.zeros((100, 100)) for _ in range(len(self.voxel.neuron_ref.Ca_samples))
        ]
        self.voxel.record_fluorescence_aposteriori(images, 1.0)
        assert np.sum(images[0]) > 0

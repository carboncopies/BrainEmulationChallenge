"""Tests for module Spatial.py."""
import pytest
import unittest
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from . import context
from src.components.prototyping.Spatial import (
    PlotInfo,
    vec3add,
    vec3sub,
    get_cube_vertices,
    get_cube_edges,
    VecBox,
    point_is_within_box,
    colset0,
    colset1,
    colset2,
    colset3,
)


class TestPlotInfo(unittest.TestCase):
    def setUp(self):
        title = "Test Plot"
        self.plot_info = PlotInfo(title)

    def test_initialization(self):
        """Test if the instance is correctly initialized."""
        assert isinstance(self.plot_info.fig, plt.Figure)
        assert isinstance(self.plot_info.ax, Axes3D)

    def test_colors_exist(self):
        """Test if the colors that are expected to exist in
        a PlotInfo instance exist."""
        assert "spheres" in self.plot_info.colors
        assert "cylinders" in self.plot_info.colors
        assert "boxes" in self.plot_info.colors
        assert "voxels" in self.plot_info.colors

    def test_colors_values(self):
        """Test the values associated with different colors."""
        assert self.plot_info.colors["spheres"] in colset0
        assert self.plot_info.colors["cylinders"] in colset1
        assert self.plot_info.colors["boxes"] == colset2[0]
        assert self.plot_info.colors["voxels"] == colset3[1]


class TestVecBox(unittest.TestCase):
    """Tests for class VecBox."""

    def setUp(self):
        self.center = np.array([0, 0, 0])
        self.half = np.array([1, 1, 1])
        self.vec_box = VecBox(self.center, self.half)

    def test_initialization(self):
        assert self.vec_box.center.tolist() == self.center.tolist()
        assert self.vec_box.half.tolist() == self.half.tolist()
        assert self.vec_box.dx == None
        assert self.vec_box.dy == None
        assert self.vec_box.dz == None


def test_vec3add():
    """Test for function vec3add."""
    result = vec3add((1, 2, 3), (4, 5, 6))
    assert result == (5, 7, 9)


def test_vec3sub():
    """Test for function vec3sub."""
    result = vec3sub((4, 5, 6), (1, 2, 3))
    assert result == (3, 3, 3)


def test_get_cube_vertices():
    """Test for function get_cube_vertices."""
    cube_definition = [(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)]
    vertices = get_cube_vertices(cube_definition)
    expected_vertices = np.array(
        [
            [0, 0, 0],
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1],
            [1, 1, 0],
            [1, 0, 1],
            [0, 1, 1],
            [1, 1, 1],
        ]
    )
    np.testing.assert_array_almost_equal(vertices, expected_vertices)


def test_get_cube_edges():
    """Tests the function get_cube_edges."""
    vertices = np.array(
        [
            [0, 0, 0],
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1],
            [1, 1, 0],
            [1, 0, 1],
            [0, 1, 1],
            [1, 1, 1],
        ]
    )
    edges = get_cube_edges(vertices)
    expected_edges = [
        [
            np.array([0, 0, 0]),
            np.array([0, 0, 1]),
            np.array([1, 0, 1]),
            np.array([1, 0, 0]),
        ],
        [
            np.array([1, 0, 0]),
            np.array([1, 0, 1]),
            np.array([1, 1, 1]),
            np.array([1, 1, 0]),
        ],
        [
            np.array([1, 1, 0]),
            np.array([0, 1, 0]),
            np.array([0, 1, 1]),
            np.array([1, 1, 1]),
        ],
        [
            np.array([0, 1, 0]),
            np.array([0, 1, 1]),
            np.array([0, 0, 1]),
            np.array([0, 0, 0]),
        ],
        [
            np.array([0, 0, 0]),
            np.array([0, 1, 0]),
            np.array([1, 1, 0]),
            np.array([1, 0, 0]),
        ],
        [
            np.array([0, 0, 1]),
            np.array([0, 1, 1]),
            np.array([1, 1, 1]),
            np.array([1, 0, 1]),
        ],
    ]
    edges = np.asarray(edges)
    expected_edges = np.asarray(expected_edges)
    np.testing.assert_array_almost_equal(edges, expected_edges)


@pytest.fixture
def sample_vec_box():
    """This fixture sets up tests for the function point_is_within_box."""
    center = np.array([0, 0, 0])
    half = np.array([1, 1, 1])
    dx = np.array([1, 0, 0])
    dy = np.array([0, 1, 0])
    dz = np.array([0, 0, 1])
    return VecBox(center, half, dx, dy, dz)


def test_point_within_box(sample_vec_box):
    """Test a point that is within the box."""
    point = np.array([0.5, 0.5, 0.5])
    result = point_is_within_box(point, sample_vec_box)
    assert result


def test_point_on_edge_of_box(sample_vec_box):
    """Test a point that is on the edge of the box."""
    point = np.array([1.0, 0.5, 0.5])  # On the edge of the box in the x-direction
    result = point_is_within_box(point, sample_vec_box)
    assert result


def test_point_outside_box(sample_vec_box):
    """Test a point that is outside the box."""
    point = np.array([1.5, 0.5, 0.5])  # Outside the box in the x-direction
    result = point_is_within_box(point, sample_vec_box)
    assert not result


def test_point_not_3d_vector(sample_vec_box):
    """Test a point that is not a 3D vector."""
    point = np.array([1.0, 0.5])  # 2D point, should raise a ValueError
    with pytest.raises(ValueError):
        point_is_within_box(point, sample_vec_box)

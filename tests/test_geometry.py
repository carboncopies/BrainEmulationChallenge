from types import SimpleNamespace

import numpy as np
import pytest

from common import Spatial
from common import _Geometry as G


X = np.array([1.0, 0.0, 0.0])
Y = np.array([0.0, 1.0, 0.0])
Z = np.array([0.0, 0.0, 1.0])

# Box spanning [-5, 5] on every axis.
VECBOX = Spatial.VecBox(np.zeros(3), np.array([5.0, 5.0, 5.0]), X, Y, Z)
BOX = Spatial.SixPlanesBox(VECBOX)

# Plane at x=0 with its outward normal along +x.
PLANE = Spatial.Plane(np.zeros(3), X)


def sphere(center, radius):
    return SimpleNamespace(center_um=center, radius_um=radius)


def cylinder(end0, end1):
    return SimpleNamespace(end0_um=end0, end1_um=end1)


def test_plane_distance_is_signed():
    assert G.plane_distance(PLANE, np.array([3.0, 7.0, -2.0])) == pytest.approx(3.0)
    assert G.plane_distance(PLANE, np.array([-4.0, 0.0, 0.0])) == pytest.approx(-4.0)


@pytest.mark.parametrize('center, expected', [
    ((5.0, 0.0, 0.0), 1),     # fully on the outward side
    ((-5.0, 0.0, 0.0), -1),   # fully on the inward side
    ((0.5, 0.0, 0.0), 0),     # straddles the plane
])
def test_sphere_vs_plane(center, expected):
    s = sphere(center, 1.0)
    assert G.sphere_inside_outside_intersects_plane(s, PLANE) == expected
    assert G.sphere_outside_plane(s, PLANE) == (expected == 1)
    assert G.sphere_inside_plane(s, PLANE) == (expected == -1)
    assert G.sphere_intersects_plane(s, PLANE) == (expected == 0)


def test_sphere_intersects_plane_point():
    res = G.sphere_intersects_plane_point(sphere((0.6, 2.0, 3.0), 1.0), PLANE)
    assert res['intersects']
    np.testing.assert_allclose(res['point'], [0.0, 2.0, 3.0])
    assert res['radius'] == pytest.approx(0.8)  # sqrt(1 - 0.6^2)


@pytest.mark.parametrize('center, radius, inside, intersects, outside', [
    ((0.0, 0.0, 0.0), 1.0, True, False, False),
    ((4.5, 0.0, 0.0), 1.0, False, True, False),
    ((20.0, 0.0, 0.0), 1.0, False, False, True),
])
def test_sphere_vs_box(center, radius, inside, intersects, outside):
    s = sphere(center, radius)
    assert G.sphere_inside_box(s, BOX) == inside
    assert G.sphere_intersects_box(s, BOX) == intersects
    assert G.sphere_outside_box(s, BOX) == outside


def test_cylinder_outside_box():
    assert G.cylinder_outside_box(cylinder((10.0, 0, 0), (20.0, 0, 0)), VECBOX)
    assert not G.cylinder_outside_box(cylinder((0.0, 0, 0), (20.0, 0, 0)), VECBOX)


def test_voxel_containing_point():
    v = G.voxel_containing_point(np.array([2.5, 0.1, -0.5]), 1.0)
    assert v['indices'] == (2, 0, -1)
    assert v['key'] == '2_0_-1'
    np.testing.assert_allclose(v['center'], [2.0, 0.0, -1.0])


def test_voxel_containing_point_scales_with_voxel_size():
    v = G.voxel_containing_point(np.array([9.9, 10.0, 0.0]), 5.0)
    assert v['indices'] == (1, 2, 0)

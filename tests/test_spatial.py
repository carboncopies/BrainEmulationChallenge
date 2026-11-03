import numpy as np
import pytest

from common import Spatial


X = np.array([1.0, 0.0, 0.0])
Y = np.array([0.0, 1.0, 0.0])
Z = np.array([0.0, 0.0, 1.0])


def unit_box(center=(0.0, 0.0, 0.0), half=(1.0, 1.0, 1.0)):
    return Spatial.VecBox(np.array(center), np.array(half), X, Y, Z)


def test_vec3add():
    assert Spatial.vec3add((1, 2, 3), (10, 20, 30)) == (11, 22, 33)


def test_vec3sub():
    assert Spatial.vec3sub((11, 22, 33), (10, 20, 30)) == (1, 2, 3)


def test_get_cube_vertices_unit_cube():
    vertices = Spatial.get_cube_vertices([(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)])
    assert vertices.shape == (8, 3)
    corners = {tuple(int(c) for c in v) for v in vertices}
    expected = {(x, y, z) for x in (0, 1) for y in (0, 1) for z in (0, 1)}
    assert corners == expected


def test_get_cube_edges_gives_six_quad_faces():
    vertices = Spatial.get_cube_vertices([(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)])
    faces = Spatial.get_cube_edges(vertices)
    assert len(faces) == 6
    assert all(len(face) == 4 for face in faces)


@pytest.mark.parametrize('point, inside', [
    ((0.0, 0.0, 0.0), True),
    ((0.9, -0.9, 0.9), True),
    ((1.0, 1.0, 1.0), True),    # boundary counts as inside
    ((1.1, 0.0, 0.0), False),
    ((0.0, 0.0, -2.0), False),
])
def test_point_is_within_box(point, inside):
    assert Spatial.point_is_within_box(np.array(point), unit_box()) == inside


def test_point_is_within_offset_box():
    box = unit_box(center=(10.0, 0.0, 0.0), half=(2.0, 1.0, 1.0))
    assert Spatial.point_is_within_box(np.array([11.5, 0.0, 0.0]), box)
    assert not Spatial.point_is_within_box(np.array([0.0, 0.0, 0.0]), box)


def test_six_planes_box_normals_point_outwards():
    box = Spatial.SixPlanesBox(unit_box())
    assert set(box.sides) == {'front', 'back', 'top', 'bottom', 'left', 'right'}
    for plane in box.sides.values():
        # Each face sits one unit from the center, along its outward normal.
        np.testing.assert_allclose(plane.point, plane.direction)

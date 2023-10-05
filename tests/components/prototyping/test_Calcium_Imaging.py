"""Tests for module Calcium_Imaging.py"""

import unittest
import pytest
import numpy as np
from . import context
from src.components.prototyping.Spatial import VecBox
from src.components.prototyping.Geometry import Box
from src.components.prototyping.BS_Aligned_NC import BS_Aligned_NC
from src.components.prototyping.System import System
from src.components.prototyping.Geometry import fluorescent_voxel
from src.components.prototyping.Calcium_Imaging import (
    voxels_within_bounds,
    Calcium_Imaging,
)


class TestCalciumImaging(unittest.TestCase):
    """Tests for class Calcium_Imaging."""

    def setUp(self):
        # Create a basic ball and stick neural circuit and
        # set it up inside a box domain
        domain = Box()
        circuit = BS_Aligned_NC("test_nc")
        circuit.init_cells(domain)
        system = System("test_system")
        system.add_circuit(circuit)

        specs = {
            "id": "calcium_" + str(np.random.rand())[2:5],
            "fluorescing_neurons": system.get_all_neuron_IDs(),
            "calcium_indicator": "jGCaMP8",
            "indicator_rise_ms": 2.0,
            "indicator_decay_ms": 40.0,
            "indicator_interval_ms": 20.0,
            "imaged_subvolume": VecBox(
                center=np.array([0, 0, 0]),
                half=np.array([5.0, 5.0, 2.0]),
                dx=np.array([1.0, 0.0, 0.0]),
                dy=np.array([0.0, 1.0, 0.0]),
                dz=np.array([0.0, 0.0, 1.0]),
            ),
            "voxelspace_side_px": 30,
            "imaging_interval_ms": 30.0,
            "generate_during_sim": True,
        }
        show = {"voxels": False}
        self.imaging = Calcium_Imaging(specs, system, show)
        self.imaging.instantiate_voxel_space(show)

    def test_get_voxel_size_um(self):
        """Test if the correct voxel size is returned."""
        # TODO: Implement this after API update.
        pass

    def test_get_visible_components_list(self):
        """Test if the correct list of visible components is returned."""

        # Case 1: jGCaMP8
        self.imaging.calcium_indicator = "jGCaMP8"
        visible_components = self.imaging.get_visible_components_list()
        assert "soma" in visible_components
        assert "axon" in visible_components
        assert "synapse" not in visible_components

        # Case 2: synGCaMP6f
        self.imaging.calcium_indicator = "synGCaMP6f"
        visible_components = self.imaging.get_visible_components_list()
        assert "soma" in visible_components
        assert "axon" in visible_components
        assert "synapse" in visible_components

        # Case 2: Something else
        # TODO: Replace this with something meaningful
        self.imaging.calcium_indicator = "something else"
        visible_components = self.imaging.get_visible_components_list()
        assert "soma" in visible_components
        assert "axon" not in visible_components
        assert "synapse" not in visible_components

    def test_set_image_sizes(self):
        """Test if the image sizes are set correctly."""
        self.imaging.set_image_sizes()
        assert self.imaging.image_dims_px[0] == int(
            (2 * self.imaging.specs["imaged_subvolume"].half[0])
            // self.imaging.voxel_um
        )
        assert self.imaging.image_dims_px[1] == int(
            (2 * self.imaging.specs["imaged_subvolume"].half[1])
            // self.imaging.voxel_um
        )

    def test_instantiate_voxel_space(self):
        """Test if the voxel space is instantiated correctly."""
        assert len(self.imaging.voxelspace) != 0
        assert isinstance(self.imaging.voxelspace[0], fluorescent_voxel)

    def test_initialize_depth_dimming(self):
        """Test if the dimming of pixels at specified depth is done
        correctly."""
        self.imaging.initialize_depth_dimming()
        dimming = []
        for voxel in self.imaging.voxelspace:
            assert voxel.depth_brightness != 0

    def test_initialize_projection_circles(self):
        """Test if the projection circles are initialized correctly."""
        self.imaging.initialize_projection_circles()
        for voxel in self.imaging.voxelspace():
            assert len(voxel.image_pixels) > 0
        assert self.imaging.max_pixel_contributions != 0

    def test_initialize_fluorescence_kernel(self):
        """Test if the fluorescence kernel is initialized correctly."""
        self.imaging.initialize_fluorescence_kernel()
        assert self.imaging.fluorescence_kernel is not None
        assert len(self.imaging.fluorescence_kernel) > 0

    def test_initialize_fluorescing_neurons_FIFOs(self):
        """Test if the FIFOs for the fluorescing neurons are initialized
        correctly."""

        pass

    def test_record(self):
        """"""
        pass

    def test_record_aposteriori(self):
        """"""
        pass

    def test_get_recording(self):
        """"""
        pass

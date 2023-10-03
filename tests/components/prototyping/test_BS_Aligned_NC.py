"""Tests for module BS_Aligned_NC.py"""

import unittest
import pytest
import scipy.stats as stats
from . import context
from src.components.prototyping.BS_Aligned_NC import BS_Aligned_NC
from src.components.prototyping.Geometry import Box


class TestBSAlignedNC(unittest.TestCase):
    """Tests for class BS_Aligned_NC."""

    def setUp(self):
        self.circuit = BS_Aligned_NC("SomeID")

    def test_init_cells(self):
        """Test if the cells are initialized correctly."""

        # No cells for uninitialized cells.
        assert len(self.circuit.cells) == 0

        domain = Box()
        assert hasattr(domain, "equal_slice_bounds")
        self.circuit.init_cells(domain)
        assert len(self.circuit.cells) == self.circuit.num_cells

    def test_get_cell_centers(self):
        """Test if the correct cell centers are returned."""
        cell_centers = self.circuit.get_cell_centers()
        assert len(cell_centers) == 0

        domain = Box()
        self.circuit.init_cells(domain)
        cell_centers = self.circuit.get_cell_centers()
        assert len(cell_centers) == 2

    def test_Set_Weight(self):
        """Test if the weights for connections between cells are set properly."""
        # Case 1: Method supplied is not implemented
        method = "foobar"
        from_val, to = "0", "1"
        with pytest.raises(ValueError) as excinfo:
            self.circuit.Set_Weight((from_val, to), method)

        # Case 2: Method supplied is "binary", but either "from" or
        # "to" cells are invalid.
        from_val, to = "99", "1"
        with pytest.raises(Exception) as excinfo:
            self.circuit.Set_Weight((from_val, to), "binary")
        assert "Unknown target cell" in excinfo.value.args[0]

        from_val, to = "0", "99"
        with pytest.raises(Exception) as excinfo:
            self.circuit.Set_Weight((from_val, to), "binary")
        assert "Unknown source cell" in excinfo.value.args[0]

        # Case 3: All parameters supplied are valid
        from_val, to = "0", "1"
        self.circuit.Set_Weight((from_val, to), "binary")
        target_cell = self.circuit.cells[to]
        source_cell = self.circuit.cells[from_val]
        assert target_cell.receptors[-1][0] == source_cell
        assert target_cell.receptors[-1][1] == 1.0
        assert (
            target_cell.morphology["receptor"].center_um
            == source_cell.morphology["soma"].center_um
        )

    def test_Encode(self):
        """Test if encoding is done in a correct fashion."""
        # Case 1: Encoding method is invalid
        pattern_set = [("0", "1")]
        with pytest.raises(ValueError) as excinfo:
            self.circuit.Encode(pattern_set, "foobar", "method")

        # Case 2: Synapse weight method is invalid
        with pytest.raises(ValueError) as excinfo:
            self.circuit.Encode(pattern_set, "instant", "foobar")

        # Case 3: All parameters are valid but empty pattern set
        self.circuit.Encode([], "instant", "binary")
        # No receptors have been added to any cell
        for cell_id in self.circuit.cells:
            assert len(self.circuit.cells[cell_id].receptors) == 0

        # Case 4: All parameters valid and non-empty pattern set
        pattern_set = [("0", "1")]
        self.circuit.Encode(pattern_set, "instant", "binary")
        for from_cell, to_cell in pattern_set:
            target_cell = self.circuit.cells[to_cell]
            source_cell = self.circuit.cells[from_cell]
            assert target_cell.receptors[-1][0] == source_cell
            assert target_cell.receptors[-1][1] == 1.0
            assert (
                target_cell.morphology["receptor"].center_um
                == source_cell.morphology["soma"].center_um
            )

    def test_attach_direct_stim(self):
        """
        Test if direct stimulus is correctly attached to the
        cells in the neural circuit.
        """
        # Case 1: An empty list is passed.
        tstim_ms = []
        self.circuit.attach_direct_stim(tstim_ms)
        for cell_id in self.circuit.cells:
            cell = self.circuit.cells[cell_id]
            assert len(cell.t_directstim_ms) == 0

        # Case 2: A non-existent cell's ID is passed.
        tstim_ms = [(0.1, 99)]
        with pytest.raises(Exception) as excinfo:
            self.circuit.attach_direct_stim(tstim_ms)
        assert (
            "BS_Aligned_NC.attach_direct_stim: Cell 99 not found."
            in excinfo.value.args[0]
        )

        # Case 3: All parameters are valid.
        tstim_ms = [(0.1, 0), (0.1, 1)]
        self.circuit.attach_direct_stim(tstim_ms)
        for cell_id in self.circuit.cells:
            cell = self.circuit.cells[cell_id]
            assert len(cell.t_directstim_ms) == 1

    def test_set_spontaneous_activity(self):
        """
        Test if spontaneous activity is set correctly in the
        neurons of the circuit.
        """
        # Case 1: An empty list is supplied.
        spont_spike_settings = []
        self.circuit.set_spontaneous_activity(spont_spike_settings)
        for cell_id in self.circuit.cells:
            cell = self.circuit.cells[cell_id]
            assert cell.dt_spont_dist == None

        # Case 2: A nonexistent cell ID is supplied.
        spont_spike_settings = [((0.1, 0.05), "bah")]
        with pytest.raises(ValueError) as excinfo:
            self.circuit.set_spontaneous_activity(spont_spike_settings)

        # Case 3: All parameters are valid.
        spont_spike_settings = [((0.1, 0.05), "0"), ((0.15, 0.1), "1")]
        for count, cell_id in enumerate(self.circuit.cells):
            mu, sigma = spont_spike_settings[count][0]
            a, b = 0, 2 * mu
            calculated = stats.truncnorm(
                (a - mu) / sigma, (b - mu) / sigma, loc=mu, scale=sigma
            )
            assert self.cells[cell_id].dt_spont_dist.stats() == calculated.stats()

    def test_show(self):
        """"""
        pass

    def test_update(self):
        """Test if the update function updates all cells of the
        neural circuit correctly."""
        self.circuit.update(0.1, False)
        for cell_id in self.circuit.cells:
            assert self.circuit.cells[cell_id].t_ms == 0.1

    def test_get_recording(self):
        """Test if each neuron's recorded data is returned correctly."""
        data = self.circuit.get_recording()
        for cell_id in self.circuit.cells:
            assert data[cell_id] == self.circuit.cells[cell_id].get_recording()

"""
Tests for class BS_Aligned_NC.py.
"""
import unittest
from . import context
from src.components.NES_interfaces.BS_Aligned_NC import BS_Aligned_NC


class TestBSAlignedNC(unittest.TestCase):
    """Tests for BS_Aligned_NC"""

    def setUp(self):
        self.circuit = BS_Aligned_NC("test_id", 2)

    def initialize_cells(self):
        """Helper function to initialize cells with a box domain."""
        domain = Box()
        self.circuit.init_cells(domain)

    def test_init_cells(self):
        """Test if the cells are initialized correctly."""

        # No cells for uninitialized cells.
        assert len(self.circuit.cells) == 0

        domain = Box()
        assert hasattr(domain, "equal_slice_bounds")
        self.circuit.init_cells(domain)
        assert len(self.circuit.cells) == self.circuit.num_cells

    def test_Set_Weight(self):
        """Test if the weights for connections between cells are set properly."""
        self.initialize_cells()

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
        self.initialize_cells()

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
        self.initialize_cells()

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

#!/usr/bin/env python3
# aifinch_acquisition.py
# Randal A. Koene, 20230215

"""
This file is used to generate a simulated data acquisition protocol that is applied to
the ground-truth system that was generated with aifinch_groundtruth.py.
"""

import aifinch_groundtruth as kgt

# == Functional Recording Procedures: ===================================================================


class Placement:
    def __init__(self):
        pass


class PlacementRectangle(Placement):
    """
    Rectangular electrode placement arrangement.
    """

    def __init__(
        self,
        arrangement: tuple,
        method="uniformrandom",
    ):
        self.arrangement = arrangement
        self.method = method


# == Functional Recoding Tools: =========================================================================


class EFP_ElectrodeArray:
    """
    Multi-site multi-electrode electric field potential recording system.
    """

    def __init__(
        self,
        target_region: kgt.Region,
        electrode_placement: Placement,
        num_electrodes: int = 10,
        sites_per_electrode: int = 1,
    ):
        self.target_region = target_region
        self.num_electrodes = num_electrodes
        self.sites_per_electrode = sites_per_electrode
        self.electrode_placement = electrode_placement

    def show(self):
        pass


# == Structure Recording Tools: =========================================================================


class TEM_VolumeImaging:
    """
    Transmission Electron Microscope high-throughput volume imaging system.
    """

    def __init__(
        self,
        target_region=kgt.Region,
        section_depth_nm: int = 100,
        xy_resolution_nm: int = 5,
    ):
        self.target_region = target_region
        self.section_depth_nm = section_depth_nm
        self.xy_resolution_nm = xy_resolution_nm

    def show(self):
        pass


# == Initialize: ========================================================================================


def init(kgt_system: dict):
    # TODO:
    # - Either cue the default random selection.
    # - Or make a specific cue selection.

    # 2. Set up functional recording tools and procedures:
    aif_acq_efp = EFP_ElectrodeArray(
        target_region=kgt_system["regions"]["ltm"],
        num_electrodes=100,
        sites_per_electrode=10,
        electrode_placement=PlacementRectangle(
            arrangement=(10, 10),
            method="equidistant",
        ),
    )

    # 3. Specify structure scanning tools and procedures:
    aif_acq_em = TEM_VolumeImaging(
        target_region=kgt_system["regions"]["ltm"],
        section_depth_nm=150,
        xy_resolution_nm=4,
    )

    aif_acq_system = {
        "scanners": {
            "dyn": aif_acq_efp,
            "struc": aif_acq_em,
        },
    }
    return aif_acq_system


HELP = """
Usage: aifinch_acquisition.py [-h]

       -h         Show this usage information.

       This script acquires data from a known ground-truth system.

       Note that system identification and translation are carred out in
       aifinch_translation, and that emulation building and evaluation are
       carred out in aifinch_emulation.py.

       By default, this script calls class methods in aifinch_groundtruth.py
       to carry out the stages:

       1. Specification of a known ground-truth system and its behavior.
       2. Acquisition of data from the ground-truth system.

"""


def parse_command_line():
    from sys import argv

    cmdline = argv.copy()
    scriptpath = cmdline.pop(0)
    while len(cmdline) > 0:
        arg = cmdline.pop(0)
        if arg == "-h":
            print(HELP)
            exit(0)


if __name__ == "__main__":
    parse_command_line()

    # 1. Instantiate or import the known ground-truth system.
    aif_kgt_system = kgt.init(melodies_notes)

    aif_acq_system = init(aif_kgt_system)

    # 4. Default ACQ run:
    #    While the system runs, carry out data acquisition with the simulated acquisition
    #    tools.
    aif_kgt_system["regions"]["cue"].random_selection(
        num_sets=3, cue_pattern_ratio=0.4, cue_sequence_length=3
    )
    aif_acq_system["scanners"]["dyn"].show()

# Autoassociative memory test example

This is an example of a simple autoassociative network.
It's main purpose to is to provide example data for use by the Data Science subgroup
in developing functional metrics to compare a virtual ground-truth with an attempted
emulation thereof from generated data.

## Development notes

This model was started by:

- Creating the link to the `BrainGenix` folder just like in `xor_scnm`.
- Copying the file `vbp_common.py` from `xor_scnm`.
- Copying `nesvbp-autoassociative` from the `NetmorphCMake` repository's examples folder.
  This will be the raw initial Netmorph configuration upon which to build this example.

Also copying for subsequent modification:

- `xor_scnm/.gitignore`
- `xor_scnm/Run.sh`
- `xor_scnm/xor_scnm_acquisition_direct.py` to `autoassociative_acquisition.py`
- `xor_scnm/xor_scnm_groundtruth_connectome.py` to `autoassociative_connectome.py`
- `xor_scnm/xor_scnm_groundtruth_reservoir.py` to `autoassociative_reservoir.py`

--

Randal A. Koene, 20250620

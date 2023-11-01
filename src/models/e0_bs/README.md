# Calls for `e0_bs` scripts

In this directory, the following calls demonstrate the typical process of:

1. KGT
2. ACQ
3. VAL
4. EMU

Examples follow.

### KGT: Generating a known ground-truth system

`./bs_vbp00_groundtruth_xi_sampleprep.py -p -V all -R 23233 -N 20 -D unirand -x png`

Options used:

- Use the prototype code (`-p`).
- Be very verbose (`-V all`), showing all figures.
- Use a specific random seed (`-R 23233`) to reliably recreate the same model.
- Generate a KGT containing 20 neurons (`-N 20`).
- Arrange neurons using a uniform random distribution (`-D unirand`).
- Save figures in PNG format (`-x png`).

When this was run, the default directory created to store results was time-stamped
and was `/tmp/vbp_2023-10-07_21:38:44`. This directory is used in subsequent
calls, to store additional results or to reuse stored results. to reuse the KGT model that was saved in JSON format (`kgt.json`).

### ACQ: Carry out simulated data acquisition in the KGT

`./bs_vbp01_doubleblind_x_acquisition.py -p -V all -t 2000 -R 23233 -C 20 -c 0 -x png -d /tmp/vbp_2023-10-07_21:38:44`

Options used:

- Use the prototype code (`-p`).
- Be very verbose (`-V all`), showing all figures.
- Run data acquisition for 2000 simulated milliseconds (`-t 2000`).
- Use a specific random seed (`-R 23233`) to reliably recreate the same model.
- Use a calcium imaging field-of-view of 20 micrometers (`-C 20`).
- Place calcium imaging y-axis center position at 0 (`-c 0`).
- Save figures in PNG format (`-x png`).
- Use the specified storage directory (`-d /tmp/vbp_2023-10-07_21:38:44`).

The acquisition script can call KGT the generation function from the previous script to build a new KGT if an empty KGT is specified (`-L ''`). Here, the default KGT file
(`kgt.json`) file is loaded from the specified storage directory
(`/tmp/vbp_2023-10-07_21:38:44`). It is also possible to specify a KGT to load that
does not reside in the storage directory if an absolute path is given to `-L`.

### EMU: Carry out system identificaton and translation

`./bs_vbp02_translation_iv_system_identification.py -p -V all -d /tmp/vbp_2023-10-07_21:38:44 -s`

Options used:

- Use the prototype code (`-p`).
- Be very verbose (`-V all`), showing all figures.
- Use the specified storage directory (`-d /tmp/vbp_2023-10-07_21:38:44`).

### VAL: Calculate validation metrics on the emulation

`./bs_vbp03_emulation_iii_validation.py -p -V all -d /tmp/vbp_2023-10-07_21:38:44`

Options used:

- Use the prototype code (`-p`).
- Be very verbose (`-V all`), showing all figures.
- Use the specified storage directory (`-d /tmp/vbp_2023-10-07_21:38:44`).

---
Randal A. Koene, 2023

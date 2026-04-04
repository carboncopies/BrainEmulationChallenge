# Implementation Plan - 8-Bit LIFC Shift Register (v12.0 Burst Fidelity)

Based on analysis of the `full_adder_lifc.py` reference, we will transition to a burst-based stimulation model to provide robust temporal integration across the deep 8-stage cascade.

## Proposed Changes

### [Component] [Shift Register Model](file:///Users/apple/fun_project/BrainEmulationChallenge/src/models/shift_register_lifc/shift_register_lifc.py)

#### [MODIFY] [shift_register_lifc.py](file:///Users/apple/fun_project/BrainEmulationChallenge/src/models/shift_register_lifc/shift_register_lifc.py)

*   **Burst Stimulation (v12.0)**:
    *   **Logic**: Every '1' bit and 'CLK' pulse will consist of a **compact burst of 10 spikes** at 5ms intervals.
    *   **Integration**: LIFC neurons will integrate these 10 spikes to cross the threshold, providing a much cleaner "Digital High" signal than a single pulse.
*   **Parameter Alignment**:
    *   **Weights**: Reset to `1.0` (standard).
    *   **g_peak**: Set to `20-40` (standard).
    *   **Rm/Cm**: Standard `100/100` (10ms Tau), allowing the burst to integrate while clearing quickly between clock cycles.
*   **Refractory**: Set to `200ms` (allows the 10-spike burst but blocks the next clock cycle).

## Verification Plan

### Automated Verification
*   **Remote Run**: Execute `./Run.sh -R`.
*   **Expected Result**: `VERIFICATION: [ PASS ]` with observed pattern `[1, 1, 0, 0, 1, 1, 0, 1]`.

### Visual Validation
*   Check `groundtruth-Vm.png` for solid "blocks" of activity representing each bit.

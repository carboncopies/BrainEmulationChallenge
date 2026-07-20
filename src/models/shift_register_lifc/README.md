# Shift Register LIFC - 4-bit Serial-In Parallel-Out (SIPO)

A 4-bit shift register implemented using LIFC (Leaky Integrate-and-Fire with Conductance-based synapses) spiking neurons on the BrainGenix NES platform.

## Circuit Overview

This model demonstrates sequential logic using spiking neurons. A shift register
stores binary data and shifts it by one position on each clock pulse.

```
                         CLK (clock input)
                          |
                          | (AMPA to all gate interneurons)
                          v
  Din ──AMPA──> I_Gate0 ──GABA──> P_Latch0 ──AMPA──> I_Gate1 ──GABA──> P_Latch1
                                     |                                     |
                                     v                                     v
                                    Q0                                    Q1
                                     |                                     |
                                     +--AMPA--> I_Gate2 ──GABA──> P_Latch2 |
                                                                     |
                                                                     v
                                                                    Q2
                                                                     |
                                                   I_Gate3 ──GABA──> P_Latch3
                                                                     |
                                                                     v
                                                                    Q3
```

### Neuron Types

- **CLK, Din**: Input principal neurons (excitatory)
- **I_Gate0–3**: Inhibitory interneurons activated by clock signal
- **P_Latch0–3**: Principal neurons that store/latch data
- **Q0–Q3**: Output principal neurons (parallel output)

### Operation

1. **Data input** (`Din`) provides serial data
2. **Clock** (`CLK`) activates gate interneurons with a brief delay
3. Gate interneurons inhibit (GABA) latch neurons, resetting them
4. Latch neurons then capture excitatory input from the previous stage
5. On each clock pulse, data shifts right through the cascade

## Usage

```bash
# Run on remote BrainGenix NES server
./Run.sh -R

# Run with specific host/port
./shift_register_lifc.py -Host pve.braingenix.org -Port 8000

# Run locally
./shift_register_lifc.py
```

## Development Notes

This model was created by:

- Using the `full_adder_lifc` example as a template
- Creating the link to the `BrainGenix` folder matching the pattern in other models
- Copying `vbpcommon.py` from `full_adder_lifc`
- Creating a symlink to `NES_interfaces` for recording utilities
- Designing a novel shift register circuit using timing-based gating with
  inhibitory interneurons

## Dependencies

- BrainGenix NES server (remote or local)
- Python 3 with numpy, matplotlib
- BrainGenix Python client library

--

Created 2026-04-03

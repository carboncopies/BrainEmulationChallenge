# Autoassociative memory test example

This is an example of a simple autoassociative network.
It's main purpose to is to provide example data for use by the Data Science subgroup
in developing functional metrics to compare a virtual ground-truth with an attempted
emulation thereof from generated data.

## Hand-designed LIFC autoassociative demo: `LIFtest.py -Autoassociative`

`LIFtest.py -Autoassociative -STDP` builds 8 pyramidal neurons per pattern plus 3
interneurons, and runs one of two trial protocols:

- **Default (encode, then retrieve):** each pattern is presented `-EncodeTrials` times
  (default 200, every `-EncodeInterval` = 70 ms) with STDP on. Each neuron's spike gets
  a random delay of up to `-EncodeJitter` (default 5 ms). After a 500 ms gap, STDP is
  switched off (unless `-RetrievalSTDP`), and each pattern is cued `-RetrievalTrials`
  times (default 20, every `-RetrievalInterval` = 200 ms). Each cue is a different subset
  of the pattern, with cue sizes between `-CueMin` and `-CueMax` (default 50% to 80%,
  so 4, 5 or 6 of 8 neurons). `-T` is ignored, because T follows from the trials.
- **`-inspectSTDP`:** the original protocol. Batches of 4 full-pattern presentations
  alternate with batches of 4 half-pattern cues (always the same first 4 neurons) for
  the whole run (`-T`, default 80000 ms), with STDP on throughout. This shows the gradual
  encoding in the Vm traces.

Both protocols write per-trial records to `output/trials.csv` and `output/trials.json`.
Each trial is scored by the spikes in its window `[t_ms, t_ms+window_ms)`:

| column | meaning |
|---|---|
| `phase` | `encode` (full pattern) or `retrieve` (partial cue) |
| `pattern`, `t_ms`, `window_ms` | pattern index, stimulus onset, response window |
| `cue_fraction`, `stimulated` | fraction and IDs of the pattern neurons that were stimulated |
| `recalled` | non-stimulated pattern neurons that spiked |
| `intruders` | pyramidal neurons outside the pattern that spiked |
| `interneurons_spiking` | number of interneurons that spiked |
| `recall`, `complete` | fraction of non-stimulated pattern neurons recalled; 1 if all recalled and there were no intruders |

`trials.json` also has the per-neuron stimulation offsets (`stim_offsets_ms`), the STDP
on/off segments, and the pattern and interneuron neuron IDs.

Notes:
- Without jitter, synchronous presentations only strengthen connections from lower to
  higher neuron IDs (the weight matrix becomes upper-triangular). Then recall only works
  for cues that include the low-ID neurons. This is why `-inspectSTDP` always cues
  neurons 0-3, and why the default protocol adds jitter.
- With `-Patterns > 1`, the default protocol currently produces cross-pattern weights.
  Once within-pattern weights saturate in both directions, a pattern can ignite without
  being stimulated, and STDP then links it to the other pattern.

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

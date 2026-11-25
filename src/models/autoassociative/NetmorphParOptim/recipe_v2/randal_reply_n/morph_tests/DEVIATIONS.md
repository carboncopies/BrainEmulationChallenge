# Deviations from PREREGISTRATION_morph.md

- **M1 (before any growth, launch tooling).** The first three launches of `run_batch.py 0` exited before contacting NES:
  - the system python has no pandas;
  - the `bec-netmorph` checkout has `bio_check.py` but no `bio_ranges.json`.

  Fix: the driver runs with the BrainEmulationChallenge venv python and imports `bio_check` from `/home/johnjose/cos/netmorph_work/bec/.../NetmorphParOptim`. That is the checkout the earlier E4 growths used, and it holds the same hard limits. No growth was started or lost.
- **M2 (observed at launch, no effect).** pandas reads the sheet value `false` back as the boolean `False`, so the directive sent is `detailed_chemical_factors=False;`. NetMorph lowercases the value before comparing (network.cc:220 `downcase(...)==String("true")`), so the setting is the intended false. Randal's reuse note in the README says this.

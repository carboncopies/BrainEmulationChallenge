# Netmorph configuration test

Tests Netmorph configuration files independent of any specific example model,
in particular files produced by the browser based Netmorph configuration tool.

```
./test_generated_config.py -configfile <file> -checkonly    # local preflight only
./test_generated_config.py -configfile <file> [-growdays N] [-modelname NAME]
```

The preflight parses the file and reports regions, expected neuron counts and suspicious
statements (missing `;`, non-integer counts, reassigned parameters, regions without shape
or neurons, parameter prefixes that are not declared regions or labels, `include=` lines).

A full run grows the network in NES using LIFC neurons, optionally saves the model at the
server, compares the resulting connectome with the counts expected from the configuration,
and writes AMPA/GABA connectivity plots and `configtest_summary.json` to `output/`.
Results are also appended to `ExpsDB.json` under the key `configtest`.

A known-good configuration to compare against is `../autoassociative/nesvbp-autoassociative`.

## Development notes

- `BrainGenix` links to the PythonClient, as in the other model folders.
- `vbpcommon.py` is copied from `../autoassociative`.

--

Randal A. Koene, 20261014

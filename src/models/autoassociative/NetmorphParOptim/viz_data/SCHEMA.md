# viz_data schema (schema_version 1)

One file per Netmorph sample run: `sample_NNNN.json` (NNNN = runID, the row index in the Excel file passed to `gen_autonm_labels.py -excel`; for the smoke test this is the row in `NetmorphParOptim/smoke_samples4.xlsx`, whose `orig_sample_index` column maps back to the 700-sample sheet).
Written by `save_viz_data()` in `gen_autonm_labels.py` when run with `-vizdir`. Sources: NES `GetConnectome`, `GetAbstractConnectome(Sparse=True)`, `GetSomaPositions`.

```
{
  "schema_version": 1,
  "run_id": int,
  "regions": { "<region name>": [neuron ids] },          // from GetAbstractConnectome Regions
  "neurons": [
    { "id": int,                       // neuron index, 0..N-1 (same index space as pre/post below)
      "soma_type": 0|1|2,              // 0 unknown, 1 principal (pyramidal), 2 interneuron
      "soma_type_name": "unknown"|"principal"|"interneuron",
      "soma_type_from_positions": int|null,  // raw SomaTypes entry from GetSomaPositions
      "region": string|null,           // region containing the neuron
      "x": float, "y": float, "z": float,   // soma centre in um (SomaCenters)
      "soma_radius": float|null          // um
    } ],
  "connections": [                     // one entry per (pre, post, type), parallel synapses aggregated
    { "pre": int, "post": int,
      "type": 1|2|3, "type_name": "AMPA"|"GABA"|"NMDA",   // ConnectionTypes: 1 AMPA, 2 GABA, 3 NMDA, 0 unknown
      "num_receptors": int,            // number of physical synapses/receptors (NumReceptors, summed)
      "g_peak_sum": float,             // summed peak conductance in nS (ConnectionGPeakSum, summed)
      "weight_sum": float } ],         // summed ConnectionWeights
  "abstract_pair_receptors": [         // GetAbstractConnectome sparse list: receptors per ordered pair, any type
    { "pre": int, "post": int, "num_receptors": int } ]
}
```

Notes
- Connections are directed pre -> post. A pair can have several entries with different `type` (e.g. AMPA and NMDA from a pyramidal cell).
- `soma_type` uses the abstract connectome `Types` field, falling back to `SomaTypes`. NES derives type from outgoing transmitter, so cells without outgoing connections are reported as 0; by default `gen_autonm_labels.py` infers those as interneurons (type 2; disable with `-KEEPUNKNOWNTYPE`). The raw reported value stays in `soma_type_from_positions`.
- Only one region (`In`) exists in Netmorph samples; all neurons are in it.

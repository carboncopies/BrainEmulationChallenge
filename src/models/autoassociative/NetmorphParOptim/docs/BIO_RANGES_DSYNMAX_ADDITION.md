# bio_ranges.json: D_synmax additions (2026-11-13)

`bio_ranges.json` is gitignored (`*.json`), and these limits were added to local copies only. Add the four entries below to reproduce them. Source for all four: team, Randal Koene, 2026-11-13. Maxima only, minimum 0 (the interneuron-pair runs used 0.1 um).

```json
{
  "D_synmax.pyramidal.pyramidal":       {"min": 0, "max": 1.5,  "source": "team Randal Koene 2026-11-13"},
  "D_synmax.pyramidal.interneuron":     {"min": 0, "max": 0.15, "source": "team Randal Koene 2026-11-13"},
  "D_synmax.interneuron.pyramidal":     {"min": 0, "max": 0.15, "source": "team Randal Koene 2026-11-13"},
  "D_synmax.interneuron.interneuron":   {"min": 0, "max": 0.15, "source": "team Randal Koene 2026-11-13"}
}
```

Adapt the key layout to the existing structure of the file if it differs. Units: um.

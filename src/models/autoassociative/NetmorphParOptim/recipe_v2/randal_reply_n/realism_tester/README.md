# Realism tester

The realism tester is a reusable command-line app that runs the realism checks Randal proposed (spec saved verbatim in `RANDAL_SPEC.md`) on any grown model. It compares the results with a tissue profile and writes a browser report. It reads model files only. It uses no NES API and runs no simulation.

```
python3 realism_tester.py --model <path-or-id> [--model ...] --profile ca3 --out report/<name>
```

- `--model` takes any of:
  - a NetMorph output folder (`*_net.txt.neurons`, node files, `.synapses`, `.nibr.clp`);
  - a converted NES model file (the saved model under `.../Admonishing/Models/`);
  - an id resolved through `roots.json`: an alias such as `s66666`, a NetMorph uuid, or an NES model name.

  You can repeat `--model`; the report then has a model selector.
- `--format auto|netmorph|nes`: `auto` detects the format, a folder with `*_net.txt.neurons` means NetMorph, and a file with a valid NES saver header means NES. For an alias that has both forms, `auto` picks NetMorph.
- `--profile ca3 | drosophila_mushroom_body | v1 | path/to/profile.json`
- `--name LABEL` (one per `--model`) labels each model in the report.
- `--voxel 20` sets the heat-map voxel size in µm.
- `--region disc:cx,cy,cz,R,T` or `--region-from <NetMorph folder>` sets the model volume and centre. NES files carry no region geometry, so without this option the convex hull of the somata is used.
- `--cell-types FILE|NETMORPH_DIR` supplies type names. NES files do not store them, so by default they are inferred from the outgoing receptor type.
- `--no-one-axon-rule` turns off a rule for NES input only: by default, synapse-free neurite trees of a cell whose axon is already known count as dendrite.
- `--volume-um3 V` sets the model volume directly.

Requirements: Python 3 with numpy, plus scipy only for the convex-hull fallback. No pandas, no network. Tests: `python3 -m unittest discover -s tests -v`; there are 13 tests on a tiny synthetic model, and they also round-trip a synthetic NetMorph folder and a synthetic NES binary.

## Outputs (in `--out`)
| file | content |
|---|---|
| `report.html` | Self-contained page that opens from disk, with no server, no CDN and data embedded. Tabs: checks vs literature (status, evidence, reference, tissue, comments); 3D heat map (grid selector; log/linear scale; XY, XZ and YZ slices with sliders, starting at the region centre; region zoom; max projection; rotatable 3D voxel view); radial profile (axon ball plot plus ball-index table); all metrics (n, mean, median, SD, min, p10, p90, max); model metadata and notes. Hash links `#tab=heat&model=1` open a given view. |
| `results.json` | Every metric with all statistics, every literature comparison with its status, and the model metadata. |
| `summary.txt` | Plain-text table of the literature comparisons. |
| `grids/<model>/*.npy`, `grids.json` | Full-precision float32 grids (nx, ny, nz) with their origin, voxel size and units. There are length densities per kind × type, soma and synapse densities, and, for NES input, volume fractions. |
| `radial.json` | Radial profiles (column and slab) and ball indices. |

## Checks (Randal's list → metric ids)
Every metric is a distribution over cells or pairs. The report shows the mean and the median, plus n, SD, min, max, p10 and p90.
| Randal's check | metric id(s) |
|---|---|
| proportions of cell types | `proportion.<T>` |
| cells per volume | `cells_per_volume` (volume: region, `--region`, or soma convex hull; the source is stated) |
| density per cell type | `cells_per_volume.<T>` |
| total dendrite / axon length per cell | `length.dendrite.<T>`, `length.axon.<T>` (sum of all segments) |
| average and max spherical range | `reach_max.<K>.<T>` (farthest arbor point from the soma centre, per cell: the mean and median over cells, and the max over cells); `reach_mean.<K>.<T>` (length-weighted mean distance) |
| target cells per type and per target type | `targets.<T>`, `targets.<T>.to.<U>` (distinct cells; autapses excluded and counted separately in `autapses.<T>`) |
| source cells per type and per source type | `sources.<T>`, `sources.<T>.from.<U>` |
| synapses on axons and dendrites per type | `syn_axon.<T>[.to.<U>]` (contacts made), `syn_dendrite.<T>[.from.<U>]` (contacts received) |
| (extra) connection probability, contacts per pair | `conn_prob.<T>.to.<U>`, `syn_per_pair.<T>.to.<U>` |
| 3D heat map of axon and dendrite density | grids `<K>_length.<T>` (km/mm³ = µm/µm³), `<K>_volfrac.<T>` (when radii exist), `soma.*`, `synapse.all`; radial profile and `ball_index.<K>.<T>` = slab density at r < R/3 ÷ density at 2R/3 ≤ r < R |

Contacts: one per synapse, i.e. one per AMPA or GABA record. NMDA records duplicate an AMPA contact and are skipped.

## Profiles: how to add one, and how to add literature numbers
A profile is a JSON file in `profiles/`. Copy a stub (`v1.json`, `drosophila_mushroom_body.json`) and fill it in:
```json
{"name": "my_tissue", "description": "...", "species": "...", "tissue": "...",
 "type_map": {"excitatory": "pyramidal", "inhibitory": "interneuron"},
 "defaults": {"tolerance_rel": 0.5, "sd_k": 2.0},
 "comments": {"length.axon": "shown next to every length.axon.* check"},
 "literature": [
  {"metric": "length.dendrite.pyramidal", "stat": "mean", "value": 12481, "sd": 2999, "range": null, "unit": "um",
   "reference": "full citation + doi/PMC", "source_tissue": "rat CA3 pyramidal, slice", "evidence": "READ (abstract) | DERIVED | RECALLED | ...",
   "verified": false, "derived_estimate": false, "comparable": true, "comment": "optional"}]}
```
- `type_map` maps the model's type names to the profile's names. Several model types may not map to one profile type.
- `metric` uses the ids above, with profile type names. You can give several entries per metric, for example from different sources or tissues; each gets its own status row.
- Give `range: [lo, hi]` (either end may be `null`), or `value` with `sd`, or `value` alone. Leave both `value` and `range` null for a TODO entry, which shows as **unknown**.
- Mark `verified: true` only after checking the number in the original paper. Set `derived_estimate: true` when the number is your own derivation, or comes from a similar tissue or a model rather than a direct measurement. Set `comparable: false` when the quantity is not like for like (for example a whole-cell axon against a local patch); it is then shown as **info**.
- **Status rules:**
  - **pass**: inside the range, or within `sd_k`·SD of the value, or within ±`tolerance_rel` of a single value.
  - **flag**: outside.
  - **unknown**: no literature number.
  - **n/a**: the model has no such metric.

The `ca3` profile holds 33 entries copied from `../CA3_MORPH_COMPARE.md` and `../../CA3_NATURAL_RANGES.md`, with their own evidence tags. **All are `verified: false`**, because those notes say the numbers were seen through snippets or summarising fetches, not the papers. The ball-index range (0.5–2) is my own expectation for uniform neuropil, not literature.

## Demos (s66666 and s77777, 2026-11-24)
- `report/demo_netmorph/`: NetMorph input, both models, one report.
- `report/demo_nes/`: the converted NES model files, both models, with `--region disc:0,0,-300,120,30`.

Verification done:
1. **Cross-validation with earlier scripts:** the s66666 per-type means (lengths, reach) equal `../morph_e4.json` exactly; for example, pyramidal dendrite 27,162 µm and reach 702.8 µm, interneuron axon 45,711 µm. The axon centre/rim ratio is of the same order as `../morph_check.json` (about 1,150–1,400, with different bins).
2. **NES input against NetMorph input** (same region): all 57 metrics are identical for s66666 (0 differences). Per-cell axon and dendrite lengths agree to 0.00 µm, and the contact matrices are identical (13,108 contacts).
3. **Grid conservation:** the deposited length equals the segment length (`grids.json` → `length_check_um`).
4. **Report page:** `node --check` passes on the embedded script. Headless Firefox screenshots of the checks, heat-map, radial and model tabs render, with no external requests.
5. **Read-only:** model file timestamps are unchanged (2026-11-19).

What the demos show (CA3 profile; s66666 and s77777 give the same pattern; 10 pass, 15 flag, 3 unknown, 5 info):
- **Axon ball:**
  - Axon length density is about 40 km/mm³ in the central 10 µm and about 0.01 at the rim, giving a ball index of about 2,500–5,400. The heat map and radial plot show it directly.
  - Dendrites are nearly uniform (ball index about 1.3–1.6).
  - Max axon reach is 122–144 µm, against a derived 390–870 µm for basket cells.
- **Connectivity is far too dense** (connection probabilities 0.29–0.64 against 0.10–0.25 in the Ecker model and < 1% measured for CA3 PC→PC). Contacts per connected pair are within 1–10.
- **Lengths:**
  - Interneuron axon length (about 45.7k µm on both models) is inside the slice/SWC range.
  - Pyramidal dendrite length (s66666: mean 27.2k, median 21.7k µm; s77777: 27.9k, 19.8k) is 1.3–3.0× the Ishizuka values. It is heavy-tailed: the longest cell has 155k µm (s66666) and 221k µm (s77777).
- **Interneuron fraction** is 17% against 7–15%.

## Limits
- **NES input:**
  - The converted model files store every neurite cylinder twice, and the dendrite and axon compartment lists are identical copies that both mix axon and dendrite. The tester uses one copy and infers axon or dendrite per neurite tree from synapse roles, plus the one-axon-per-cell rule. It agreed exactly with NetMorph on s66666/s77777, but a tree with no synapses on a cell without an identified axon stays "unclassified".
  - Cell type names are not stored and are inferred from the receptor type, or supplied with `--cell-types`.
  - The struct sizes are those of this x86-64 NES build. `_check_layout` asserts them and will stop with a message if a future build changes them.
- **NetMorph input has no radii,** so no volume fraction is available, only length density.
- **Volume:** without a declared region, cells per volume uses the convex hull of the somata, which underestimates the tissue volume.
- **Literature:** every number is unverified and many come from CA1 or from models. Several CA3 rows are whole-cell quantities that a local patch cannot match (status info). The Drosophila and V1 profiles are empty stubs.
- **Spherical range** is measured from the soma centre (Euclidean), not along the path.
- **Heat map:**
  - Grids are sized to all neurite, so wide arbors make large boxes. The default "region ±3R" view crops the display; the saved grids are full size.
  - Embedded grids are log-quantised to 8 bits (about 4% steps); the `.npy` files are exact.
  - Report size is about 5 MB per model at 20 µm voxels.
- **Scope:** the app reads static structure only. It does not check activity, receptor kinetics, or anything about the NES simulation.
